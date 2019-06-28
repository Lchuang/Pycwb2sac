import numpy as np
from obspy.core import Trace, Stats, UTCDateTime


def check_file_type(fnum):
    if fnum == 0:
        return "Vax"
    else:
        return "PC"


def append_file(d_file_content, segment_length):
    remainder = int(len(d_file_content) % segment_length)
    if remainder == 0:
        d_file_content_append = d_file_content
    else:
        d_file_content_append = np.append(d_file_content, np.zeros((1, segment_length-remainder), dtype=int))

    return d_file_content_append


def break_file_into_pieces(d_file_content_append, file_length):
    segment_number = int(len(d_file_content_append)/file_length)
    data_matrix = d_file_content_append.reshape(segment_number, file_length)
    return data_matrix


def trim_data_matrix(data_matrix, sta_num_limit):
    station_ids = data_matrix[:, 1]
    remove_row_index = np.argwhere(station_ids > sta_num_limit)
    return np.delete(data_matrix, remove_row_index, 0)


def map_blocks(header_one_block):
    breaking_points = []
    b_position = 0
    for i in range(header_one_block.shape[0]-1):
        break_flag = np.array_equal(header_one_block[i, 0:3], header_one_block[i+1, 0:3])
        if break_flag is False:
            e_position = i
            breaking_points.append((b_position, e_position))
            b_position = i+1
    return breaking_points


def load_station_file(station_info_file):
    whole_list = np.asarray(station_info_file.read().splitlines())
    whole_list_reformat = []
    for i in range(len(whole_list)):
        Station_name = whole_list[i][0:4].strip()
        Station_indx = int(whole_list[i][28:31])
        Station_lats = int(whole_list[i][4:6]) + float(whole_list[i][6:11])/60
        Station_lons = int(whole_list[i][12:15]) + float(whole_list[i][15:20]) / 60
        Station_elev = float(np.char.strip(whole_list[i][21:27]))
        Station_begt = fix_station_op_time(str(whole_list[i][66:72]), 'b')
        Station_endt = fix_station_op_time(str(whole_list[i][73:79]), 'e')
        whole_list_reformat.append({"station": f'{Station_name:s}', "stationid": f'{Station_indx:d}',
                                     "stla": f'{Station_lats:.4f}', "stlo": f'{Station_lons:.4f}',
                                     "stel": f'{Station_elev:.2f}', "stbt": Station_begt, "stet": Station_endt})
    return whole_list_reformat


def fix_station_op_time(station_be_time, be):
    year = int(station_be_time[0:2])
    mont = int(station_be_time[2:4])
    dayt = int(station_be_time[4:6])
    if be == 'e':
        hh = 23
        mm = 59
        ss = 59
    elif be == 'b':
        hh = 0
        mm = 0
        ss = 0
    # ---- fix year mon day
    if year == 0 and mont == 0 and dayt == 0:
        time = UTCDateTime(1900, 1, 1, hh, mm, ss)
    elif year == 99 and mont == 24 and dayt == 31:
        year = year + 2000
        time = UTCDateTime(year, 12, 31, hh, mm, ss)
    elif mont > 12:
        year = year + 2000
        mont = mont - 12
        time = UTCDateTime(year, mont, dayt, hh, mm, ss)
    elif year >= 60:
        year = year + 1900
        time = UTCDateTime(year, mont, dayt, hh, mm, ss)
    else:
        raise AttributeError("Please check station operation time format")
    return time


