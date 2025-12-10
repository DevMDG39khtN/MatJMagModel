function fh = FigOutIdIqMap(mIdqs, fh)
	if nargin < 2 || isempty(fh) || ~isgraphics(fh, 'figure')
		fh = figure;
	end

	sz = size(mIdqs);
	if all(sz(1:2) == [2,4])
		hs = cell(1,4);
		% vIdq0A = squeeze(mIdqs(1,1:2,:));  vIqq0B = squeeze(mIdqs(1,3:4,:));
		% vIdqA  = squeeze(mIdqs(2,1:2,:));  vIqqB  = squeeze(mIdqs(2,3:4,:));
		ax = reset(fh);
		hold(ax, "on");
		ax.Box = 'on';
		xline(0, Color='k', LineWidth=1);
		yline(0, Color='k', LineWidth=1);
		ax.XAxis.FontSize = 11;
		ax.YAxis.FontSize = 11;
		xlabel('Id [A]', FontSize=12);
		ylabel('Iq [A]', FontSize=12);
		grid(ax,'on');

		cs = {'b', 'c', 'r', 'm'}; ss = {30, 25};
		for i = 1:size(mIdqs, 1)
			for j = 1:-1:0
				if j==1 && all(abs(mIdqs(i,1:2,:)-mIdqs(i,3:4,:)) < 1.e-5,"all")
					continue;
				end
				jj = 2*j+1;
				vx = squeeze(mIdqs(i, jj  , :));
				vy = squeeze(mIdqs(i, jj+1, :));
				cm = cs{2*(i-1)+j+1};
				if i == 1
					h = scatter(ax, vx, vy, 30, cm, LineWidth=1.5);
				else
					h = scatter(ax, vx, vy, 15, cm, "filled");
				end
				hs{i} = h;
			end
		end
		hold(ax, "off");
	end
end

function ax = reset(fh)
	clf(fh);
	ax = axes(fh);
end
