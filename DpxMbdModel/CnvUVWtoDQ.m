function [Vdq, Vab, Vuvw] = CnvUVWtoDQ(Vuvw, th)
    if isnan(Vuvw)
        Vab = nan;
        Vdq = nan;
        return
    end
	%% 高速化のため 多次元配列の場合，２次元配列に変換
	sz = size(Vuvw);
	nd = ndims(Vuvw);
	if nd > 2
		Vuvw = Vuvw(:, :);	% ２次元化
	end
	if sz(1) ~= 3 || mod(size(Vuvw, 2), length(th))
		error('Unmatch Vuvw size');
	end
	%%
    M = sqrt(2/3) * [1 -1/2 -1/2; 0 sqrt(3)/2 -sqrt(3)/2; [-1, -1, -1] / sqrt(2)];
    Vab = M * Vuvw; % αβ相 + Vz

    %% JMAGの励磁順が逆なため
    vcos=cosd(th + 180);
    vsin=sind(th + 180);
	% α-β相 ⇒ dq軸変換
	m0=[ vcos; vsin];
	m1=[-vsin; vcos];
	sz0 = length(th);
	szx = size(Vuvw,2);
	
	mx=repmat([m0; m1], [1 szx/sz0]);
	m0x = mx(1:2, :); m1x = mx(3:4,:);
	Vdq = [sum(m0x .* Vab(1:2,:));sum(m1x .* Vab(1:2, :))];
    Vdq(3,:) = Vab(3, :);	% dq軸 + Vz

	if nd > 2	% 多次元配列の場合，元に戻す
		Vab = reshape(Vab, sz);
		Vdq = reshape(Vdq, sz);
	end
end
