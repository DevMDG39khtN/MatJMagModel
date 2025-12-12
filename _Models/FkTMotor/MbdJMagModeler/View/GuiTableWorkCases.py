from __future__ import annotations

from os import path
from typing import Dict, Union

from PySide6.QtCore import (
    QItemSelection,
    QModelIndex,
    QPersistentModelIndex,
    QSettings,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAction,
    QKeyEvent,
    QKeySequence,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHeaderView,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QTableView,
    QWidget,
)

from JMagDatas.AxesContents import Axis2D, MotAxes
from JMagDatas.ModelJMagMBD import ModelJMagMBD
from JMagDatas.WorkCase import LnkPrjStatus, StudyInfo, WorkCase, WorkStatus
from Model.MdlWorkCaseStore import MdlWorkCaseStore
from View.GuiDialogs import SttDialog, showDialog

TQszPlcy = QSizePolicy.Policy  # type alias
TQfrmShp = QFrame.Shape  # type alias
TQwTyp = Qt.WindowType  # type alias
TQwgtN = Union[QWidget, None]  # type alias
TQmIdx = Union[QModelIndex, QPersistentModelIndex]  # type alias
TAxEdits = Dict[MotAxes, Dict[Axis2D, QLineEdit]]  # type alias
TQAlgn = Qt.AlignmentFlag  # type alias
TQScbP = Qt.ScrollBarPolicy  # type alias


"""
25/02/20 新規作成  ベース MdnMldJMagCode/JMagConditions/ViewAnalysisTable
    DataS
"""


