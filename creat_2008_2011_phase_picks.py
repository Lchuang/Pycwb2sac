#!/Users/lindsaychuang/miniconda3/envs/obspy/bin/python
import pandas as pd
from Pycwb2sac_lib import *
import glob
from geopy.distance import great_circle
input_folder="./CWB_2008_Pfiles/2008_pfile"
output_file="2008_cwb_phase_picks.csv"
Station_file_name="NSTA.DAT"
station_info_file = open(Station_file_name)
whole_list_reformat = load_station_file(station_info_file)

# ---- reformat p file
phase_picks=[]
list_of_folders = glob.glob(f'{input_folder}/*')
for fd in list_of_folders:
    print(fd)
    p_file_list = glob.glob(f'{fd}/*.*08')
    for P_file_name in p_file_list:
        print(P_file_name)
        P_file_content = open(f'{P_file_name}')
        reformat_p_file = load_p_file(P_file_content)
        # ---- get event info
        evt = reformat_p_file[0]
        year = evt["o"].year
        month = evt["o"].month
        day = evt["o"].day
        hour = evt["o"].hour
        minute = evt["o"].minute
        second = evt["o"].second + evt["o"].microsecond/1e6
        evla = evt["evla"]
        evlo = evt["evlo"]
        evdp = evt["evdp"]
        mag = evt["mag"]
        # --- get phase info
        for i in range(1,len(reformat_p_file)):
            stap = reformat_p_file[i]
            station = stap["station"]
            stinfo = list(filter(lambda sta: sta['station'] == station, whole_list_reformat))
            stla = stinfo[0]["stla"]
            stlo = stinfo[0]["stlo"]
            dist = great_circle((stla,stlo),(evla,evlo)).km/111
            if stap["t1"] != -12345:
                p = stap["t1"] - stap["o"]
            else:
                p = "Nan"
            if stap["t2"] != -12345:
                s = stap["t2"] - stap["o"]
            else:
                s = "Nan"
            phase_picks.append({"station": station, "year": year, "month": month, "day": day, "hour": hour,
                                "minute": minute, "second": second, "p_arrival": p, "s_arrival": s,
                                "evla": evla, "evlo": evlo, "evdp": evdp, "mag": mag, "stla": stla,
                                "stlo": stlo, "dist": dist})

pd_files = pd.DataFrame(phase_picks)
cols = ["year", "month", "day", "hour", "minute", "second", "station", "p_arrival", "s_arrival",
        "evla", "evlo", "evdp", "mag", "stla", "stlo", "dist"]
pd_files = pd_files[cols]
pd_files.to_csv("CWB_2008_phase.csv")