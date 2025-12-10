function Vab = CnvDQtoAB(Vdq, th)
    if isnan(Vdq)
        Vab = nan;
        return
    end
    %% JMAGの励磁順が逆なため
    vcos=cosd(th + 180);
    vsin=sind(th + 180);
    Vab = [sum([vcos; -vsin] .* Vdq); sum([vsin; vcos] .* Vdq)];
end