function [map, sRngs, axIdq] = MappingDQ(o, dIdq, stt, nPara)
    arguments
        o       (1,1)   MagData
        dIdq    (1,1)   double
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange
        nPara   (1,1)   double  = 1
    end
    
    import Data.MapType

    th = o.axTime.theta;
    [cDats, sIdqs] = o.CellData();
    if isempty(cDats)
        map = [];
        axIdq = [];
        sRngs = [];
        return;
    end

    cDats = cellfun(@(m)m/nPara, cDats, "UniformOutput", false);
    o.OnProcessExceed() % 001

    sIds = sIdqs{1}; sIqs = sIdqs{2};       % Id-Iq @ 解析データ
    axMdq = o.idxDQ.MappedAx;
    vIds = axMdq.D; vIqs = axMdq.Q; 

    %% 回生トルク側のデータを力行側から拡張
        % 位相を時間軸の逆方向に修正
    if bitand(stt, MapType.MirrorQ)
        % Ignore Negative Iq Axis Value (sIqs < 0)
        if any(abs(sIqs) < -1.e-6)
            warning("Iq < 0 data exists and will be ignored.")
        end
        % extend Mirror Q-Axis Data
        inIqs = abs(sIqs) > 1.e-6;
        nsIqs = -sIqs(inIqs);
        nsIds = sIds(inIqs);
        nsDat = cDats(inIqs);
        if o.dShape(1) == 3
            nsDat = cellfun(@(d)d([1 3 2], end:-1:1), nsDat, "UniformOutput", false);
        elseif o.type == Data.Type.TorqueD
            nsDat = cellfun(@(d)-d(:, end:-1:1), nsDat, "UniformOutput", false);
        else
            warning("Not Validation. As Is. Maybe some error ")
            nsDat = cellfun(@(d) d, nsDat, "UniformOutput", false);
        end
        sIds = [sIds, nsIds]; sIqs = [sIqs, nsIqs]; cDats = cat(2, cDats, nsDat);
        vIqs=[-vIqs(end:-1:2), vIqs];
    end
    o.OnProcessExceed() % 002
    
    %% Idq分割幅が 0以下の場合，元のデータのIdq Map軸で作成
    if dIdq > 1.0e-6
        rIdqs  = o.MapAxes({vIds, vIqs}, dIdq);
    else
        rIdqs = {vIds, vIqs};
    end
    
    axDQ = AxisDQ(rIdqs{1}, rIdqs{2});
    mIdqs  = axDQ.Mapped;
    mIds   = mIdqs{1}; mIqs = mIdqs{2};
 
    axIdq.Id = axDQ.D; axIdq.Iq = axDQ.Q; axIdq.Theta = th;
    %%
    if o.dShape(1) == 3
        % map dim -> [Iq, Id, DQ, th]
        mc = cellfun(@(d)o.CnvUVWtoDQ(d, th), cDats, "UniformOutput", false);
        % mm = permute(reshape(cell2mat(mc), [3, o.dShape(2), length(cDats)]), [3, 1, 2]);
        mm = permute(reshape(cell2mat(mc), [2, o.dShape(2), length(cDats)]), [3, 1, 2]);
        mc = arrayfun(@(i) ...
                arrayfun(@(j) ...
                    griddata(sIds,sIqs,mm(:,j,i),mIds,mIqs,'cubic'), ...
                    1:2,'UniformOutput',false), ...
                1:o.dShape(2), "UniformOutput", false);
                    % 1:3,'UniformOutput',false), ...
        mc = vertcat(mc{:})';
        nDims = reshape([size(mIds); size(mc)],1,[]);
        map = permute(reshape(cell2mat(mc), nDims), [1, 3, 2, 4]);
        o.OnProcessExceed() % 003
        
        if bitand(stt, MapType.CorrectMean)
            idIq0 = find(abs(axDQ.Q) < 1.e-6, 1);
            % mTmap = mean(squeeze(map( :, :, 3, 1:end-1)), 3);
            mTmap = mean(squeeze(map( :, :, 2, 1:end-1)), 3);
            mTmapH = (mTmap(idIq0:end,:)-mTmap(idIq0:-1:1,:))/2;
            mTmapH = [-mTmapH(end:-1:2, :); mTmapH];
            map(:,:,2,:) =  map(:,:,2,:) - mTmap + mTmapH;
            % map(:,:,3,:) =  map(:,:,3,:) - mTmap + mTmapH;
        end
        o.OnProcessExceed() % 004

        if bitand(stt, MapType.OnlyDrvIq)   % Id 弱め磁束領域のみ
            vfId = axDQ.D < eps;
            axIdq.Id = axDQ.D(vfId);
            map = map(:, vfId, :, :);
        end
        
        if bitand(stt, MapType.OnlyDrvIq)   % Iq 力行マップのみ
            vfIq = axDQ.Q > -eps;
            axIdq.Iq = axDQ.Q(vfIq);
            map = map(vfIq, :, :, :);
        end
        o.OnProcessExceed() % 005

        %% 補間結果の最大最小値 map dim nIq, nId, nDQ, nTh
            % 時間軸データの場合，各時間毎の最小・最大値の中で，
            % 最小の最大値，最大の最小値が必要
        fmin = @(d) min(d, [], "all"); fmax = @(d) max(d, [], "all");
        fdm =@(map, i) map(:, :, i, :);
        if bitand(stt, MapType.MinRange)
            crs = arrayfun( ...
                    @(j)arrayfun( ...
                        @(i)[fmin(map(:,:,i,j)), fmax(map(:,:,i,j))], ...
                        1:size(map,3), "UniformOutput", false), ...
                    1:size(map,4), "UniformOutput", false);
            crs = mat2cell(cell2mat(cat(1, crs{:})), length(crs), [2, 2]);
            % crs = mat2cell(cell2mat(cat(1, crs{:})), length(crs), [3, 3]);
            cRngs = cellfun(@(r)[max(r(:,1)), min(r(:,2))], crs, 'UniformOutput', false);
        else
            cRngs = arrayfun( ...
                        @(i)[fmin(fdm(map, i)), fmax(fdm(map, i))], ...
                        1:2, "UniformOutput", false);
        end
        sRngs.D = cRngs{1}; sRngs.Q = cRngs{2};
        o.OnProcessExceed() % 006
    elseif o.type == Data.Type.TorqueD
        % map dim -> [Iq, Id, th]
        msz = reshape([o.dShape; size(cDats)], 1, []);
        m = reshape(cell2mat(cDats), msz(3:4))';
        mc = arrayfun(@(i)griddata(sIds,sIqs,m(:,i),mIds,mIqs,'cubic'), ...
                1:o.dShape(2), "UniformOutput", false);
        o.OnProcessExceed() % 003
        map = permute(reshape(vertcat(mc{:}) ...
                        , [size(mIds,1), o.dShape(2), size(mIds,2)]) ...
                ,[1 3,2]);
        o.OnProcessExceed() % 004
        if bitand(stt, MapType.CorrectMean)
            idIq0 = find(abs(axDQ.Q) < 1.e-6, 1); % Index @ Iq = 0 
            mTmap = mean(map( :, :, 1:end-1), 3);   % 過渡データの平均値
            mTmapH = (mTmap(idIq0:end,:)-mTmap(idIq0:-1:1,:))/2;
            mTmapH = [-mTmapH(end:-1:2, :); mTmapH];
            map = map - mTmap + mTmapH;
        end
        o.OnProcessExceed() % 005

        if bitand(stt, MapType.OnlyDrvIq)   % Id 弱め磁束領域のみ
            vfId = axDQ.D < eps;
            axIdq.Id = axDQ.D(vfId);
            map = map(:, vfId, :);
        end
        
        if bitand(stt, MapType.OnlyDrvIq)   % Iq 力行マップのみ
            vfIq = axDQ.Q > -eps;
            axIdq.Iq = axDQ.Q(vfIq);
            map = map(vfIq, :, :);
        end

        sRngs = [min(map, [], "all"), max(map, [], "all")];
        o.OnProcessExceed() % 006
    else
        error("Not Implemeted yet.");
    end
end
