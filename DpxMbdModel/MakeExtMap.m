function m = MakeExtMap(cmIdqDs, vIds, vIqs, aDats)
	% データ妥当性
	nsz= size(cmIdqDs);
	if length(nsz) ~=2 || nsz(2) ~= 4
		error("Idq Data should be required [n x 4] Matrix [%5d, %2d](%3d)" ...
				, nsz(1), nsz(2), ndims(nsz));
	end

	% 2重系電流条件マップ
	[mIqA0s, mIdA0s, mIqB0s, mIdB0s] = ndgrid(vIqs, vIds, vIqs, vIds);
	% mIdqABs = sortrows([mIdA0s(:), mIqA0s(:), mIdB0s(:), mIqB0s(:)], 1:4);
	vIdqABs = [mIdA0s(:), mIqA0s(:), mIdB0s(:), mIqB0s(:)];
	mIdqABs = cat(5, mIdA0s, mIqA0s, mIdB0s, mIqB0s);
	mIdqABs = permute(mIdqABs, [5,1:4]);

	m1 = mIdqABs(:,:)-vIdqABs';
	if any(abs(m1)>1.e-5,"all")
		error('Idq Conds Matrix construction error');
	end

	dIdqABs = cmIdqDs;
	tDat = aDats;
	szd = size(tDat);
	mDat = nan([szd(1:end-1), size(mIdA0s)]);
	fds = false(size(mIdA0s));

	fn0s = all(abs(dIdqABs(:, 1:2) - dIdqABs(:, 3:4)) < 1.e-5, 2);
	dIdqAB0s = dIdqABs(fn0s, :);
	tDat0 = tDat(:,:,:,fn0s);
	[mDat, fds] = SetMapData(vIds, vIqs, mIdqABs, mDat, dIdqAB0s, tDat0, fds);
	fn1s = all(abs(dIdqABs(:, 3:4)) < 1.e-5, 2);
	dIdqAB1s = dIdqABs(fn1s, :);
	tDat0 = tDat(:,:,:,fn1s);
	[mDat, fds] = SetMapData(vIds, vIqs, mIdqABs, mDat, dIdqAB1s, tDat0, fds);
	fn2s = all(abs(dIdqABs(:, 1:2))<1.e-5, 2); % & all(abs(dIdqABs(:, 3:4)) > 1.e-5, 2);
	dIdqAB2s = dIdqABs(fn2s, :);
	tDat0 = tDat(:,:,:,fn2s);
	[mDat, fds] = SetMapData(vIds, vIqs, mIdqABs, mDat, dIdqAB2s, tDat0, fds);

	m = struct('map',mDat, 'axis',struct('Id',vIds, 'Iq',vIqs), 'axm', mIdqABs, ...
				'dat', tDat0, 'axd', dIdqABs, 'flg', fds);
	% tDat0 はテンポラリ
end

function [tMapData, fds] = SetMapData(vIds, vIqs, mIdqABs, tMapData, ...
								dIdqABs, tDats, fds)
	eps = 1.e-5;

	ta = dIdqABs(:, 1:2); tb = dIdqABs(:, 3:4);
	% 補間用片側 Idq map 軸
	[tIds, tIqs] = meshgrid(vIds, vIqs);
	vIdq0s = permute(cat(3, tIds, tIqs),[3,1:2]);	% Id, Iq 並びを先頭
	zIdq0s = zeros(size(vIdq0s));	% 別側 
	isNoZ = true;
	if all(abs(ta - tb) < eps, 2)
		% sideA = sideB
		vIdqs = repmat(vIdq0s, [2, 1, 1]);
		isNoZ = false;
	elseif all(abs(tb)<1.e-5)
		vIdqs = cat(1, vIdq0s, zIdq0s);
	elseif all(abs(ta)<1.e-5)
		vIdqs = cat(1, zIdq0s, vIdq0s);
	else
		fprintf("Not processed .....")
	end

	% 対象データインデックス
		% 出力マップ Idq Index と 補間map Idq Index の紐付
	fvs0 = ismembertol(mIdqABs(:,:)', vIdqs(:,:)', eps, 'ByRows', true);
	    % All 0
	eOff = 0;
	nzIdt = true(numel(tIds), 1);
	if isNoZ
		zIdm = all(abs(mIdqABs(1:4,:)')<eps, 2);
		fvs0 = fvs0 & ~zIdm;
		eOff = sum(zIdm); 
		if eOff == 0
			warning("All zero data not exist");
		elseif eOff > 1
			warning("Multiple zero data exist");
		end
		nzIdt = ~all(abs(vIdqs(:,:)')<eps,2);
	end
		% 結果の検証
	if sum(fvs0) ~= numel(tIds) - eOff	% 補間map Index が出力map Index に存在しない
		error('mismatch map data');
	end
	if any(fds(:) & fvs0, 'all') % 既に計算されている出力map Index 有
		error('multiple mapped data index exists.');
	end
	fvs =  reshape(fvs0,size(fds)); % 紐付されたindex配列を多次元に変換

	% Map Data 作成
	mdat = true(size(tIds));
	for i0 = 1:size(tMapData,1)
		for i1 = 1:size(tMapData,2)
			for i2 = 1:size(tMapData,3)
				fprintf('---%4d, %4d, %4d\n', i0, i1,i2);
				tMapData(i0, i1, i2, fvs)=shiftdim(mdat(nzIdt),-3);
				disp(size(tMapData))
			end
		end
	end
	fds = fds | fvs; % 計算済 Indexとして登録
end

function sz = sprintv(fmt, d)
	sz = sprintf(sprintf('%s, ', fmt), d);
	sz = sz(1:end-2);
end
