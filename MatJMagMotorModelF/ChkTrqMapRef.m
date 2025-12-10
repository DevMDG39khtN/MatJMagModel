function ChkTrqMapRef(map, simDat ,fh)
    ayt = map.Axis.rTrq;
    axn = map.Axis.cNrpm;
    azv = map.Axis.zVdc;

    tm = map.Map.D;

    ts = simDat.time;
    dts = simDat.signals(1).values;
    dns = simDat.signals(2).values;
    dvs = simDat.signals(3).values;
    dis = simDat.signals(4).values;

    dv0 = mean(dvs);

    [t1, t2] =meshgrid(axn, ayt);
    t3 = zeros(size(t1)); t3(:)=dv0;

    tmap = interp3(axn,ayt, azv, tm, t1, t2, t3, 'linear');

    tc0 = interp2(axn, ayt, tmap, dns, dts, 'linear');

    clf(fh);
    tfo =tiledlayout(fh, 1, 2);
    axm = nexttile(tfo);
    axt = nexttile(tfo);

    [pcm, pca] = contourf(axm,axn,ayt,tmap, -800:50:0, 'ShowText', 'on');
    cl = line(axm, dns, dts, 'LineWidth', 2, 'Color', 'r');
    grid(axm, 'on');
    xlabel(axm, '回転数 [rpm]');
    ylabel(axm, 'トルク [Nm]');
    title(axm, 'トルク->IdReq マップ');



return