function nMap = LimitTrq(map, rs)
    maxTs = rs*max(map);
    dTs = diff(map);

    nMap = zeros(size(map));
    for i=1:length(maxTs)
        rt = maxTs(i);
        t0 = map(:,i);
        flg = t0 < rt; 
        id1=find(flg, 1);
        id0=find(dTs(:,1),1);
        if id0<id1-1
            t0(id0:id1-1) = interp1(t0([id0,id1-1]), [1 rs],t0(id0:id1-1)) .* t0(id0:id1-1);
        end
        t0(flg) = t0(flg)*rs;
        nMap(:, i) = t0;
    end
end

