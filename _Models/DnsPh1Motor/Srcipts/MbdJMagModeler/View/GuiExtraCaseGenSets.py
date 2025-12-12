from __future__ import annotations

from typing import Union

from PySide6.QtCore import (
    QModelIndex,
    QPersistentModelIndex,
    QSettings,
    Qt,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHeaderView,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from Model.ItemExtGenWorkCase import TypDefExtCase
from Model.MdlWorkCaseGen import MdlWorkCaseGen
from View.CustomWidgets import QtAf, QtSp

QSP = QSizePolicy.Policy
QAF = Qt.AlignmentFlag

uQRole = Qt.ItemDataRole
uQTIdx = Union[QModelIndex, QPersistentModelIndex]


class StyleDataItem(QStyledItemDelegate):
    def _onTextChanged(self, idx: uQTIdx, text: str):
        print(f"Row: {idx.row()}, Column: {idx.column()}, New Text: {text}")

    def createEditor(
        self, p: QWidget, opt: QStyleOptionViewItem, idx: uQTIdx
    ) -> QLineEdit | QComboBox | None:
        if not idx.isValid():
            print("@@@@@ ExCase-CreateEditor: Invalid Index")
            return
        if idx.column() == 0:
            cmb = QComboBox(p)
            cmb.addItems([mn.name for mn in TypDefExtCase])
            # cmb.setCurrentText(idx.data(uQRole.EditRole))
            return cmb
        else:
            nr = idx.row()
            if nr < idx.model().rowCount():
                _mdl: MdlWorkCaseGen = idx.model()
                editor = QLineEdit(p)
                editor.setPlaceholderText("---")

                def _onTextChanged(idx: uQTIdx, text: str):
                    print(
                        f"Row: {idx.row()}, Column: {idx.column()},"
                        f" New Text: {text}"
                    )

                editor.textChanged.connect(
                    lambda txt: _onTextChanged(idx, txt)
                )
            return editor

    def setEditorData(self, edtr: QLineEdit | QComboBox, idx: uQTIdx) -> None:
        if not idx.isValid():
            print("@@@@@ ExCase-CreateEditor: Invalid Index")
            return
        m: MdlWorkCaseGen = idx.model()
        val = m.data(idx, uQRole.EditRole)
        if isinstance(edtr, QComboBox):
            edtr.setCurrentText(val)
        elif isinstance(edtr, QLineEdit):
            if val is None:
                val = "---"
            if isinstance(val, str):
                if len(val) < 1:
                    val = "---"
            else:
                print("@invalid Val Data @ LineEdit")
            edtr.setText(val)

    def setModelData(
        self,
        edtr: QLineEdit | QComboBox,
        mdl: MdlWorkCaseGen,
        idx: uQTIdx,
    ) -> None:
        if not idx.isValid():
            return

        if isinstance(edtr, QComboBox):
            mdl.setData(idx, edtr.currentText(), uQRole.EditRole)
        elif isinstance(edtr, QLineEdit):
            mdl.setData(idx, edtr.text(), uQRole.EditRole)


class GuiExtraCases(QTableView):
    _css = """"""

    _mdl: MdlWorkCaseGen

    def __init__(
        self,
        m: MdlWorkCaseGen,
        s: QSettings | None = None,
        p=None,
    ):
        super().__init__(p)

        self.setModel(m)

        self.setWordWrap(False)
        self.setCornerButtonEnabled(True)

        hHdr = self.horizontalHeader()
        hHdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 45)
        hHdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hHdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        vHdr = self.verticalHeader()
        vHdr.setDefaultAlignment(Qt.AlignmentFlag.AlignRight)
        vHdr.setFixedWidth(25)

        self.setStyleSheet("""
            QHeaderView::section {
                background-color: #ddf;
                font-weight: bold;
                text-align: center;
            }
        """)

        self.setItemDelegate(StyleDataItem(self))

        self._mdl = self.model()

        return

    def showEvent(self, event):
        super().showEvent(event)

    def addContextMenu(self, menu: QMenu):
        clrAct = QAction("Clear Data", self)
        clrAct.triggered.connect(self.clrData)
        clrAct.setEnabled(len(self._mdl._dList) > 0)
        menu.addAction(clrAct)

        selRows = self.selectionModel().selectedRows()
        if selRows:
            delAct = QAction("削除", self)
            delAct.triggered.connect(lambda: self.delData(selRows))
            menu.addAction(delAct)

    def clrData(self):
        s = QMessageBox.question(
            self, "", "All Data will be Cleared. Are you OK?"
        )
        if s != QMessageBox.StandardButton.Yes:
            return
        self._mdl.beginResetModel()
        self._mdl._dList.clear()
        self._mdl.endResetModel()
        self._mdl.layoutChanged.emit()

    def delData(self, tgt: list[QModelIndex]):
        s = QMessageBox.question(
            self, "", "Selected Data will be Removed. Are you OK?"
        )
        if s != QMessageBox.StandardButton.Yes:
            return
        for idx in sorted(tgt, key=lambda x: x.row(), reverse=True):
            if idx.isValid():
                if idx.row() < len(self._mdl._dList):
                    self._mdl.beginRemoveRows(
                        QModelIndex(), idx.row(), idx.row()
                    )
                    self._mdl._dList.pop(idx.row())
                    self._mdl.endRemoveRows()

    _fdExts = [
        "ini Files (*.ini)",
        "All Files (*)",
    ]

    def _onRowCountChanged(self, ps, hint) -> None:
        print("**** Row Count Changed: ")
        vScrB = self.verticalScrollBar()
        ncw = 0
        if vScrB.isVisible():
            print("**** Scroll Bar is Visible")
            ncw = vScrB.width() + 1
        vHdr = self.verticalHeader()
        ncw += vHdr.width() + 3
        for i in range(self.model().columnCount()):
            ncw += self.columnWidth(i)
        self.setFixedWidth(ncw)


class GuiExtraCaseGenSets(QGroupBox):
    _tObj: GuiExtraCases

    def __init__(self, m: MdlWorkCaseGen, parent: QWidget | None = None):
        super().__init__("拡張領域設定", parent)
        self.setSizePolicy(QtSp.Expanding, QtSp.Fixed)

        lv0 = QVBoxLayout(self)
        self.setLayout(lv0)
        self._tObj = GuiExtraCases(m, self)
        lv0.addWidget(self._tObj, QtAf.AlignCenter)

    @property
    def table(self) -> GuiExtraCases:
        if not hasattr(self, "_tObj"):
            self._tObj = GuiExtraCases(self.model())
        return self._tObj