def reformat_data_header(data_header_block):
    if len(data_header_block) != 15:
        raise AttributeError("data header format error")
    else:
        if len(str(data_header_block[4])) == 2:
            year = data_header_block[4] + 1900
        else:
            year = data_header_block[4]
        stid = int(data_header_block[1])
        stcp = int(data_header_block[2])
        stsp = int(data_header_block[3])
        stin = int(data_header_block[13])
        mont = int(f'{data_header_block[5]:04d}'[0:2])
        dayt = int(f'{data_header_block[5]:04d}'[2:4])
        hour = int(data_header_block[6])
        mins = int(data_header_block[7])
        secs = int(data_header_block[8]) + int(data_header_block[9])/stsp
        time = UTCDateTime(year, mont, dayt, hour, mins, secs)
        if stcp == 1:
            stcptr = "Z"
        elif stcp == 2:
            stcptr = "N"
        elif stcp == 3:
            stcptr = "E"
        else:
            raise AttributeError("component format error")
        if stin == 0:
            instrument_type = "S13"
        elif stin == 1:
            instrument_type = "RTD"
        elif stin == 2:
            instrument_type = "BB_V"
        elif stin == 3:
            instrument_type = "FBA"
        else:
            raise AttributeError("instrument type error")

        data_block_headers = {"stationid": stid, "stationcp": stcp, "sampling_rate": stsp,
                              "starttime": time, "channel": stcptr, "instrument_type": instrument_type}
    return data_block_headers


def map_blocks_header(whole_list_reformat, data_block_headers):
    network = "CWBSN"
    station_id = str(data_block_headers["stationid"])
    event_time = data_block_headers["starttime"]
    channel = data_block_headers["channel"]
    sampling_rate = data_block_headers["sampling_rate"]
    starttime = data_block_headers["starttime"]
    instrument_type = data_block_headers["instrument_type"]
    list_of_single_station = list(filter(lambda staid: staid['stationid'] == station_id, whole_list_reformat))
    list_lt_evt_time = [element for element in list_of_single_station if
                        element['stet'] > event_time and element['stbt'] <= event_time ]
    if len(list_lt_evt_time) != 1:
        raise AttributeError("station operational date ambiguity")
    else:
        station = list_lt_evt_time[0]["station"]
        stla = list_lt_evt_time[0]["stla"]
        stlo = list_lt_evt_time[0]["stlo"]
        stel = list_lt_evt_time[0]["stel"]
        trace_stats = Stats(header={"station": station, "sampling_rate": sampling_rate,
                                    "starttime": starttime, "channel": channel, "network": network,
                                    "stla": stla, "stlo": stlo, "stel": stel, "instrument_type": instrument_type})
    return trace_stats


def make_sac_trace(data_block, sac_header, data_length):
    from obspy.io.sac import SACTrace
    flatten_data = np.concatenate(data_block[..., 15::])
    sac_header.npts = flatten_data.size
    new_trace = Trace(data=flatten_data, header=sac_header)
    sac_trace = SACTrace.from_obspy_trace(new_trace)
    sac_trace.stla = sac_header.stla
    sac_trace.stlo = sac_header.stlo
    sac_trace.stel = sac_header.stel
    if int(new_trace.stats.npts % data_length) is not 0:
        raise AttributeError("data format error!")
    else:
        return sac_trace


def make_obspy_trace(data_block, sac_header, data_length):
    from obspy.core import Stream
    flatten_data = np.concatenate(data_block[..., 15::])
    sac_header.npts = flatten_data.size
    new_trace = Trace(data=flatten_data, header=sac_header)
    if int(new_trace.stats.npts % data_length) is not 0:
        raise AttributeError("data format error!")
    else:
        return Stream(traces=new_trace)


def add_arrival_to_sac_trace(sac_trace, reformat_p_file):
    station = sac_trace.kstnm
    old_reference_time = sac_trace.reftime
    arrival = list(filter(lambda sta: sta['station'] == station, reformat_p_file))
    sac_trace.o = reformat_p_file[0]["o"]
    if arrival:
        sac_trace.t1 = arrival[0]["t1"]
        sac_trace.t2 = arrival[0]["t2"]
        sac_trace.evla = reformat_p_file[0]["evla"]
        sac_trace.evlo = reformat_p_file[0]["evlo"]
        sac_trace.evdp = reformat_p_file[0]["evdp"]
        sac_trace.mag = reformat_p_file[0]["mag"]
    sac_trace.iztype = "io"
    return sac_trace


