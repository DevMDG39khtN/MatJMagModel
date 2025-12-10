function mustBeScalarAndEven(A)
    if isscalar(A) && mod(A, 2) ~= 0
            throwAsCaller(MException(message('MATLAB:validators:mustBeScalarAndEven')));
    end
end