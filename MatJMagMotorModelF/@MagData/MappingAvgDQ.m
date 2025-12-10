function [map, sRngs, axIdq] = MappingAvgDQ(o, dIdq, skId, stt, nPara)
    arguments
        o       (1,1)   MagData
        dIdq    (1,1)   double
        skId            int32       = []
        stt     (1,1)   int32   = MapType.MirrorQ ...
                                + MapType.CorrectMean ...
                                + MapType.SetZeroQ0 ...
                                + MapType.MinRange
        nPara   (1,1)   double  = 1
    end

    import Data.MapType


    if isempty(o.data)
        map = [];
        axIdq = [];
        sRngs = [];
        return
    end

    [map0, sRngs, axIdq] = o.MappingDQ(dIdq, skId, stt, nPara);
    if ndims(map0) == 4
        map = mean(map0(:, :, :, 1:end-1), 4);
    elseif ndims(map0) == 3
        map = mean(map0(:, :, 1:end-1), 3);
    else
        error("Not supported Dimension : %d", ndims(map0))
    end
    
    %% 0 @ Q軸 = 0 
    vIqs = axIdq.Iq;
    if bitand(stt, MapType.SetZeroQ0)
        iIq0 = abs(vIqs) < 1.e-6;
        if sum(iIq0) > 1
            error("Exists Multiple Iq = 0 Data");
        end
        if o.type == Data.Type.TorqueD
            map(iIq0, :) = 0;
        else
            map(iIq0, :, 2) = 0;
        end
    end

    %% 補間結果の最大最小値 (平均値）
    fmin = @(d) min(d, [], "all"); fmax = @(d) max(d, [], "all");
    if ndims(map) == 3
        sRngs.D = [fmin(map(:, :, 1)), fmax(map(:, :, 1))];
        sRngs.Q = [fmin(map(:, :, 2)), fmax(map(:, :, 2))];
    else
        sRngs = [fmin(map(:, :)), fmax(map(:, :))];
    end

    %% 時間軸データの削除
    axIdq = rmfield(axIdq, 'Theta');
end

