classdef IndexDQ < handle
    properties(SetAccess = immutable)
        D   (1, :) double {mustBeFinite}
        Q   (1, :) double {mustBeFinite}
    end
    properties(Dependent)
        DQ
        range
        len
    end
    methods
        function o = IndexDQ(vdqs)
            %%
            if nargin < 1
                % o = IndexDQ.empty;
                % return
                vdqs = zeros(2,1);
            end
            o.D = vdqs(1, :);
            o.Q = vdqs(2, :);
        end
        
        function axm = MappedAx(o, eps)
            if nargin < 2
                eps = 0.001;
            end
            % ids = sort(uniquetol(o.D, eps), 'descend');
            ids = sort(uniquetol(o.D, eps));
            iqs = sort(uniquetol(o.Q, eps));
            axm = AxisDQ(ids, iqs);
        end

        function v = get.range(o)
            v = {[min(o.D), max(o.D)], [min(o.Q), max(o.Q)]};
        end

        function v = get.D(o)
            v = o.D;
        end

        function v = get.Q(o)
            v = o.Q;
        end

        function v = get.DQ(o)
            v = {o.D; o.Q};
        end

        function v = get.len(o)
            v = length(o.D);
        end

        
    end
end