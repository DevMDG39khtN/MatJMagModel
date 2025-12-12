from __future__ import annotations

import base64
import gzip
import json
from typing import Any, Union

# import dill
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSettings,
    Qt,
    Signal,
    Slot,
)

from JMagDatas.WorkCase import MotAxes, WorkCase, WorkStatus

# from View.GuiCaseSetting import GuiCaseSetting

uQRole = Qt.ItemDataRole
uQItmF = Qt.ItemFlag
uQDir = Qt.Orientation
uQTIdx = Union[QModelIndex, QPersistentModelIndex]

_defIdx = QModelIndex()

"""_summary_
"""


class MdlWorkCaseStore(QAbstractTableModel):
    onModeChanged = Signal(MotAxes)
    onPlotRequested = Signal()

    numRows0 = 1
    _mode: MotAxes
    _list: list[WorkCase]
    __selList: list[WorkCase] | None
    __hdrCmnTs_tgt: WorkCase | None

    __isDataModified: bool

    # Case Generator
    #################################################
    def __init__(self):
        super().__init__()
        self._mode = MotAxes.DQ
        self._list = []
        self.__selList = []
        self._tgt = None

        self.__isDataModified = False
        self.dataChanged.connect(self._onChanged)

        def _fn():
            self.IsDataModified = True
            self.onPlotRequested.emit()

        self.layoutChanged.connect(lambda: self._onChanged(None, None, None))

    # endregion
    #################################################

    def setGrpIdx(self, iaLmts: list[float]) -> int:
        tIds = {i for i in range(len(self._list))}
        tIdsHys = []
        tIdCnts = []
        for i, v in enumerate(iaLmts):
            sIds = {i for i in tIds if self._list[i].valACi[0] < v * 1.001}
            tIdsHys.append(tIds)
            tIdCnts.append(len(sIds))
            tIds -= sIds
            for j in sIds:
                self._list[j].grpIdx = i
        tIdsHys.append(tIds)
        tIdCnts.append(len(tIds))
        for i in tIds:
            self._list[i].grpIdx = len(iaLmts)
        return sum(tIdCnts)

    ########################################################
    def toDict(self) -> dict[str, Any]:
        """MdlMapDef オブジェクトを辞書形式に変換"""
        return {
            "Mode": self.Mode.name,
            "WorkCases": [wc.toDict() for wc in self._list],
        }

    ########################################################
    def saveToJson(self) -> str:
        dic = self.toDict()
        return json.dumps(dic, indent=2, ensure_ascii=False)

    ########################################################
    @staticmethod
    def fromDict(data: dict[str, str], tgt: MdlWorkCaseStore | None = None) -> MdlWorkCaseStore:
        """辞書形式のデータから MdlWorkCaseStore オブジェクトを生成"""
        if tgt is None:
            tgt = MdlWorkCaseStore()

        mode = MotAxes[data["Mode"]]
        tgt.Mode = mode

        workCases: str | list[dict] = data.get("WorkCases", [])

        if len(workCases) > 0 and isinstance(workCases, list):
            d0: list[dict] = workCases
            tgt.beginResetModel()
            tgt._list = [WorkCase.fromDict(dicWc) for dicWc in d0]
            tgt.endResetModel()
            tgt.layoutChanged.emit()
        return tgt

    ########################################################
    def loadFromJson(self, jst: str) -> None:
        if len(jst) == 0:
            return
        dic = json.loads(jst)
        self.fromDict(dic, self)

    ########################################################
    def loadSettings(self, s: QSettings) -> None:
        if s is None:
            return
        s.beginGroup("WorkCaseStore")
        txtB64: str = str(s.value("object", ""))
        if txtB64 and len(txtB64) > 0:
            oDat = base64.b64decode(txtB64.encode("utf-8"))
            sTxt = gzip.decompress(oDat).decode("utf-8")
            self.loadFromJson(sTxt)
        s.endGroup()

    ########################################################
    def saveSettings(self, s: QSettings, isFdo: bool = False) -> None:
        s.beginGroup("WorkCaseStore")
        if self.IsDataModified or isFdo:
            print("Saving WorkCaseStore to settings")
            sTxt = self.saveToJson()
            oDat = gzip.compress(sTxt.encode("utf-8"))
            txtB64 = base64.b64encode(oDat).decode("utf-8")
            s.setValue("object", txtB64)
            print("Saving WorkCaseStore to settings ... done")
        else:
            print("WorkCaseStore not modified, skipping save")
        s.endGroup()

    ########################################################
    def saveToJsonFile(self, fpath: str, isZip: bool = False) -> None:
        if isZip:
            """_list属性をJSON形式でgzip圧縮してバイナリデータとして保存"""
            with gzip.open(fpath, "wb") as f:
                json_data = json.dumps(
                    [work_case.toDict() for work_case in self._list],
                    indent=2,
                    ensure_ascii=False,
                )
                f.write(json_data.encode("utf-8"))
        else:
            """_list属性をJSONファイルに保存"""
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(
                    [work_case.toDict() for work_case in self._list],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    def loadToJsonFile(self, fpath: str, isZip: bool = False) -> None:
        if isZip:
            with gzip.open(fpath, "rb") as f:
                jsData = f.read().decode("utf-8")
                dList = json.loads(jsData)
        else:
            """JSONファイルから_list属性を読み込み"""
            with open(fpath, "r", encoding="utf-8") as f:
                dList = json.load(f)
        self.beginResetModel()
        self._list = [WorkCase.fromDict(data) for data in dList]
        self.endResetModel()
        self.layoutChanged.emit()

    @Slot()
    def _onChanged(self, topLeft, bottomRight, roles):
        self.IsDataModified = True
        self.onPlotRequested.emit()

    def ChangeSkewStatus(self, stt: tuple[int, float, bool]) -> None:
        tgt = [wc for wc in self._list if wc.status < WorkStatus.Defined]
        for t in tgt:
            t.ChangeSkewStatus(stt)
        return

    def addIdqDatas(
        self,
        vBase: list[tuple[float, float]],
        vExts: list[tuple[float, float]],
        nDivSk: int = 0,
        thSk: float = 0.0,
        isSlice: bool = False,
    ) -> int:
        self.beginResetModel()
        n = len(self._list)
        wcBases = [
            WorkCase(
                v,
                self._mode,
                idx=n + i,
                thSkew=thSk,
                nDivSkew=nDivSk,
                isSlice=isSlice,
            )
            for i, v in enumerate(vBase)
        ]
        self._list.extend(wcBases)
        n = len(self._list)
        wcExts = [
            WorkCase(
                v,
                self._mode,
                isExA=True,
                idx=n + i,
                thSkew=thSk,
                nDivSkew=nDivSk,
                isSlice=isSlice,
            )
            for i, v in enumerate(vExts)
        ]
        self._list.extend(wcExts)
        self._list.sort(key=lambda x: x.valDQi)
        self.endResetModel()

        n = len(self._list)
        self.dataChanged.emit(0, n, [uQRole.DisplayRole])
        return n

    @Slot()
    def clrData(self):
        nrs = self.rowCount()
        if nrs > 0:
            self.beginResetModel()
            self._list.clear()
            self.endResetModel()
            self.layoutChanged.emit()

    def delData(self, ids: list[QModelIndex]):
        # 分割された選択時の処理が必要
        dTgt = [self._list[i.row()] for i in ids if i.isValid()]
        self.beginResetModel()
        for d in dTgt:
            self._list.remove(d)
            for v in self._list:
                if v.index >= d.index:
                    v.index -= 1
        self.endResetModel()
        self.dataChanged.emit(0, len(self._list) - 1, [uQRole.DisplayRole])

    def setData(self, idx: uQTIdx, value: Any, role: int = 0) -> bool:
        if not idx.isValid():
            return False
        nc = idx.column()
        nr = idx.row()

        print(f">>>>> setData Function: idx({nr}, {nc}), {role}")
        if nr >= len(self._list):
            print(f"***** Row Index Overflow: {nr} >= {len(self._list)}")
            return False
        tgt = self._list[nr]

        if role == uQRole.EditRole:
            print(f">>>>>>>>>> set Data Edit Role: idx({nr}, {nc}), {role}")
            if nc >= 4 and nc <= 5:  # status GUIで設定不可
                isUpd = False
                if nc == 4:
                    if tgt.grpIdx != value:
                        isUpd = True
                        tgt.grpIdx = value
                elif nc == 5:
                    if tgt.caseNo != value:
                        isUpd = True
                        tgt.caseNo = value
                else:
                    if tgt.status != value:
                        isUpd = True
                        tgt.status = value

                if isUpd:
                    self.dataChanged.emit(idx, idx, [uQRole.DisplayRole, uQRole.EditRole])
                    return True

        return False

    def flags(self, index: uQTIdx) -> Qt.ItemFlag:
        if index.isValid():
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        else:
            return Qt.ItemFlag.NoItemFlags

    def data(
        self, idx: uQTIdx = _defIdx, role: uQRole = uQRole.DisplayRole
    ) -> str | Qt.CheckState | Qt.AlignmentFlag | None:
        if not idx.isValid():
            return None
        nr = idx.row()
        nc = idx.column()

        if nr >= len(self._list):
            return None
        tgt = self._list[nr]

        v = self._valByIndex(tgt, nc)
        if role == uQRole.DisplayRole:
            return v
        if role == uQRole.EditRole:
            if nc >= 4 and nc <= 5:
                return v
        if role == uQRole.TextAlignmentRole:
            vTyp = type(idx.data())
            if vTyp is str:
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            if vTyp is int:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if vTyp is float:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignCenter
        return None

    def _valByIndex(self, t: WorkCase, idx: int) -> Any:
        if idx < 2:
            return t.valDQi[idx] if t.mode == MotAxes.DQ else t.valACi[idx]
        elif idx < 4:
            idx -= 2
            return t.valACi[idx] if t.mode == MotAxes.DQ else t.valDQi[idx]
        elif idx == 4:
            return t.status.name
        elif idx == 5:
            return t.caseNo
        elif idx == 6:
            return t.grpIdx
        elif idx == 7:
            return "Id-Iq" if t.mode == MotAxes.DQ else "Ia-Fw"
        else:
            return t.mode

    # region Properties

    @property
    def dataList(self) -> list[WorkCase]:
        return self._list

    @property
    def Mode(self) -> MotAxes:
        return self._mode

    @Mode.setter
    def Mode(self, mode: MotAxes):
        if self._mode != mode:
            self._mode = mode
            # if self._tgt is not None:
            #     self._tgt.mode = mode # データ取得時に調整でOK
            self.headerDataChanged.emit(uQDir.Horizontal, 0, 1)
            self.onModeChanged.emit(self._mode)

    @property
    def IsDataModified(self) -> bool:
        return self.__isDataModified

    @IsDataModified.setter
    def IsDataModified(self, isMod: bool):
        self.__isDataModified = isMod

    @property
    def TargetData(self) -> WorkCase | None:
        return self._tgt

    @TargetData.setter
    def TargetData(self, tgt: WorkCase | None):
        self._tgt = tgt

    @property
    def SelectedData(self) -> list[WorkCase] | None:
        return self.__selList

    @SelectedData.setter
    def SelectedData(self, lst: list[WorkCase] | None):
        self.__selList = lst

    @property
    def isLastDataModified(self) -> bool:
        return self.__isDataModified

    def resetDataModified(self):
        self.__isDataModified = False
        return

    # endregion

    def rowCount(self, p: uQTIdx = _defIdx):
        return len(self._list) if self._list is not None else 0

    def columnCount(self, p: uQTIdx = _defIdx):
        return len(self._hdtTitles[0])

    # Table View のヘッダタイトルを返す
    __hdrCmnTs = ["Status", "CaseIdx", "GrpIdx", "Mode"]
    _hdtTitles: list[list[str]] = [
        ["Id [A]", "Iq [A]", "Ia [Arms]", "Fw [deg.]"] + __hdrCmnTs,
        ["Ia [Arms]", "Fw [deg.]", "Id [A]", "Iq [A]"] + __hdrCmnTs,
    ]

    def headerData(self, nSec: int, oDir: uQDir, role=uQRole.DisplayRole):
        if role == uQRole.DisplayRole:
            if oDir == uQDir.Horizontal:
                return self._hdtTitles[MotAxes.DQ][nSec]
            else:
                return str(nSec + 1)
        return None
