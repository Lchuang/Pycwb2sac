#!/home/lchuang/anaconda/envs/obspy/bin/python
import sys
from Pycwb2sac_lib import *
from obspy.core import Stream

# ---- 01. Ask user for inputs ---------------------------
if len(sys.argv) == 4:
    D_file_name = sys.argv[1]
    Station_file_name = sys.argv[2]
    Output_format = sys.argv[3]
    add_arrivals = "n"
elif len(sys.argv) == 5:
    D_file_name = sys.argv[1]
    Station_file_name = sys.argv[2]
    Output_format = sys.argv[3]
    P_file_name = sys.argv[4]
    add_arrivals = "y"
else:
    print("Please enter three or four variables. i.e. Pycwb2sac <Dfile> "
          "<NSTA.DAT> <output_format SAC:0, Obspy:1> <Pfile(optional)>")
    sys.exit()

print(f'====== converting {D_file_name} =======')

# ---- 02. define file format ------------------------------
D_file_version = {"Vax": 1311, "PC": 1311}
segment_length = 1311
header_length = 15
sta_num_limit = 200

# ---- 03. Read in Station files ---------------------------
station_info_file = open(Station_file_name)
whole_list_reformat = load_station_file(station_info_file)
print(f'- read Station file: {Station_file_name}')

# ---- 04. Read in .D file ----------------------------------
with open(D_file_name) as f:
    D_file_content = np.fromfile(f, dtype=np.int16)
print(f'- read Dfile: {D_file_name}')

# ---- 04-2 Read in .P file (optional) -----------------------
if add_arrivals == "y":
    print(f'- read Pfile: {P_file_name}')
    P_file_content = open(P_file_name)
    reformat_p_file = load_p_file(P_file_content)
else:
    pass

# ---- 05. Analyze and re-organize D file contents ----------
format_flag = check_file_type(D_file_content[0])
print(f'- Dfile {D_file_name} format: {format_flag}')
# ---- Append file to length of length * d
print(f'- processing Dfile: {D_file_name}')
D_file_content_append = append_file(D_file_content, segment_length)
# ---- Slice long data array and make it to a big matrix
Data_matrix = break_file_into_pieces(D_file_content_append, segment_length)
# ---- Trim data matrix base on station number
Data_matrix = trim_data_matrix(Data_matrix, sta_num_limit)
# ---- map blocks
header_one_block = Data_matrix[:, 0:3]
breaking_points = map_blocks(Data_matrix[:, 0:3])

# ---- 06. Process D-file blocks and write to output
obspy_stream = Stream()
for i in range(0, len(breaking_points)):
    # ----- extract data block
    Data_block = Data_matrix[breaking_points[i][0]:breaking_points[i][1], :]
    # ----- re-format header
    Data_header = reformat_data_header(Data_block[0, 0:15])
    # ----- extract trace header by comparing two tables
    trace_header = map_blocks_header(whole_list_reformat, Data_header)
    # ----- output sac format
    if int(Output_format) is 0:
        sac_trace = make_sac_trace(Data_block, trace_header, segment_length - header_length)
        # ----- add phase arrivals
        if add_arrivals == "y":
            sac_trace = add_arrival_to_sac_trace(sac_trace, reformat_p_file)
        # ----- write to sac file
        sac_f_name = f'{trace_header.network}.{trace_header.station}.{trace_header.instrument_type}.' \
            f'{trace_header.channel}.SAC'
        print(f'- write to {sac_f_name}')
        sac_trace.write(sac_f_name)
    # ------ output obspy stream format
    elif int(Output_format) is 1:
        obspy_trace = make_obspy_trace(Data_block, trace_header, segment_length - header_length)
        # ----- add phase arrivals
        if add_arrivals == "y":
            obspy_trace = add_arrival_to_obspy_trace(obspy_trace[0], reformat_p_file)
        obspy_stream += obspy_trace
    else:
        raise AttributeError("Unknown output format")
# ----- write to obspy stream format
if int(Output_format) is 1:
    f_name = f'{obspy_stream[0].stats.starttime}_{obspy_stream[0].stats.endtime}.pk'
    print(f'- write to obspy stream file: {f_name}')
    obspy_stream.write(f_name, format="PICKLE")
