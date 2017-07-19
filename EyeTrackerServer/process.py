#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May  8 15:28:39 2017

@author: gareth

Process collected eye data
"""

#%% Imports

eyeDir = "/home/gareth/Code/SpatialTaskV2/EyeTracker"

import sys
import os

os.chdir(eyeDir)
sys.path.append(eyeDir)

import EyeTracker as et
  

#%% Run 
# clear
  
## Params
fn = "11XY"
dPath = "Data/"


eye = et.eyeTracker(fn = dPath+fn)
eye.process()