class GuiTableWorkCases(QTableView):
    _model: MdlWorkCaseStore
    _dMdl: ModelJMagMBD
    _settings: QSettings
    _defIdExtFlt: list[int]
    _lastDirDataOut: str
    _lstExIdJSon: int
    _lstExIdJzip: int
    _lstFldData: str
    _lstExIdData: int

    onShowCaseGen = Signal()

    @property
    def Model(self) -> MdlWorkCaseStore:
        return super().model()

    def __init__(
        self,
        mdl: MdlWorkCaseStore,
        dModel: ModelJMagMBD,
        s: QSettings,
        parent: TQwgtN = None,
    ) -> None:
        super().__init__(parent)
        self._model = mdl
        self._dMdl = dModel
        self._settings = s
        self._ctxMenu = None

        self._lastDirDataOut = ""
        self._defIdExtFlt = [i for i in range(2)]
        self._lstExIdJSon = 0
        self._lstExIdJzip = 0
        self._lstFldData = ""
        self._lstExIdData = 0

        self.setStyleSheet("""
            QHeaderView::section {
                color:#004;
                background-color:#ddf;
                font-weight:bold;
                text-align: center;
            }
        """)

        src = QHeaderView.ResizeMode.Fixed
        self.horizontalHeader().setSectionResizeMode(src)
        self.horizontalHeader().setDefaultAlignment(TQAlgn.AlignCenter)
        self.verticalHeader().setSectionResizeMode(src)
        self.verticalHeader().setDefaultAlignment(TQAlgn.AlignRight)
        self.verticalHeader().setDefaultSectionSize(25)
        self.setWordWrap(False)
        self.setModel(mdl)

        self.setCornerButtonEnabled(True)

        colWs = [60, 60, 60, 60, 60, 50, 50, 40]
        for i in range(self.Model.columnCount()):
            if len(colWs) > i:
                self.setColumnWidth(i, colWs[i])

        nw0 = self.verticalHeader().width()
        nw = nw0 + 20  # + tb.columnSpan(0, 0)
        for i in range(mdl.columnCount()):
            n0 = self.columnWidth(i)
            nw += n0

        nh0 = self.horizontalHeader().height()
        nh = nh0  # + tb.rowSpan(0, 0)
        n1 = 100
        for i in range(mdl.rowCount()):
            n1 = self.rowHeight(i)
            nh += n1

        self.setMinimumWidth(nw - 30)
        self.setMaximumWidth(nw)
        self.setMinimumHeight(nh0 + 200)

        self.selectionModel().selectionChanged.connect(self.__selectionChanged)

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self.loadSettings(self._settings)
        return

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

    def rstCases(self):
        msg = "全ての条件を条件生成状態に戻します\n  よろしいですか？"
        showDialog(SttDialog.Question, msg, p=self)
        """Reset the cases in the model."""

        def _rstData(v: WorkCase):
            v.status = WorkStatus.Created
            v.StudyInfo = StudyInfo()
            v.caseNo = -1
            v.grpIdx = -1
            v._data.clear()
            v._pfStatus = LnkPrjStatus.Normal
            for _, vv in v.skewedDatas.items():
                vv.status = WorkStatus.Created
                vv.StudyInfo = StudyInfo()
                vv.caseNo = -1
                vv.grpIdx = -1
                vv._data.clear()
                vv._pfStatus = LnkPrjStatus.Normal
            v.skewedDatas.clear()

        self.Model.beginResetModel()
        for v in self.Model._list:
            _rstData(v)
        self.Model.endResetModel()
        self._dMdl._listStdInfo.clear()
        self.Model.layoutChanged.emit()

    def rstPrjs(self):
        msg = "全ての条件を結果抽出前状態に戻します\n  よろしいですか？"
        showDialog(SttDialog.Question, msg, p=self)
        """Reset the cases in the model."""

        def _rstData(v: WorkCase):
            v.status = WorkStatus.Defined
            v._data.clear()
            for _, vv in v.skewedDatas.items():
                vv.status = WorkStatus.Defined
                vv._data.clear()

        self.Model.beginResetModel()
        for v in self.Model._list:
            if v.status >= WorkStatus.Extracted:
                _rstData(v)
        self.Model.endResetModel()
        self.Model.layoutChanged.emit()

    @Slot(QItemSelection, QItemSelection)
    def __selectionChanged(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        m: MdlWorkCaseStore = self.model()
        # ids = selected.indexes()
        # 行／列選択後にカーソル移動するとなぜかselectedが空になる
        ids = self.selectedIndexes()
        if len(ids) == 1:
            tid = ids[0]
            if tid.isValid():
                nr = tid.row()
                if nr < len(m._list):
                    tv = m._list[nr]
                    self.Model.TargetData = tv
                    self.Model.SelectedData = [tv]
                    return
        elif len(ids) > 1:
            tvs = [
                m._list[id.row()]
                for id in ids
                if id.isValid() and id.row() < len(m._list)
            ]
            if len(tvs) > 0:
                self.Model.SelectedData = tvs
                self.Model.TargetData = tvs[1]
                return

        print("+++++ Selected data set to null")
        self.Model.TargetData = None
        self.Model.SelectedData = []

    ######################################################################3
    def showContextMenu(self, pos):
        menu = QMenu(self)
        self._ctxMenu = menu

        caseGenAct = QAction("Case生成", self)
        caseGenAct.setShortcut(QKeySequence("Ctrl+G"))
        caseGenAct.triggered.connect(lambda: self.onShowCaseGen.emit())
        menu.addAction(caseGenAct)
        menu.addSeparator()

        clrAct = QAction("Clear Data", self)
        clrAct.triggered.connect(self.clrData)
        clrAct.setEnabled(len(self.Model._list) > 0)
        menu.addAction(clrAct)

        selRows = self.selectionModel().selectedRows()
        if selRows:
            delAct = QAction("削除", self)

            def _delData():
                s = QMessageBox.question(
                    self, "", "Selected Data will be Removed. Are you OK?"
                )
                if s != QMessageBox.StandardButton.Yes:
                    return
                self.Model.delData(selRows)

            delAct.triggered.connect(lambda: _delData())
            menu.addAction(delAct)

        menu.addSeparator()

        # JSON Data Out
        saveJsonAct = QAction("Save JSON Data", self)
        saveJsonAct.triggered.connect(lambda: self._saveJsonData())
        menu.addAction(saveJsonAct)
        readJsonAct = QAction("Load JSON Data", self)
        readJsonAct.triggered.connect(lambda: self._loadJsonData())
        menu.addAction(readJsonAct)
        saveZipJsonAct = QAction("Save JSON Zipped Data", self)
        saveZipJsonAct.triggered.connect(lambda: self._saveJsonData(True))
        menu.addAction(saveZipJsonAct)
        readZipJsonAct = QAction("Load JSON Zipped Data", self)
        readZipJsonAct.triggered.connect(lambda: self._loadJsonData(True))
        menu.addAction(readZipJsonAct)
        menu.addSeparator()
        caseIniCaseAct = QAction("Case生成時に戻す", self)
        caseIniCaseAct.triggered.connect(lambda: self.rstCases())
        menu.addAction(caseIniCaseAct)
        caseIniPrjAct = QAction("Data抽出前に戻す", self)
        caseIniPrjAct.triggered.connect(lambda: self.rstPrjs())
        menu.addAction(caseIniPrjAct)
        menu.addSeparator()

        menu.exec_(self.viewport().mapToGlobal(pos))

    _doFlt = [
        "zipped JSON File(*.wcjz)",
        "JSON File(*.wcj)",
        "All Files (*)",
    ]
    _doIdxFlt: int

    def _saveWorkCaseData(self):
        options = QFileDialog.Options()
        fName, exFlt = QFileDialog.getSaveFileName(
            self,
            "Save WorkCase Data",
            self._lastDirDataOut,
            ";;".join(self._doFlt),
            self._doFlt[self._doIdxFlt],
            options=options,
        )
        if len(fName) == 0:
            return

    def _saveJsonData(self, isZipped: bool = False):
        filters0 = [
            ["Data File(*.wct)", "JSON File(*.json)", "All Files (*)"],
            ["Data File(*.wcd)", "All Files (*)"],
        ]
        fid = 1 if isZipped else 0
        filters = filters0[fid]
        tgtFil = filters[self._defIdExtFlt[fid]]
        options = QFileDialog.Options()
        fName, flt = QFileDialog.getSaveFileName(
            self,
            "Save WorkCase JSon Data",
            self._lastDirDataOut,
            ";;".join(filters),
            tgtFil,
            options=options,
        )
        if len(fName) == 0:
            return

        self._defIdExtFlt[fid] = filters.index(flt)
        self._lastDirDataOut = path.dirname(fName)
        try:
            dlg = showDialog(SttDialog.NoModeMsg, "データ保存中 ...", p=self)
            QApplication.processEvents()
            self.Model.saveToJsonFile(fName, isZipped)
            QApplication.processEvents()
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"保存エラー:{em}\n\n{sm}"
            print(f"@@@@@  {msg}")
            QMessageBox.critical(
                self, "保存エラー", f"ファイルの保存に失敗しました: {msg}"
            )
        finally:
            dlg.accept()

    def _loadJsonData(self, isZipped: bool = False):
        if isZipped:
            filters = ["Data File(*.wcd)", "All Files (*)"]
            fid = self._lstExIdJSon
        else:
            filters = [
                "Data File(*.wct)",
                "JSON File(*.json)",
                "All Files (*)",
            ]
            fid = self._lstExIdJzip
        tgtFil = filters[fid]

        options = QFileDialog.Options()
        fName, sFil = QFileDialog.getOpenFileName(
            self,
            "Load WorkCase JSON Data",
            self._lastDirDataOut,
            ";;".join(filters),
            tgtFil,
            options=options,
        )

        if len(fName) == 0:
            return

        self._lastDirDataOut = path.basename(fName)
        fid = filters.index(sFil)
        if isZipped:
            self._lstExIdJSon = fid
        else:
            self._lstExIdJzip = fid

        try:
            dlg = showDialog(SttDialog.NoModeMsg, "データ読込中 ...", p=self)
            QApplication.processEvents()
            self.Model.loadToJsonFile(fName, isZipped)
            QApplication.processEvents()
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"読込エラー:{em}\n\n{sm}"
            print(f"@@@@@  {msg}")
            QMessageBox.critical(
                self, "読込エラー", f"ファイルの読込に失敗しました: {msg}"
            )
        finally:
            dlg.accept()

    def clrData(self):
        s = QMessageBox.question(
            self, "", "All Data will be Cleared. Are you OK?"
        )
        if s != QMessageBox.StandardButton.Yes:
            return
        self.Model.clrData()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # 右クリック時は選択処理を行わない
            return

        super().mousePressEvent(event)

    def keyPressEvent(self, evt: QKeyEvent):
        if evt.key() == Qt.Key.Key_Tab:
            cIdx = self.currentIndex()
            nr = cIdx.row()
            nc = cIdx.column()
            isShift = evt.modifiers() & Qt.KeyboardModifier.ShiftModifier
            if not isShift:
                if nc < 0:
                    nc = 0
                elif nc > 0:
                    nr += 1
                    nc = 0
                else:
                    nc += 1
                if nr < 0:
                    nr = 0
                elif not nr < self.model().rowCount():
                    nr = 0
                    nc = 0
            else:
                if nr < 0:
                    nr = 0
                if nc < 0:
                    nc = 0
                elif nc == 0:
                    nc = 1
                    nr -= 1
                else:
                    nc -= 1
                if nr < 0:
                    nr = self.model().rowCount() - 1
                    nc = 1
            print(
                f"**** Tab Key: from ({cIdx.row()}, "
                f"{cIdx.column()})to ({nr}, {nc})"
            )
            self.setCurrentIndex(self.model().index(nr, nc))
        else:
            super().keyPressEvent(evt)

    def loadSettings(self, s: QSettings) -> None:
        s.beginGroup("WorkCaseStore")
        v = s.value("lastDirDataOut", "", str)
        self._lastDirDataOut = v
        v = s.value("lastDirJson", [0, 0])
        self._defIdExtFlt = [int(v[0]), int(v[1])]

        s.endGroup()

    def saveSettings(self, s: QSettings) -> None:
        if s is None:
            return

        s.beginGroup("WorkCaseStore")

        s.setValue("lastDirDataOut", self._lastDirDataOut)
        s.setValue("lastDirJson", self._defIdExtFlt)

        s.endGroup()

    def closeEvent(self, event):
        self.saveSettings(self._settings)
        return super().closeEvent(event)
