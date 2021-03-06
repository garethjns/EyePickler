#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:40:09 2017
Collect gaze and surface data
@author: gareth

Run eye tracker

Connect to eye server
Swap times with MATLAB computer
Collect data. Saved in to eyeDir.

"""

#%% Imports

import sys
import os

# Set to '...EyePickler/EyeTrackerServer/' or navigate and restart console 
# there (then use os.getcwd())
eyeDir = os.getcwd()

# Get EyeTracker class
os.chdir(eyeDir)
sys.path.append(eyeDir)
import EyeTracker as et
  

#%% Run 
# clear
  
## Params
fn = "15SI"
dPath = "Data/"
port = 50020 # Eye tracker server port on localhost
TCPAddr = '128.40.249.99' # Time server address (this computer)
TCPPort = 52012 # Time server port

# Connect, wait, run, process
eye = et.EyeTracker(fn=dPath+fn, port=port, subs=['surface', 'gaze'],
                 TCPAddr=TCPAddr, TCPPort=TCPPort,
                 connectNow=True, startNow=True, processNow=True)


