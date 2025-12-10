function [sTrqMap, sFluxMap, sMapLdq, sMapLdqS] = ...
                                        MappingController(o, stt)
    arguments
        o       (1,1)   MotorModel
        stt         (1, 1) int32 = MapType.MeanMap + MapType.SetZeroQ0 ...
                                 + MapType.MirrorQ + MapType.CorrectMean + MapType.MinRange ... 
                                 + MapType.OnlyDrvIq  + MapType.OnlyWeakId;
    end
   
    import Data.MapType

    defM = o.defMap;
    dIdq = defM.dIdq;
    % dFdq = defM.dIdq;

    [sTrqMap, sFluxMap]  = o.MappingTrqToIdq(stt);
    [sMapLdq, sMapLdqS] = o.MappingIdqToLdq(dIdq, stt);
end