def add_arrival_to_obspy_trace(obspy_trace, reformat_p_file):
    from obspy.core import Stream
    station = obspy_trace.stats.station
    arrival = list(filter(lambda sta: sta['station'] == station, reformat_p_file))
    obspy_trace.stats.o = reformat_p_file[0]["o"]
    if arrival:
        obspy_trace.stats.t1 = arrival[0]["t1"]
        obspy_trace.stats.t2 = arrival[0]["t2"]
        obspy_trace.stats.evla = reformat_p_file[0]["evla"]
        obspy_trace.stats.evlo = reformat_p_file[0]["evlo"]
        obspy_trace.stats.evdp = reformat_p_file[0]["evdp"]
        obspy_trace.stats.mag = reformat_p_file[0]["mag"]
    return Stream(traces=obspy_trace)


def load_p_file(p_file_content):
    p_file_list = p_file_content.read().splitlines()
    reformat_p_file = []
    evt_dic = reformat_p_file_header(p_file_list[0])
    reformat_p_file.append(evt_dic)
    for i in range(1, len(p_file_list)):
        if int(len(p_file_list[i])) is 75 or int(len(p_file_list[i])) is 83:
            station = p_file_list[i][1:5].strip()
            p_arrival_time = evt_dic["o"] - evt_dic["o"].minute*60 - evt_dic["o"].second - \
                             evt_dic["o"].microsecond/1e6 + float(p_file_list[i][23:29]) + int(p_file_list[i][21:23])*60
            s_arrival_time = evt_dic["o"] - evt_dic["o"].minute*60 - evt_dic["o"].second - \
                             evt_dic["o"].microsecond/1e6 + float(p_file_list[i][39:45]) + int(p_file_list[i][21:23])*60
            if s_arrival_time <= p_arrival_time:
                s_arrival_time = -12345
            reformat_p_file.append({"station": station, "t1": p_arrival_time, "t2": s_arrival_time, "o": evt_dic["o"],
                                    "mag": evt_dic["mag"]})
        else:
            # raise AttributeError("P file arrival time format incorrect")
            print("P file arrival time format incorrect")
    return reformat_p_file


def reformat_p_file_header(p_file_header):
    if int(len(p_file_header)) is 72:
        year = int(p_file_header[1:5])
        mont = int(p_file_header[5:7])
        dayt = int(p_file_header[7:9])
        hour = int(p_file_header[9:11])
        mint = int(p_file_header[11:13])
        secs = float(p_file_header[13:19])
        time = UTCDateTime(year, mont, dayt) + hour * 3600 + mint * 60 + secs
        evla = float(p_file_header[19:21]) + float(p_file_header[21:26]) / 60
        evlo = float(p_file_header[26:29]) + float(p_file_header[29:34]) / 60
        evdp = float(p_file_header[34:40])
        magn = float(p_file_header[40:44])
        evgp = int(p_file_header[51:54])
        evrm = float(p_file_header[54:58])
        errh = float(p_file_header[58:62])
        errz = float(p_file_header[62:66])
        evt_info = {"station": None, "o":time, "evla": evla, "evlo": evlo, "evdp": evdp, "mag": magn,
                    "evrms": evrm, "everror_h": errh, "evrror_z": errz}
    elif int(len(p_file_header)) is 70:
        year = int(p_file_header[1:3]) + 1900
        mont = int(p_file_header[3:5])
        dayt = int(p_file_header[5:7])
        hour = int(p_file_header[7:9])
        mint = int(p_file_header[9:11])
        secs = float(p_file_header[11:17])
        time = UTCDateTime(year, mont, dayt) + hour * 3600 + mint * 60 + secs
        evla = float(p_file_header[17:19]) + float(p_file_header[19:24]) / 60
        evlo = float(p_file_header[24:27]) + float(p_file_header[27:32]) / 60
        evdp = float(p_file_header[32:38])
        magn = float(p_file_header[38:42])
        evgp = int(p_file_header[49:52])
        evrm = float(p_file_header[52:56])
        errh = float(p_file_header[56:60])
        errz = float(p_file_header[60:64])
        evt_info = {"station": None, "o":time, "evla": evla, "evlo": evlo, "evdp": evdp, "mag": magn,
                    "evrms": evrm, "everror_h": errh, "evrror_z": errz}
    else:
        raise AttributeError("p file header format incorrect")
    return evt_info