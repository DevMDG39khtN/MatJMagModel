classdef ModelParms < handle
    properties(Constant)
        kRaT = 0.00393;     % 抵抗温度係数
    end
    properties
        nP                  double {mustBeScalarAndEven}
        Ra          (1, 1)  double      % Coil Resistance@Phase   
        maxIa       (1, 1)  double      % Max Current
        nPrlCoil    (1, 1)  double      % Coil 並列数
        bMotSpd0    (1, 1)  double      % Model Analysis Mot. Speed
        tempRa      (1, 1)  double      % Ra @ Coil温度
    end

    properties(Dependent)
        Fa0         (1, 1)  double      % 解析時電気角周波数
    end

    methods
        function o = ModelParms(nP, Ra, maxIa, nCoil, nSpd, tAtRa)
            o.nP = nP;
            o.Ra = Ra;
            o.maxIa = maxIa;
            o.nPrlCoil = nCoil;
            o.bMotSpd0 = nSpd;
            o.tempRa = tAtRa;
        end

        % 電気角周波数
        function fas = Fa(o, nRpms)
            arguments
                o      (1, 1)   ModelParms
                nRpms  (1, :)   double
            end
            fas = o.nP * nRpms /120;  
        end

        % 解析時電気角周波数
        function fa0 = get.Fa0(o)
            fa0 = o.nP * o.bMotSpd0 /120;  
        end

        % 抵抗@指定温度
        function Ra = RaT(o, temp)
            arguments
                o      (1, 1)   ModelParms
                temp   (1, 1)   double = 20
            end
            Ra = (1 + o.kRaT*(temp - o.tempRa)) * o.Ra;
        end
    end
end