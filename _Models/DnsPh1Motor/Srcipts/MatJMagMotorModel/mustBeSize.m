function mustBeSize(value, nr, nc)
    if isvector(value)
        if length(value) ~= nr
            error("Should be same length to %4d", nr);
        end
    elseif ismatrix(value)
        if ~isequal(size(value), [nr, nc])
            error("Should be same size to (%4d, %4d)", nr, nc);
        end
    else
        error("Should be vector or matrix")
    end
end