function stMap = MappingIdqToFdq(o, dIdq, stt)
    arguments
        o       (1,1)   MotorModel
        dIdq    (1,1)   double
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange
    end

    import Data.MapType

    %% 磁束データ有効性確認
    if ~isKey(o.mData, Data.Type.CoilFluxD)
        error("Not Exist Coil Flux Data.");
    end

    mdt = o.mData(Data.Type.CoilFluxD);
    if isempty(mdt)
        error("Coil Flux Data is Empty");
    end

    nc=o.prmModel.nPrlCoil;

    %% Create Flux Map
    stMap.Axis = [];
    if bitand(stt, Data.MapType.MeanMap) %+Data.MapType.CorrectZero)
        [mData, sRngs, axIdq] = mdt.MappingAvgDQ(dIdq, stt, nc);
        stMap.Map.D = mData(:,:,1);
        stMap.Map.Q = mData(:,:,2);
    else
        [mData, sRngs, axIdq] = mdt.MappingDQ(dIdq, stt, nc);
        stMap.Map.D = squeeze(mData(:, :, 1, :));
        stMap.Map.Q = squeeze(mData(:, :, 2, :));
    end

    stMap.Axis = axIdq;

    stMap.Range = sRngs;

    if bitand(stt, Data.MapType.DivideMIf)
        vIds = axIdq.Id; % vIqs = axIdq.Iq;
        %% 整合性チェック
            % d軸
        fId0 = abs(vIds) < 1.e-6;
        if sum(fId0) ~= 1
            error("Id = 0 Data should be only one[%d]", sum(fId0));
        end
        iId0 = find(fId0, 1);
    
        %% MIf 分離 nId, nth
        maMIf = stMap.Map.D(:, iId0,:); % 平均化一般化のため低次元化しない
        stMap.Map.D = stMap.Map.D - maMIf;
        stMap.Map.MIf = squeeze(maMIf);
        %% 補間結果の最大最小値
        cvRngs = GetRanges({stMap.Map.D, maMIf});
        stMap.Range.D = cvRngs{1};
        stMap.Range.MIf = cvRngs{2};
    end
end

function cvRngs = GetRanges(cvMaps)
    %% 補間結果の最大最小値
        % 時間軸データの場合，各時間毎の最小・最大値の中で，
        % 最小の最大値，最大の最小値が必要
        % 時間軸，平均化によらず，処理を一般化した
        % 平均化データの場合，[fmin(cvMaps{@}), fmax(cvMaps{@})] と一致
    fmin = @(d) min(d, [], "all"); fmax = @(d) max(d, [], "all");
    crs = cellfun( ...
            @(d)arrayfun( ...
                @(i)[fmin(d(:, :, i)), fmax(d(:, :, i))], ...
                1:size(d,3), "UniformOutput", false), ...
            cvMaps, "UniformOutput", false);
    crs = mat2cell(cell2mat(cat(1,crs{:})'), length(crs{1}), [2, 2]);
    cvRngs = cellfun(@(r)[max(r(:,1)), min(r(:,2))], crs, 'UniformOutput', false);
end
