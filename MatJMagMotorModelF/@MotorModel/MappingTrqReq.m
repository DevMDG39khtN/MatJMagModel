function sMapReqTrqToIdq ...
                = MappingTrqReq(o, sTrqMap, sFdqMap, tMaxTrq0, defMap)
    if nargin<3
        defMap = o.defMap;
    end

    Tc = defMap.tempCoil;
    Ra = o.prmModel.RaT(Tc);
    
    if ~isfield(sTrqMap, "Avg")
        disp("Add Average Torque.")
        sTrqMap.Avg = MotorModel.MeanMap(sTrqMap);
    end
    if ~isfield(sFdqMap, "Avg")
        disp("Add Average Flux.")
        sFdqMap.Avg = MotorModel.MeanMap(sFdqMap);
    end
    
    sMapReqTrqToIdq = MappingWeakenField(...
        sFdqMap, sTrqMap, tMaxTrq0, defM, prms);

end