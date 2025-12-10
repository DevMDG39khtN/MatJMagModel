function Vab = CnvUVWtoAB(Vuvw)
    if isnan(Vuvw)
        Vab = nan;
        return
    end
    %%
    M = sqrt(2/3) * [1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];
    Vab = M * Vuvw;
end