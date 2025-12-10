classdef AxisFreq < handle
    properties(SetAccess = immutable)
        freqs   (1,:)   double
    end

    properties(Dependent)
        num
    end

    methods
        function o = AxisFreq(ts)
            if nargin < 1
                ts = [];
            end
            o.freqs = ts;
        end

        function v = get.num(o)
            v = length(o.freqs);
        end
    
    end
end