function cMapDst = ReshapeCell(cMapSrc, mSizes, cOrd)
    % disp(">>>>> Start reform")
    % a = tic;
    % tic
    if iscell(cMapSrc)
        if isempty(cMapSrc)
            cMapDst={};
            return
        end
        mMap = cell2mat(cMapSrc);
    elseif ismatrix(cMapSrc)
        if isempty(cMapSrc)
            cMapDst=[];
            return
        end
        mMap = cMapSrc;
    else
        error('Reshape cell no support vector');
    end
    % toc
    % tic
    mMap = permute(reshape(mMap, mSizes), cOrd);
    % toc
    % tic % ここに一番時間がかかっている
    mcSz = mSizes(cOrd);
    cMapDst = squeeze(mat2cell(mMap, mcSz(1), mcSz(2) ...
                             , ones(1, mcSz(3)), ones(1, mcSz(4))));
    % toc
    % toc(a)
    % disp(">>>>>> End Reform")
end