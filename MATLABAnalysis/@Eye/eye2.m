classdef Eye
    
    properties
        eyePath = ''
        gaze % Table of eyedata
        gazeCorrected % "Corrected"/cleaned version of gaze
        nG % Number of gaze samples
        mTime
        mTime2
    end
    
    methods
        
        function obj = eye(eyePath)
            [obj.gaze, obj.nG] = ...
                loadGaze2(eyePath, ...
                {'TS', 'NP0', 'NP1', 'onSurf', 'mType'});
        end
        
        function obj = fixOffset(obj, trialParams)
            % If data is available
            % Get the MATLAB time and convert it to posix.
            % Calculate the offset between the two
            % Stimlog contains .timeStamp containing times of trials in MATLAB time
            % gaze contains TS in posixtime (and TS2 in readable format)
            % Add a column to gaze with the offset corrected, and converted to MATLAB
            % time
            
            if isfield(trialParams, 'pyTime') ...
                    && isfield(trialParams, 'matTime')
                
                % Convert MATLAB time to posix
                obj.mTime = ...
                    posixtime(datetime(a.params.matTime, ...
                    'ConvertFrom', 'datenum'));
                
                % Undo this to check it's not losing accuracy
                obj.mTime2 = datenum(datetime(obj.mTime, ...
                    'ConvertFrom', 'posixtime'));
                % Keyboard here if it is
                if a.params.matTime~=obj.mTime2
                    keyboard
                end
                
                % Py time is already posix
                pyTime = a.params.pyTime;
                
                % Calculate offset between py and matlab
                offset = obj.mTime - pyTime;
                % Negative = py ahead.
                
            else
                offset = 0;
            end
            
            % Save a new column with pyPosix time + offset
            obj.gaze.TS3 = obj.gaze.TS + offset;
            
            % Check this with readable column similar to TS2
            % Note that datetime shouldn't lose accuracy
            % datenum(TS4) shoud have same percision as TS3
            obj.gaze.TS4 = datetime(obj.gaze.TS3, 'ConvertFrom', 'posixtime');
            % ie:
            % Should be 100%.... almost is
            disp(sum(obj.gaze.TS3 == datenum(posixtime(obj.gaze.TS4))) ...
                / height(obj.gaze))
        end
        
        function obj = PPGaze(obj)
            % Remove empty rows
            nanIdx = all(isnan(...
                [obj.gaze.NP0, obj.gaze.NP1, obj.gaze.onSurf]),2);
            obj.gaze = obj.gaze(~nanIdx,:);
            
            % Convert time
            obj.gaze.TS2 = ...
                datetime(obj.gaze.TS, 'ConvertFrom', 'posixtime');
        end
        
        function plotSurfTime(obj)
            figure
            surfIdx = strcmp(obj.gaze.mType, 'Surf');
            plot(obj.gaze.TS(surfIdx), obj.gaze.onSurf(surfIdx))
        end
        
        function plotGaze(obj, tit)
            % Plot normals ignoring head movement
            eye.plotGazeStat([obj.gaze.NP0, obj.gaze.NP1], ...
                obj.gaze.onSurfED, tit)

        end
        
        function obj = processGaze(obj)
            % Centre space, reduce noise, correct for drift during experiment. Expand
            % surface?
            
            % Steps:
            % Find surface region in gaze
            % Copy gaze to gazeCorrected
            % Limit extreme values of NP
            % Plot (sp 1 of 3)
            % Find and correct for drift. This zeros space.
            % Limit new extreme values
            % Plot (sp 2 and 3 of 3)
            % Shift surface to centre of space
            % Expand square surface by some factor
            % Recalculate onSurf
            % Calcualte "surface" from eculidan distance from [0,0](gazeCorrected.onSurfED)
            % Plot gazeCorrected.onSurf
            % Plot gazeCorrected.onSurfED
            
            % Parameters
            lim = 4; % Extreme value limit
            sExp = 1.5; % Surface expansion factor
            
            GC = obj.gaze;
            GZ = obj.gaze;
            
            % onSurf extent [xMin, xMax, yMin, yMax]
            onSurfEx = [min(GZ.NP0(GZ.onSurf==true)), ...
                max(GZ.NP0(GZ.onSurf==true)), ...
                min(GZ.NP1(GZ.onSurf==true)), ...
                max(GZ.NP1(GZ.onSurf==true))];
            
            % First, cap extreme values
            GC.NP0(GC.NP0>lim) = lim;
            GC.NP0(GC.NP0<-lim) = -lim;
            GC.NP1(GC.NP1>lim) = lim;
            GC.NP1(GC.NP1<-lim) = -lim;
            
            subplot(3,1,1)
            plot([GC.NP0, GC.NP1])
            ylim([-5,5])
            title('Limited gaze')
            
            % Find drift in eye data
            % Does mean eye position drift with time?
            mAvRange = 2000; % pts
            drift.NP0 = tsmovavg(GC.NP0, 's', mAvRange, 1);
            drift.NP1 = tsmovavg(GC.NP1, 's', mAvRange, 1);
            
            % Corret drift in NP0
            GC.NP0(mAvRange+1:end) = ...
                GZ.NP0(mAvRange+1:end) ...
                - drift.NP0(mAvRange+1:end); % Avoid adding NaNs
            % Corret drift in NP1
            GC.NP1(mAvRange+1:end) = ...
                GZ.NP1(mAvRange+1:end) ...
                - drift.NP1(mAvRange+1:end); % Avoid adding NaNs
            
            % Again, limit extreme values
            GC.NP0(GC.NP0>lim) = lim;
            GC.NP0(GC.NP0<-lim) = -lim;
            GC.NP1(GC.NP1>lim) = lim;
            GC.NP1(GC.NP1<-lim) = -lim;
            
            % Finish current figure
            subplot(3,1,2)
            plot([drift.NP0, drift.NP1])
            ylim([-5,5])
            title('Gaze drift')
            
            subplot(3,1,3)
            plot([GC.NP0, GC.NP1])
            ylim([-5,5])
            title('Corrected gaze')
            
            % Space has now been centered around [0,0] (hopefully)
            % Shift surface from eg. [0,1,0,1] to [-0.5,0.5,-0.5,0.5]
            onSurfEx(1:2) = onSurfEx(1:2) - mean(onSurfEx(1:2));
            onSurfEx(3:4) = onSurfEx(3:4) - mean(onSurfEx(3:4));
            % Also expand by some tolerance value
            onSurfEx = onSurfEx*sExp;
            
            % Reclassify onSurf
            GC.onSurf = ...
                GC.NP0>onSurfEx(1) ...
                & GC.NP0<onSurfEx(2) ...
                & GC.NP1>onSurfEx(3) ...
                & GC.NP1<onSurfEx(4);
            
            % Try eculidian distance
            GC.ED = ...
                sqrt(GC.NP0.^2 + GC.NP1.^2);
            EDLim = max(onSurfEx*sExp);
            GC.onSurfED = GC.ED<EDLim;
            
            % Plot onSurf comparison
            Eye.plotGazeStat([GC.NP0, GC.NP1], ...
                GC.onSurf, 'GC')
            
            % Plot onSurf comparison (ED)
            Eye.plotGazeStat([GC.NP0, GC.NP1], ...
                GC.onSurfED, 'GC - ED')
            
            obj.gazeCorrected = GC;
        end
        
        
        
    end
    
    methods (Static)
        function h = plotGazeStat(NPs, onSurf, tit)
            idx = obj.gaze.onSurf;
            h = figure
            title(tit)
            scatter(obj.gaze.NPs(idx,1), obj.gaze.NPs(idx,2))
            hold on
            scatter(obj.gaze.NPs(~idx,1), obj.gaze.NPs(~idx,2))
            axis([-20,20,-20,20])
            xlabel('Norm pos. 0')
            ylabel('Norm pos. 1')
            
        end
    end
    
end