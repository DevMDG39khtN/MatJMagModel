function [MsU, vlsU] = SplitCntMx(M, vls)
    
    % fprintf('>>>>>> Convert Contour Matrix\n');

    if ~isvector(vls)
        error('level value should be vector %3d-%3d', size(vls, 1), size(vls, 2))
    end
    vchk = unique(vls,'stable');
    if length(vchk) ~= length(vls) % スカラー値の場合複数できる
        error('level value is not unique');
    end
    flgs = zeros(1, length(vls));

    Ms = cell(1, length(vls));
    i = 1;
    maxv = length(M);
    while i < maxv
        nc = M(2, i); v = M(1, i);
        n = find(abs(vls-v) < 1.0e-8, 1);
        vs = M(:, (1:nc) + i);
        i = i + nc + 1;
        ns = 1; i0 = i; ntot = 0;
        while i0 <= maxv
            nc0 = M(2, i0); v0 = M(1, i0);
            if abs(v-v0) < 1.e-8
                ns = ns + 1;
                i0 = i0 + nc0 + 1;
                ntot = ntot + nc0;
            else
                break;
            end
        end
        if ns > 1
            warning('Multi-Contour line detected. @ %f (%03d)', v, ns);
            Ms0 = zeros(size(M,1), ntot+ns-1);
            i0 = i; nc0 = nc; ik = 1;
            for j = 1:ns
                Ms0(:, ik:(ik + nc0)) = vs;
                Ms0(:, ik + nc0 + 1) = nan;
                ik = ik + nc0 + 2;
                i0 = i0 + nc0 + 1;
                if i0 <= maxv
                    nc0 = M(2, i0);
                    vs = M(:, (1:nc0) + i0);
                else
                    clear nc0
                end
            end
        else
            Ms0 = vs;
        end
        clear vs
        if isempty(n)
            warning('Contour Value is not in Level Values (%f)', v);
            continue;
        end
        Ms{n} = Ms0;
        flgs(n) = true;
    end
    MsU = Ms(flgs == 1);
    vlsU = vls(flgs == 1);
end

