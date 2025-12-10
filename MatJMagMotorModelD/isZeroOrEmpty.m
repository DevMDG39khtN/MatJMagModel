function fStt = isZeroOrEmpty(d, eps)
    arguments
        d
        eps (1,1)   double = 1.e-3
    end

    fStt = isempty(d) || all(abs(d)<eps, "all") ;
end