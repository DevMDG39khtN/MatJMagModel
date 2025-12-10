function sMapTrqToIdq = WeakenFieldMap(defMap, stTrq, tblMxT, stFdq, motPrm)
    arguments(Input)
        defMap  (1, 1)  MapDefinition
        stTrq    (1, 1)  struct
        tblMxT  (:, :)  table
        stFdq    (1, 1)  struct
        motPrm  (1, 1)  ModelParms
    end

    %% ベースパラメータ
    eps = 0.001;

    sIaMax     = defMap.maxIa;          % 最大電流 [Arms]
    skVaMax    = defMap.rLmtVdc * defMap.maxMrRatio;    % 最大電圧係数
    skVaMaxLmt = sqrt(6)/pi; % 最大電圧係数
    
    sRa = motPrm.RaT(defMap.tempCoil);  % 抵抗[Ohm] 温度考慮 [def. 20℃]
    
    %% マップ初期設定
    mFd  = stFdq.Map.D;    % d軸磁束マップ [Wb]
    mFq  = stFdq.Map.Q;    % d軸磁束マップ [Wb]
    mTrq = stTrq.Map;      % トルクマップ  [Nm]              

    vId = stFdq.Axis.Id; vIq = stFdq.Axis.Iq;
    [mId, mIq] = meshgrid(vId, vIq); % dq電流軸マップ [A]
    mIa = sqrt((mId.^2 + mIq.^2) / 3);
    
    % 電流指令マップ 分解能
    vrTrq = defMap.axTrqs; vcNrpm = defMap.axNrpms; vzVdc = defMap.axVdcs;
    snV = length(vzVdc); snS = length(vcNrpm); snT = length(vrTrq);

    fnorm = @(m) sqrt(sum(m.^2)); fnorp=@(m) fnorm(m)/sqrt(3);

    %% 出力電圧 @ (トルク/回転数) <<< 磁束 @ 最大トルクライン @ トルクマップ軸
        % dq軸電流 @ 最大トルク @ マップトルク軸
    mIdqTmax = interp1(tblMxT.Trq, [tblMxT.Id, tblMxT.Iq], vrTrq, "linear")';
    vTrqR = interp2(vId, vIq, mTrq, mIdqTmax(1, :), mIdqTmax(2, :), "linear");
    tol = max(abs((vTrqR-vrTrq)./vrTrq)) * 100;
    fprintf(">>>>>>> Max Err @ maxTrq Line %g [%%]\n", tol);
        % 最大トルク @ 最大電流補正値
    vIaTmax  = sqrt(sum(mIdqTmax.^2) / 3);
    sIaTMax = max(vIaTmax);
    if sIaTMax < sIaMax
        sIaMax = floor(sIaTMax/10)*10;
    end
    vIdqIm   = interp1(vIaTmax, mIdqTmax', sIaMax, "linear")';
    sTrqIm   = interp2(vId, vIq, mTrq, vIdqIm(1), vIdqIm(2), "linear");
    %% MTPA 等制限電圧ライン <<< 出力電圧 @ (トルク/回転数)
    mFdqTmax = [interp2( ...         % dq軸磁束 @ 最大トルク @ マップトルク軸
                stFdq.Axis.Id, stFdq.Axis.Iq, stFdq.Map.D, ...
                mIdqTmax(1,:), mIdqTmax(2,:), 'linear');
               interp2( ...
                stFdq.Axis.Id, stFdq.Axis.Iq, stFdq.Map.Q, ...
                mIdqTmax(1,:), mIdqTmax(2,:), 'linear')]; 
        %% 等制限電圧ライン <<< 出力電圧 @ (トルク/回転数)
    ws = 2 * pi *motPrm.Fa(vcNrpm); mVd0 = [0 -1; 1 0] * mFdqTmax;
    mVdqAtMaxT = zeros([size(mFdqTmax, 2), snS, 2]);
    for i = 1:size(mVdqAtMaxT, 3)
        mVdqAtMaxT(:, :, i) = sRa * mIdqTmax(i,:)' + ws .* mVd0(i,:)';
    end
    mVaAtMaxT = sqrt(sum(mVdqAtMaxT.^2, 3));
    vVaMax  = skVaMax * vzVdc;
    Ms = contourc(vcNrpm, vrTrq, mVaAtMaxT, vVaMax);  % c1:vcNrpm(x), c2:vrTrq(y)
    [cVaMax, veVaMax] = SplitCntMx(Ms, vVaMax);
    if any(~ismembertol(vVaMax, veVaMax))
        warning("***** Exist No Fieald Weakening Area Voltage");
    end
        %%
    sIsUseVaMaxLmt = ~ismembertol(skVaMaxLmt, skVaMax);
    % 物理的出力限界以下なら，マップをこの物理的出力限界で制限
    if sIsUseVaMaxLmt
        vVaMaxLmt = skVaMaxLmt * vzVdc;
        Ms0 = contourc(vcNrpm, vrTrq, mVaAtMaxT, vVaMaxLmt);
        [~, veVaMaxLmt] = SplitCntMx(Ms0, vVaMaxLmt);
        vfSame = ismembertol(vVaMaxLmt, veVaMaxLmt);
        if any(~vfSame)
            vzVdc = vzVdc(vfSame); snV = length(vzVdc);
            warning("***** Exist No Fieald Weakening Area Voltage");
        end
    end

    %% 最大電流ライン
    M = contourc(vId, vIq, mIa, [sIaMax, sIaMax]);
    cIdqIlmt = SplitCntMx(M, sIaMax); 
    mIdqIlmt = cIdqIlmt{1};     % Id, Iq @ 等最大電流ライン
    mIdqIlmt = sortrows(mIdqIlmt', 1, "descend")';  %%%%% replace
    % mIdqMaxIa = intperp1(mIdqMaxIa(1, :), mIdqMaxIa(2, :),)
    vTrqIlmt = interp2(vId, vIq, mTrq, mIdqIlmt(1, :), mIdqIlmt(2, :));
    [~, sIdxLastTrq] = max(vTrqIlmt);
    [vTrqIlmt, idx] = sort(vTrqIlmt(sIdxLastTrq:end));
    mIdqIlmt = mIdqIlmt(:, sIdxLastTrq:end); mIdqIlmt = mIdqIlmt(:, idx);
    mIsIlmt =[mIdqIlmt; sqrt(sum(mIdqIlmt.^2) / 3)];
        % 最大トルクラインのデータで置換
    vTrqIlmt(end) = sTrqIm; mIsIlmt(:, end) = [vIdqIm; sqrt(sum(vIdqIm.^2) / 3)];
    sTrqIlmtMax = vTrqIlmt(end);
        %%
    mSpdFw0TV=inf(snT, snV);
    mTrqFw0VS=nan(snV, snS);
    %%
    vIaTmax     = sqrt(sum(mIdqTmax.^2) / 3);
    mTrqMaxVS   = nan(snV, snS);  maIsMaxSV  = nan(3, snS, snV);
    mTrqBndVS   = nan(snV, snS);  maIsBndSV  = nan(3, snS, snV);
    mTrqLmtVS   = nan(snV, snS);  maIsLmtSV  = nan(3, snS, snV); 
    mTrqIalmtVS = nan(snV, snS); maIsIalmtSV = nan(3, snS, snV);
    maIdReq =    []; maIqReq = [];
    for i = 1:length(veVaMax)   % 各DC電圧毎等電圧ラインの取得
        %% DC電圧毎初期化
        sVdc = vzVdc(i);
        sVaDC = veVaMax(i);
        sVaDCLmt = inf;
        if sIsUseVaMaxLmt && i <= length(veVaMaxLmt) 
            sVaDCLmt = veVaMaxLmt(i);
        end
        fprintf('>>>>> Vdc : %g(%g, %g) [V]\n', sVdc, sVaDC, sVaDCLmt);

        mEqVmaxST = cVaMax{i};
        mEqVmaxST = sortrows(mEqVmaxST' ,1)';
        % トルク毎 電圧飽和境界回転数の取得
        if length(uniquetol(mEqVmaxST(1, :))) ~= size(mEqVmaxST,2) % 近傍データがある場合警告
            warning('***** nearist data existed. check BndData')
        end
        % 弱め界磁開始領域データ
        [vSpdFc, vSpdIc] = ismembertol(mEqVmaxST(1, :), vcNrpm);
        mTrqFw0VS(i, vSpdIc(vSpdFc)) = mEqVmaxST(2, vSpdFc);
        [vTrqFc, vTrqIc] = ismembertol(mEqVmaxST(2, :), vrTrq);
        mSpdFw0TV(vTrqIc(vTrqFc), i) = mEqVmaxST(1, vTrqFc);
        
        tmp = mTrqFw0VS(i,:);
        tmp(1:find(~isnan(tmp), 1) - 1) = inf;
        tmp(find(~isnan(tmp), 1, 'last') + 1:end) = 0;
        mTrqFw0VS(i, :) = tmp;
        
        %% 回転数毎の弱め界磁計算
        mIdTS = nan(snT, snS); mIqTS = nan(snT, snS);
        for j = 1:snS
            sSpd = vcNrpm(j);
            % fprintf('>>>>> Spd : %g[rpm]\n', sSpd);
            
            sTrqFw0 = mTrqFw0VS(i, j);  % 弱め界磁開始トルク
            sIdxLmtTrq = snT;           % トルク出力限界境界補正用インデックス
            if isinf(sTrqFw0)
                mIdTS(:, j) = mIdqTmax(1,:)';
                mIqTS(:, j) = mIdqTmax(2,:)';

                mTrqMaxVS(i, j) = vrTrq(end) - eps;
                maIsMaxSV(:, j, i) = [mIdqTmax(:, end); vIaTmax(end)];
                mTrqIalmtVS(i, j) = sTrqIlmtMax;
                maIsIalmtSV(:, j, i) = mIsIlmt(:, end); 
                mTrqBndVS(i, j) = mTrqMaxVS(i, j);
                maIsBndSV(:, j, i) = maIsMaxSV(:, j, i);
            else
                vTrqOvrVaF = vrTrq > sTrqFw0 - eps; % 電圧飽和トルクフラグ
                vTrqOvr0 = vrTrq(vTrqOvrVaF);
                
                %% 飽和未発生時の dq電流
                mIdTS(~vTrqOvrVaF, j) = mIdqTmax(1, ~vTrqOvrVaF);
                mIqTS(~vTrqOvrVaF, j) = mIdqTmax(2, ~vTrqOvrVaF);

                %% 現回転数での制限電圧時の dq電流・トルク
                w = ws(j);
                mVd = sRa * mId - w * mFq; mVq = sRa * mIq + w * mFd;
                mVa = sqrt(mVd .^2 + mVq .^2);
                M = contourc(vId, vIq, mVa, [sVaDC, sVaDC]);
                cIdqVlmtVS = SplitCntMx(M, sVaDC);
                mIdqVlmtVS = cIdqVlmtVS{1};
                vIaVlmtVS  = sqrt(sum(mIdqVlmtVS.^2) / 3);
                [~, sIdxLastTrq] = max(vIaVlmtVS);            % AC電圧 
                isInc = true;
                if sIdxLastTrq == 1
                    isInc = false;
                % elseif sIdxLastTrq >= length(vIaVlmtVS)
                elseif sIdxLastTrq ~= length(vIaVlmtVS)
                    error('@@@@@ Ia is not monotonic.')
                end

                %% 最大トルクピーク検出　屈曲点あり Idq @ 最大電圧 トルク @ 最大電圧
                vTrqVlmtVS = interp2(vId, vIq, mTrq, mIdqVlmtVS(1, :), mIdqVlmtVS(2, :), "linear");
                [sTrqVlmtMax, sIdxLastTrq] = max(vTrqVlmtVS);    % 最大トルク @ 制限電圧
                vIdqVlmtMax = mIdqVlmtVS(:, sIdxLastTrq);       % dq軸電流 @ 制限電圧 
                if isInc
                    vTrqVlmtVS = vTrqVlmtVS(1:sIdxLastTrq); mIdqVlmtVS = mIdqVlmtVS(:, 1:sIdxLastTrq);   % 
                else
                    vTrqVlmtVS = vTrqVlmtVS(sIdxLastTrq:end); mIdqVlmtVS = mIdqVlmtVS(:, sIdxLastTrq:end);   % 
                end
                 %トルク昇順ソート 
                [vTrqVlmtVS, idx] = sort(vTrqVlmtVS);
                mIdqVlmtVS = mIdqVlmtVS(:, idx);
                vIaVlmtVS  = sqrt(sum(mIdqVlmtVS.^2) / 3);
                [sIaVlmtMaxT, sIdxLastTrq] = max(vIaVlmtVS);            % AC電圧 
                if sIdxLastTrq ~= length(vIaVlmtVS)
                    error("@@@@@@ fail mono increase ")
                end

                if min(vTrqVlmtVS) > min(vTrqOvr0)
                    % 電圧飽和トルクが制限電圧化に無いもの有
                    error('@@@@@ Fail Search Min. Eqv. Va Trq');
                end
                    % 制限電流時電圧
                vVaIlmt = interp2(vId, vIq, mVa, mIsIlmt(1, :), mIsIlmt(2, :), "linear");
                    %
                %%  電圧飽和時出力限界
                vTrqOvr = vTrqOvr0;
                vTrqLmtF = vTrqOvr > sTrqVlmtMax + eps;
                vTrqOvr(vTrqLmtF) = nan; % 出力不可トルク除去
                mIdqFwTrq = interp1(vTrqVlmtVS, mIdqVlmtVS', vTrqOvr, "linear")';
                sIdxLastTrq = find(~isnan(vTrqOvr), 1, 'last');
                if isnan(mIdqFwTrq(1, sIdxLastTrq)) % 有効な最後のトルクがnan -> 境界ギリギリ
                    mIdqFwTrq(:, sIdxLastTrq) = vIdqVlmtMax;
                end

                if any(vTrqLmtF)
                    tis = [vIdqVlmtMax; sIaVlmtMaxT];
                    mTrqMaxVS(i, j) = sTrqVlmtMax;
                    maIsMaxSV(:, j, i) = tis;
                    %
                    id = find(~isnan(vTrqOvr), 1, "last"); % この時だけId更新
                    mTrqBndVS(i, j) = vTrqOvr(id);
                    td  = mIdqFwTrq(:, id);
                    maIsBndSV(:, j, i) = [td; sqrt(sum(td.^2) / 3)];
                    % 制限電流時のトルク・dq軸電流の計算
                    if sIaVlmtMaxT > sIaMax + eps
                        if max(vVaIlmt) < sVaDC + eps
                            mTrqIalmtVS(i, j) = sTrqIlmtMax;
                            maIsIalmtSV(:, j, i) = mIsIlmt(:, end);
                        else % 最大電圧に制限
                            t = interp1(vVaIlmt, [vTrqIlmt; mIsIlmt]', sVaDC, "linear");
                            mTrqIalmtVS(i, j) = t(1);
                            maIsIalmtSV(:, j, i) = t(2:end);
                        end
                    else % 制限電圧下の最大電流が小さい場合
                        mTrqIalmtVS(i, j) = sTrqVlmtMax;
                        maIsIalmtSV(:, j, i) = tis;
                    end
                else
                    mTrqMaxVS(i, j) = vTrqOvr(end) - eps;
                    td = mIdqFwTrq(:, end);
                    maIsMaxSV(:, j, i) = [td; sqrt(sum(td.^2) / 3)];
                    if max(vVaIlmt) < sVaDC + eps
                        mTrqIalmtVS(i, j) = sTrqIlmtMax;
                        maIsIalmtSV(:, j, i) = mIsIlmt(:, end);
                    else
                        t = interp1(vVaIlmt, [vTrqIlmt; mIsIlmt]', sVaDC, "linear");
                        mTrqIalmtVS(i, j) = t(1);
                        maIsIalmtSV(:, j, i) = t(2:end);
                    end
                    mTrqBndVS(i, j) = mTrqMaxVS(i, j);
                    maIsBndSV(:, j, i) = maIsMaxSV(:, j, i);
                end

                mIdTS(vTrqOvrVaF, j) = mIdqFwTrq(1, :);
                mIqTS(vTrqOvrVaF, j) = mIdqFwTrq(2, :);
                
                idc = find(~isnan(mIdTS(:, j)), 1, "last");
                if idc < snT
                    sIdxLmtTrq = idc;
                end
                %%
            end
            jj = max(j - 1, 1);
            mTrqLmtVS(i, jj) = mTrqBndVS(i, j);

            if sIdxLmtTrq < snT
                tm = [mIdTS(:, j)'; mIqTS(:, j)'];
                td = tm(:, max(sIdxLmtTrq-1, 1));
                maIsLmtSV(:, j, i) = [td; fnorp(td)];
            else
                maIsLmtSV(:, j, i) = maIsBndSV(:, j, i);
            end

            if j == snS
                did = sIdxLmtTrq0 - sIdxLmtTrq;
                mTrqLmtVS(i, j) = vrTrq(max(sIdxLmtTrq - did, 1));
                tm = [mIdTS(:, j)'; mIqTS(:, j)'];
                td = tm(:, max(sIdxLmtTrq-did, 1));
                maIsLmtSV(:, j, i) = [td; fnorp(td)];
            end
            sIdxLmtTrq0 = sIdxLmtTrq;
        end
        
        maIdReq = cat(3, maIdReq, mIdTS);
        maIqReq = cat(3, maIqReq, mIqTS);
        for j1 = 1:snS
            idj1 = find(isnan(maIdReq(:, j1, end)), 1);
            if ~isempty(idj1)
                maIdReq(idj1:end, j1, end) = maIsMaxSV(1, j1, i);
                maIqReq(idj1:end, j1, end) = maIsMaxSV(2, j1, i);
            end
        end
        if any(isnan(maIdReq(:,:,end)), 'all') || any(isnan(maIqReq(:,:,end)), 'all')
            error(">>>>> IdqReqMap has some nan");
        end
    end

    %     %% 出力整形
    sMapTrqToIdq = [];
    sMapTrqToIdq.Axis.rTrq = vrTrq;
    sMapTrqToIdq.Axis.cNrpm = vcNrpm;
    sMapTrqToIdq.Axis.zVdc = vzVdc;

    sMapTrqToIdq.Map.D = maIdReq;
    sMapTrqToIdq.Map.Q = maIqReq;

    sMapTrqToIdq.Limit.MaxTrqOut   = mTrqMaxVS;
    sMapTrqToIdq.Limit.IdqTrqOut.D = squeeze(maIsMaxSV(1, :, :))';
    sMapTrqToIdq.Limit.IdqTrqOut.Q = squeeze(maIsMaxSV(2, :, :))';
    sMapTrqToIdq.Limit.TrqMaxIa    = mTrqIalmtVS;
    sMapTrqToIdq.Limit.IdqMaxIa.D  = squeeze(maIsIalmtSV(1, :, :))';
    sMapTrqToIdq.Limit.IdqMaxIa.Q  = squeeze(maIsIalmtSV(2, :, :))';
    sMapTrqToIdq.Limit.IdqMaxIa.Ia = squeeze(maIsIalmtSV(3, :, :))';
    sMapTrqToIdq.Limit.TrqBnd      = mTrqBndVS;
    sMapTrqToIdq.Limit.IdqBnd.D   = squeeze(maIsBndSV(1, :, :))';
    sMapTrqToIdq.Limit.IdqBnd.Q   = squeeze(maIsBndSV(2, :, :))';
    sMapTrqToIdq.Limit.TrqLmt     = mTrqLmtVS;
    sMapTrqToIdq.Limit.IdqLmt.D   = squeeze(maIsLmtSV(1, :, :))';
    sMapTrqToIdq.Limit.IdqLmt.Q   = squeeze(maIsLmtSV(2, :, :))';

    sMapTrqToIdq.Limit.BndSpdFw  = mSpdFw0TV;
    sMapTrqToIdq.Limit.BndTrqFw  = mTrqFw0VS;

    sMapTrqToIdq.Ref.Trq  = stTrq;
    sMapTrqToIdq.Ref.Flux = stFdq;
end
