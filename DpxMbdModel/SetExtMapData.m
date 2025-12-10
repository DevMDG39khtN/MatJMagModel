function [tMapData, fds] = SetExtMapData(m, tMapData, fds)
	vIds	 = m.axis.Id;
	vIqs	 = m.axis.Iq;
	mIdqABs  = m.axm;
	tMapData = m.map;
	dIdqABs  = m.axd;
	tDats	 = m.dat;
	fds		 = m.flg;
%%
	% データ妥当性
	nsz= size(mIdqABs(:,:)');
	if length(nsz) ~=2 || nsz(2) ~= 4
		error("Idq Data should be required [n x 4] Matrix [%5d, %2d](%3d)" ...
				, nsz(1), nsz(2), ndims(nsz));
	end

	eps = 1.e-5;


	[tIds, tIqs] = meshgrid(vIds, vIqs);	% 補間用片側 Idq map 軸
	tIdqs = cat(2, tIds(:), tIqs(:));

	tIdIqABs = cell(1,4);
	for i = 1:size(dIdqABs, 2)
	   [~, ia] = unique(round(dIdqABs(:,i), 5));
	   tIdIqABs{i} = sort(dIdqABs(ia, i));
	end

	ftd = true(size(dIdqABs,1), 4);

	tdt0 = tMapData;

	msIdqAB = mIdqABs(:,:)';

	fds0 = fds(:);
	tFds = fds(:);
	for nn = 1:2
		fprintf('----- Dat Map %d:2\n', nn)
		flg0= ftd(:, nn);
		tid = (2*nn-1):(2*nn);
		while any(flg0)
			tv0 = dIdqABs(flg0, :);
			if isempty(tv0), warning('No Data'); end
			% 片側サイドのIdq毎の解析結果を抽出
			tv	= tv0(1, :);	%  解析 片側Idq値
			f1	= all(abs(tv0(:, tid) - tv(tid)) < eps, 2); % 同一値抽出
			tvs = tv0(f1, :);
			flg0(flg0) = flg0(flg0) & ~f1;	% 処理済データフラグ追加
			ftd(:, nn) = flg0;
			% 既存のMap補間値からも抽出
			fM0 =all(abs(msIdqAB(:,tid)-tv(tid))<eps,2);
			fmd = tFds & fM0; % 既にmap化されている軸フラグ
			if all(fmd(fM0))
				fprintf("all data processed @ %s\n", sprintv("%8.1f", tv));
				continue;
			end
			if sum(fmd) == 0
				fprintf("----- No map data @ %s\n", sprintv("%8.1f", tv));
			else
				fprintf("----- Some mapped data (%4d) Exist @ %s\n", ...
							sum(fmd), sprintv("%8.1f", tv));
				tmv = msIdqAB(fmd, :);
				tgs = [tvs; tmv];
				[~, ia] = unique(round(tgs, round(-log10(eps))), 'rows');
				tvg = sortrows(tgs(ia, :), 1:4);
				if size(tvg, 1) ~= size(tvs, 1)
					fprintf(">>>>> Extend map data (%4d)->(%4d)[%4d]\n", ...
								size(tvs, 1), size(tvg, 1), size(tmv, 1));
				end
			end
			
			smnx = sprintv("%8.1f", [min(tvs);max(tvs)]);
			fprintf("(%5d):[%5d]-(%s)\n%s\n", sum(~ftd(:,nn)), sum(f1), ...
						sprintv("%8.1f",tv(tid)), smnx);

			if size(tvs,1) > 4
				fprintf("+++++ Create map data @ %s\n", sprintv("%8.1f", tv));
				zz=sum(tFds);
				tFds(fM0 & ~fmd) = true;
				fprintf("\t\t All:%4d, Before:%4d, tgt:%4d, new:%4d\n", ...
					sum(tFds), zz, sum(fM0), sum(fM0 & ~fmd));
				dmy = 0;
			end
		end

	end
	fds = reshape(tFds, size(fds));
	for i0 = 1:size(fds, 1)
		for i1 =1:size(fds, 2)
			tmv = squeeze(fds(i0, i1, :, :));
			if all(tmv, 'all')
				continue;
			end
			if any(~tmv([1,end],[1,end]),'all')
				warning('Not Box Data');
			end
			fds(i0,i1,:,:) = true;
			tmv = squeeze(fds(i0, i1, :, :));
		end
	end


	ftd(:) = true;
	for nn = 1:4
		fprintf('----- Dat Map Index %d\n', nn)
		while any(ftd(:, nn))
			flg0= ftd(:, nn);
			tv0 = dIdqABs(flg0, :);
			if isempty(tv0), warning('No Data'); end
			tv	= tv0(1, :);
			f1	= all(abs(tv0(:, nn) - tv(nn)) < eps, 2);
			ftd(flg0, nn) = flg0(flg0) & ~f1;
			tvs = tv0(f1, :);

			smnx = sprintv("%8.1f", [min(tvs);max(tvs)]);
			fprintf("(%5d):[%5d]-(%2d:%s) [%s]\n%s\n", sum(~ftd(:,nn)), sum(f1), ...
						nn, sprintv("%8.1f", tv(nn)), sprintv("%8.1f", tv), smnx);
		end
	end


end

function sz = sprintv(fmt, d)
	d = d(:, :); % 2次元化
	if size(d,1) > size(d, 2)
		d = d'; 
	end
	sz=[];
	for i = 1:size(d,1)
		sz0 = sprintf(sprintf('%s, ', fmt), d(i,:));
		sz0 = sprintf('%s \n', sz0(1:end-2));
		sz = sprintf('%s%s', sz, sz0);
	end
	sz = sz(1:end-2);
end

		

