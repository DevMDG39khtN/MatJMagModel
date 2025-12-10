function [sDat, sIdqs] = EnableData(o)
    arguments
        o       (1,1)   MagData
    end

    % 将来的には，この関数処理を無くし，内部的には直列データのみとする
    % と思ったが，CELLでの処理は避けれれなさそう

    if isempty(o.data)
        warning("[%s]: Empty Data", o.type)
        sDat=[]; sIdqs = {};
        return
    end
    
            
    % NaNでないデータのみを抽出
    tgt = o.data;
    cIdx = cellfun(@(d) all(~isnan(d), 'all'), tgt); % 有効データフラグ

    sIdqs = cellfun(@(d) d(cIdx)', o.axMapDQ.Mapped, 'UniformOutput', false);
    
    sDat = tgt(cIdx)';
    if isempty(sDat)
        sDat = [];
        return;
    end
end