#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:40:09 2017

Collect gaze and surface data


@author: gareth
"""


import zmq
from msgpack import loads  
import time
import pandas as pd
import pickle
import scipy.io as scio
import numpy as np
import matplotlib.pyplot as plt


def connect(ip='127.0.0.1', port='35453', subs=['gaze', 'pupil.0']):
    # Connect and subscribe to requested messages
    
    # Create ZMQ object
    context = zmq.Context()
    
    # Open REQ Port
    ip = str(ip)
    port = str(port)
    adrStr = "tcp://%s:%s" %(ip, port)
    
    print 'Attempting to connect to:', adrStr
    req = context.socket(zmq.REQ)
    req.connect(adrStr)
    
    # Ask for the sub port
    print '   Requesting sub port'
    req.send_string('SUB_PORT')
    subPort = req.recv(0)
    
    # open a sub port to listen to pupil
    print '   Connecting to sub port:', subPort
    sub = context.socket(zmq.SUB)
    sub.connect("tcp://%s:%s" %(ip, int(subPort)))
    print 'Connected'
    
    # Subscribe to messages
    if not isinstance(subs, list):
        subs=[subs]
    for msgs in subs:
        sub.setsockopt(zmq.SUBSCRIBE, msgs)
        print 'Subscribed to', msgs
        
    return(sub)
    
    
def runExp(fn, sub):
    # Run collection of eye data and pickle to disk
    # Adds time.time() timestamp, no other processing
    # Stop with ABORT    

    # Open a pickle file to write to
    f = open(fn,"wb")
    
    # Run until abort
    print 'Running collection:'
    try:
        while True: 
            # Do minimal processing while collecting
            
            # Get message
            topic,msg =  sub.recv_multipart()
            
            # Convert to dict and add timestamp
            t = time.time()
            msg = {'TS':t, 'msg':msg}

            # Dump to pickle file
            pickle.dump(msg, f)
            print "Collected at " + str(t)
            
    except: # Catch abort
        print 'Stopped' 
        
        # Close open file    
        f.close()      

    
def unpickle(fn):
    # Reload pickled data and return in list
    
    # Reopen to read
    f = open(fn, 'rb')    
    
    # Loop to load and tabulate saved data
    # Continue until EOF Error
    pickle.load(f) 
    objs = []
    while True:
        try:
            # OK for now, maybe update for performance later
            objs.append(pickle.load(f))
        except EOFError:
            break
  
    return(objs)
    

def surfaceToPandasDF(objs, surfs = ['Target'], fnOut='processed.mat'):
    # Convert objs containg gaze information to pandas dataframe and 
    # save a .mat version to disk
    # (Might be better to skip conversion to df as scio.savemat saves dicts)
    
    # Get n and track its for reporting
    n = len(objs)
    it = 0.0
    # Prepare df (df.append perf ok?)
    df = pd.DataFrame()
    
    # For each message, process JSON, append as row to df
    for data in objs:
        it+=1
        
        # Extract time stamp
        ts = data['TS']
        # Process message
        msg = loads(data['msg'])
        
        # Find requested surfaces in msg
        # (Just 1 for now)
        filtSurf = msg
        # Get gaze data - may be more than one entry
        gaze = filtSurf['gaze_on_srf']
        gd = {'NP':[], 'on':[]}
        for subGaze in gaze:
            gd['NP'].append(subGaze['norm_pos'])
            gd['on'].append(subGaze['on_srf'])
            # print subGaze['topic'], subGaze['on_srf']

        # Average available data
        # 'on_srf'
        # Here no data returns NaN
        onSurf = np.mean(gd['on'])
        
        # 'norm_pos'
        # Works for now, but needs updating
        # Need to handle mean on [x,y]
        # Need to handle mean on []
        try:
            NP = np.mean(gd['NP'], axis=0)
            if isinstance(NP, np.float64):
                NP = [0,0]
        except:
            NP = [0,0]
        
        # Report progress
        print str(ts) + ' (' + str(it/n*100) + '%)'
        
       
        # Get save norm_pos data and TS
        dRow = pd.DataFrame({'TS': ts, 
                      'onSurf' : onSurf,
                      'NP0' : NP[0],
                      'NP1' : NP[1]},
                       index = [int(it)])
        # Append to df
        df = df.append(dRow)
        
    # Save as .mat
    # Can't save pandas df directly, so convert to dict to be saved as 
    # structure    
    dv = {col : df[col].values for col in df.columns.values}    
    scio.savemat(fnOut, {'struct': dv})
    
    return(df)
    
    
## Params
fn = "SurfaceTest3.p"
port = 43191

## Run
sub = connect(port=port, subs='surface')
runExp(fn, sub)

## End    
objs = unpickle(fn)
df = surfaceToPandasDF(objs, fn+'.mat')

## Plots
# Logical on surface plot
plt.plot(df['onSurf'])
plt.show()

# Scatter norm_pos data, color read when on target surface
plt.figure(figsize=(10,10))
plt.scatter(df['NP0'][df['onSurf']==1], df['NP1'][df['onSurf']==1], c='r')
plt.scatter(df['NP0'][df['onSurf']==0], df['NP1'][df['onSurf']==0], c='b')
	
