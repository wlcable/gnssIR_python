# very simple code to pick up all the RH results and make a plot.
# adapted from plot_results.py by Kristine Larson May 2019

# 15 Sept. 2020 William Cable
# Changing script so that all SatNum are plotted with the same color and connected by a line.
# Added the option to plot only a range of azimuths
# no longer doing any averaging
# saving

import argparse
import datetime
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

#used for parsing boolean inputs
def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# where the results are stored
xdir = os.environ['REFL_CODE'] 

# must input start and end year
parser = argparse.ArgumentParser()
parser.add_argument("station", help="station name", type=str)
parser.add_argument("year1", help="first year", type=int)
parser.add_argument("year2", help="end year", type=int)
# optional inputs: filename to output daily RH results 
parser.add_argument("-az_range", help="azimuth range, min max", type=int, nargs=2, default=[0, 360])
parser.add_argument("-show", help='show plot', type=str2bool, default=True)
parser.add_argument("-extension", "--extension", default='', type=str, help="extension for solution names")
args = parser.parse_args()
station = args.station
year1= args.year1
year2= args.year2
az_range = args.az_range
show = args.show
extension = args.extension

# where the summary files will be written to
txtdir = xdir + '/Summary_Files' 

if not os.path.exists(txtdir):
    print('make an output directory', txtdir)
    os.makedirs(txtdir)

# init an array for the indiviual measurements
# year, doy, maxF,sat,UTCtime, Azim, Amp,  eminO, emaxO,  Nv,freq,rise,EdotF, PkNoise  DelT     MJD   refr-appl
# (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10) (11) (12) (13)  (14)     (15)     (16)   (17)
d = []
dat_header=['year', 'doy', 'RH', 'sat', 'time', 'Az', 'amp', 'emin', 'emax', 'Nv', 'frq', 'rise', 'Edot', 'PkN', 'Td', 'MJD', 'refa']

year_list = np.arange(year1,year2 + 1,1)
print('Years to examine: ',year_list)
for yr in year_list:
    if extension == '':
        direc = xdir + '/' + str(yr) + '/results/' + station + '/'
    else:
        direc = xdir + '/' + str(yr) + '/results/' + station + '/' + extension + '/'
    print('loading ', yr, ' data from', direc)
    # check to make sure the directory exists
    if os.path.isdir(direc):
        files = os.listdir(direc)
        for f in files:
            fname = direc + f
            if (len(f) == 7): # file names have 7 characters in them ... 
            # check that it is a file and not a directory and that it has something/anything in it
                try:
                    a = pd.read_csv(fname,comment='%', delimiter='\s+', header=0, names=dat_header)
                    if (len(a) > 0):
                        d.append(a)
                except:
                    print('problem reading ', fname, ' so skipping it')    
        #end files loop, within years
    else:
        print('that directory does not exist - so skipping')
#end years loop
#concatenate all the days
dat = pd.concat(d, axis=0, ignore_index=True)
del d #save some memory :-)
#add a column with the datetime
hrs = dat.time % 24         #just the hours, makes sure hours are 0-24
dat.doy = dat.doy + (dat.time-hrs)/24     #add these extra days to doy, adjusts for overrun in hours
dat.time = hrs
t1 = pd.to_datetime(dat.year*10000+101,format='%Y%m%d') + pd.to_timedelta(dat.doy-1,'d') + pd.to_timedelta(dat.time,'h')
dat.insert(0, 'datetime', t1)
del t1, hrs #cleaning up

#sort based on datetime
dat.sort_values('datetime')

#find all the satellites
satellites = dat.sat.unique()
satellites.sort()

plt.figure(figsize=[14, 8], dpi=100)
#plt.ion()
legend_txt = []
for sat in satellites:
    #select the sat
    id = (dat.sat == sat) & (dat.rise == 1)
    az = dat.Az[id].mean()
    if az_range[0] <= az < az_range[1]:    #check if it is in range
        legend_txt.append('{:3d}, {:3.0f}°'.format(sat,az))
        plt.plot(dat.datetime[id],dat.RH[id],marker='.')

plt.ylabel('Reflector Height (m)')
plt.title('GNSS station: {}:{} Azimuth: {:d}° to {:d}°'.format(station, extension, az_range[0], az_range[1]))
plt.gca().invert_yaxis()
plt.grid()
plt.legend(legend_txt, title=' sat,  az', bbox_to_anchor=(1.0, 1.0), loc=2)
# save the plot to a png file
pltname = '{}/{}-{}_RH_{:d}-{:d}_{:03.0f}-{:03.0f}_{}.png'.format(txtdir, station, extension, year1, year2, az_range[0], az_range[1], datetime.now().strftime("%Y%m%d%H%M%S"))
plt.savefig(pltname)
print('Saved figure to: ' + pltname)
if show:
    plt.show()

