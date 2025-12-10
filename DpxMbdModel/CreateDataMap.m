function oDats = CreateDataMap(vIds, vIqs, zTh, tcDats, tIdqABs)
	fns = all(abs(tIdqABs(:, 1:2) - tIdqABs(:, 3:4)) < 1.e-5, 2);
	tIdqABs = tIdqABs(fns, :);

	nd = 1;
	if iscell(tcDats)
		nd = length(tcDats);
		oDats = cell(1, nd);
		for i=1:nd
			d0 = tcDats{i};
			sbs = repmat({':'}, 1, ndims(d0));
			sbs{end} = fns;
			tcDats{i} = d0(sbs{:});
		end
	end

	eps = 1.e-5;
	cvIdqs={vIds, vIqs, vIds, vIqs};
	
	cmIdqABs=cell(size(cvIdqs));
	[cmIdqABs{[4,3,2,1]}]=ndgrid(cvIdqs{[2,1,4,3]});
	vmIdqABs = reshape(permute(cat(5, cmIdqABs{:}),[5,1:4]), 4,[])';
	% 補間軸抽出　全ての行データが一致しないもの
	ntd = size(tIdqABs,1);  % 解析データ個数
	% 解析電流条件妥当性
	tflg = all(abs(tIdqABs - tIdqABs(1, :)) > eps, 1);
		% map電流条件作成
	cmIdqs = cell(1, 2);
	if sum(tflg) == 2
		[cmIdqs{:}] = meshgrid(cvIdqs{tflg});
		vmIdqs = reshape(permute(cat(3,cmIdqs{:}),[3,1,2]), 2,[])';
		vc0 = tIdqABs(1, ~tflg); % 固定値電流データ
		vaIdqABs = [vmIdqs, repmat(vc0, size(vmIdqs,1), 1)];
		tids = [find(tflg), find(~tflg)];	% 元の列順に戻す
		vaIdqABs(tids, :) = vaIdqABs;
	elseif all(abs(tIdqABs(:, 1:2) - tIdqABs(:, 3:4)) < eps, 2)
		[cmIdqs{:}] = meshgrid(cvIdqs{1:2});
		tids = 1:4;
		vmIdqs = reshape(permute(cat(3,cmIdqs{:}),[3,1,2]), 2,[])';
		vaIdqABs = [vmIdqs, vmIdqs];
	else
		error('マップ作成のためのAB相dq軸電流条件不正')
	end
	mdFlg = ismembertol(vmIdqABs, , eps, 'ByRows',true);
	% nf = length(tIds);
	% if nf == 0
	% 	if all(abs(tIdqABs(:, 1:2) - tIdqABs(:, 1:2)) < eps, 2)
		% 	tIds = 1:2;
	% 	else
		% 	error('マップ作成のためのAB相dq軸電流条件不正')
	% 	end
	% elseif nf ~= 2
	% 	error('マップ作成のために，２軸固定必要')
	% end
	% clear nf
	for i=1:nd
		tDats0 = tcDats{i};
		ndt = ndims(tDats0); 
		if  ndt > 2
			nds = size(tDats0, 1);	% データ相次元数
			nth = size(tDats0, 2);	% 角度次元数
		elseif ndt == 2
			nds = 1;
			nth = size(tDats0, 1);
		end
		if nth ~= length(zTh)
			error('角度データ長不一致 :%d(%d)', length(zTh), nth);
		end
		if nds==3	% ３相データ ２重系電源
			tDats = CnvUVWtoDQ(tDats0, zTh);
		else % トルク等データ次元合わせ
			tDats = reshape(tDats0, 1, nth, 1, []);
		end
		mDats = nan([size(tDats, 1:ndims(tDats)-1), ...
						cellfun(@length, cvIdqs([2,1,4,3]))]);
		for id1 = 1:size(tDats, 1)			% データ軸次元
			for id3 = 1:size(tDats, 3)		% ２重系電流次元
				fprintf('>>>>>> [%04d]:Data Ax[%3d]- Side[%3d]]\n', i, id1, id3)
				nc = 0;
				for id2 = 1:size(tDats,2)	% 電気角次元 
					tdv = squeeze(tDats(id1, id2, id3, :));
					mds = squeeze(mDats(id1, id2, id3, :,:,:,:));
					if any(~isnan(mds(mdFlg)), "all")
						warning('Already Defined map');
						nzd=reshape(mds(mdFlg),size(mds,1:2));
					end
					nc = nc + 1;
					% if mod(nc, 15) == 0
					% 	fprintf("\t\ttheta:%5.3f\n", zTh(nc));
					% end

					tIds = tIdqABs(:,tids(1)); tIqs = tIdqABs(:,tids(2));
					sfn = scatteredInterpolant(tIds, tIqs, tdv, "natural");
					mdv = sfn(cmIdqs{1}, cmIdqs{2});
					mDats(id1, id2, id3, mdFlg) = mdv(:);
				end
			end
		end
		oDats{i} = mDats;
	end
end
