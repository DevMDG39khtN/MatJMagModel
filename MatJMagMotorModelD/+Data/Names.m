classdef Names < handle
    properties(SetAccess = immutable)
        names(1, :) string
        % names {mustBeVector(names, 'allow-all-empties'), mustbeA(names, "string")}
    end

    properties(Dependent)
        num    (1, 1)  uint32
    end

    methods
        function o = Names(names)
            % arguments
            %     names {mustBeVector(names, 'allow-all-empties')}
            % end
            if nargin == 0
                names = string.empty();
            end
            o.names = names;
        end

        function v = get.num(o)
            v = length(o.names);
        end

    end
end