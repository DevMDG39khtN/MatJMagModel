function axes = MapAxes(rng, div, eps)
    if nargin<3
        eps = 0.01;
    end
    if iscell(rng)
        rng0 = rng;
        if size(rng0, 1) < size(rng0, 2)
            rng = rng';
        end
        rng = cell2mat(cellfun(@(d) [d(1), d(end)], rng, "UniformOutput", false));
    end
    eps0 = eps;
    eps = div * eps;
    rng = rng(:,[1, end]);
    rngV = fix(rng ./ div) .* div;
    k = [-1, 1];
    rngC = mat2cell(rngV, ones(1,size(rng,1)), 2);
    axes = cellfun(@(d) d(1):(k((d(1) < d(end)) + 1) * div):d(end), rngC, "UniformOutput", false);
    flg = ~IsSame(rng, rngV, eps);
    rngC0 = mat2cell(rng, ones(1,size(rng,1)), 2);
    flgC0 = mat2cell(flg, ones(1,size(rng,1)), 2);
    axes = cellfun(@(ax, rv, fv) [rv(fv(1),1), ax, rv(fv(2),2)], axes, rngC0, flgC0, "UniformOutput", false);
    if isscalar(axes)
        axes = cell2mat(axes);
    end
end

function flg = IsSame(vs, vd, eps)
    flg = abs((vs - vd) ./ vs) <eps;
    chkv0 = abs(vs - vd) < eps;
    idf = abs(vs) < eps;
    flg(idf) = chkv0(idf);
end

