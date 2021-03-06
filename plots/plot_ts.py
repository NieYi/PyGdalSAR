#!/usr/bin/env python2
# -*- coding: utf-8 -*-
############################################
#
# PyGdalSAR: An InSAR post-processing package 
# written in Python-Gdal
#
############################################
# Author        : Simon DAOUT (Oxford)
############################################

"""\
plot_ts.py
-------------
Plot a time series file (cube in binary format) 

Usage: clean_ts.py --infile=<path> [--vmin=<value>] [--vmax=<value>] [--lectfile=<path>] [--imref=<value>] \
[--list_images=<path>] [--crop=<values>] 

Options:
-h --help           Show this screen.
--infile PATH       path to time series (depl_cumule)
--lectfile PATH     Path of the lect.in file [default: lect.in]
--imref VALUE       Reference image number [default: 1]
--list_images PATH  Path to image_retuenues file [default: images_retenues]
--crop VALUE        Crop option [default: 0,nlign,0,ncol]
--vmax              Max colorscale [default: 98th percentile]
--vmin              Min colorscale [default: 2th percentile]
"""

# numpy
import numpy as np
from numpy.lib.stride_tricks import as_strided

import os
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from pylab import *

# scipy
import scipy
import scipy.optimize as opt
import scipy.linalg as lst

import docopt
arguments = docopt.docopt(__doc__)
infile = arguments["--infile"]
if arguments["--lectfile"] ==  None:
   lecfile = "lect.in"
else:
   lecfile = arguments["--lectfile"]

if arguments["--imref"] !=  None:
    if arguments["--imref"] < 1:
        print '--imref must be between 1 and Nimages'
    else:
        imref = int(arguments["--imref"]) - 1

# read lect.in 
ncol, nlign = map(int, open(lecfile).readline().split(None, 2)[0:2])

if arguments["--crop"] ==  None:
    crop = [0,nlign,0,ncol]
else:
    crop = map(float,arguments["--crop"].replace(',',' ').split())
ibeg,iend,jbeg,jend = int(crop[0]),int(crop[1]),int(crop[2]),int(crop[3])

if arguments["--list_images"] ==  None:
    listim = "images_retenues"
else:
    listim = arguments["--list_images"]

nb,idates,dates,base=np.loadtxt(listim, comments='#', usecols=(0,1,3,5), unpack=True,dtype='i,i,f,f')
N=len(dates)
print 'Number images: ', N

# lect cube
cubei = np.fromfile(infile,dtype=np.float32)
cube = as_strided(cubei[:nlign*ncol*N])
kk = np.flatnonzero(np.logical_or(cube==9990, cube==9999))
cube[kk] = float('NaN')

_cube=np.copy(cube)
_cube[cube==0] = np.float('NaN')
print 'Number of line in the cube: ', cube.shape
maps = cube.reshape((nlign,ncol,N))
print 'Reshape cube: ', maps.shape
if arguments["--imref"] !=  None:
    cst = np.copy(maps[:,:,imref])
    for l in xrange((N)):
        maps[:,:,l] = maps[:,:,l] - cst
        if l != imref:
            index = np.nonzero(maps[:,:,l]==0.0)
            maps[:,:,l][index] = np.float('NaN')


if arguments["--vmax"] ==  None:
    vmax = np.nanpercentile(maps, 98)*4.4563
else:
    vmax = np.float(arguments["--vmax"])

if arguments["--vmin"] ==  None:
    vmin = np.nanpercentile(maps, 2)*4.4563 
else:
    vmin = np.float(arguments["--vmin"])


# plot diplacements maps
fig = plt.figure(1,figsize=(14,10))
fig.subplots_adjust(wspace=0.001)

# vmax = np.abs([np.nanmedian(maps[:,:,-1]) + 1.*np.nanstd(maps[:,:,-1]),\
#     np.nanmedian(maps[:,:,-1]) - 1.*np.nanstd(maps[:,:,-1])]).max()
# vmin = -vmax

for l in xrange((N)):
    d = as_strided(maps[ibeg:iend,jbeg:jend,l])*4.4563
    #ax = fig.add_subplot(1,N,l+1)
    ax = fig.add_subplot(4,int(N/4)+1,l+1)
    #cax = ax.imshow(d,cmap=cm.jet,vmax=vmax,vmin=vmin)
    cmap = cm.jet
    cmap.set_bad('white')
    cax = ax.imshow(d,cmap=cm.jet,vmax=vmax,vmin=vmin)
    ax.set_title(idates[l],fontsize=6)
    setp( ax.get_xticklabels(), visible=False)
    setp( ax.get_yticklabels(), visible=False)

setp(ax.get_xticklabels(), visible=False)
setp(ax.get_yticklabels(), visible=False)
fig.tight_layout()
plt.suptitle('Time series maps')
fig.colorbar(cax, orientation='vertical',aspect=10)
fig.savefig('maps_clean.eps', format='EPS',dpi=150)


plt.show()

