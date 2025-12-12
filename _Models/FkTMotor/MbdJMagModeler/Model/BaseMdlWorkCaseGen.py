from __future__ import annotations

from typing import Any, Union

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QSizePolicy

from Model.ItemExtGenWorkCase import ItemExtGenWorkCase, TypDefExtCase

uQRole = Qt.ItemDataRole
uQItmF = Qt.ItemFlag
uQDir = Qt.Orientation
uQTIdx = Union[QModelIndex, QPersistentModelIndex]

_defIdx = QModelIndex()

QSP = QSizePolicy.Policy
QAF = Qt.AlignmentFlag


uQRole = Qt.ItemDataRole
uQTIdx = Union[QModelIndex, QPersistentModelIndex]


""" New Id Iq Extra Region Case Definition """


class BaseMdlWorkCaseGen(QAbstractTableModel):
    _dList: list[ItemExtGenWorkCase]

    def __init__(
        self,
        p: QObject | None = None,
    ) -> None:
        super().__init__(p)

        self._dList = []

    @property
    def exWcGenDefSets(self) -> list[ItemExtGenWorkCase]:
        return self._dList

    ########################################################
    def GenNewData(self) -> None:
        self.beginResetModel()
        self._dList.clear()
        self.endResetModel()
        self.layoutChanged.emit()

    ########################################################

    def clrData(self, newData: list[ItemExtGenWorkCase] | None = None):
        self.beginResetModel()
        self._dList.clear()
        if newData is not None:
            self._dList.extend(newData)
        self.endResetModel()
        self.layoutChanged.emit()

    # Define Table Model ####################################
    # region Table Model
    ########################################################
    def rowCount(self, p: QModelIndex = _defIdx):
        return len(self._dList) + 1

    ########################################################
    def columnCount(self, p: QModelIndex = _defIdx):
        return 3

    ########################################################
    def setData(self, idx: QModelIndex, value: Any, role: int = 0) -> bool:
        if not idx.isValid():
            return False
        nc = idx.column()
        nr = idx.row()

        if nr == len(self._dList):
            self.beginInsertRows(_defIdx, nr, nr)
            self._dList.append(ItemExtGenWorkCase())
            self.endInsertRows()
            self.dataChanged.emit(idx, idx, [uQRole.EditRole])

        tgt = self._dList[nr]

        rStt = True
        if role == uQRole.EditRole:
            if nc == 0:
                tgt.type = TypDefExtCase[value]
            elif nc == 1:
                tgt.defId = value
            elif nc == 2:
                tgt.defIq = value
            else:
                rStt = False
                print(f"**** Invalid Column {nc} @ {nr}")
        else:
            rStt = False

        if rStt:
            self.dataChanged.emit(idx, idx, [uQRole.EditRole])
        return rStt

    def data(
        self, idx: QModelIndex = _defIdx, role=uQRole.DisplayRole
    ) -> str | Qt.CheckState | QColor | QAF | QFont | None:
        if not idx.isValid():
            return None
        nr = idx.row()
        nc = idx.column()
        # last row
        if nr < len(self._dList):
            tgt = self._dList[nr]

            # Table Display Data
            if role == uQRole.DisplayRole or role == uQRole.EditRole:
                if nc == 0:
                    return tgt.type.name
                elif nc == 1:
                    return "---" if len(tgt.defId) == 0 else tgt.defId
                elif nc == 2:
                    return "---" if len(tgt.defIq) == 0 else tgt.defIq
                else:
                    return None
            # Data Alignment Setting
            if role == uQRole.TextAlignmentRole:
                if nc == 0:
                    return QAF.AlignLeft | QAF.AlignVCenter
                else:
                    return QAF.AlignRight | QAF.AlignVCenter
            # Background Color
            if role == uQRole.BackgroundRole:
                if self.flags(idx) == uQItmF.NoItemFlags:  # BkColor@Invalid
                    return QColor("lightgray")
                if not tgt.isValid:
                    return QColor("#fcc")

            if role == uQRole.ForegroundRole:
                if not tgt.isValid:
                    return QColor("red")

            if role == uQRole.FontRole:
                if not tgt.isValid:
                    # f: QFont = idx.data(uQRole.FontRole)
                    # if f is None:
                    f = QFont()
                    f.setBold(True)
                    return f
        else:
            if role == uQRole.BackgroundRole:
                if nc > 0:
                    return QColor("lightgray")

        return None

    def flags(self, idx: QModelIndex) -> Qt.ItemFlag:
        if not idx.isValid():
            return uQItmF.NoItemFlags
        nc = idx.column()
        nr = idx.row()

        if nr >= len(self._dList) and nc > 0:
            # last row
            return uQItmF.NoItemFlags
        elif nc == 2 and self._dList[nr].type == TypDefExtCase.Both:
            # Disable if type is Both
            return uQItmF.NoItemFlags
        else:
            return (
                uQItmF.ItemIsEnabled
                | uQItmF.ItemIsSelectable
                | uQItmF.ItemIsEditable
            )

    def headerData(self, nSec: int, oDir: uQDir, role=uQRole.DisplayRole):
        if role == uQRole.DisplayRole:
            if oDir == uQDir.Horizontal:
                return ["Type", "Id [A]", "Iq [A]"][nSec]
            else:
                return str(nSec + 1)
        return None

    # endregion
    # <--- End. Define Table Model ##########################
