classdef MotorModel < handle
    properties(SetAccess = immutable)
        idxDQ       (1, 1)  IndexDQ
        axTime      (1, 1)  AxisTime
        axFreq      (1, 1)  AxisFreq
        axMapDQ     (1, 1)  AxisDQ
        prmModel    ModelParms = ModelParms.empty
        isSlice (1, 1)  logical = false
    end
    properties(Access = public)
        defMap     MapDefinition {mustBeScalarOrEmpty} = MapDefinition.empty
    end
    properties(Access = private)
        mData       (1, 1)  dictionary = dictionary(Data.Type.empty, MagData.empty)
        lData       (1, 1)  dictionary = dictionary(Data.Type.empty, LossData.empty)
        mCaseData   (1, 1)  dictionary = dictionary(Data.Type.empty, MagData.empty)
        lCaseData   (1, 1)  dictionary = dictionary(Data.Type.empty, LossData.empty)
        mCaseIds    (1, 1)  dictionary
    end

    properties(Dependent)
        namMagData
        cMagData
        mMagData
        namLossData
        cLossData
        mLossData

        dMagData        
        dLossData
    end

    methods(Static)
        function avgMap = MeanMap(tMap)
            if ~isstruct(tMap)
                error('Input should be MbdMap Format (struct')
            end
            % if = ~isfield(tMap, "Map") || 
            m = tMap.Map;
            avgMap = [];
            avgMap.Axis = rmfield(tMap.Axis, 'Theta');
            if isnumeric(m)
                avgMap.Map = mean(m(:,:,1:end-1),3);
                avgMap.Range = [min(avgMap.Map, [], 'all'),max(avgMap.Map, [], 'all')];
            else
                avgMap.Map.D = mean(m.D(:,:,1:end-1),3);
                avgMap.Map.Q = mean(m.Q(:,:,1:end-1),3);
                avgMap.Range.D = [min(avgMap.Map.D, [], 'all'),max(avgMap.Map.D, [], 'all')];
                avgMap.Range.Q = [min(avgMap.Map.Q, [], 'all'),max(avgMap.Map.Q, [], 'all')];
            end
            if isfield(tMap, "Ref")
                avgRefMap = MotorModel.MeanMap(tMap.Ref);
                avgMap.Ref = avgRefMap;
            end
        end
    end

    methods(Access = public)
        [sTrqMap, sFluxMap, sMapLdq, sMapLdqS]  = MappingController(o, stt)
        [sTrqMap, sFluxMap] = MappingModel(o, stt)

        [tblMaxTrq0, tblMaxTrqBase, pFitEq] = FitMaxTrqLines(o, sMapTrq, defMap)
        [sTrqMap, sFluxMap] = MappingTrqReq(o, sMapTrq, sMapFdq, sMapIdq, defMap)

        [sTrqToIdq,sMapIdqToFdq] = MappingTrqToIdq(o, stt)
        mTrqToIdIq = MakeReqMapTtoIdq(o, vTrqs, vNrpms, vVlts, rLmtV, dltTrq, dltIdq)

        tMap = MappingIdqToTrq(o, dltIdq, stt)    % Torque Map
        tMap = MappingIdqToFdq(o, dIdq, stt)
        stFIMap = MappingFdqToIdq(o, dIdq, dFdq, stt)
        [sMapLdq, sMapLdqS] = MappingIdqToLdq(o, dIdq, stt)
        
    end

    methods
        function  o = MotorModel(ids, axt, axf, mPrm, defMap, isMs)
            % if nargin < 5
            %     defMap = MapDefinition();
            % end
            if nargin < 6
                isMs = false;
            end
            o.idxDQ  = ids;
            o.axMapDQ = ids.MappedAx();
            o.axTime = axt;
            o.axFreq = axf;
            o.prmModel = mPrm;
            o.isSlice = isMs;
            o.defMap = defMap;
            o.mData = dictionary();
            o.lData = dictionary();
        end
        
        function tgt = pySetTimeDataAtCase(o, name, data, dNames)
            arguments
                o       MotorModel
                name    string
                data    (:, :, :)   double
                dNames  string
            end
            axes = {o.idxDQ, o.axTime};
            % サイズのチェック必要 axesからのサイズとdata
            tgt = MagData(name, axes, data, dNames);
            o.mData(tgt.type) = tgt;
        end
        
        function tgt = pySetFreqDataAtCase(o, name, data, dNames)
            arguments
                o       MotorModel
                name    string
                data    (:, :, :)   double
                dNames  string
            end
            axes = {o.idxDQ, o.axFreq};
            % サイズのチェック必要 axesからのサイズとdata
            % tgt = MagData(name, axes, vertcat(data{:}), o.axTime.num, dNames);
            tgt = LossData(name, axes, data, dNames);
            o.lData(tgt.type) = tgt;
        end

        function tgt = SetCaseTimeDataPy(o, name, ids, data, dNames)
            arguments
                o       MotorModel
                name    string
                ids     cell
                data    cell
                dNames  string
            end
            axes = {o.axMapDQ, o.axTime};
            tgt = MagData(name, axes, vertcat(data{:}), o.axTime.num, dNames);
            o.mData(tgt.type) = tgt;
        end

        function tgt = SetCaseFreqDataPy(o, name, ids, data, dNames)
            arguments
                o       MotorModel
                name    string
                ids     cell
                data    cell
                dNames  string
            end
            axes = {o.axMapDQ, o.axFreq};
            tgt = LossData(name, axes, vertcat(data{:}), o.axFreq.num, dNames);
            o.lData(tgt.type) = tgt;
        end

        function tgt = SetTimeDataPy(o, name, data, dNames)
            arguments
                o       MotorModel
                name    string
                data    cell
                dNames  string
            end
            axes = {o.axMapDQ, o.axTime};
            tgt = MagData(name, axes, vertcat(data{:}), o.axTime.num, dNames);
            o.mData(tgt.type) = tgt;
        end

        function tgt = SetFreqDataPy(o, name, data, dNames)
            arguments
                o       MotorModel
                name    string
                data    cell
                dNames  string
            end
            axes = {o.axMapDQ, o.axFreq};
            tgt = LossData(name, axes, vertcat(data{:}), o.axFreq.num, dNames);
            o.lData(tgt.type) = tgt;
        end

        function vs = getJMagData(o)
            vs = cellfun(@(m) m.mapData, values(o.dMagData,'cell'), 'UniformOutput', false)';
        end

        function names = get.namMagData(o)
            names = keys(o.mData)';
        end
    
        function names = get.namLossData(o)
            names = keys(o.lData)';
        end

        function dat = get.cMagData(o)
            dat = cellfun(@(m) m.mapData, values(o.dMagData,'cell') ...
                                        , 'UniformOutput', false)';
        end
    
        function dat = get.cLossData(o)
            dat = cellfun(@(m) m.mapData, values(o.dLossData,'cell') ...
                                        , 'UniformOutput', false)';
        end

        function dat = get.dMagData(o)
            dat = o.mData;
        end

        function dat = get.dLossData(o)
            dat = o.lData;
        end
    end
end