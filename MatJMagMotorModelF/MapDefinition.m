classdef MapDefinition < handle
    properties
        tempCoil    (1, 1) double = 25
        maxIa       (1, 1) double = 600
        dIdq        (1, 1) double = 10
        dFdq        (1, 1) double = 0.001
        axTrqs      (1, :) double = 0:50:3000
        axNrpms     (1, :) double = 0:10:1500
        axVdcs      (1, :) double = 500:20:900
        rLmtVdc     (1, :) double = 0.95
        isOvrMod    (1, 1) logical = false
        nOrdFitMtl  (1, 1) int32 = 4
    end

    properties(Access = public)
        maxMrRatio
        AxesMapIdq
        SizeCmap
    end

    methods
        function o = MapDefinition(dMs, axList, prms, vlmt, isOv, nFit)
            o.dIdq = dMs(1);
            o.dFdq = dMs(2);

            o.axTrqs  = axList{1};
            o.axNrpms = axList{2};
            o.axVdcs  = axList{3};

            o.maxIa      = prms(1);
            o.tempCoil   = prms(2);
            o.rLmtVdc    = vlmt;
            o.isOvrMod   = isOv;
            o.nOrdFitMtl = nFit;
        end

        function v = get.maxMrRatio(o)
            if o.isOvrMod
                v = sqrt(6) / pi;
            else
                v = 1 / sqrt(2);
            end
        end

        function v = get.AxesMapIdq(o)
            v = {o.axTrqs, o.axNrpms, o.axVdcs};
        end

        function v = get.SizeCmap(o)
            v = [length(o.axTrqs), length(o.axNrpms), length(o.axVdcs)];
        end

        function set.dIdq(o, v)
            if v ~= o.dIdq
                o.dIdq = v;
            end
        end

        function set.dFdq(o, v)
            if v ~= o.dFdq
                o.dFdq = v;
            end
        end

        % function disp(o)
        %     fprintf(">>>>> Control Trq to Idq Order Map Size\n")
        %     fprintf("\t x:Trq %4d\n", length(o.vTrqs));
        % end
    end
end
