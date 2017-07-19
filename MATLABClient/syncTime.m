function [PTBTime, pyTime, delayTime, matTime] = ...
    syncTime(params)
% Connect to TCP server running on EyeTracker computer and exchange time.
% Requires PsychToolBox.
% Input time should be string
% Outputs are nums

% Prepare connection
t = tcpip(params.TCPAddr, params.TCPPort, 'NetworkRole', 'client');

% Open connection
fopen(t);

% Get GetSecs time
% Python is waiting for 24 characters - it deosn't know length in advance
% and GetSecs lengh can vary
% So, buffer with 24 zeros
t1 = [num2str(GetSecs), '000000000000000000000000'];

% Send PTBTime
fwrite(t, t1)

% Wait for bytes available
disp('Waiting for time sync...') 
d1 = GetSecs;
while t.BytesAvailable==0   
end

% Get pyTime in reply
ti = fread(t, t.BytesAvailable);
% Record the delay
delayTime = GetSecs-d1;

% Tell py to close
% Python is now expecting 100 chars - ie. more than could have been in the
% first buffer. Send more than enough data.
fwrite(t, repmat('1', 1, 101))

% Convert to num
pyTime = str2double(native2unicode(ti'));
PTBTime = str2double(t1);
matTime = now;

% Close down connection
fclose(t);
