function MakeDuplexMap(vIdq, vIqs)
	% 2重系電流条件マップ
	[mIqA0s, mIdA0s, mIqB0s, mIdB0s] = ndgrid(vIqs, vIds, vIqs, vIds);
	% 2重系 Idq map 組合せ　A-B Id-q 昇順
	svIdqAB0s = sortrows([mIdA0s(:), mIqA0s(:), mIdB0s(:), mIqB0s(:)], 1:4);
	fzIdqAB0s = false(1, size(svIdqAB0s, 1)); 

	idABs = {{1:2},{3:4}};
	svIdqABts = svIdqAB0s;
	fzIdqABts = fzIdqAB0s;	% マップ処理済みフラグ
	while ~isempty(svIdqABts)
		% map作成 条件
		siAt = svIdqABts(1, idABs{1});	% map作成 SideA Idq値
			%  同一 SideA Idq値　解析結果リスト
		fzIdqAts = all(abs(svIdqAB0s(:, idABs{1}) - siAt) < 1.e-4, 2);	% フラグ
		tvIdqABs = svIdqAB0s(fzIdqAts, :);

		svIdqABts = svIdqABts(~fzIdqAts, :);
	end

end
