%% Run time sync

% Set parameters
params.TCPAddr = '128.40.249.99';
params.TCPPort = 52012;

% Run sync
[PTBTime, pyTime, delayTime, matTime] = syncTime(params);
