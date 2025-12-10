classdef AxisDQ < handle
    % properties
    properties(SetAccess = immutable)
        D   (1, :) double {mustBeFinite}
        Q   (1, :) double {mustBeFinite}
    end
    properties(Dependent)
        DQ
        range
        size
    end
    methods
        function o = AxisDQ(vds, vqs)
            if nargin < 2
                vqs = [];
            end
            if nargin < 1
                vds = [];
            end
            %%
            % 最後の, を無くした文字列
            % ff = @(s) regexprep(sprintf("%4d, ", size(s)), ', $','');
            % 引数のベクトル確認
            % if ~isvector(vds)
            %     error('D-Axis Value shoule be vector [%s]', ff(vds))
            % end
            % if ~isvector(vqs)
            %     error('Q-Axis Value shoule be vector [%s]', ff(vqs))
            % end
            % if size(vds, 1) ~= 1
            %     vds = vds';
            % end
            % if size(vqs, 1) ~= 1
            %     vqs = vqs';
            % end
            %%
            o.D = vds;
            o.Q = vqs;
        end
        
        function [mIds, mIqs] = Mapped(o)
            [mIds, mIqs] = meshgrid(o.D, o.Q);
            if nargout <= 1
                mIds = {mIds, mIqs};
            end
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

        function v = get.size(o)
            v = [length(o.Q), length(o.D)];
        end

        
    end
end