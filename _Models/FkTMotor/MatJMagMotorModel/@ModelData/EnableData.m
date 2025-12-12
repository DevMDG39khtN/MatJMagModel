function [sDat, sIdqs] = EnableData(o, skId)
    arguments
        o       (1,1)   MagData
        skId            int32       = []
    end

    if isempty(o.data)
        warning("[%s]: Empty Data", o.type)
        sDat=[]; sIdqs = {};
        return
    end
    
            
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
    
    cIdx = cellfun(@(d) all(~isnan(d), 'all'), tgt); % 有効データフラグ

    sIdqs = cellfun(@(d) d(cIdx)', o.axMapDQ.Mapped, 'UniformOutput', false);
    
    sDat = tgt(cIdx)';
    if isempty(sDat)
        sDat = [];
        return;
    end
end