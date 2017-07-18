"""
Created on Fri Dec  9 12:08:15 2016

Collect eye gaze data, pickle to disk. Then reload as pandas dataframe and save
as .mat.

@author: gareth
"""

import zmq
from msgpack import loads  
import time
import pandas as pd
import pickle
import scipy.io as scio


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
    if type(subs) (not isinstance(subs, list)):
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
    

def gazeToPandasDF(objs, fnOut='processed.mat'):
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
        
        # Report progress
        print str(ts) + ' (' + str(it/n*100) + '%)'
        
        # Note:
        # Base data is dict
        # baseData = msg['base_data']
        # Containg pupil [0] and [1]
        # baseData[0].keys()
        # baseData[1].keys()
        
        # msg['norm_pos']
        
        # Get save norm_pos data and TS
        dRow = pd.DataFrame({'TS': ts, 
                      'NP0' : msg['norm_pos'][0], 
                      'NP1' : msg['norm_pos'][1]},
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
fn = "ClockTest.p"
port = 35453

## Run
sub = connect(port=port, subs='gaze')
runExp(fn, sub)

## End    
objs = unpickle(fn)
df = gazeToPandasDF(objs, 'ClockTest.mat')