"""_summary_
Obsolete
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Union

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)

from Model.MdlWorkCaseStore import MotAxes

uQRole = Qt.ItemDataRole
uQItmF = Qt.ItemFlag
uQDir = Qt.Orientation
uQTIdx = Union[QModelIndex, QPersistentModelIndex]

_defIdx = QModelIndex()


@dataclass
class DefCaseSets:  # ダミーデータ
    XC: str = "---"
    YR: str = "---"
    mode: MotAxes = MotAxes.DQ
    isMtx: bool = False


class MdlDefJMagCases(QAbstractTableModel):  # Obsolete
    onModeChanged = Signal(MotAxes)
    _voPat = re.compile(r"[+-]?\d+(\.\d+)?")

    numRows0 = 1
    _mode: MotAxes
    _list: list[DefCaseSets]
    _tgt: DefCaseSets | None

    def __init__(self):
        super().__init__()
        self._mode = MotAxes.DQ
        self._list = []
        self._tgt = None

        self.dataChanged.connect(self._onChanged)

    @Slot()
    def _onChanged(self, topLeft, bottomRight, roles):
        print(f"**** Changed: {topLeft}, {bottomRight}, {roles}")

    # region Mode Property
    @property
    def Mode(self) -> MotAxes:
        return self._mode

    @Mode.setter
    def Mode(self, mode: MotAxes):
        if self._mode != mode:
            self._mode = mode
            if self._tgt is not None:
                self._tgt.mode = mode
            self.headerDataChanged.emit(uQDir.Horizontal, 0, 1)
            self.onModeChanged.emit(self._mode)

    # endregion

    def _addData(self):
        if self._tgt is not None:
            self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
            self._list.append(self._tgt)
            self._tgt = DefCaseSets("---", "---", self._mode, False)
            self.endInsertRows()

    def delData(self, ids: list[QModelIndex]):
        for idx in sorted(ids, key=lambda x: x.row(), reverse=True):
            if idx.isValid():
                if idx.row() < len(self._list):
                    self.beginRemoveRows(QModelIndex(), idx.row(), idx.row())
                    self._list.pop(idx.row())
                    # self.removeRow(idx.row())
                    self.endRemoveRows()

    def chkEnabled(self, idx: uQTIdx) -> bool:
        if not idx.isValid():
            return False
        nc = idx.column()
        nr = idx.row()
        if nr < len(self._list):
            tgt = self._list[nr]
        else:
            tgt = self._tgt
        vrTxt = None
        if nc == 0:
            vrTxt = tgt.XC
        elif nc == 1:
            vrTxt = tgt.YR
        else:
            return True

        m = self._voPat.match(vrTxt)
        if m is not None and m.span() == (0, len(vrTxt)):
            return True
        return False

    def rowCount(self, p: uQTIdx = _defIdx):
        return len(self._list) + self.numRows0

    def columnCount(self, p: uQTIdx = _defIdx):
        return 4

    _vPat0 = r"[+-]?\d+(\.\d*)?"
    _rPat0 = rf"({_vPat0})(:({_vPat0})){{0,2}}"
    _tPat0 = rf"\s*(({_rPat0})(\s*,\s*({_rPat0}))*)\s*"
    vPat = re.compile(_tPat0)
    #              12        23       4        43 1
    s = r"(:[+-]?\d+(\.\d*)?){0,2}"
    _mPats = (
        r"\s*(((([+-]?\d+(\.\d*)?)(:[+-]?\d+(\.\d*)?){0,2})"
        r"(\s*,\s*(([+-]?\d+(\.\d*)?)(:[+-]?\d+(\.\d*)?){0,2}))*))\s*"
    )

    def setData(self, idx: uQTIdx, value: Any, role: int = 0) -> bool:
        if not idx.isValid():
            return False
        nc = idx.column()
        nr = idx.row()
        # if idx.row() >= len(self._list):
        if nr < len(self._list):
            tgt = self._list[nr]
        else:
            tgt = self._tgt

        rStt = True
        if role == uQRole.EditRole:
            if nc == 0:
                tgt.XC = value
            elif nc == 1:
                tgt.YR = value
            else:
                rStt = False
                print(f"**** Invalid Column {nc} @ {nr}")
            if rStt and tgt == self._tgt:
                m0 = self.vPat.match(self._tgt.XC)
                s0 = m0 is not None and m0.span() == (0, len(self._tgt.XC))
                m1 = self.vPat.match(self._tgt.YR)
                s1 = m1 is not None and m1.span() == (0, len(self._tgt.YR))
                if s0 and s1:
                    self._addData()
                    # self._list.append(self._tgt)
                    # self._tgt = DefCaseSets("---", "---", self._mode, False)
                # self.chkEnabled(idx)

        elif role == uQRole.CheckStateRole and nc == 3:
            tgt.isMtx = value == Qt.CheckState.Checked.value
        else:
            rStt = False

        if rStt:
            self.dataChanged.emit(idx, idx, [uQRole.DisplayRole, uQRole.EditRole])
        return rStt

    def flags(self, index: uQTIdx) -> Qt.ItemFlag:
        if index.isValid():
            nc = index.column()
            if nc < 2:
                return uQItmF.ItemIsEnabled | uQItmF.ItemIsSelectable | uQItmF.ItemIsEditable
            elif nc == 3:
                return uQItmF.ItemIsUserCheckable | uQItmF.ItemIsEnabled | uQItmF.ItemIsSelectable
            else:
                return uQItmF.ItemIsEnabled
        return Qt.ItemFlag.NoItemFlags

    def data(self, idx: uQTIdx = _defIdx, role=uQRole.DisplayRole) -> str | Qt.CheckState | None:
        if not idx.isValid():
            return None
        nr = idx.row()
        nc = idx.column()
        if nr >= len(self._list):
            if self._tgt is None:
                self._tgt = DefCaseSets("---", "---", self._mode, True)
            tgt = self._tgt
        else:
            tgt = self._list[nr]

        if role == uQRole.DisplayRole or role == uQRole.EditRole:
            if nc == 0:
                return tgt.XC
            elif nc == 1:
                return tgt.YR
            elif nc == 2:
                return "Id-Iq" if tgt.mode == MotAxes.DQ else "Ia-Fw"
        elif role == uQRole.CheckStateRole and nc == 3:
            return Qt.CheckState.Checked if tgt.isMtx else Qt.CheckState.Unchecked
        return None

    def headerData(self, nSec: int, oDir: uQDir, role=uQRole.DisplayRole):
        if role == uQRole.DisplayRole:
            if oDir == uQDir.Horizontal:
                if self._mode == MotAxes.DQ:
                    return ["Id [A]", "Iq [A]", "Mode", "Both"][nSec]
                else:
                    return ["Ia [Arms]", "Fw [deg.]", "Mode", "Both"][nSec]
            else:
                return str(nSec + 1)
        return None
