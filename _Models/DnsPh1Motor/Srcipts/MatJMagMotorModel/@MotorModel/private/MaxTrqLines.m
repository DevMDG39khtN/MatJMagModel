function [tblMaxTrqFit, tblMaxTrqData, pFitEq] = ... 
    MaxTrqLines(mTrq, maxTrq, maxIa, nOrdFitEq, dltIa, ax)
%
    arguments
        mTrq    (1, 1)
        maxTrq      (1, 1)    double
        maxIa       (1, 1)    double  
        nOrdFitEq   (1, 1)    int32 = 4
        dltIa       double {mustBeScalarOrEmpty} = 50
        ax          {mustBeScalarOrEmpty}  = gobjects(0)
    end
%
     ax = ChkArgAxes(ax);

    %% 電流・界磁角マップ変換
    vIds = mTrq.Axis.Id;
    vIqs = mTrq.Axis.Iq;
    mapTrq = mTrq.Map;

    [mIds, mIqs] = meshgrid(vIds, vIqs);
    mIas = sqrt((mIds.^2 + mIqs.^2) / 3);
    mxIas = max(mIas, [], "all");   % データ最大電流

    M = contourc(vIds, vIqs, mIas, [maxIa, maxIa]);
    cmiIdq = SplitCntMx(M, maxIa); miIdq = cmiIdq{1};
    mFwx = atan2d(-miIdq(1,:), miIdq(2,:));
    mTqx = interp2(vIds, vIqs, mapTrq, miIdq(1,:), miIdq(2,:));
    if ~isempty(ax)
        line(ax, mFwx, mTqx, 'LineStyle',':', 'LineWidth',3, 'Color','r')
    end
    %%　最大トルク抽出 電流範囲
     % 最大トルク時最小電流
    M = contourc(vIds, vIqs, mapTrq, [maxTrq, maxTrq]);
    cmtIdq = SplitCntMx(M, maxTrq); vmtIdq = cmtIdq{1};
    vtIas =  sqrt((vmtIdq(1,:).^2 + vmtIdq(2,:).^2) / 3);
    tIaMax = min(vtIas);
    % 電流範囲設定
    vIas = 0:dltIa:tIaMax;
    vIasExt = (vIas(end) + 50 ):50:mxIas; % 範囲最大値修正前に設定必要
    if vIas(end) < tIaMax * 0.999   
        vIas = [vIas tIaMax];
    end
    if vIasExt(end) < mxIas * 0.999   
        vIasExt = [vIasExt mxIas];
    end
    %% 電流毎最大トルクデータ抽出
        % avMxTrqs: @maxTrq, Ia, Fw, Id, Iq
    avMxTrqs = SearchMaxTrqbyIas(mIas, vIas, vIasExt, mTrq, ax);
    
    tblMaxTrqData = table('Size', size(avMxTrqs'), 'VariableTypes', ... 
                                repmat("double", 1, size(avMxTrqs,1)));
    tblMaxTrqData.Properties.VariableNames = ["Trq","Ia","Fw","Id","Iq"];
    tblMaxTrqData.Variables = avMxTrqs';
    %% 高次式フィット
    [avMxTrqFits, pFitEq] = FitMaxTrqbyIas( ...
                tblMaxTrqData.Ia, tblMaxTrqData.Fw, nOrdFitEq, ...
                mTrq, ax);
    
    tblMaxTrqFit = table('Size', size(avMxTrqFits'), 'VariableTypes' ...
                        , repmat("double", 1, size(avMxTrqFits,1)));
    tblMaxTrqFit.Properties.VariableNames = ...
        ["Trq","Ia","Fw","Id","Iq"];
    tblMaxTrqFit.Variables = avMxTrqFits';

    % % 最トルクラインデータの確認
    % mFws = atan2d(-mIds, mIqs);
    % sVas = evalin('base', 'MdlVotlMap');
    % mVd = sVas.Ref.Map.D; mVq = sVas.Ref.Map.Q;
    % vVid = sVas.Ref.Axis.Id; vViq = sVas.Ref.Axis.Iq;
    % mVasT = sqrt((mVd.^2+mVq.^2)/3); mVas=mean(mVasT(1:201,201:end,1:end-1),3);
    % mVasT0=mean(mVasT(:,:,1:end-1),3);
    % mVas=mVasT0(201:end, 201:-1:1) * 2*pi*100*1050/120;
    %   %contourf(vVid(201:-1:1), vViq(201:end), mVasT0(201:end,201:-1:1)*2*pi*1050*100/120)
    % tIas = [0:50:mxIas, mxIas];
    % Mc = contourc(vIds, vIqs, mIas, tIas);
    % cmcIdqs=SplitCntMx(Mc, tIas);
    % fh = figure();  fhv = figure();
    % ax = axes(fh);  axv=axes(fhv);
    % v0=zeros(1,length(cmcIdqs));
    % for i = 1:length(cmcIdqs)
    %     mtIdqs = cmcIdqs{i}; mtId = mtIdqs(1,:); mtIq = mtIdqs(2,:);
    %     mtIa = sqrt((mtId.^2+mtIq.^2)/3);
    %     mtFw = atan2d(-mtId, mtIq);
    %     mtTrq = interp2(vIds, vIqs, mapTrq, mtId, mtIq, "cubic");
    %     line(ax, mtFw, mtTrq, 'LineWidth', 1, 'Color', 'r');
    %     mtVa = interp2(vIds, vIqs, mVas, mtId, mtIq, "cubic");
    %     line(axv, mtFw, mtVa, 'LineWidth', 1, 'Color', 'b');
    % end
    % l0 = line(ax, tblMaxTrqData.Fw, tblMaxTrqData.Trq, 'LineWidth', 1, "Color", "c");
    % l1 = line(ax, tblMaxTrqFit.Fw, tblMaxTrqFit.Trq, 'LineWidth', 2, "Color", "b");
    % 
    % vr = [tblMaxTrqFit.Id,tblMaxTrqFit.Iq]';
    % mtVa=interp2(vIds, vIqs, mVas, vr(1,:), vr(2,:), 'cubic');
    % lv9 = line(axv, tblMaxTrqFit.Fw, mtVa, 'LineWidth', 2, "Color", "g");
    % grid(ax, 'on');
    % grid(axv, 'on');

end

function [avMxTrqFits, pFitEq] = FitMaxTrqbyIas(vIas, vFws, nOrdFitP, mTrq, ax)
    pFitEq = polyfix(vIas, vFws, nOrdFitP,  0, 0);
        % フィット式データ確認
    vftIas = linspace(vIas(1), vIas(end), 501); % 電流軸
    vftFws = polyval(pFitEq, vftIas);    % フィット界磁角
    vftIds = sqrt(3)*vftIas.*sind(-vftFws);     % Id変換
    vftIqs = sqrt(3)*vftIas.*cosd(-vftFws);     % Iq変換

    vIds = mTrq.Axis.Id;
    vIqs = mTrq.Axis.Iq;
    mapTrq = mTrq.Map;

    % 補間トルク
    vftTrq = interp2(vIds, vIqs, mapTrq, vftIds, vftIqs, "cubic");
    if ~isempty(ax)
        line(ax, vftFws, vftTrq, 'LineWidth', 2, 'Color', 'r')
    end

    avMxTrqFits =[vftTrq; vftIas; vftFws; vftIds; vftIqs];
end

function avMxTrqs = SearchMaxTrqbyIas(mIas, vIas, vIasExt, mTrq, ax)
% function avMxTrqs = SearchMaxTrqbyIas(ciIdqs, vIas, mTrq, maxIa, ax)
    vIds = mTrq.Axis.Id;
    vIqs = mTrq.Axis.Iq;
    mapTrq = mTrq.Map;

    M = contourc(vIds, vIqs, mIas, vIas);
    [ciIdqs, vIas] = SplitCntMx(M, vIas);

    if ~isempty(ax)
        ax.XLim = [0, 90]; ax.XTick = 0:5:90;
    end
    nlIas = length(ciIdqs);
    sflgs = false(1, nlIas);
    sflgs(1) = true;
    % 最大トルク値　抽出
    avMxTrqs = zeros(5,nlIas);    %検索結果 maxTrq, @Ia, @Fw, @Id, @Iq
    for i = 2:nlIas
        % 個別 等電流 位相角
        tIa = vIas(i);
        miIdqs = ciIdqs{i};
        vMsTrqD = SearcMaxTrqs(miIdqs, tIa, mTrq, ax);
        sflgs(i) = true;
        avMxTrqs(:, i) = vMsTrqD';
    end
    avMxTrqs = avMxTrqs(:, sflgs);    % 有効データのみ
    
    if ~isempty(ax)
        M = contourc(vIds, vIqs, mIas, vIasExt);
        [cixIdqs, vIasx] = SplitCntMx(M, vIasExt);
        for i = 1:length(cixIdqs)
            tIa = vIasx(i);
            miIdqs = cixIdqs{i};
            tx  = interp2(vIds, vIqs, mapTrq, miIdqs(1,:), miIdqs(2,:), "cubic");
            fx = atan2d(-miIdqs(1,:), miIdqs(2,:));
            line(ax, fx, tx, 'LineWidth', 1, 'Color', 'c');
        end
    end

    if ~isempty(ax)
        line(ax, avMxTrqs(3,:), avMxTrqs(1,:), 'LineWidth', 1, 'Color', 'g');
    end
end

function [vMsTrqD, rFws] = SearcMaxTrqs(miIdqs, tIa, mTrq, ax, isDot)
    if nargin < 5
        isDot = true;
    end
    vFws = atan2d(-miIdqs(1,:), miIdqs(2,:));
    [vFws, vsIds] = sort(vFws);     % 界磁角昇順ソート
    msiIdqs = miIdqs(:, vsIds);     % 等電流 Id-Iq 界磁角 昇順ソート
    err = ChkCntIntPValue(sqrt((msiIdqs(1,:).^2 + msiIdqs(2,:).^2)/3), tIa);
    fprintf("*** Ia IntP max Error : %14.5e\n", err);
        % 範囲取得
    nFws = length(vFws);
    [maxFw, ide] = max(vFws); [minFw, ids] = min(vFws);
    fprintf('**** Fw : min %12.4f, max %12.4f\n', minFw, maxFw);
    if ids ~= 1 || ide ~= nFws     % データチェック
        warning("Fw Sort will be unmatched [%d to %d]@%d\n", ids, ide, nFws)
    end
    
    vIds = mTrq.Axis.Id;
    vIqs = mTrq.Axis.Iq;
    mapTrq = mTrq.Map;

        % 最大トルク取得
    pTrqs  = interp2(vIds, vIqs, mapTrq, msiIdqs(1,:), msiIdqs(2,:), "cubic");
    [maxTrq, idTmax] = max(pTrqs);
    % 有効界磁角チェック % if maxFw < 60 || maxFw > 30 % continue; %end
        % 詳細トルク取得
    dRngFw = vFws([max([idTmax-2, 1]), min([idTmax+2, nFws])]);
    
    [mxTrqD, mxFwD] = SearcMaxTrqByDetailFw(dRngFw, tIa, mTrq, 100);
    tId = sqrt(3)*tIa*sind(-mxFwD);
    tIq = sqrt(3)*tIa*cosd(-mxFwD);
    vMsTrqD = [mxTrqD, tIa, mxFwD, tId, tIq]; %maxTrq, @Ia, @Fw, @Id, @Iq
    rFws = [minFw, maxFw];
    
    if ~isempty(ax)
        line(ax, vFws, pTrqs, 'LineWidth', 1, 'Color', 'm');
        if isDot
            line(ax, vFws(idTmax), maxTrq, ...
                "LineStyle", "none", "Marker", "o", "MarkerEdgeColor", 'm')
            line(ax, mxFwD, mxTrqD, ...
              "LineStyle", "none", "Marker", "o", "MarkerEdgeColor", 'b')
        end
    end

end

function [maxTrq, tFw] = SearcMaxTrqByDetailFw(rFws, tIa, mTrq, nDiv)
    vFws = linspace(rFws(1), rFws(2), nDiv);
    tIds = sqrt(3)*tIa*sind(-vFws);
    tIqs = sqrt(3)*tIa*cosd(-vFws);
    
    vIds = mTrq.Axis.Id;
    vIqs = mTrq.Axis.Iq;
    mapTrq = mTrq.Map;

    diTrqs = interp2(vIds, vIqs, mapTrq, tIds, tIqs, "cubic");
    [maxTrq, idTmax] = max(diTrqs);
    tFw = vFws(idTmax);
end

function [maxErr, id] = ChkCntIntPValue(vcVals, tv)
    [maxErr, id] = max(abs((vcVals-tv)/tv));
end

function ax = ChkArgAxes(ax)
    %% グラフプロット変数の追加
    if ~isa(ax, 'matlab.graphics.Graphics')
        ax = gobjects(0);
    else
        if ~isempty(ax)
            if isa(ax, 'matlab.ui.Figure')
                fh = ax;
                if isvalid(fh)
                    ax = findobj(fh, 'Type', 'Axes');
                    if isempty(ax)
                        ax = axes(fh);
                    end
                else
                    ax = gobjects(0);
                end
            elseif ~isa(ax, 'matlab.graphics.axis.Axes') || ~isvalid(ax)
                ax = gobjects(0);
            end
        end
    end
    if ~isempty(ax)
        cla(ax, 'reset')
    end
end