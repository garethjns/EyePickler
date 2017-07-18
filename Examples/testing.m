
%% Load and plot gaze data
[tb, n] = pyStructToTable(struct);


% Time going in the correct direction?
plot(tb.TS)

% Gaze moving?
plot(tb.NP)

% Gaze moving with time?
plot(tb.TS, tb.NP)
plot(tb.TS, tb.NP(:,1).*tb.NP(:,2));

lag = 50;
np = tsmovavg(tb.NP, 's', lag, 1);

for nn = 1:100:n 
    clf
    plot(tb.NP(nn:nn+100,1), tb.NP(nn:nn+100,2))
    hold on
    plot(np(nn:nn+100,1), np(nn:nn+100,2))
    axis([-1,1,-1,1])
    drawnow
    input('')
end


%% Time notes

% posix -> datetime
datetime(tb.TS(1), 'ConvertFrom', 'posixtime')

% Clock -> posix
posixtime(datetime(clock));

% Matlab datetime -> posix
posixtime(datetime('now'))


tb.TS2 = datetime(tb.TS, 'ConvertFrom', 'posixtime')

%% Load trial data




%% Epoch gaze data