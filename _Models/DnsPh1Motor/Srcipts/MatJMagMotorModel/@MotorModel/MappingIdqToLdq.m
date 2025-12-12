function [sMapLdq, sMapLdqS] = MappingIdqToLdq(o, dltIdq, stt)
    arguments
        o       (1,1)   MotorModel
        dltIdq  (1,1)   double = 50
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.MeanMap ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange ...
                                + MapType.OnlyDrvIq ...
                                + MapType.OnlyWeakId
    end
    
    import Data.MapType

    fprintf(">>>>>>>>>> Make Inductance Map\n")
    %% 磁束データ有効性確認
    if ~isKey(o.mData, Data.Type.CoilFluxD)
        error("Not Exist Coil Flux Data.");
    end

    mdt = o.mData(Data.Type.CoilFluxD);
    if isempty(mdt)
        error("Coil Flux Data is Empty");
    end
    %% dq軸 磁束計算
    fprintf(">>>> Make Idq -> Fdq Map\n")
    mFdq = o.MappingIdqToFdq(dltIdq, bitor(stt, MapType.MeanMap));   
    
    %% dq軸 静的・動的インダクタンス計算
    fprintf(">>>> Make Fdq -> Dynamic Inductance Map\n")
    sMapLdq  = DynamicInductance(mFdq, dltIdq/2);
    fprintf(">>>> Make Fdq -> Static Inductance Map\n")
    sMapLdqS = StaticInductance(mFdq);

    %% 静的・動的インダクタンス結果プロット
    fh = figure;
    clf(fh);
    t = tiledlayout(fh, 2, 2);
    t.reset;
    t.Padding = "compact";
    t.TileSpacing = "compact";

    axs1 = nexttile(t);
    axs2 = nexttile(t);
    axd1 = nexttile(t);
    axd2 = nexttile(t);
    
    vcIds = sMapLdq.Axis.Id; vcIqs = sMapLdq.Axis.Iq;
    contourf(axs1, vcIds, vcIqs, sMapLdqS.Map.D*1e6, "ShowText", "on");
    contourf(axs2, vcIds, vcIqs, sMapLdqS.Map.Q*1e6, "ShowText", "on");
    contourf(axd1, vcIds, vcIqs, sMapLdq.Map.D*1e6, "ShowText", "on");
    contourf(axd2, vcIds, vcIqs, sMapLdq.Map.Q*1e6, "ShowText", "on");
end

function sMapLdq = DynamicInductance(mFdq, dIdq)
    vIds = mFdq.Axis.Id; vIqs = mFdq.Axis.Iq;
    maFd = mFdq.Map.D; maFq = mFdq.Map.Q;
    %% MIf分離検証
    if isfield(mFdq.Map, 'MIf')
        mMIf = mFdq.Map.MIf;
        maFd = maFd + mMIf;
    end

    %% 動的インダクタンス計算
    [mIds, mIqs] = meshgrid(vIds, vIqs);
        % d軸差分データ
    minId = min(vIds); maxId = max(vIds);
    mIds0 = min(max(mIds - dIdq, minId), maxId);
    mIds1 = min(max(mIds + dIdq, minId), maxId);
        % d軸インダクタンス
    mapFd = maFd;
    mFd0  = interp2(vIds, vIqs, mapFd, mIds0, mIqs, 'cubic');
    mFd1  = interp2(vIds, vIqs, mapFd, mIds1, mIqs, 'cubic');
    maLd   = (mFd1-mFd0) ./ (mIds1 - mIds0);
        % q軸差分データ
    minIq = min(vIqs); maxIq = max(vIqs);
    mIqs0 = min(max(mIqs - dIdq, minIq), maxIq);
    mIqs1 = min(max(mIqs + dIdq, minIq), maxIq);
        % q軸インダクタンス
    mapFq = maFq;
    mFq0  = interp2(vIds, vIqs, mapFq, mIds, mIqs0, 'cubic');
    mFq1  = interp2(vIds, vIqs, mapFq, mIds, mIqs1, 'cubic');
    maLq   = (mFq1-mFq0) ./ (mIqs1 - mIqs0);
    % 平滑化
    maLd0 = maLd; maLq0 = maLq;
    [maLd, wLd] = smoothdata(maLd, "sgolay",50); %, "gaussian", 30); % org 90
    [maLq, wLq] = smoothdata(maLq, "sgolay",20); %, "gaussian", 30); % org 60
    %% 出力データ
    sMapLdq = [];
    sMapLdq.Axis  = mFdq.Axis;
    sMapLdq.Map.D = maLd;
    sMapLdq.Map.Q = maLq;
    sMapLdq.Range.D = [min(maLd,[],"all"), max(maLd, [], "all")];
    sMapLdq.Range.D = [min(maLq,[],"all"), max(maLq, [], "all")];
end

function sMapLdqS = StaticInductance(mFdq)
    vIds = mFdq.Axis.Id; vIqs = mFdq.Axis.Iq;
    maFd = mFdq.Map.D; maFq = mFdq.Map.Q;
    %% データ整合性検証
    fId0 = abs(vIds) < 1.e-6;
    if sum(fId0) ~= 1
        error("Exists Multiple Id = 0 Data");
    end
    iId0 = find(fId0, 1);

    fIq0 = abs(vIqs) < 1.e-6;
    if sum(fIq0) ~= 1
        error("Exists Multiple Iq = 0 Data");
    end
    iIq0 = find(fIq0, 1);

    %% MIf分離検証
    if ~isfield(mFdq.Map, 'MIf')
        mMIf = maFd(:, fId0);
        maFd = maFd - mMIf;
    else
        mMIf = mFdq.Map.MIf; % No Use
    end
    %% 静的インダクタンス計算
    [mIds, mIqs] = meshgrid(vIds, vIqs);

    maLd = abs(maFd ./ mIds);
    % d軸 0割修正
    if iId0 == 1
        maLd(:, fId0) = maLd(:, iId0+1);
    elseif iId0 == length(vIds)
        maLd(:, fId0) = maLd(:, iId0-1);
    else
        maLd(:, fId0) = mean(maLd(:, iId0+[-1, 1]), 2);
    end
    % if iId0 ~= 1
    %     maLd(:, fId0) = mean(maLd(:, iId0+[-1, 1]), 2);
    % elseif iId0 == 1
    %     maLd(:, fId0) = maLd(:, iId0+1);
    % end

    maLq = abs(maFq ./ mIqs);
    % q軸 0割修正
    if iIq0 == length(vIqs)
        maLq(:, iIq0) = maLq(:, iIq0-1);
    elseif iIq0 == 1
        maLq(:, iIq0) = maLq(:, iIq0+1);
    else
        maLq(iIq0, :) = mean(maLq(iIq0+[-1, 1], :));
    end
    % if iIq0 ~= 1
    %     maLq(iIq0, :) = mean(maLq(iIq0+[-1, 1], :));
    % elseif fId0 == 1
    %     maLq(:, iIq0) = maLq(:, iIq0+1);
    % end
    %% 出力データ
    sMapLdqS = [];
    sMapLdqS.Axis  = mFdq.Axis;
    sMapLdqS.Map.D = maLd;
    sMapLdqS.Map.Q = maLq;
    sMapLdqS.Range.D = [min(maLd,[],"all"), max(maLd, [], "all")];
    sMapLdqS.Range.D = [min(maLq,[],"all"), max(maLq, [], "all")];
end