
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
        skewedData(1, 1) dictionary  = dictionary(double.empty, ModelData.empty);
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

        [sDat, sIdqs] = EnableData(o, skId)
        % [sDat, sIdqs] = EnableData(o, skId, isDQ)

        function [cDat, cIdqs] = CellData(o, skId)
            % NaNでないデータのみを抽出
            if isempty(skId)
                tgt = o.data;
                fprintf('>>>>> Normal Data Selected.\n')
            elseif skId>=0 && skId <= numEntries(o.skewedData)
                tgt = o.SkewedData(skId);
                fprintf('>>>>> Skewed Data [%3d] Selected.\n', skId);
            else
                error('Reqested SkewedData Index is Out of Range');
            end

            n = size(tgt, 3);
            cDat = cell(1, n);
            for i = 1:n
                cDat{i} = tgt(:, :, i);
            end
            
            cIdqs = o.idxDQ.DQ';
        end

        function o =SetSkewedDataPy(o, pyIdx, pyData)
            % % da = cellfun(@(d) ModelData(o.axMapDQ , o.type, vertcat(d{:}) ...
            % %                         , o.dShape(2), o.dNames.names) ...
            % %            , pyData, 'UniformOutput', false);
            % da = cellfun(@(d) ModelData(o.idxDQ , o.type, vertcat(d{:}) ...
            %                         , o.dShape(2), o.dNames.names) ...
            %            , pyData, 'UniformOutput', false);
            da=cellfun(@(d) ModelData(o.idxDQ , o.type, d, o.dNames.names), pyData, 'UniformOutput', false);
            o.skewedData=dictionary(cell2mat(pyIdx), da);
        end

        function [tDat, th] = SkewedData(o, idx, isReal)
            if nargin < 3
                isReal = false; % SkewDataが 1/nSkew倍として出力されている
            end
            
            n = numEntries(o.skewedData);
            if n <= 0
                warning('No Skewed Data %4d', n);
                return
            end

            if idx > n || idx < 0
                error('SkewData Indexer should be from 0 to %d', n);
            end
            if idx > 0
                skvs = o.skewedData.keys('cell');
                th = skvs{idx};
                k = 1;
                if isReal
                    k = n;
                end
                tDat = o.skewedData.values{idx};
                % sz = size(tgt.data);
                % fprintf(">>>> [No.%2d] (%11.6g deg.) SkewData(%3d, %3d) k:%g\n", idx, th, sz(1), sz(2), k)
                % if o.type == Data.Type.IronLossD || o.type == Data.Type.HysLossD
                %     tDat = cellfun(@(d) OnlyFirstData(d) * k, o.skewedData.values{idx}.data, "UniformOutput", false);
                % else
                %     tDat = cellfun(@(d) d * k, o.skewedData.values{idx}.data, "UniformOutput", false);
                % end
            else
                if isReal
                    fcn = @sum;
                else
                    fcn = @mean;
                end

                fprintf(">>>> Averaged SkewData (%s) \n", char(fcn))
                th  = 0;
                d0 = cellfun(@(d) d.data, o.skewedData.values, 'UniformOutput', false);
                cds=cat(4,d0{:});
                tDat = fcn(cds,4);
                % 
                % d1 = cat(3,d0{:});
                % d2 = cellfun(@(d) o.ExtNaN(d), d1, 'UniformOutput', false);
                % d3 = cell2mat(d2);
                % d4  = fcn(d3,3);
                % dsz = o.dShape; msz = o.axMapDQ.size;
                % d5  = mat2cell(d4, repmat(dsz(1),1,msz(1)), repmat(dsz(2),1,msz(2)));
                % if o.type == Data.Type.IronLossD || o.type == Data.Type.HysLossD
                %     tDat = cellfun(@(d) OnlyFirstData(o.MonoNan(d)), d5, "UniformOutput", false);
                % else
                %     tDat = cellfun(@(d) o.MonoNan(d), d5, "UniformOutput", false);
                % end
            end
        end

        function [dMapPy, th] = SkewedDataToPy(o, idx, isReal)
            if nargin < 3
                isReal = false;
            end
            [dMap, th] = o.SkewedData(idx, isReal);
            msz = o.axMapDQ.size;
            dMapPy = mat2cell(dMap, ones(1,msz(1)), msz(2))';
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