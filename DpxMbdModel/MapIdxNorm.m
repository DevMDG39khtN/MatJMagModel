function [ids, chkv] = MapIdxNorm(cmIdqs)
	vIdA = cmIdqs{1}; vIqA = cmIdqs{2};
	vIdB = cmIdqs{3}; vIqB = cmIdqs{4};
	fid = (vIdA == vIdB) & (vIqA == vIqB);
	chkv = [vIdA(fid),vIqA(fid),vIdB(fid),vIqB(fid)];
	ids = fid;

	cIdqs={vIdA, vIqA, vIdB, vIqB};
	
	% cIdqs=cell(size(cIdqs));
	% [cIdqs{[4,3,2,1]}]=ndgrid(cmIdqs{[2,1,4,3]});
	vIdqs = reshape(permute(cat(5, cmIdqs{:}),[5,1:4]), 4,[])';
	idss = ismembertol(vIdqs, chkv, 'ByRows', true);
	[idA, iqA, idB, iqB] = ind2sub(size(vIdA), find(idss));
	ids = [idA, iqA, idB, iqB];
end
