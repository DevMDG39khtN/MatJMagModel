function v = CnvRealIdqs(vIdqs)
	arguments (Input)
		vIdqs	(:, 4)	double
	end
	arguments (Output)
		v		(:, 4)	double
	end

	% vIdqs0 = vIdqs;
	% vIdqs = cat(3, vIdqs(:,1:2), vIdqs(:,3:4));
	sz0 = size(vIdqs);
	vIdqs = reshape(vIdqs, size(vIdqs, 1), 2, 2);
	ias = sqrt(sum(vIdqs.^2, 2));
	% fws0 = atan2d(-vIdqs(:, 1, :), vIdqs(:, 2, :));
	% fws  = fws0 + shiftdim([-15 15], -1);
	fws = atan2d(-vIdqs(:, 1, :), vIdqs(:, 2, :)) ...
					+ shiftdim([-15 15], -1);
	v = reshape(ias .* [sind(-fws), cosd(fws)], sz0);
end
