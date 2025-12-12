function stV0Map = MappingFdqToVdq0(o, dIdq, dFdq, skId, stt)
    arguments
        o       (1,1)   MotorModel
        dIdq    (1,1)   double
        dFdq    (1,1)   double
        skId    int32   {mustBeScalarOrEmpty}  = []
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange
    end

    import Data.MapType

    th = o.axTime.theta;

    hPrgBar = waitbar(0, 'Converting start', 'Name', 'Convert Flux to Current');
    nth = length(th); n = nth * 4 + 15; c = 0;

    tDeFlg = Data.MapType.MeanMap + Data.MapType.DivideMIf; % 無効化マップフラグ
    [sVdq0Map,sVdqT0Map, sFdqMap] = ...
        o.MappingIdqToVdq0(dIdq, skId, bitand(stt, bitcmp(tDeFlg)));
    % vcIds = sVdq0Map.Axis.Id; vrIqs = sVdq0Map.Axis.Iq; % DQ各軸電流軸ベクトル
    % [maIds, maIqs] = meshgrid(vcIds, vrIqs);            % DQ各軸電流軸マップ

    mFdM = sFdqMap.Map.D; mFqM = sFdqMap.Map.Q;         % DQ各軸磁束
    vFdR = sFdqMap.Range.D; vFqR = sFdqMap.Range.Q;     % DQ各軸磁束範囲

    mVd0M = sVdq0Map.Map.D; mVq0M = sVdq0Map.Map.Q;     % DQ各軸相電圧
    mVdT0M = sVdqT0Map.Map.D; mVqT0M = sVdqT0Map.Map.Q; % DQ各軸端子電圧

    cvFdqAx = MagData.MapAxes({vFdR, vFqR}, dFdq);      % DQ磁束軸セル
    vcFds = cvFdqAx{1}; vrFqs = cvFdqAx{2};             % DQ各軸磁束軸ベクトル
    [maFds, maFqs] = meshgrid(vcFds, vrFqs);
    
    c = c + 5; waitbar(c/n, hPrgBar, 'Finished Initialize.')
    %
    %% 磁束⇒電流 逆変換
    disp(">>>>> Flux to Current Inv Map")
    maVdq0s = cat(4, mVd0M, mVq0M);
    maVdqT0s = cat(4, mVdT0M, mVqT0M);
    cmFVdq0Map=cell(2, nth);
    cmFVdqT0Map=cell(2, nth);
    for i = 1:nth
        for j = 1:2
            % mFd = reshape(mFdM(:, :, i), [], 1);
            % mFq = reshape(mFqM(:, :, i), [], 1);
            % mVa0 = reshape(maVdq0s(:, :, i, j), [], 1)
            % Vcnv=scatteredInterpolant(mVd,mVq, mVa0, "natural"); %, "nearest");
            % cmFVdq0Map{j, i} = Vcnv(maFds, maFqs);
            % mVaT0 = reshape(maVdqT0s(:, :, i, j), [], 1)
            % VTcnv=scatteredInterpolant(mVd,mVq, mVaT0, "natural"); %, "nearest");
            % cmFVdqT0Map{j, i} = VcTnv(maFds, maFqs);
            cmFVdq0Map{j, i} = griddata( ...
                mFdM(:, :, i), mFqM(:, :, i), maVdq0s(:, :, i, j), ...
                maFds, maFqs, "cubic");
            
            c = c + 1;
            waitbar(c/n, hPrgBar, sprintf('Fdq->Vdq0 Counterted (%d,%d) @ %d', i,j, nth));

            cmFVdqT0Map{j, i} = griddata( ...
                mFdM(:, :, i), mFqM(:, :, i), maVdqT0s(:, :, i, j), ...
                maFds, maFqs, "cubic");
            
            c = c + 1;
            waitbar(c/n, hPrgBar, sprintf('Fdq->Vdq0 Counterted (%d,%d) @ %d', i,j, nth));
        end
    end
    maVdq0Map = permute(reshape(cell2mat(cmFVdq0Map), ...
                    reshape([size(maFds);size(cmFVdq0Map)], 1, [])), ...
                    [1, 3, 4, 2]);
    maVdq0TMap = permute(reshape(cell2mat(cmFVdqT0Map), ...
                    reshape([size(maFds);size(cmFVdqT0Map)], 1, [])), ...
                    [1, 3, 4, 2]);
    waitbar(c/n, hPrgBar, 'Finished to Conver Fdq->Idq');

    vd = maVdq0Map(:,:,:,1);
    vq = maVdq0Map(:,:,:,2);

    vdt = maVdq0TMap(:,:,:,1);
    vqt = maVdq0TMap(:,:,:,2);

    axis.Fd = vcFds;
    axis.Fq = vrFqs;
    if bitand(stt, Data.MapType.MeanMap)
        vd0 = vd;  vq0 = vq; vdt0 = vdt; vqt0 = vqt;

        vd = mean(vd(:, :, 1:end-1), 3);
        vq = mean(vq(:, :, 1:end-1), 3);
        vdt = mean(vdt(:, :, 1:end-1), 3);
        vqt = mean(vqt(:, :, 1:end-1), 3);
    else
        axis.Theta = sFdqMap.Axis.Theta;
    end


    %% 出力データ
    stV0Map.Axis = axis;
    stV0Map.Map.D = vd;
    stV0Map.Map.Q = vq;
    % 補間結果の最大最小値
    cvRngs = GetRanges({stV0Map.Map.D , stV0Map.Map.Q});
    stV0Map.Range.D = cvRngs{1}; stV0Map.Range.Q = cvRngs{2};
    close(hPrgBar)

    stVt0Map.Axis = axis;
    stVt0Map.Map.D = vqt;
    stVt0Map.Map.Q = vdt;
    % 補間結果の最大最小値
    cvRngs = GetRanges({stVt0Map.Map.D , stVt0Map.Map.Q});
    stVt0Map.Range.D = cvRngs{1}; stVt0Map.Range.Q = cvRngs{2};

    stV0Map.Ref = sVdq0Map;
    stVt0Map.Ref = sVdqT0Map;
    stV0Map.RefT  = stVt0Map;
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
