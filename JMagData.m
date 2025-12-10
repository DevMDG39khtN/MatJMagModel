classdef JMagData < handle
    properties(SetAccess = private, GetAccess = public)
		theta (1,:) double
		time  (1,:) double
		freqs (1,:) double
		% dtNames (1, :) string
		% unNames (1, : )string
		CaseId  (1, :) int32
		IdqVals (:, :) double
		MagDatas  struct
		FreqDatas struct
    end

    properties(Dependent)
		% NumCase
		% NumDatas
    end
	methods
		function o=JMagData()
			o.theta = [];
			o.time  = [];
			o.freqs = [];
			% o.dtNames = [];
			% o.unNames = [];
			o.CaseId = [];
			o.IdqVals = [];
			o.MagDatas = struct();
			o.FreqDatas = struct();
		end

		function pySetData(o, tdName, caseIds, caseVals, dNames, uNames, dtMs)
			arguments
				o			
				tdName		(1,1)	string
				caseIds		(:,1)	cell
				caseVals	(:, :)  cell
				dNames		(:, :)  cell
				uNames		(:, :)  cell
				dtMs		(:, :, :) double % (nDataCols, n[Time/Frequency], nCase) 
			end
		
			cIds = int32(cell2mat(caseIds))';
			cVals = cell2mat(cellfun(@cell2mat, caseVals, 'UniformOutput', false)')';
			s=cellfun(@string, dNames, 'UniformOutput', false);
			dpNams = vertcat(s{:});
			s=cellfun(@string, uNames, 'UniformOutput', false);
			dUntNams = vertcat(s{:});
		
			tds = squeeze(dtMs(2:end, :, :));

			if ~isvector(cIds)
				warning('!!!!!! Case Index はベクトルである必要有　このデータ無視')
				return
			end

			isAdding = false;
			ndmv = ndims(tds);
			if  isempty(o.CaseId)
				o.CaseId = cIds;
				o.IdqVals = cVals;
			else
				if size(cIds, 1) > 1
					cIds = cIds';
				end
				fids = ~ismember(cIds, o.CaseId);
				aIds = cIds(fids);
				if any(fids)
					if ~all(fids)
						warning('@@@@@@@ 部分的な新規ケースの追加 @ [%s] - %d', tdName)
					end
					cIds0 = cIds;
					tds0 = tds;
					cIds  = aIds;
					if ndmv == 2
						tds = tds(:, fids);
					elseif ndmv == 3
						tds = tds(:, :, fids);
					else
						error("Not Supported dimension")
					end
					o.CaseId  = horzcat(o.CaseId, aIds);
					o.IdqVals = horzcat(o.IdqVals, cVals(:,fids));
					if isfield(o.MagDatas, tdName) || isfield(o.FreqDatas, tdName)
						isAdding =true;
					else
						warning('@@@@@@@ データ間の存在ケース不整合 @ [%s] - %d', tdName)
					end
				end
			end

			tAxs = squeeze(dtMs(1, :, :));
			if strcmpi(dUntNams(1,1),"s")
				if contains(tdName, "損")
					fprintf(">>>>>> Ignore Data [%s]\n", tdName)
					return
				end
				fprintf("-------> Time Data Set [%s]\n", tdName);
				zAxs = tAxs-tAxs(1,:);
				if max(abs(diff(zAxs,2)),[], 'all') > 1.e-10
					warning('!!!!!!!!! Mismatch Time Axis Data in {%s} Some Case.', tdName)
				end
				eAxs = zAxs./zAxs(end,:) * 360;
				if isempty(o.theta)
					o.theta = eAxs(:, 1);
				else
					if max(abs(o.theta-eAxs(:, 1)')) > 1.e-10
						warning('!!!!!!!!! Mismatch Theta Data in {%s} Data.', tdName)
					end
				end
				if isempty(o.time)
					o.time = zAxs(:,1);
				else
					if max(abs(o.time-zAxs(:, 1)')) > 1.e-10
						warning('!!!!!!!!! Mismatch Time Data in {%s} Data.', tdName)
					end
				end

				if size(tds, 1) == 6
					sid = [1:2:6, 2:2:6];
					tds = tds(sid, :, :);
					dpNams(:, 2:end) = dpNams(:, sid+1);
				end
				
				if ~isfield(o.MagDatas, tdName)
					o.MagDatas.(tdName).Values = tds;
					o.MagDatas.(tdName).Names = dpNams(1, 2:end);
					o.MagDatas.(tdName).UnitName  = dUntNams(1, 2);
				else
					if length(o.CaseId) > size(o.MagDatas.(tdName).Values, 3)
						o.MagDatas.(tdName).Values = cat(ndmv, o.MagDatas.(tdName).Values, tds);
						fprintf('>>>>>>> Add Data in [%s]\n',tdName)
					else
						warning('!!!!!!!!! Duplex Case Data in {%s} Data.', tdName)
					end
				end

			% dAx = [eAxs(:,1), zAxs(:,1)];
			else
				fprintf("-------> Freq Data Set [%s]\n", tdName);
				if max(abs(diff(tAxs,2)),[], 'all') > 1.e-10
					warning('!!!!!!!!! Mismatch Freq. Axis Data in {%s} Some Case.', tdName)
				end
				if isempty(o.freqs)
					o.freqs = tAxs(:, 1);
				else
					if max(abs(o.freqs-tAxs(:, 1)')) > 1.e-10
						warning('!!!!!!!!! Mismatch Theta Data in {%s} Data.', tdName)
					end
				end
				if ~isfield(o.FreqDatas, tdName)
					o.FreqDatas.(tdName).Values = tds;
					o.FreqDatas.(tdName).Names = dpNams(1, 2:end);
					o.FreqDatas.(tdName).UnitName  = dUntNams(1, 2);
				else
					if length(o.CaseId) > size(o.FreqDatas.(tdName).Values, 3)
						o.FreqDatas.(tdName).Values = cat(ndmv, o.FreqDatas.(tdName).Values, tds);
						fprintf('>>>>>>> Add Data in [%s]\nsa',tdName)
					else
						warning('!!!!!!!!! Duplex Case Data in {%s} Data.', tdName)
					end
				end
			end

		end
	end
end