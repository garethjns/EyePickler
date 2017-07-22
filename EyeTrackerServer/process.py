#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May  8 15:28:39 2017

@author: gareth

Process collected eye data
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
  

#%% Example: Run for surface subscription
# Just process out surface information
# MATLAB import script included in /EyeTracker/MATLABAnalysis/
  
## Params
fn = "15SI"
dPath = "Data/"

eye = et.EyeTracker(fn = dPath+fn)
eye.processSurface()


#%% Example: Run for all subscriptions
# Extract all availale information
# Convert from "tree" JSON to "linear" table columns
# Will require custom MATLAB import script

## Params
fn = "15SI"
dPath = "Data/"

eye = et.EyeTracker(fn = dPath+fn)
eye.processAll(verb=False)

# eye.allToDF(objs=eye.objs[50006:5100])
