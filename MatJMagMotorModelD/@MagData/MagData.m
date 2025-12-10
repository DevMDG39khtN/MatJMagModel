classdef MagData < ModelData
    properties(Constant, Hidden)
        dicNames = dictionary( ...
             ["トルク", "回路の電流", "コイルの鎖交磁束" ...
            , "回路の電圧", "電位差", "FEMコイルのインダクタンス"] ...
            , [Data.Type.TorqueD,  Data.Type.CurrentD,  Data.Type.CoilFluxD ...
            ,  Data.Type.VoltageD, Data.Type.VoltTermD, Data.Type.InductanceD] ...
            )
        dicTypes  = dictionary( ...
              ["Torque", "LineCurrent", "FEMCoilFlux", "TerminalVoltage" ...
            , "VoltageDifference", "FEMCoilInductance"] ...
            , [Data.Type.TorqueD,  Data.Type.CurrentD, Data.Type.CoilFluxD ...
            ,  Data.Type.VoltageD, Data.Type.VoltTermD, Data.Type.InductanceD] ...
            )
        dicTypesR = dictionary( ...
              [Data.Type.TorqueD,  Data.Type.CurrentD, Data.Type.CoilFluxD ...
            ,  Data.Type.VoltageD, Data.Type.VoltTermD, Data.Type.InductanceD] ...
            ,["Torque", "LineCurrent", "FEMCoilFlux", "TerminalVoltage" ...
            , "VoltageDifference", "FEMCoilInductance"])
    end

    properties(SetAccess = immutable)
        axTime   (1, 1) AxisTime
        RangeDQ
        RangeDQs
    end

    events
        onNotifyProcessExceed
    end

    methods(Static)
        [Vdq, Vab, Va] = CnvUVWtoDQ(Va,  th, flag)
        Vab = CnvUVWtoAB(Vuvw)
        [Va, Vab, Vdq] = CnvDQtoUVW(Vdq, th)
        Vab = CnvDQtoAB(Vdq, th)
    end

    methods(Access = protected)
        function OnProcessExceed(o)
            notify(o, 'onNotifyProcessExceed');
        end
    end

    methods(Access = public)
        [map, cRngs, axIdq] = MappingDQ(o, dIdq, stt, nPara)
        [map, cRngs, axIdq] = MappingAvgDQ(o, dIdq, stt, nPara)
    end

    methods
        % function  o = MagData(name, axes, data, dNum, dNames)
        function  o = MagData(name, axes, data, dNames)
            o@ModelData(axes{1}, MagData.dicTypes(name), data, dNames)
            o.axTime = axes{2};
        end

        function s = SetData(o, data, i)
            if size(o.data, 1:2) ~= size(data)
                warning("Sizeが違います")
                s = false;
                return
            end
            o.data(:,:, i) = data;
            s = true;
        end
        % function s = SetData(o, data, i, j)
        %     o.data{i, j} = data;
        %     s = true;
        % end
        
    end
end