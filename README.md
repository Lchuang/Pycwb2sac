## Pycwb2sac
Pycwb2sac is a python version of Cwb2sac which convers CWB .D files to either SAC or Obspy Stream format  
Written by Lindsay Chuang @ June 24, 2019  
Please contact author by kanglianan@gmail.com if there is any question  

### To run this program, please make sure you have these packages installed:
1. Python 3  
2. Obspy  

### Before execute the code, please 
Modify the first line of Pycwb2sac.py and change it to where your python path is. i.e.  

Change it from   
#!/Users/anaconda/envs/obspy/bin/python  
to    
#!/Linda/anaconda/envs/obspy/bin/python  

### Run the script and input three or four(optional) parameters in this order:  
Pycwb2sac <Dfile> <NSTA.DAT> <output_format SAC:0, Obspy:1> <Pfile(optional)>   

$ ./Pycwb2sac 13010557.d05 NSTA.DAT 0 13010557.p05

Note:   
(1) NSTA.DAT in here is a fixed version from the original one.  
(2) Pfile is optional. If given, the earthquke and station information will be wrote to headers  
(3) All the data files in .D file will be converted regardless if the station is listed in .P file.

