function [sTrqMap, sFluxMap] = MappingModel(o, skId, stt)
    arguments
        o       (1,1)   MotorModel
        skId            int32       = []
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.MinRange
    end
   
    import Data.MapType
    defM = o.defMap;
    dIdq = defM.dIdq;
    dFdq = defM.dFdq;

    sTrqMap  = o.MappingIdqToTrq(dIdq, skId, stt);
    sFluxMap = o.MappingFdqToIdq(dIdq, dFdq, skId, stt);
end