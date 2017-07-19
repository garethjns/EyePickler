# EyePickler

Initial time synchronisation, eye tracker data collection and conversions between separate systems running eye tracking (Linux/Python 2.7) and psychophysical task (Windows/MATLAB).

## Requirements
- [Pupil labs](https://github.com/pupil-labs/pupil) eyetracker and software.
- Python 2.7
- MATLAB (code included), or another TCP client.

# Classes

## EyeTrackerServer
- Creates TCP server for time exchange.
- Connects to PupilLabs ZMQ server to receive live eye tracker data (currently supports surface subscription).
- Pickles eye data to disk.
- Converts .p to .mat.

## MATLAB client
- Connects to TCP server, exchanges current time.

# Running
## Data Collection
1) Launch Pupil Capture, prepare surfaces to track, calibrate etc.
2) Launch eye server in Pupil Capture.
3) Set parameters in EyeTrackerServer/run.py and run, Python will wait for TCP connection.
4) Set parameters in MATLABClient/run.m and run. MATLAB will connect to TCP server and exchange time.
5) If time exchange is successful, Python will continue and connect to Pupil Capture server, data collection (to disk) will start automatically.
6) Stop execution in Python, if processNow==True, conversion to .mat will run automatically.

## Conversion
To convert already collected data to .mat format (for example, if not set to automatically process after collection), see EyeTrackerServer/process.py

# To do
- Add other subscriptions. This can be done in EyeTracker class, conversion methods will also need updating.
- Add live functionality. This requires adding persistent TCP client to EyeTracker that can be monitored by the client. For example, client to check gaze is on surface before starting a trial.

