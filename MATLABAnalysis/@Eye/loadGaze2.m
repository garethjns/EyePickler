function [tb, nR] = loadGaze2(obj)

a = load(obj.eyePath);
struct = a.struct;
clear a

fields = obj.fields;
nF = numel(fields);
nR = size(struct.(fields{1}),2);

mat = NaN(nR, nF);
ca = cell(nR, nF);

% Convert to mat
mc = 0;
cc = 0;
for f = 1:numel(fields)
   
    if isa(struct.(fields{f}), 'double')
        mc = mc+1;
        mat(:,mc) = struct.(fields{f})'; 
    end
    
    if isa(struct.(fields{f}), 'cell')
        cc = cc+1;
        ca(:,cc) = struct.(fields{f})'; 
    end

end
mat = mat(:,1:mc);
ca = ca(:,1:cc);


% Convert to table 
% tb = table(struct.TS', [struct.NP0', struct.NP1'], struct.onSurf');
% tb.Properties.VariableNames = {'TS', 'NP', 'onSurf'};
% tb = table(struct.TS', struct.onSurf');
% tb.Properties.VariableNames = {'TS', 'onSurf'};

tb = array2table(mat);
tb.tmp = ca;
tb.Properties.VariableNames = fields; 
