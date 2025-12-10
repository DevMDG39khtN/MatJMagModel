function stFIMap = MappingFdqToIdq(o, dIdq, dFdq, stt)
    arguments
        o       (1,1)   MotorModel
        dIdq    (1,1)   double
        dFdq    (1,1)   double
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange
    end

    import Data.MapType

    th = o.axTime.theta;

    hPrgBar = waitbar(0, 'Converting start', ...
                        'Name', 'Convert Flux to Current');
                        % 'WindowStyle', 'modal');
    nth = length(th); n = nth * 2 + 15; c = 0;

    stFdqMap = o.MappingIdqToFdq( ...
                dIdq, bitand(stt, bitcmp(Data.MapType.MeanMap)));
    vcIds = stFdqMap.Axis.Id; vrIqs = stFdqMap.Axis.Iq;     % DQ各軸電流軸ベクトル
    [maIds, maIqs] = meshgrid(vcIds, vrIqs);                % DQ各軸電流軸マップ
    maFdMap = stFdqMap.Map.D; maFqMap = stFdqMap.Map.Q;     % DQ各軸磁束
    vFdRng = stFdqMap.Range.D; vFqRng = stFdqMap.Range.Q;   % DQ各軸磁束範囲

    cvFdqAx = MagData.MapAxes({vFdRng, vFqRng}, dFdq);      % DQ磁束軸セル
    vcFds = cvFdqAx{1}; vrFqs = cvFdqAx{2};                 % DQ各軸磁束軸ベクトル
    
    [maFds, maFqs] = meshgrid(vcFds, vrFqs);
    
    c = c + 5; waitbar(c/n, hPrgBar, 'Finished Initialize.')
    %
    %% 磁束⇒電流 逆変換
    disp(">>>>> Flux to Current Inv Map")
    % maIdqs = cat(3, maIds, maIqs);
    cmFIdqMap=cell(2, nth);
    clIdqs = {reshape(maIds, [], 1), reshape(maIqs, [], 1)};
    for i = 1:nth
        mfd = reshape(maFdMap(:, :, i), [], 1);
        mfq = reshape(maFqMap(:, :, i), [], 1);
        for j = 1:2
            Fcnv=scatteredInterpolant(mfd,mfq, clIdqs{j}, "natural"); %, "nearest");
            cmFIdqMap{j, i} = Fcnv(maFds, maFqs);
            % cmFIdqMap{j, i} = griddata( ...
            %     maFdMap(:, :, i), maFqMap(:, :, i), maIdqs(:, :, j), ...
            %     maFds, maFqs, "cubic");
            c = c + 1;
            waitbar(c/n, hPrgBar, sprintf('Fdq->Idq Counterted (%d,%d) @ %d', i,j, nth));
        end
    end
    maFIdqMap = permute(reshape(cell2mat(cmFIdqMap), ...
                    reshape([size(maFds);size(cmFIdqMap)], 1, [])), ...
                    [1, 3, 4, 2]);
    waitbar(c/n, hPrgBar, 'Finished to Conver Fdq->Idq');

    %% 出力データ
    stFIMap.Axis.Fd = vcFds;
    stFIMap.Axis.Fq = vrFqs;
    if isfield(stFdqMap.Map, 'MIf')
        stFIMap.Axis.Id = stFdqMap.Axis.Id;
        stFIMap.Axis.Iq = stFdqMap.Axis.Iq;
    end
    if ~ bitand(stt, MapType.MeanMap)
        stFIMap.Axis.Theta = stFdqMap.Axis.Theta;
        
        stFIMap.Map.D = maFIdqMap(:, :, :, 1);
        stFIMap.Map.Q = maFIdqMap(:, :, :, 2);
        if isfield(stFdqMap.Map, 'MIf')
            stFIMap.Map.MIf = stFdqMap.Map.MIf;
        end
    else
        stFIMap.Map.D = mean(maFIdqMap(:, :, 1:end-1, 1), 3);
        stFIMap.Map.Q = mean(maFIdqMap(:, :, 1:end-1, 2), 3);
        if isfield(stFdqMap.Map, 'MIf')
            stFIMap.Map.MIf = stFdqMap.Map.MIf;
            stFIMap.Range.MIf = stFdqMap.Range.MIf;
        end
    end

    %% 補間結果の最大最小値  maFIdqMap dim nFq, nFd, nTh, nDQ
    % cvRngs = GetRanges(squeeze(cat(4,stMap.Map.D, stMap.Map.Q)), ...
    %                    stt, bitand(stt, MapType.MeanMap));
    cvRngs = GetRanges({stFIMap.Map.D, stFIMap.Map.Q});
    stFIMap.Range.D = cvRngs{1}; stFIMap.Range.Q = cvRngs{2};
    if isfield(stFdqMap.Map, 'MIf')
        stFIMap.Range.MIf = stFdqMap.Range.MIf;
    end
    stFIMap.Ref = stFdqMap;
    close(hPrgBar)

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
