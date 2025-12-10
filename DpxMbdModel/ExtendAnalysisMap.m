function m = ExtendAnalysisMap(cmIdqDs, vIds, vIqs, aDats)
	% データ妥当性
	nsz= size(cmIdqDs);
	if length(nsz) ~=2 || nsz(2) ~= 4
		error("Idq Data should be required [n x 4] Matrix [%5d, %2d](%3d)" ...
				, nsz(1), nsz(2), ndims(nsz));
	end
	% 2重系電流条件マップ
	[mIqA0s, mIdA0s, mIqB0s, mIdB0s] = ndgrid(vIqs, vIds, vIqs, vIds);
	% 2重系 Idq map 組合せ　A-B Id-q 昇順]]
	svIdqAB0s = sortrows([mIdA0s(:), mIqA0s(:), mIdB0s(:), mIqB0s(:)], 1:4);
	fzIdqAB0s = false(1, size(svIdqAB0s, 1)); 

	[mIdCs, mIqCs]=meshgrid(vIds, vIqs);	% 片側IdqMap 条件
	svIdqCs = sortrows([mIdCs(:), mIqCs(:)], 1:2);	% 片側 IdIq ソート 順

	idPabD = {(1:2), (3:4)};	% Side-A, Side-B index

	tas0 = cmIdqDs;
	cvs0 = round([tas0(:, idPabD{1}); tas0(:, idPabD{2})]/100)*100;

	[cIdqA, ia, ic] = unique(round(tas0(:, idPabD{1}), 5), 'rows');
	% Side-A   解析マップ Side-B データマップ
	svIdqAB1s = [repelem(cIdqA, size(svIdqCs,1),1), ...
					repmat(svIdqCs, size(cIdqA, 1), 1)];
	fzIdqAB1s = false(1, size(svIdqAB1s, 1)); 

	tas = tas0;
	fas = false(length(tas), 1);
	tms = svIdqAB1s;
	fms = false(length(tms), 1);
	faa = fas;
	
	cvIdqs = cell(1, 2);
	for i=1:2
		[~, idc] = unique(round(cIdqA(:,i), 5));
		cvIdqs{i} = sort(cIdqA(idc, i));
	end
	cmMvs = cell(length(cvIdqs{2}), length(cvIdqs{1}));
	[mIds, mIqs] = meshgrid(cvIdqs{1}, cvIdqs{2});
	vIdqs = [mIds(:), mIqs(:)];

	nl=0;
	while any(~faa)
		nl = nl+1;
		tav = tas(~faa, idPabD{1});
		tcA = tav(1, :);
		vIdx = find(all(abs(vIdqs-tcA)<1.e-5, 2), 1);
		[rIdx, cIdx] = ind2sub(size(mIds), vIdx);
		fa = all(abs(tas(:, idPabD{1}) - tcA) < 1.e-5, 2);
		na = sum(fa);
		fm = all(abs(tms(:, idPabD{1}) - tcA) < 1.e-5, 2);
		nm = sum(fm);
		fprintf("%04d:[%5d/%5d]-(%s)\n",nl, nm, na, sprintv("%8.1f",tcA))
		faa = faa | fa;
		if na < 3
			cmMvs{rIdx, cIdx} = {tcA, tas(fa, idPabD{2})};
			continue;
		end
		fprintf(">>>>> Mapping\n");
		cmMvs{rIdx, cIdx} = {tcA, size(mIdCs), tas(fa, idPabD{2})};
		% 一致データの確認
		smIdqCs =[repmat(tcA, size(svIdqCs,1), 1), svIdqCs];
		[f0, mIdx0] = ismembertol(svIdqAB1s, smIdqCs, 1.e-5, 'ByRows', true);
		if any(xor(fm, f0)) || sum(fm) ~= size(smIdqCs, 1)
			warning('Mimatch or lack map procece')
		end

		if any(fms & fm, "all")
			warning('Multiple Tgt. Anl. Data Exist.')
		end
		fms = fms | fm;
		if any(fas & fa, "all")
			warning('Multiple Tgt. Anl. Data Exist.')
		end
		fas = fas | fa;
	end

	tmb = svIdqAB0s;
	fprintf("To Full Map tms:[%5d/%5d]-> tma:[%5d]\n", ...
				size(tms, 1), sum(fms), size(tmb, 1));
	fmb = true(size(tmb, 1));
	while any(fmb)
		tbv = tmb(fmb, :); 
		tcB = tbv(1, idPabD{2});
		fb = all(abs(tms(:, idPabD{2}) - tcB) < 1.e-5, 2);
	end

	m = [];
end

function tMapData = SetMapData(vIds, vIqs, tMapData, tIdqABs, tDats)
	[mIqA0s, mIdA0s, mIqB0s, mIdB0s] = ndgrid(vIqs, vIds, vIqs, vIds);
	% 2重系 Idq map 組合せ　A-B Id-q 昇順]]
	mIdqABs = sortrows([mIdA0s(:), mIqA0s(:), mIdB0s(:), mIqB0s(:)], 1:4);
	tm = mIdqABs;
	tv = tIdqABs;
	ta = tv(:, 1:2); tb = tv(:, 3:4);
	if all(ismembertol(ta, tb, 1.e-5, 'ByRows',true), 1)
		[tIqs, tIds] = meshgrid(vIds, vIqs);
		vIdqs = reshape([tIds(:), tIqs(:)]',[2, size(tIqs)]);
		tIdqAB = repmat(vIdqs, [2, size(vIdqs)]);
		% Map Data 作成
		mdat = true(size(mIds));
		f = ismembertol(mIdqABs, tIdqAB, 1.e-5, 'ByRows',true);
	end

end


function sz = sprintv(fmt, d)
	sz = sprintf(sprintf('%s, ', fmt), d);
	sz = sz(1:end-2);
end
