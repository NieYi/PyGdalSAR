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
plot_profile_r4.py
-------------
Plot profiles for r4 files (slope_corr_var, APS_*, DEF_* ...) given a strike, an origin and the size of the profile

Usage: plot_profile_r4.py [--lectfile=<path>] [--demfile=<path>] [--outfile=<path>] \
[--ramp=<None/all/north/south>] [--cst=<value>] --name=<path> --strike=<value> <x0> <y0> <w> <l>
plot_slope.py -h | --help

Options:
-h --help           Show this screen.
--lectfile PATH     Path of the lect.in file [default: lect.in]
--demfile PATH      Path of the dem file [default: lect.in]
--name PATH         Path of the slope file
--outfile PATH      Create a flatten r4 file
--ramp VALUE        flatten profrile to the north (if ramp=north), south (if ramp=north), or all the profile (if ramp=all) [default: None]
--cst VALUE         Shift the displacements by an optional cst [default:0]
--strike VALUE      Azimuth of the profile
--x0,y0 VALUES      Origine of the profile
--w,l VALUES        Width and Length of the profile
"""

# os
import math,sys,getopt
from os import path

# numpy
import numpy as np
from numpy.lib.stride_tricks import as_strided

# plot modules
from pylab import *
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl

# docopt (command line parser)
import docopt

# read arguments
arguments = docopt.docopt(__doc__)
if arguments["--lectfile"] ==  None:
    arguments["--lectfile"] = "lect.in"
if arguments["--demfile"] ==  None:
    plotdem = 'no'
else:
    plotdem = 'yes'
if arguments["--ramp"] ==  'south':
    ramp = 'south'
elif arguments["--ramp"] ==  'north':
    ramp = 'north'
elif arguments["--ramp"] ==  'all':
    ramp = 'all'
else:
    ramp = None
if arguments["--cst"] ==  None:
   cst = 0
else:
   cst = float(arguments["--cst"])

rad2mm = 4.4563

x0 = int(arguments["<x0>"])
y0 = int(arguments["<y0>"])
w = int(arguments["<w>"])
l = int(arguments["<l>"])

infile = arguments["--name"]

# Read number of col, lines from lect.in
lectfile = arguments["--lectfile"]
ncol, nlign = map(int, open(lectfile).readline().split(None, 2)[0:2])

# fault azimuth
str=(float(arguments["--strike"])*math.pi)/180
s=[math.sin(str),math.cos(str),0]
n=[math.cos(str),-math.sin(str),0]

# Load data and convert in mm/yr
los = -np.fromfile(arguments["--name"],np.float32)*rad2mm
# clean los
kk = np.flatnonzero(np.logical_or(los==0, los==9999))
#kk = np.flatnonzero(los>9990)
los[kk] = float('NaN')

if plotdem is 'yes':
    dem = np.fromfile(arguments["--demfile"],np.float32)/1000

# reshape in 2d matrix 
insar = los.reshape((nlign,ncol))
if plotdem is 'yes':
    topo = dem.reshape((nlign,ncol))

insarxx = np.arange(ncol)
insaryy = np.arange(nlign)
insarx, insary = np.meshgrid(insarxx,insaryy,sparse=True)

insarxp=(insarx-x0)*s[0]+(insary-y0)*s[1]
insaryp=(insarx-x0)*n[0]+(insary-y0)*n[1]

insarxp, insaryp = insarxp.flatten(), insaryp.flatten()

# plot profile
ypmin,ypmax = -l/2, +l/2
xpmin,xpmax = -w/2, +w/2
print 'Coordinate profile: '
print 'x: %i, xpmin: %i, xpmax: %i '%(x0,xpmin,xpmax)
print 'y: %i, ypmin: %i, ypmax: %i '%(y0,ypmin,ypmax)

# select data in the profile
index=np.nonzero((abs(insarxp)>w/2)|(abs(insaryp)>l/2))
#print shape(index)
iilos,iix,iiy,iixp,iiyp=np.delete(los,index),np.delete(insarx,index),np.delete(insary,index),np.delete(insarxp,index),np.delete(insaryp,index)
if plotdem is 'yes':
    iitopo = np.delete(topo,index)

# clean profile
index=np.nonzero((np.isnan(iilos)==True))
#print shape(index)
ilos,ix,iy,ixp,iyp=np.delete(iilos,index),np.delete(iix,index),np.delete(iiy,index),np.delete(iixp,index),np.delete(iiyp,index)
if plotdem is 'yes':
    itopo = np.delete(iitopo,index)

# estimate ramp
if ramp is 'north':
    kk = np.nonzero((iyp>0))
elif ramp is 'south':
    kk = np.nonzero((iyp<0))
elif ramp is 'all':
    kk = np.arange(len(iyp))

if ramp is not None:
    temp_los = ilos[kk]
    temp_yp = iyp[kk]
    G=np.zeros((len(temp_los),2))
    G[:,0] = temp_yp
    G[:,1] = 1

    # remove ramp
    pars = np.dot(np.dot(np.linalg.inv(np.dot(G.T,G)),G.T),temp_los)
    a = pars[0]; b = pars[1]
    blos = a*iyp + b - cst
    print 'Remove ramp estimate on the {}: '.format(ramp)
    print '%f yperp  + %f  '%(a,b)
    print
    ilos = ilos - blos

    # remove ramp from all the track
    blos = a*insaryp + b
    los = los - blos - cst

    insar = los.reshape((nlign,ncol))

# save output file
if arguments["--outfile"] ==  None:
     print 'No output file save'
else:
     fid = open(arguments["--outfile"], 'wb')
     sar = -insar
     sar.astype('float32').tofile(fid)
     fid.close()

# get min max
# vmax = np.mean(ilos) + 2*np.nanstd(ilos)
# vmin = np.mean(ilos) - 2*np.nanstd(ilos)
vmax = np.nanpercentile(ilos,99.9)
vmin = np.nanpercentile(ilos,.1)
#vmax=2
#vmin=-3

# plot profile
if plotdem is 'yes':
    bins = np.arange(min(iyp),max(iyp),2)
    inds = np.digitize(iyp,bins)
    distance=[]
    moy_topo=[]
    std_topo=[]
    moy_los= []
    std_los=[]
    for j in range(len(bins)-1):
        uu = np.flatnonzero(inds == j)
        if len(uu)>0:
            distance.append(bins[j] + (bins[j+1] - bins[j])/2.)
            std_los.append(np.std(ilos[uu]))
            moy_los.append(np.mean(ilos[uu]))
            std_topo.append(np.std(itopo[uu]))
            moy_topo.append(np.mean(itopo[uu]))
    distance, moy_topo, std_topo, moy_los, std_los = np.array(distance), np.array(moy_topo), np.array(std_topo), np.array(moy_los), np.array(std_los)
    
    fig = plt.figure(10, figsize=(14,8))
    ax1 = plt.subplot2grid((3,2), (0,0), colspan=2)
    ax1.set_xlim([-l/2,l/2])

    # maxpro = moy_los.max() + 4*np.mean(std_los)
    # minpro = moy_los.min() - 4*np.mean(std_los)

    #ax1.legend(loc=3)
    ax1.set_ylabel('Elevation (km)')
    ax1.set_title('LOS displacements profile')
    ax1.plot(distance,moy_topo,lw=0.5,color='black',label='Average topography (km)')
    ymin,ymax=ax1.get_ylim()
    ax1.plot([0,0],[ymin,ymax],color='red')
    ax1.legend(loc='best',fontsize='x-small')
    
    ax2 = plt.subplot2grid((3,2), (1,0), colspan=2,rowspan=2)
    ax2.set_xlim([-l/2,l/2])
    ax2.set_ylim([vmin,vmax])
    ax2.plot(distance,moy_los-std_los,lw=1,color='gray')
    ax2.plot(distance,moy_los+std_los,lw=1,color='gray')
    ax2.plot(distance,moy_los,lw=2,color='black',label='{}'.format(arguments["--name"]))
    ymin,ymax=ax2.get_ylim()
    ax2.plot([0,0],[ymin,ymax],color='red')
    ax2.legend(loc=3)
    ax2.set_xlabel('distance to the fault')
    ax2.set_ylabel('LOS (Positive toward the Sat., mm)')

else: 
    bins = np.arange(min(iyp),max(iyp),2)
    inds = np.digitize(iyp,bins)
    distance = []
    moy_los= []
    std_los=[]
    for j in range(len(bins)-1):
        uu = np.flatnonzero(inds == j)
        if len(uu)>0:
            distance.append(bins[j] + (bins[j+1] - bins[j])/2.)
            std_los.append(np.std(ilos[uu]))
            moy_los.append(np.mean(ilos[uu]))
    distance, moy_los, std_los = np.array(distance), np.array(moy_los), np.array(std_los)

    # maxpro = moy_los.max() + 4*np.mean(std_los)
    # minpro = moy_los.min() - 4*np.mean(std_los)
    
    fig = plt.figure(10, figsize=(14,6))
    ax1 = plt.subplot2grid((3,2), (0,0), colspan=3,rowspan=2)
    ax1.set_xlim([-l/2,l/2])
    ax1.set_ylim([vmin,vmax])
    ax1.plot(distance,moy_los-std_los,lw=1,color='gray')
    ax1.plot(distance,moy_los+std_los,lw=1,color='gray')
    ax1.plot(distance,moy_los,lw=2,color='black',label='{}'.format(arguments["--name"]))
    ymin,ymax=ax1.get_ylim()
    ax1.plot([0,0],[ymin,ymax],color='red')
    ax1.legend(loc='best',fontsize='x-small')
    ax1.set_xlabel('Distance to the center of the profile (in pixel)')
    ax1.set_ylabel('LOS (Positive toward the Sat., mm)')

name = path.splitext(infile)[0]

# save
fig.savefig(name+'_profile.eps', format='EPS')

# define profile boudaries
xp,yp=np.zeros((7)),np.zeros((7))
xp[:]=x0-w/2*s[0]-l/2*n[0],x0+w/2*s[0]-l/2*n[0],x0+w/2*s[0]+l/2*n[0],x0-w/2*s[0]+l/2*n[0],x0-w/2*s[0]-l/2*n[0],x0-l/2*n[0],x0+l/2*n[0]
yp[:]=y0-w/2*s[1]-l/2*n[1],y0+w/2*s[1]-l/2*n[1],y0+w/2*s[1]+l/2*n[1],y0-w/2*s[1]+l/2*n[1],y0-w/2*s[1]-l/2*n[1],y0-l/2*n[1],y0+l/2*n[1]

fig=plt.figure(1)
# get min max
vmax -= cst
vmin -= cst

# plot map profile
ax2=fig.add_subplot(1,2,2)
#cax2 = ax2.imshow(insar[y0-w:y0+w,x0-w:x0+w],cmap=cm.jet,vmax=vmax,vmin=vmin,extent=None)
cax2 = ax2.imshow(insar,cmap=cm.jet,vmax=vmax,vmin=vmin,extent=None)
#ax2.plot(xp[:],yp[:],color='black',lw=1.)
ax2.legend(loc=3)
setp( ax2.get_xticklabels(), visible=False)
ax2.set_title('Velocity map and profile')
# add colorbar
cbar = fig.colorbar(cax2,fraction=0.3,shrink=.5)

# plot map
ax3=fig.add_subplot(1,2,1)
cax3 = ax3.imshow(insar,cmap=cm.jet,vmax=vmax,vmin=vmin,extent=None)
ax3.plot(xp[:],yp[:],color='black',lw=1.)
ax3.legend(loc=3)
setp( ax3.get_xticklabels(), visible=False)
#ax3.set_title('Velocity Map')

# add colorbar
#cbar = fig.colorbar(cax3)
#cbar = fig.colorbar(cax3,ticks=[-1, 0, 1])
#cbar.ax.set_yticklabels(['< -{}'.format(vmax), '0', '> {}'.format(vmax)])# vertically oriented colorbar


fig.savefig(name+'_map_profile.eps', format='EPS')
plt.show()
