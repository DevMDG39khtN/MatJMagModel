function [Vuvw, Vab, Vdq]=CnvDQtoUVW(Vdq, th)
    if isnan(Vdq)
        Vab = nan;
        Vuvw = nan;
        return
    end
    %% JMAGの励磁順が逆なため
    vcos=cosd(th + 180);
    vsin=sind(th + 180);
    Vab = [sum([vcos; -vsin] .* Vdq(1:2,:)); sum([vsin; vcos] .* Vdq(1:2,:))];
    Vab(3, :) = Vdq(3, :);
    % th = o.axTime.theta;
    %%
    % M = sqrt(2/3) * [1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];
    M = sqrt(2/3) * [1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2; [-1, -1, -1] / sqrt(2)];
    Vuvw = M' * Vab;
end