classdef AxisTime < handle
    properties(SetAccess = immutable)
        times   (1,:)   double
        fa      (1,1)   double
    end

    properties(Dependent)
        theta
        num
        period
    end

    methods
        function o = AxisTime(ts, fa)
            if nargin < 2
                fa = 1;
            end
            if nargin < 1
                ts = [];
            end
            o.times = ts;
            o.fa = fa;
        end

        function v = get.theta(o)
            v = o.times * o.fa * 360;
        end

        function v = get.period(o)
            v = 1 / o.fa;
        end

        function v = get.num(o)
            v = length(o.times);
        end

    end
end