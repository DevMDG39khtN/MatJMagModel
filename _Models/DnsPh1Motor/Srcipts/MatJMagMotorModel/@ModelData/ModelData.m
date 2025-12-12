
classdef ModelData < handle

    properties(SetAccess = immutable)
        type    (1, 1)  Data.Type
        idxDQ   (1, 1)  IndexDQ
        dShape  (1, 2)  int32
        dNames  (1, :)  Data.Names
    end
        % axMapDQ (1, 1)  AxisDQ

    properties(SetAccess = public)
        isSlice (1, 1)  logical = true
    end

    properties(Transient)
        mData   double
    end

    properties(SetAccess = protected)
        listener;
    end


    properties(SetAccess = protected, GetAccess = public)
        data (:, :, :) double = double.empty
    end
        % data (:, :) cell = {double.empty}
        % sData(:, :) double = double.empty

    properties(Dependent)
        Range
        mapData
    end

    properties(Constant)
        EvnMapTypeChanged = "MapTypeChanged"
    end

    methods(Static)
        function mType = MapType(mt)
            arguments
                mt  (1,1)  Data.MapType = Data.MapType.MirrorQ
            end
            persistent typ

            typ0 = typ;
            if nargin > 0 && isempty(typ)
                typ = mt;
            end
            mType = typ;

            % if typ0 ~= mType
            %     notify(ModelData, ModelData.EvnMapTypeChanged, mType)
            % end
        end

        cMapDst = ReshapeCell(cMapSrc, mSizes, cOrd)
        axes = MapAxes(rng, div, eps)
    end
    
    methods(Access = protected)
        function m = ExtNaN(o, d)
            if isnan(d)
                m = NaN(o.dShape);
            else
                m = d;
            end
        end

        function m = MonoNan(~, d)
            if all(isnan(d))
                m = NaN;
            else
                m = d;
            end
        end
    end

    methods
        % function o = ModelData(axMapDQ, type, dmap, dNum, dNames)
                % axMapDQ (1,1)   AxisDQ
                % dmap            cell
                % dNum    (1, 1)      uint32
        function o = ModelData(idxDQ, type, tData, dNames)
            arguments
                idxDQ   (1, 1)      IndexDQ
                type    (1, 1)      Data.Type
                tData   (:, :, :)   double %データ数(1 or 3), 時間軸，条件
                dNames              string
            end
            o.idxDQ = idxDQ;
            o.type = type;
            o.dShape = size(tData,1:2); %[length(dNames), dNum];
            o.dNames = dNames;

            % o.axMapDQ = axMapDQ;
            o.data = tData;

            % %% MapTypeが変更されたときに処理をするイベント生成
            % o.listener = addlistener(ModelData, o.EvnMapTypeChanged, ...
            %                 @(src, evt) o.ChangeMapType(src, evt));
        end

        [sDat, sIdqs] = EnableData(o)

        function [cDat, cIdqs] = CellData(o)
            % NaNでないデータのみを抽出
            tgt = o.data;

            n = size(tgt, 3);
            cDat = cell(1, n);
            for i = 1:n
                cDat{i} = tgt(:, :, i);
            end
            
            cIdqs = o.idxDQ.DQ';
        end

        function rng = get.Range(o)
            n = size(o.data,1);
            rng = zeros(n, 2);
            for i = 1:n
                d = squeeze(o.data(i, :, :));
                rng(i, :) = [min(d), max(d)];
            end
        end


        function d = get.data(o)
            d = o.data;
        end

        function md = get.mapData(o)
            md = o.data;
        end

    end
  

end

function d = OnlyFirstData(d)
    if all(isnan(d), "all")
        return
    end
    d = d(:,1)';
end