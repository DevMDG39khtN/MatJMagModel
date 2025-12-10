classdef MapType < int32
    enumeration
        None            (0x00000000)
        MeanMap         (0x00000001)
        SetZeroQ0       (0x00010000)
        OnlyDrvIq       (0x00020000)
        OnlyWeakId      (0x00040000)
        MirrorQ         (0x00000004)
        DivideMIf       (0x00000008)
        CorrectEnd      (0x00000010)
        CorrectMean     (0x00000020)
        CorrectPhase    (0x00000040)
        CorrectPeriod   (0x00000080)
        MinRange        (0x00000100)
        MaxModRatio     (0x00000200)
        LimitMaxIa      (0x00000400)
        MatWrite        (0x00004000)
        MatRead         (0x00008000)
    end
end