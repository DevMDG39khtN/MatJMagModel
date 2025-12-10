function tMap = MappingIdqToTrq(o, dIdq, skId, stt)
    arguments
        o       (1,1)   MotorModel
        dIdq    (1,1)   double
        skId            int32 = []
        stt     (1,1)   = MapType.MirrorQ + MapType.CorrectMean ...
                        + MapType.MinRange
    end

    import Data.MapType
    import Data.Type
    %% Check Torque Data
    if ~isKey(o.mData, Type.TorqueD)
        error("Not Exist Torque Data.");
    end
    mdt = o.mData(Data.Type.TorqueD);
    if isempty(mdt)
        error("Torque Data is Empty");
    end
    stt = bitor(stt,MapType.MirrorQ + MapType.CorrectMean); 
    %% Create Torque Map
    if bitand(stt, Data.MapType.MeanMap) %+Data.MapType.CorrectZero)
        [mData, mRng, axIdq] = mdt.MappingAvgDQ(dIdq, skId, stt);
    else
        [mData, mRng, axIdq] = mdt.MappingDQ(dIdq, skId, stt);
    end

    tMap = [];
    tMap.Axis = axIdq;

    tMap.Map = mData;
    tMap.Range = mRng;
end