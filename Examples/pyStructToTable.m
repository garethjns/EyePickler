function [tb, n] = pyStructToTable(struct)

tb = table(struct.TS', [struct.NP0', struct.NP1']);
tb.Properties.VariableNames = {'TS', 'NP'};



