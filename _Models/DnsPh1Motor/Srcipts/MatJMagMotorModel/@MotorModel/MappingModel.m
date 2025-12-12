function [sTrqMap, sFluxMap] = MappingModel(o, stt)
    arguments
        o       (1,1)   MotorModel
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange
    end
   
    import Data.MapType
    defM = o.defMap;
    dIdq = defM.dIdq;
    dFdq = defM.dFdq;

    sTrqMap  = o.MappingIdqToTrq(dIdq, stt);
    sFluxMap = o.MappingFdqToIdq(dIdq, dFdq, stt);
end