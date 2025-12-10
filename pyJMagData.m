function pyJMagData(tdName, caseIds, caseVals, dNames, uNames, dtMs)
	arguments
		tdName		(1,1)	string
		caseIds		(:,1)	cell
		caseVals	(:, :)  cell
		dNames		(:, :)  cell
		uNames		(:, :)  cell
		dtMs		(:, :, :) double % (nDataCols, n[Time/Frequency], nCase) 
	end

	cIds = cell2mat(caseIds);
	cVals = cell2mat(cellfun(@cell2mat, caseVals, 'UniformOutput', false)');
	s=cellfun(@string, dNames, 'UniformOutput', false);
	dpNams = vertcat(s{:});
	s=cellfun(@string, uNames, 'UniformOutput', false);
	dUntNams = vertcat(s{:});

	tAxs = squeeze(dtMs(1, :, :));
	zAxs = tAxs-tAxs(1,:);
	if max(abs(diff(zAxs,2)),[], 'all') > 1.e-10
		error('Mismatch Axis Data in {%s} Some Case.', tdName)
	end
	eAxs = zAxs./zAxs(end,:) * 360;
	dAx = [eAxs(:,1), zAxs(:,1)];

	tds = squeeze(dtMs(2:end, :, :));

end