function [sMapTrqReq, sMapFlux] = MappingTrqToIdq(o, stt)
    arguments(Input)
        o           (1, 1)  MotorModel
        stt         (1, 1) int32 = MapType.MeanMap + MapType.SetZeroQ0 ...
                                 + MapType.MirrorQ + MapType.CorrectMean ... 
                                 + MapType.MinRange ... 
                                 + MapType.OnlyDrvIq  + MapType.OnlyWeakId;
    end

    import Data.MapType

    %% Set Inner Parameter
    prms = o.prmModel;

    persistent sMapIdqToTrq dIdq0 sMapIdqToFdq tTmax0 tbMaxTrqs nOrd

    maxIa = prms.maxIa;
    defM = o.defMap;
    dIdq = defM.dIdq;
    nOrdFit = defM.nOrdFitMtl;

    vyTrq = defM.axTrqs;
    % vxNrpms = defM.axNrpms; vzVdc = defM.axVdcs;

    fmaxa = @(v) max(v, [], "all");
    % fnRng = @(v)[min(v, [], "all"), max(v, [], "all")];
    % fnLmt = @(v, vlm) min(v, vlm);

    isUpd = ~isequal(dIdq0,dIdq);
    if isempty(sMapIdqToTrq) || isUpd
        fprintf(">>>> Make Idq -> Trq Map\n")
        sMapIdqToTrq = o.MappingIdqToTrq(dIdq, stt);
    end

    if isempty(sMapIdqToFdq) || isUpd
        fprintf(">>>> Make Idq -> Fdq Map\n")
        sMapIdqToFdq = o.MappingIdqToFdq(dIdq, stt);
    end    
    sMapFlux = sMapIdqToFdq;
    dIdq0 = dIdq;
    
    tTmax = min(max(vyTrq)*1.1, fmaxa(sMapIdqToTrq.Range));
    if isempty(tbMaxTrqs) || ~isequal(nOrd, nOrdFit) ...
                          || ~isequal(tTmax0, tTmax) 
        fprintf(">>>> Make MaxTrqLine Table\n")
        tbMaxTrqs = MaxTrqLines(sMapIdqToTrq, tTmax, maxIa, nOrdFit);
    end
    nOrd = nOrdFit;
    tTmax0 = tTmax;

    sMapTrqReq = WeakenFieldMap(defM, sMapIdqToTrq, tbMaxTrqs, sMapIdqToFdq, prms);
end