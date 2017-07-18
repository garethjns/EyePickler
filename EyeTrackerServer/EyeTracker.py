#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:40:09 2017
Collect gaze and surface data
@author: gareth
"""

#%% Imports

import time       
import numpy as np
import zmq
import socket
import pickle
import pandas as pd
from msgpack import loads 
import scipy.io as scio

        
#%% Prepare

     
class EyeTracker():
    """
    Create connections to TCP and eye tracker. 
    Run through each stage automatically with flags.
    
    Automatic processing uses defualts and saves data to disk and self
    Assumes one surface called target
    
    surfaceToPandasDF fails when trying to deal with anything that's not a 
    surface subscription - needs updating
     - Replaced with surfaceGazeToPandasDF for now but a more flexible 
     implenetation would be useful
    """
    
    def __init__(self, fn='Test.p', ip='127.0.0.1', port='35453', 
                subs=['gaze', 'pupil.0', 'pupil.1', 'surface'], 
                TCPAddr='localhost', TCPPort=52000,
                connectNow=False, startNow=False, processNow=False):

        # Set propeties and/or defaults
        self.ip = ip
        self.port = port
        self.fn = fn
        self.fnOut = fn + '.mat'
        self.connectNow = connectNow
        self.startNow = startNow
        self.processNow = processNow
        self.TCPPort = TCPPort
        self.TCPAddr = TCPAddr
        self.timeSwapRec = np.nan
        self.timeSwapSend = np.nan
        
        if not isinstance(subs, list):
            subs=[subs]

        self.subs = subs
        
        self.creationTime = time.time()
        
        # And attemppt to connect
        if self.connectNow:
            eyeTracker.connect(self)
    

    def connect(self):
        # Connect and subscribe to requested messages
        
        # Create ZMQ object
        context = zmq.Context()
        
        # Open REQ Port
        ip = str(self.ip)
        port = str(self.port)
        adrStr = "tcp://%s:%s" %(ip, port)
        
        print 'Attempting to connect to eye tracker:', adrStr
        req = context.socket(zmq.REQ)
        req.connect(adrStr)
        
        # Ask for the sub port
        print '    Requesting sub port'
        req.send_string('SUB_PORT')
        subPort = req.recv(0)
        
        # open a sub port to listen to pupil
        print '    Connecting to sub port:', subPort
        sub = context.socket(zmq.SUB)
        sub.connect("tcp://%s:%s" %(ip, int(subPort)))
        print '    Connected'
        
        # Subscribe to messages
        
        for msgs in self.subs:
            sub.setsockopt(zmq.SUBSCRIBE, msgs)
            print '    Subscribed to', msgs
        
        self.sub = sub
        
        # Now create TCP server and wait for MATLAB
        eyeTracker.connectTCP(self, addr=self.TCPAddr, port=self.TCPPort)
        
        return(sub)
        
    
    def connectTCP(self, addr='localhost', port=51200):
        
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the port
        server_address = (addr, port)
        print('Starting TCP on ' + str(addr) + ':' + str(port))
        sock.bind(server_address)
        
        try:
            # Wait for a connection
            sock.listen(1)
            print('    Waiting for MATLAB')
            connection, client_address = sock.accept()
            print('    MATLAB connected')
            
            # Expecting buffer of length 24. MATLAB is buffering GetSecs time
            # with 24 zeros
            data = connection.recv(24)
            
            # When MATLAB connects, send time
            t = repr(time.time())
            connection.send(t)
            
            print('    Times swapped')
            self.timeSwapRec = data
            self.timeSwapSend = t
            
            # Wait for an OK for MATLAB - expect length 100 to avoid data 
            # remaining from first buffer
            data = connection.recv(100)
            
            connection.close()
            sock.close()
            print('    TCP closed')
            
            TCPOK=True
        except Exception as ex:
            # Any errors? Attempt close and don't continue
            TCPOK = False
            print('    TCP connection failed:')
            print(str(ex))
            connection.close()
            sock.close()
            
            
        if self.startNow and TCPOK:
                eyeTracker.runExp(self)   
        
                
    def runExp(self):
        # Run collection of eye data and pickle to disk
        # Adds time.time() timestamp, no other processing
        # Stop with ABORT    
        
        self.runExpTime = time.time()
        
        # Open a pickle file to write to
        f = open(self.fn, "wb")
        
        # Run until abort
        print 'Running collection:'
        try:
            while True: 
                # Do minimal processing while collecting
                
                # Get message
                topic,msg = self.sub.recv_multipart(0)
                
                # Convert to dict and add timestamp
                t = time.time()
                msg = {'TS':t, 'msg':msg}
    
                # Dump to pickle file
                pickle.dump(msg, f)
                print "Collected at " + str(t)
                
        except: # Catch abort
            print '    Stopped' 
            
            # Close open file    
            f.close()      
    
        if self.processNow:
            eyeTracker.process(self)
            
            
    def process(self):
        print('Processing')
        eyeTracker.unpickle(self)
        eyeTracker.surfaceGazeToPandasDF(self)
        
        
    def unpickle(self):
        # Reload pickled data and return in list
        
        # Reopen to read
        f = open(self.fn, 'rb')    
        
        # Loop to load and tabulate saved data
        # Continue until EOF Error
        objs = []
        try:
            pickle.load(f) # Fails if empty
            
            while True:
                try:
                    # OK for now, maybe update for performance later
                    objs.append(pickle.load(f))
                except EOFError:
                    print('    Loaded all')
                    break

            
        except:
            print('    Pickle file empty')
      
        
        self.objs = objs    
        return(objs)
                
    
    def surfaceToPandasDF(self, objs=[], surfs = ['Target'], fnOut=''):
        # Convert objs containg gaze information to pandas dataframe and 
        # save a .mat version to disk
        # (Might be better to skip conversion to df as scio.savemat saves dicts)
        
        if len(fnOut)==0:
                fnOut=self.fnOut
            
        if len(objs)==0:
                objs = self.objs
        
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
            onSurf = np.nanmean(gd['on'])
            
            # 'norm_pos'
            # Works for now, but needs updating
            # Need to handle mean on [x,y]
            # Need to handle mean on []
            try:
                NP = np.nanmean(gd['NP'], axis=0)
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
        
        # Also add time data to dv
        dv['timeSwapRec'] = self.timeSwapRec
        dv['timeSwapSend'] = self.timeSwapSend
        dv['creationTime'] = self.creationTime
        dv['fn'] = self.fn 
        dv['subs'] = self.subs
         
        scio.savemat(fnOut, {'struct': dv})
        
        print('    Saved: ' + fnOut)
        self.df = df
        return(df)
        
        
    def surfaceGazeToPandasDF(self, objs=[], surfs = ['Target'], fnOut=''):
        # Convert objs containg gaze information to pandas dataframe and 
        # save a .mat version to disk
        # (Might be better to skip conversion to df as scio.savemat saves dicts)
        
        if len(fnOut)==0:
                fnOut=self.fnOut
            
        if len(objs)==0:
                objs = self.objs
        
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
            
            if 'name' in msg.keys() and msg['name'] in surfs:
                mType = 'Surf'
                # This is a surface message

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
                onSurf = np.nanmean(gd['on'])
                
                # 'norm_pos'
                # Works for now, but needs updating
                # Need to handle mean on [x,y]
                # Need to handle mean on []
                try:
                    NP = np.nanmean(gd['NP'], axis=0)
                    if isinstance(NP, np.float64):
                        NP = [0,0]
                except:
                    NP = [0,0]
            
            if 'topic' in msg.keys() and msg['topic'] == 'gaze':
                mType = 'Gaze'
                # This is a gaze message
                # There are two NPs in here
                # msg['base_data']['norm_pos']
                # ['norm_pos']
                NP = msg['norm_pos']
                onSurf = np.nan

            # Report progress
            print str(ts) + ' (' + str(it/n*100) + '%)'
            
            # Get save norm_pos data and TS
            dRow = pd.DataFrame({'TS': ts, 
                          'onSurf' : onSurf,
                          'NP0' : NP[0],
                          'NP1' : NP[1],
                          'mType' : mType},
                           index = [int(it)])
            # Append to df
            df = df.append(dRow)
            
        # Save as .mat
        # Can't save pandas df directly, so convert to dict to be saved as 
        # structure    
        dv = {col : df[col].values for col in df.columns.values}   
        
        # Also add time data to dv
        dv['timeSwapRec'] = self.timeSwapRec
        dv['timeSwapSend'] = self.timeSwapSend
        dv['creationTime'] = self.creationTime
        dv['fn'] = self.fn 
        dv['subs'] = self.subs
         
        scio.savemat(fnOut, {'struct': dv})
        
        print('    Saved: ' + fnOut)
        self.df = df
        
        return(df)
        