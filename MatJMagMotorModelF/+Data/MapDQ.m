classdef MapDQ < handle
    properties(Im)
    end
    properties(SetAccess = immutable)
        axTime  ( 1, 1) Data.AxisTime
        axMapDQ ( 1, 1) Data.AxisDQ
        mData   ( :, :, 2, :) double = []
    end
    properties(Dependent)
        size
    end


end