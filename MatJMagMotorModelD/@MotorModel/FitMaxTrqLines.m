function [tblMaxTrq0, tblMaxTrqBase, pFitEq] = FitMaxTrqLines(o, sMapTrq, defMap)
    if nargin<3
        defMap = o.defMap;
    end
    %
    prms = o.prmModel;
    maxIa = prms.maxIa;
    nOrdFit = defMap.nOrdFitMtl;


    t0 = sMapTrq;
    if isfield(t0.Axis,"Theta")
        warning("Map Data is trangient. will be averaged.")
        t0 = MotorModel.MeanMap(t0);
    end
    maxAxTrq = max(defMap.axTrqs) * 1.1;


    fitMaxTrq = min(maxAxTrq, max(t0.Range, [], "all"));

    [tblMaxTrq0, tblMaxTrqBase, pFitEq] = MaxTrqLines(sMapTrq, fitMaxTrq, maxIa, nOrdFit);

end