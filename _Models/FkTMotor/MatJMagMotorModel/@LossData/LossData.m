classdef LossData < ModelData
    properties(Constant)
        dicNames = dictionary( ...
             ["鉄損(鉄損条件)", "ヒステリシス損失(鉄損条件)", "ジュール損失(鉄損条件)"] ...
            , [Data.Type.IronLossD,  Data.Type.HysLossD,  Data.Type.EddyLossD] ...
            )
        dicTypes  = dictionary( ...
              ["IronLoss_IronLoss", "HysteresisLoss_IronLoss", "JouleLoss_IronLoss"] ...
            , [Data.Type.IronLossD,  Data.Type.HysLossD,  Data.Type.EddyLossD] ...
            )
        dicTypesR = dictionary( ...
              [Data.Type.IronLossD,  Data.Type.HysLossD,  Data.Type.EddyLossD] ...
            , ["IronLoss_IronLoss", "HysteresisLoss_IronLoss", "JouleLoss_IronLoss"])
    end

    properties(SetAccess = immutable)
        axFreq   (1, 1)  AxisFreq
    end

    methods
        function  o = LossData(name, axes, data, dNames)
            o@ModelData(axes{1}, LossData.dicTypes(name), data, dNames)
            o.axFreq = axes{2};
            % o.type  = o.dicTypes(name);
        end

        function s = SetData(o, data, i)
            try
                o.tDatas(:,:, i) = data;
                s = true;
            catch e
                warning(e.message)
                s = false;
            end
        end

    end
end