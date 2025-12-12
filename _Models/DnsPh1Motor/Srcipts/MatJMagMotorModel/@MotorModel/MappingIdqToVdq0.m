function [stFdqDvMap, stVtMap, sFdqMap] = MappingIdqToVdq0(o, dIdq, skId, stt)
    arguments
        o       (1,1)   MotorModel
        dIdq    (1,1)   double
        skId    int32   {mustBeScalarOrEmpty}  = []
        stt     (1,1)   int32   = MapType.MirrorQ + MapType.CorrectMean ...
                                + MapType.MinRange
    end

    import Data.MapType

    tDeFlg = Data.MapType.MeanMap + Data.MapType.DivideMIf; % 無効化マップフラグ
    sFdqMap = o.MappingIdqToFdq(dIdq, skId, bitand(stt, bitcmp(tDeFlg)));
    
    th = sFdqMap.Axis.Theta;
    % マップ軸 Iq, Id, th, DQ
    vSz0 = [size(sFdqMap.Map.D), 2];   % 磁束データ Matrixサイズ
    maFdqD  = zeros(vSz0);
    maFdqDT = zeros(vSz0);
    caVas = cell(vSz0(1:2));
    caVts = cell(vSz0(1:2));
    for i = 1:vSz0(1)
        for j = 1:vSz0(2)
            mFd = squeeze(sFdqMap.Map.D(i, j, :))';
            mFq = squeeze(sFdqMap.Map.Q(i, j, :))';
            % mVdq0 = [mFq; -mFd];    % Flux の方向から, JMAGでは，-1
            mFdqD0 = [mFq; -mFd];    % Flux の方向から, JMAGでは，-1
            mFdqD1 = MagData.CnvDQtoUVW(mFdqD0, th); % DQ軸->3相変換
            mVa = FluxToVoltBase(mFdqD1, th) * 360 / (2*pi); % 微分電圧計算
            mVt = mVa - mVa([2, 3, 1], :); % 端子電圧
            maFdqD(i,j,:,:) = MagData.CnvUVWtoDQ(mVa, th)';
            maFdqDT(i,j,:,:) = MagData.CnvUVWtoDQ(mVt, th)';
            caVas{i,j} = mVa;
            caVts{i,j} = mVt;
        end
    end

    fdD = squeeze(maFdqD(:,:,:,1));
    fqD = squeeze(maFdqD(:,:,:,2));

    vdt = squeeze(maFdqDT(:,:,:,1));
    vqt = squeeze(maFdqDT(:,:,:,2));

    axis = sFdqMap.Axis;
    if bitand(stt, Data.MapType.MeanMap) %+Data.MapType.CorrectZero)
        vd0 = fdD;  vq0 = fqD; vdt0 = vdt; vqt0 = vqt;

        fdD = mean(fdD(:, :, 1:end-1), 3);
        fqD = mean(fqD(:, :, 1:end-1), 3);
        vdt = mean(vdt(:, :, 1:end-1), 3);
        vqt = mean(vqt(:, :, 1:end-1), 3);

        axis = rmfield(axis, 'Theta');
    end

    stFdqDvMap = [];
    stFdqDvMap.Axis = axis;
    stFdqDvMap.Map.D = fdD;
    stFdqDvMap.Map.Q = fqD;
    % 補間結果の最大最小値
    cvRngs = GetRanges({stFdqDvMap.Map.D , stFdqDvMap.Map.Q});
    stFdqDvMap.Range.D = cvRngs{1}; stFdqDvMap.Range.Q = cvRngs{2};

    stVtMap = [];
    stVtMap.Axis = axis;
    % 多分ここが間違っていた >>>>>>
    % stVtMap.Map.D = vqt;
    % stVtMap.Map.Q = vdt;
    % <<<<<<
    stVtMap.Map.D = vdt;
    stVtMap.Map.Q = vdt;
    % 補間結果の最大最小値
    cvRngs = GetRanges({stVtMap.Map.D , stVtMap.Map.Q});
    stVtMap.Range.D = cvRngs{1}; stVtMap.Range.Q = cvRngs{2};
    % % 検証コード
    % [iData, iRng, iAxIdq] = o.mData(Data.Type.CurrentD).MappingDQ(dIdq, skId, stt);
    % [vData, vRng, vAxIdq] = o.mData(Data.Type.VoltageD).MappingDQ(dIdq, skId, stt);
    % w = 2 * pi * fa;
    % vIds = axIdq.D; vIqs = axIdq.Q;
    % id0 = 41; id1 = 41;
    % fprintf("+++++ Id %6.0f A, Iq %6.0f\n", vIds(id0), vIqs(id1));
    % fd = squeeze(mData(id0, id1, 1, :));
    % fq = squeeze(mData(id0, id1, 2, :));
    % vd0 = squeeze(vd(id0, id1, :)); 
    % vq0 = squeeze(vq(id0, id1, :));
    % id  = squeeze(iData(id0, id1, 1, :));
    % iq  = squeeze(iData(id0, id1, 2, :));
    % Ra = o.prmModel.Ra;
    % vdf = Ra*id-w*fq;
    % vqf = Ra*iq+w*fd;
end

function v = FluxToVoltBase(mFa, th)
    % 微分計算 @ Center Value 
    the = [th(end-1) - th(end) + th(1), th, th(end) + th(2) - th(1)];
    thm = mean([the(2:end); the(1:end-1)]);
    mFam = [mFa(:, end-1), mFa, mFa(:,2)]';
    mFai = interp1(the, mFam, thm);
    %
    v = diff(mFai)' ./ diff(thm);
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
