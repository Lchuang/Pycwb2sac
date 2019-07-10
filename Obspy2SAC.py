#!/home/lchuang/anaconda/envs/obspy/bin/python
# This python script convert obspy pickle files to single SAC files
from obspy import read
import sys
from obspy.io.sac import SACTrace
from obspy import UTCDateTime


# ---- 01. Ask user for inputs ---------------------------
if len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    print("Please enter one variable i.e. Obspy2SAC 1991-01-01T01:19:46.930000Z_1991-01-01T01:26:02.760000Z.pk")
    sys.exit()

# ---- 02. read in data
Waveforms = read(filename)
for wf in Waveforms:
    sac_trace = SACTrace.from_obspy_trace(wf)
    sac_reftime = sac_trace.reftime
    if "o" in wf.stats and wf.stats.o != UTCDateTime(-12345):
        sac_trace.o = wf.stats.o - sac_reftime
    if "t1" in wf.stats and wf.stats.t1 != UTCDateTime(-12345):
        sac_trace.t1 = wf.stats.t1 - sac_reftime
    if "t2" in wf.stats and wf.stats.t2 != UTCDateTime(-12345):
        sac_trace.t2 = wf.stats.t2 - sac_reftime
    if "evla" in wf.stats:
        sac_trace.evla = wf.stats.evla
    if "evlo" in wf.stats:
        sac_trace.evlo = wf.stats.evlo
    if "evdp" in wf.stats:
        sac_trace.evdp = wf.stats.evdp
    if "stla" in wf.stats:
        sac_trace.stla = wf.stats.stla
    if "stlo" in wf.stats:
        sac_trace.stlo = wf.stats.stlo
    if "stel" in wf.stats:
        sac_trace.stel = wf.stats.stel
    sac_trace.iztype = "io"
    sacfname = f'{wf.stats.network}.{wf.stats.station}.{wf.stats.instrument_type}.{wf.stats.channel}.SAC'
    print(f'- write to {sacfname}')
    sac_trace.write(sacfname)
