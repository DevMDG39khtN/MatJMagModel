function cmd = ExtMapTgt(tda,fid,is)
	td = squeeze(tda(:,:,is,:,:,:,:));
	cmd = cell(size(td,1:2));
	for i = 1:size(cmd, 1)
		for j = 1:size(cmd, 2)
			tds = squeeze(td(i,j, :,:,:,:));
			sz0 =size(tds,1,2);
			cmd{i,j} = reshape(tds(fid), sz0);
		end
	end
end