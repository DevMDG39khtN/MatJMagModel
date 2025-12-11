function cds = ModThOff(td, th, off)
	if iscell(td)
		sz = size(td);
		% map毎に変換
		tdc=[];
		for j = 1:sz(2)
			tdm = cat(3,td{1,j}, td{2,j});
			tas=sqrt((tdm(:,:,1).^2 + tdm(:,:,2).^2)/3);
			tfs=atan2d(-tdm(:,:,1), tdm(:,:,2));
			tfs(abs(tas)<1.e-3) = -off;
			tdn = sqrt(3)*tas.*cat(3,sind(-(tfs+off)),cosd(-(tfs+off)));
			tdc = cat(4,tdc, tdn);
		end
		cds = cell(sz);
		for i= sz(1)
			for j = sz(2)
				tdm = td{i,j};
				Va = CnvDQtoUVW(tdm, th);
				th0 = th+off;
				Vs = CnvUVWtoDQ(Va, th0);
				cds{i,j} = Vs;
			end
		end
	else
		tdm = td;
		tas=sqrt((tdm(:,:,1).^2 + tdm(:,:,2).^2)/3);
		tfs=atan2d(-tdm(:,:,1), tdm(:,:,2));
		tfs(abs(tas)<1.e-3) = -off;
		tdn = sqrt(3)*tas.*cat(3,sind(-(tfs+off)),cosd(-(tfs+off)));
		cds = tdn;
		% tdm = td{i,j};
		% Va = CnvDQtoUVW(tdm, th);
		% th0 = th+off;
		% Vs = CnvUVWtoDQ(Va, th0);
		% cds = Vs;
	end
end