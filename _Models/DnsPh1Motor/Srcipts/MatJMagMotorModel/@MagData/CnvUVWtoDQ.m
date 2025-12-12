function [Vdq, Vab, Vuvw]=CnvUVWtoDQ(Vuvw, th)
    if isnan(Vuvw)
        Vab = nan;
        Vdq = nan;
        return
    end
    % th = o.axTime.theta;
    %%
    M = sqrt(2/3) * [1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2];
    % M = sqrt(2/3) * [1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2; [-1, -1, -1] / sqrt(2)];
    Vab = M * Vuvw;

    %% JMAGの励磁順が逆なため
    vcos=cosd(th + 180);
    vsin=sind(th + 180);
    Vdq = [sum([vcos; vsin] .* Vab(1:2,:)); sum([-vsin; vcos] .* Vab(1:2, :))];
    % Vdq(3,:) = Vab(3, :);
end