classdef MbdModel < handle
	properties(Constant)
		xIds = [-6000:500:-1500, -1200:100:200, 500:500:6000];
		xIqs = [0:100:1200, 1500:500:6000];
		xIdms = [-6000:1000:-1500, -1200:200:200, 1000:1000:6000];
		xIqms = [0:200:1200, 2000:1000:6000];
	end
    properties(SetAccess = immutable)
		ax		% axis : ([thera, time], period]
		cnds	% IaCond : [def, real], [IdqA, IdqB], num]
		dats	% Trq[1, prd, num]. Tri[phase, prd, Side(AB), num]
		dTyps	% [type, area(AB), num]
		dNams% 	%
		dPNams %
	end
	properties(SetAccess=private, GetAccess=public)
		eps = 1.e-5;
		dFmt = "%8.1f"
		
		map = {};
		sttSet = [];
	end

	

	properties(Dependent)
		szMapIdqABs
		vMapIdqABs
		cmMapIdqABs
		vFlgNrmData
		vFlgZeroSizeB
		vFlgZeroSizeA
		vIdqABs
		vIds
		vIqs
		thE
		cvIdqs
		rdIdIqs
	end
	
	% ---------------------->>>>>
	methods(Access = private)
		function sz = sprintv(~, fmt, d)
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

		function o = InitMap(o)
			o.map = cell(size(o.dats));
			for i = 1:length(o.dats)
				td = o.dats{i};
				nd = ndims(td);
				if nd <4
					td = reshape(td, size(td,1), size(td,2), 1, []);
					nd = ndims(td);
				end
				o.map{i} = nan([size(td, 1:nd-1), o.szMapIdqABs]);
				o.sttSet = false(o.szMapIdqABs);
			end
		end

		%% Map生成用電流軸
		function [cmIdqs, vIdqs, tids] = SetTgtIdqAxis(o, tIdqs)			% 解析電流条件妥当性
			if all(abs(tIdqs(:, 1:2) - tIdqs(:, 3:4)) < o.eps, 2)
				tFlg = [true, true, false, false];
				isSameAB = true;
			else
				tFlg = ~all(abs(tIdqs - tIdqs(1, :)) < o.eps, 1);
				isSameAB = false;
			end
			cmIdqs = cell(1, 2);
			if sum(tFlg) == 2
				[cmIdqs{:}] = meshgrid(o.cvIdqs{tFlg});
				vmIdqs = reshape(permute(cat(3,cmIdqs{:}),[3,1,2]), 2,[])';
				if isSameAB
					vcs = vmIdqs;
				else
					vc0 = tIdqs(1, ~tFlg); % 固定値電流データ
					vcs = repmat(vc0, size(vmIdqs,1), 1);
				end
				vIdqs = [vmIdqs, vcs];
				tids = [find(tFlg), find(~tFlg)];	% 元の列順に戻す
				vIdqs(:, tids) = vIdqs;
			else
				error('マップ作成のためのAB相dq軸電流条件不正')
			end
		end
		%% 補間データ抽出
		function ocDats = ExtractTgtData(o, flgs, isMap)
			ocDats = cell(size(o.dats));
			for i = 1:length(ocDats)
				if ~isMap
					d0 = o.dats{i};
					sbs = repmat({':'}, 1, ndims(d0));
					sbs{end} = flgs;
					ocDats{i} = d0(sbs{:});
				else
					d0 = o.map{i};
					sbs = repmat({':'}, 1, 4);
					sbs{end} = flgs;
					ocDats{i} = d0(sbs{:});
				end
			end
		end

		%% Vector Idq軸データ (obsolete)
		function vIdqABs = VctIdqABs(o)
			cmIdqABs=cell(size(o.cvIdqs));
			[cmIdqABs{[4,3,2,1]}]=ndgrid(o.cvIdqs{[2,1,4,3]});
			vIdqABs = reshape(permute(cat(5, cmIdqABs{:}),[5,1:4]), 4,[])';
		end
	
		%% 補間mapデータ作成
		function GenMap(o, tDat, tIdqs, cmIdqs, mdFlg, i, isDef)
			for id1 = 1:size(tDat, 1)			% データ軸次元
				for id3 = 1:size(tDat, 3)		% ２重系電流次元
					% fprintf('>>>>>> [%04d]:Data Ax[%3d]- Side[%3d]]\n', i, id1, id3);
					% nc = 0;
					for id2 = 1:size(tDat, 2)	% 電気角次元 
						tdv = squeeze(tDat(id1, id2, id3, :)); 
						tIds = tIdqs(:, 1); tIqs = tIdqs(:, 2);
						sfn = scatteredInterpolant(tIds, tIqs, tdv, "natural");
						mdv = sfn(cmIdqs{1}, cmIdqs{2});
						isDef0 = isDef(mdFlg);
						if sum(isDef)>0
							cdv = squeeze(o.map{i}(id1, id2, id3, isDef));
							if sum(isDef0) > 0
								mdc = mdv(isDef0);
								dlv = cdv - mdc;
								[dlx, id] = max(abs(dlv));
								if dlx > 1.e-3
									warning('Multiple map data has error %10.5e', dlv(id));
								end
							else
								warning('Already Defined flag mismatched');
							end
						end
						% 重複データを削除して保存               
						tf = mdFlg & ~isDef; 
						mdva=mdv(:);
						o.map{i}(id1, id2, id3, tf) = mdva(~isDef0);
					end
				end
			end
			% 
		end

		function o = MakeDpxMapData(o, isTgt, isMap)
			if nargin < 3
				isMap = false;
			end

			vmIdqABs = o.vMapIdqABs;
			if ~isMap
				vIdqs = o.vIdqABs;
				tvIdqABs = vIdqs(isTgt,:);			% 補間用解析結果Idq
			else
				tvIdqABs = vmIdqABs(isTgt,:);			% 補間用解析結果Idq軸			
			end
			tDats = o.ExtractTgtData(isTgt, isMap);		% 補間用解析結果データ
			[cmIdqs, tmIdqABs, tids] = o.SetTgtIdqAxis(tvIdqABs);	% 生成マップIdq軸

			mdFlg = ismembertol(vmIdqABs, tmIdqABs, o.eps, 'ByRows',true);

			isDef = o.sttSet(:) & mdFlg;
			th = o.ax(1,:); % o.ax 2 x 角度分解能
			% 各解析結果毎計算
			for i = 1:length(tDats)	
				tDat = tDats{i};
				ndt = ndims(tDat); 
				if  ndt > 2
					nds = size(tDat, 1);	% データ相次元数
					nth = size(tDat, 2);	% 角度次元数
				elseif ndt == 2
					nds = 1;
					nth = size(tDat, 1);
				end
				if nth ~= size(o.ax, 2)
					error('角度データ長不一致 :%d(%d)', length(th), nth);
				end
				% map生成用データ変換
				if ~isMap
					if nds==3 && ndt==4 %３相データ ２重系電源
						tdt = CnvUVWtoDQ(tDat, th);
					else % トルク等データ次元合わせ
						tdt = reshape(tDat, nds, nth, 1, []);
					end
				else
					tdt = tDat;
				end

				o.GenMap(tdt, tvIdqABs(:,tids(1:2)), cmIdqs, mdFlg, i, isDef);
				if i==2
					dummy = 0;
				end
			end
			o.sttSet(mdFlg) = true;
		end
	end
	% <<<<<----------------------

	% ---------------------->>>>>
	methods
		function o = MbdModel(tax, cs, ds, ts, nd, ncd)
			o.ax = tax;
			o.cnds = cs;
			o.dats = ds;
			o.dTyps = ts;
			o.dNams = nd;
			n = 0;
			nns = cell(1, length(ncd));
			for nc = ncd
				n = n+1;
				s = string(nc{1});
				if length(s) == 6
					ss = strings(2, 3);
					ss(1,:) = s(1:2:end);
					ss(2,:) = s(2:2:end);
				else
					ss = s;
				end
				nns{n} = ss;
			end
			o.dPNams = ncd;
		end

		function o = MakeDpxMotMap(o)
			o.InitMap();
			fprintf("=======   normal   status : IdqA == IdqB\n");
			o.MakeDpxMapData(o.vFlgNrmData);
			fprintf("======= fail-stedy status : IdqB ==0\n");
			o.MakeDpxMapData(o.vFlgZeroSizeB);
			fprintf("======= fail-stedy status : IdqA ==0\n");
			o.MakeDpxMapData(o.vFlgZeroSizeA);
			
			% 不均衡Idqデータマップの一部を解析結果から作成
				% SideAB 何れかのIdq軸に一致しなければ，orphan となる
			fprintf("======= unbalance status  \n");
			vIdqs = o.vIdqABs;
			mIdqs = o.vMapIdqABs;
			tids = {1:2, 3:4};
			ss = {'Side-A', 'Side-B'};
			for nSide = 1:2
				fpds = false(size(vIdqs, 1), 1); % 処理済データフラグ
				tid = tids{nSide};
				while ~all(fpds)
					tvIdqs = vIdqs(~fpds, :);
					tv	= tvIdqs(1, :);	%  解析 片側Idq値
					fSm = all(abs(vIdqs(:, tid) - tv(tid)) < o.eps, 2); % 同一値抽出
					if any(fSm & fpds)
						warning('Already processed Idq data');
					end
					fpds = fpds | fSm;	% 処理済フラグ更新
					fMs =all(abs(mIdqs(:,tid)-tv(tid)) < o.eps,2); % 対象マップIdq軸
					fEnb = o.sttSet(:) & fMs;
					if all(fEnb(fMs))
						fprintf("all data processed @ %s\n", o.sprintv(o.dFmt, tv));
						continue;
					end
					fprintf("===== %s[%4d]: %s\n", ...
							ss{nSide}, sum(fSm), o.sprintv(o.dFmt, tv(tid)));
					if sum(fSm) < 4
						fprintf("======== pass\n");
					else
						o.MakeDpxMapData(fSm, false);
					end
					% tvs = tvIdqs(fSm, :);
				end
			end

			% 不均衡データを含む完全mapデータを作成
				% side-A 基準
			rvs=o.rdIdIqs;	% ４隅のIdqデータ
			cIdqs = o.cmMapIdqABs; 

			fprintf("======= unbalance remained map making.  \n");
			sz = o.szMapIdqABs;
			for m0 = 1:sz(3)
				for m1 = 1:sz(4)
					tdFlg = squeeze(o.sttSet(:, :, m0, m1));
					if all(tdFlg,"all")
						fprintf("==== Side-B All map data defined. pass.\n");
						continue;
					end
					if ~all(tdFlg([1,end],[1,end]),"all")
						warning("最大領域が外挿されます");
					end
					f0 = false(size(o.sttSet));
					f0(:, :, m0, m1) = true;
					f1 = f0(:) & o.sttSet(:);
					tIdqChk = mIdqs(f1, :);
					fprintf("==== Side-B Map @[%3d,%3d]:%s.\n" ...
							, m0, m1, o.sprintv(o.dFmt, tIdqChk(1,1:2)));
					o.MakeDpxMapData(f1, true);
					% 
					% fns = {m0,m1,':',':'};
					% ctIdqs = cellfun(@(c)squeeze(c(fns{:})),cIdqs ...
										% 	,'UniformOutput',false);
					% tvIdqs = cat(3, ctIdqs{:})

				end
			end
			
			% vIdqABs = o.cnds;
			% isTgt = o.vFlgNrmData;
			% 
			% tDats = o.ExtractTgtData(isTgt);
			% tvIdqAbs = vIdqABs(isTgt,:);
		end

		function flg = get.vFlgNrmData(o)
			vIdqs = o.vIdqABs;
			flg = all(abs(vIdqs(:, 1:2) - vIdqs(:, 3:4)) < 1.e-5, 2);
		end

		function flg = get.vFlgZeroSizeB(o)
			vIdqs = o.vIdqABs;
			flg = all(abs(vIdqs(:, 3:4)) < 1.e-5, 2);
		end

		function flg = get.vFlgZeroSizeA(o)
			vIdqs = o.vIdqABs;
			flg = all(abs(vIdqs(:, 1:2)) < 1.e-5, 2);
		end

		function cIdqs = get.cmMapIdqABs(o)
			dIds = o.xIdms; dIqs = o.xIqms;
			cIdqs={dIds, dIqs, dIds, dIqs};
			
			cIdqs=cell(size(cIdqs));
			[cIdqs{[4,3,2,1]}]=ndgrid(o.cvIdqs{[2,1,4,3]});
		end

		function vIdqs = get.vMapIdqABs(o)
			vIdqs = reshape(permute(cat(5, o.cmMapIdqABs{:}),[5,1:4]), 4,[])';
		end

		function v = get.vIdqABs(o)
			v = squeeze(o.cnds(1,:,:))';
		end

		function szv = get.szMapIdqABs(o)
			dIds = o.xIdms; dIqs = o.xIqms;
			cIdqs={dIds, dIqs, dIds, dIqs};

			szv = cellfun(@length, cIdqs([2,1,4,3]));
		end

		function v = get.thE(o)
			v = o.ax(1,:)';
		end

		function cvs = get.cvIdqs(o)
			cvs = {o.vIds, o.vIqs, o.vIds, o.vIqs};
		end

		function v = get.vIds(o)
			v = o.xIdms;
		end

		function v = get.vIqs(o)
			v = o.xIqms;
		end

		function v = get.rdIdIqs(o)
			rIds = [min(o.vIds); max(o.vIds)];
			rIqs = [min(o.vIqs); max(o.vIqs)];
			v = [repelem(rIds,size(rIqs,1),1), ...
					repmat(rIqs, size(rIds,1),1)]; 
		end

		function o = MakeMotMap0(o)
			n=[length(o.xIds), length(o.xIqs)];
			nm=[length(o.xIdms), length(o.xIqms)];
			% Normal Mode データ
			fns = (o.dTyps(1,:)==0);
			tIdqs = o.cnds(:,:, fns);
			
			mChk = false([nm, nm]);

			vIds = o.xIdms; vIqs = o.xIqms;
			[mIdNs, mIqNs]=meshgrid(vIds, vIqs);

			[mIqAs, mIdAs, mIqBs, mIdBs] = ndgrid(vIqs, vIds, vIqs, vIds);
			sIdqABs = [mIdAs(:), mIqAs(:), mIdBs(:), mIqBs(:)];
			ss=sortrows(sIdqABs,1:4);
			% マップ用に処理する全てのIdq(A-B) データ組合せを行方向で作成
			sIdqs = squeeze(tIdqs(1,:,:))'; % IdIq org指令 (IdA, IqA, IdB, IqB) x 解析データ数

			th=o.ax(1,:);

			Fas = o.dats{3};
			Fas0 = o.dats{3}(:,:,:,fns);
			
			Fdqn = CnvUVWtoDQ(Fas0, th);
			
			sCnv = scatteredInterpolant(sIdqs(:,1),sIdqs(:,2), squeeze(Fdqn(1,1,1,:)), "natural");
			mapF = sCnv(mIdNs, mIqNs);
			isM0=sCnv(mIdNs, mIqNs);

			% 処理した並びにフラグをセットする
			f = false(1, size(sIdqs,1));
			isM0 = repmat([mIdNs(:), mIqNs(:)],[1,2]);
			nflg = ismembertol(sIdqs,isM0,1.e-5, 'ByRows', true)';
			if any(f & nflg)
				warning('Already processed data exists.');
			end
			f = f | nflg;		% 既に処理した組合せのフラグをセット

			sIds = sIdqs(:,1); sIqs = sIdqs(:,2);
			nc = 0;
			mFdqN = repmat({zeros([size(mIdNs), length(th)])},size(Fdqn,3),size(Fdqn,1));
			for i = 1:size(Fdqn,1)		% AxD, AxQ, Vz
				for j = 1:size(Fdqn, 3)	% SideA, SideB
					for k = 1:size(Fdqn, 2) % theta
						nc = nc + 1;
						fa = squeeze(Fdqn(i, k, j, :));
						sfn = scatteredInterpolant(sIds, sIqs, fa, "natural");
						fm = sfn(mIdNs, mIqNs);
						mFdqN{j, i}(:,:, k) = fm;
						if mod(nc, 5) == 0
							fprintf("DQ-Axis:(%03d/%03d) theta:%03d\n", i, j, k);
						end
					end
				end
			end
			as = 1;


		end

		function m = MakeMap(o)
			% 定義データ
			cds = o.cnds;
			flgMds = false(1,size(o.dTyps,2));	% 解析結果処理フラグ
			tIdqs = squeeze(cds(1,:,:));		% 解析電流条件 Idq(AB) x 解析データ数
			
			% map 作成
			vIds = o.xIdms; vIqs = o.xIqms;		% Id, Iq map 分解能
			[mId0s, mIq0s]=meshgrid(vIds, vIqs);
			[mIqA0s, mIdA0s, mIqB0s, mIdB0s] = ndgrid(vIqs, vIds, vIqs, vIds);
			sIdqABs0 = [mIdA0s(:), mIqA0s(:), mIdB0s(:), mIqB0s(:)];
			sIdqAB0s  = sortrows(sIdqABs0,1:4);	% 2重系 Idq map 組合せ　A-B 昇順
			
			fmPcd = false(1, size(sIdqAB0s, 1));	% map データ処理済フラグ
			
			% o.dats cell データ長 5 Torque, Current, Flux, Va, Vt
			% 1,145,487 - 3, 145,2,487 ...
			th = o.ax(1,:);		% 電気角 row
			nth = length(th);
			nd = length(o.dats);
			
			% for id = 1:nd
			% 	tds0 = o.dats{id};	% 処理対象データ
			% 	nds = size(tds0, 1);	% 処理データ次元 3:3相データ 1:トルク
			% 	ntd = size(td2, 2); % 電気角方向データ数
			% 	for idt = 0:3			% 2重系解析データタイプ
				% 	flgMt = o.dTyps(1,:) == 3;
				% 	if any(flgMds & flgMt)
					% 	warning('Already Processed Data Exists.')
				% 	end
				% 	if nth ~= ntd
					% 	warning('not match th-Dir. Num [%3d]/[%3d]', nth, ntd);
					% 	continue;
				% 	end
				% 	if nds == 1
				% 	elseif nds == 3
				% 	end
				% 	%
				% 	flgMds = flgMds | flgMt;
			% 	end
			% end
			for idt = 0:3			% 2重系解析データタイプ
				flgMt = o.dTyps(1,:) == idt;
				if any(flgMds & flgMt)                                                                           
					warning('Already Processed Data Exists.')
				end
				%
				if idt == 0
					mIdqs = [mId0s(:), mIq0s(:), mId0s(:), mIq0s(:)];
					[f0, mIdx0] = ismembertol(sIdqAB0s, mIdqs, 1.e-3, 'ByRows', true);
					% id0c = sortrows([mIdx0(mIdx0>0), find(mIdx0)]);
					t0 = find(f0);
					id0c = [mIdx0(t0), t0];
					if size(id0c,1) ~= size(mIdqs0, 1)
						warning('Not macthed N0 Condition Exist');
					end
				end
				for id = 1:nd
					tds0 = o.dats{id};	% 処理対象データ
					nds = size(tds0, 1);	% 処理データ次元 3:3相データ 1:トルク
					ntd = size(tds0, 2); % 電気角方向データ数
					if nds == 3
						tds1 = CnvUVWtoDQ(tds0, th);
					else
						tds1 = reshape(tds0, 1, length(th), 1, []);
					end
					nta = size(tds1,3);                          
					subs = repmat({':'}, 1, ndims(tds1));
					subs{end} = flgMt;
					tds = tds1{subs{:}};	% 処理対象データ抽出
					if nth ~= ntd
						warning('not match th-Dir. Num [%3d]/[%3d]', nth, ntd);
						continue;
					end
					tIdqABs = tIdqs(1, flgMds);
					tIdAs = tIdqs(1, flgMds); tIqAs = tIdqs(2, flgMds);
					tIdBs = tIdqs(3, flgMds); tIqBs = tIdqs(4, flgMds);
					for in0 = 1:nds
						for in1 = 1:ntd
							for in2 = n
							end
						end
					end
					if nds == 1
					elseif nds == 3
					end
				end
				%
				flgMds = flgMds | flgMt;
			end

			for id = 1:nd
				tds0 = o.dats{id};	% 処理対象データ
				nds = size(tds0, 1);	% 処理データ次元 3:3相データ 1:トルク
				ntd = size(td2, 2); % 電気角方向データ数
				if nth ~= ntd
					warning('not match th-Dir. Num [%3d]/[%3d]', nth, ntd);
					continue;
				end
				if nds == 1
				elseif nds == 3
				end
			end
			for nt = 0:3
				isTgt = (o.dTyps(1, :) == nt);
			end
			m = 0;
		end



		function v = vDpxTri(o, idx)
			% th=o.ax(1,:)';
			v0 = o.dats{idx};
			vm = mean(v0,1);
			v = v0 - vm;
		end

		function DivCnds(o)
			ds = struct();
			cds = o.cnds;
			f0=true(1,length(cds));

			fs = squeeze(all(abs(cds(1,:, :))<1.e-4, 2))';
			nfs = sum(fs);
			if nfs ~= 1
				warning('Zero Data should be 1 %d', nfs);
			end
			tz = cds(:,:, fs);
			ds.Zero.ia=tz;
			ds.Zero.idx=find(fs);

			tds = o.dats;
			nds = cell(1, length(tds));
			for i = 1:length(tds)
				td = tds{i};
				sbs = repmat({':'}, 1, ndims(td));
				sbs{end} = ds.Zero.idx;
				nds{i} = td(sbs{:});
			end
			ds.Zero.dat = nds;

			f0 = f0 & ~fs;

			while any(f0)
				pcds = cds(:,:, f0);
				pcd = pcds(:,:, 1);
				
				pfIdAs = squeeze(abs(cds(1,1,:)-pcd(1,1))<1.e-4)' & f0;
				idAq = find(pfIdAs);
				f1 = pfIdAs;
				nnn1 = sum(pfIdAs);
				i1 = 0;
				flgs = nan(1,nnn1);
				while(any(f1))
					pfAs = squeeze(all(abs(cds(1,1:2,:)-pcd(1,1:2))<1.e-4,2))';
					ptz = cds(:,:, pfAs);
					pid = find(pfAs);
					pds1 = cell(1, length(tds));
					for i = 1:length(tds)
						td = tds{i};
						sbs = repmat({':'}, 1, ndims(td));
						sbs{end} = ds.Zero.idx;
						nds{i} = td(sbs{:});
					end
					f1 = f1 & ~pfAs;
				end
				f0 = f0 & pfIdAs;
				tdps = cds(:,:, f0);

			end

			% f = all(abs(squeeze(o.cnds(1,:,:)))<1.e-4, 1);
			fs = squeeze(all(abs(o.cnds(1,:,:))<1.e-4, 1))';
			cndC=o.cnds(:,:,~fs);
			o.dss = cndC;
		end

		function v = vDiffDpxTri(o, idx)
			% th=o.ax(1,:)';
			% ts=diff(o.ax(2,:));
			v0 = o.dats{idx};
			vm = mean(v0,2);
			v = v0 - vm;
		end
		
		function v = vFlux(o)
			% th=o.ax(1,:);
			% i = 1;
			v0 = o.dats{3};
			vm = mean(v0,2);
			v = v0 - vm;
		end

		function v = vIas(o)
			% th=o.ax(1,:);
			% i = 1;
			v0 = o.dats{2};
			vm = mean(v0,2);
			v = v0 - vm;
		end

		function v = vTrqs(o)
			v0 = o.dats{1};
			vm = mean(v0,2);
			vIqs = squeeze(o.cnds(1,[2,4],:));
			isZf = all(abs(vIqs)<1.e-4,1);
			zIqx = find(isZf);
			v = v0;
			v(:,:,zIqx) = v(:,:,zIqx) - vm(:,:,zIqx);
		end

		function fh = FigOut(o, fh)
			if nargin < 2
				fh = figure;
			end

			if isempty(fh.KeyPressFcn)
				fh.KeyPressFcn = @keyPress;
			end

			global isDQ
			dIdx = 1;
			nz = 1;
			nDat = length(o.dats);
			nsz  = size(o.cnds);
			nSiz = nsz(end);

			isDQ = false;
			% >>>-------------------------
			function keyPress(~, event)
				isC = false; isS = false; 
				ds = 1;
				if ismember('control', event.Modifier)
					ds = 10;
					isC = true;
				end

				ms = '';
				mm = event.Modifier;
				if ~isempty(mm)
					for i = length(mm)
						if ~isempty(ms)
							ms = sprintf('%s - ', ms);
						end
						ms = sprintf('%s%s', ms, mm{i});
					end
				end
				mk = event.Key;
				fprintf('%s-[%s]\n', mk, ms);

				if ismember(mk, event.Modifier)
					return
				end
				switch event.Key
            		case 'leftarrow'
						nz = max(nz - ds, 1);
            		case 'rightarrow'
						nz = min(nz + ds, nSiz);
					case 'uparrow'
						dIdx = min(dIdx + 1, nDat);
					case 'downarrow'
						dIdx = max(dIdx - 1, 1);
					case 'm'
						if isC
							if isDQ
								isDQ = false;
							else
								isDQ = true;
							end
							fprintf('Ts:%d\n', isDQ);
						end
				end

				PlotOut(isDQ);
		    end
			% <<<-------------------------
			% >>>-------------------------
			function PlotOut(isDQ)
				if nargin<1
					isDQ = false;
				end
				fprintf('Tsfff:%d\n', isDQ);
				clf(fh);
				fax = axes(fh);
				th = o.ax(1, :);
				tds = o.dats{dIdx};

				if ndims(tds) == 3
					line(fax,th, tds(:,:, nz), 'LineWidth', 1, 'Color', 'b');
				elseif ndims(tds) == 4
					if isDQ
						da0 = tds(:,:, 1, nz);
						db0 = tds(:,:, 2, nz);
						da = CnvUVWtoDQ(da0, th);
						db = CnvUVWtoDQ(db0, th);
					else
						da = tds(:,:, 1, nz);
						db = tds(:,:, 2, nz);
					end
					plot(fax,th, da, th, db,'LineWidth', 1);
					% line(fax,th, tds(:,:, 2, nz),  'LineWidth', 1);
				end
				ys = fax.YLim;
				if ys(1) < 0 && ys(2) > 0
					yline(fax, 0, "Color","k", "LineWidth",2);
				end
				ylabel(fax, o.dNams{dIdx}, "FontSize", 16);

				fax.XLim = [0,360]; 
				fax.XTick = 0:30:360;
				xlabel(fax, "電気角 [°]", "FontSize",16);
				fax.XAxis.FontSize = 12;
				fax.YAxis.FontSize = 12;
				Idq0 = o.cnds(1,:,nz);
				ss = sprintf("[%04d] IdA:%5.0fA-IqA:%5.0fA / IdB:%5.0fA-IqB:%5.0fA" ...
						, nz, Idq0(1),Idq0(2),Idq0(3), Idq0(4));
				title(fax, ss, "FontSize", 14);
				fax.Box = "on";
				grid(fax, 'on');
			end
			% <<<-------------------------
			PlotOut();
		end

	end
end
