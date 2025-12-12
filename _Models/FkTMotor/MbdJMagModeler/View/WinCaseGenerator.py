from __future__ import annotations

from os import path

from PySide6.QtCore import (
    QSettings,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from Model.MdlParameter import MdlParameter
from Model.MdlWorkCaseGen import MdlWorkCaseGen
from View.BaseGuiCaseGenSets import GuiBaseCaseGenSets
from View.CustomWidgets import QtAf, QtSp
from View.GuiExtraCaseGenSets import GuiExtraCaseGenSets


class WinCaseGenerator(QWidget):
    _linkedGuis: dict[str, QWidget]
    _mdl: MdlWorkCaseGen
    _pMdl: MdlParameter
    _settings: QSettings
    _extSets: GuiExtraCaseGenSets
    _lastDirDataOut: str

    onReqDataClear = Signal()
    onGenDataNew = Signal()
    onAddData = Signal(tuple)
    onAddDatas = Signal(list)
    onShow = Signal()

    onClose = Signal()

    def __init__(
        self,
        mdl: MdlWorkCaseGen,
        pMdl: MdlParameter,
        s: QSettings,
        p: QWidget = None,
    ):
        super().__init__(p)

        self.setWindowTitle("JMag Case Current Condition Generator")
        self.setWindowFlag(Qt.WindowType.Window)

        self._mdl = mdl
        self._pMdl = pMdl
        self._settings = s
        self._lastDirDataOut = ""

        self.loadSettings()

        self.setSizePolicy(QtSp.Fixed, QtSp.Fixed)

        lh0 = QHBoxLayout()
        self.setLayout(lh0)
        lv0 = QVBoxLayout()
        lh0.addLayout(lv0)

        lh1 = QHBoxLayout()
        lv0.addLayout(lh1)

        pm = self._pMdl
        bt0 = QPushButton("新規作成")

        def _genCases():
            s = QMessageBox.question(self, "", "All Data will be Cleared. Are you OK?")
            if s != QMessageBox.StandardButton.Yes:
                return
            self._mdl.genCases(
                False,
                pm.nDivSkew if pm.isSkewed else 0,
                pm.thSkew / pm.nP * 2 if pm.isSkewed else 0.0,
                pm.isMultiSlice,
            )

        bt0.clicked.connect(lambda: _genCases())

        lh1.addWidget(bt0)
        lh1.addItem(QSpacerItem(10, 0, QtSp.Fixed, QtSp.Fixed))
        bt1 = QPushButton("追加")

        def _addCases():
            s = QMessageBox.question(
                self,
                "",
                "Add Data will be ignored if already exists?\n Are you OK?",
            )
            if s != QMessageBox.StandardButton.Yes:
                return
            self._mdl.genCases(
                True,
                pm.nDivSkew if pm.isSkewed else 0,
                pm.thSkew / pm.nP * 2 if pm.isSkewed else 0.0,
                pm.isMultiSlice,
            )

        bt1.clicked.connect(lambda: _addCases())

        lh1.addWidget(bt1)
        lh1.addItem(QSpacerItem(10, 0, QtSp.Fixed, QtSp.Fixed))
        lh1.addItem(QSpacerItem(30, 0, QtSp.Fixed, QtSp.Fixed))
        bt3 = QPushButton("全削除")

        def _clrData():
            s = QMessageBox.question(self, "", "All Data will be Cleared. Are you OK?")
            if s != QMessageBox.StandardButton.Yes:
                return
            self._mdl._srcMdl.clrData()

        bt3.clicked.connect(lambda: _clrData())
        lh1.addWidget(bt3)

        lv0.addWidget(GuiBaseCaseGenSets(mdl, self))

        lv0.addItem(QSpacerItem(0, 0, QtSp.Fixed, QtSp.Expanding))
        lh0.addItem(QSpacerItem(0, 0, QtSp.Expanding, QtSp.Fixed))

        self.setSizePolicy(QtSp.Fixed, QtSp.Fixed)
        self.setStyleSheet(self._css)

        self._extSets = GuiExtraCaseGenSets(mdl, self)
        lv0.addWidget(self._extSets, QtAf.AlignCenter)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        return

    def showContextMenu(self, pos):
        menu = QMenu(self)
        # JSON Data Out
        saveJsonAct = QAction("Save JSON Data", self)
        saveJsonAct.setShortcut("Ctrl+S")
        saveJsonAct.triggered.connect(lambda: self._saveJsonData())
        menu.addAction(saveJsonAct)
        readJsonAct = QAction("Load JSON Data", self)
        readJsonAct.triggered.connect(lambda: self._loadJsonData())
        menu.addAction(readJsonAct)

        if self._extSets is not None:
            menu.addSeparator()
            self._extSets.table.addContextMenu(menu)

        menu.exec_(self.mapToGlobal(pos))

    _css = """
QGroupBox {
    border: 2px solid black;
    border-radius: 10px;
    font: bold;
    padding: 5px;
    margin-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center; /* タイトルの位置を中央に設定 */
        padding: 0 3px; /* タイトルのパディングを設定 */
    }
    QLineEdit {
        qproperty-alignment: AlignRight | AlignVCenter;
    }
"""
    ########################################################
    ########################################################

    # region SerDes Data
    __filters = ["Data File(*.wcgj)", "All Files (*)"]

    ########################################################
    def _saveJsonData(self) -> None:
        fName, filt = QFileDialog.getSaveFileName(
            self,
            "Save WorkCaseGen JSon Data",
            self._lastDirDataOut,
            ";;".join(self.__filters),
            self.__filters[0],
            options=QFileDialog.Options(),
        )
        if len(fName) == 0:
            return

        self._lastDirDataOut = path.dirname(fName)

        try:
            self._mdl.saveToJsonFile(fName)
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"保存エラー:{em}\n\n{sm}"
            print(f"@@@@@  {msg}")
            QMessageBox.critical(self, "保存エラー", f"ファイルの保存に失敗しました: {e}")

    ########################################################
    def _loadJsonData(self, isZipped: bool = False):
        fName, sfil = QFileDialog.getOpenFileName(
            self,
            "Load WorkCaseGen JSON Data",
            self._lastDirDataOut,
            ";;".join(self.__filters),
            self.__filters[0],
            options=QFileDialog.Options(),
        )

        if len(fName) == 0:
            return

        self._lastDirDataOut = path.dirname(fName)

        try:
            self._mdl.loadToJsonFile(fName)
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"読込エラー:{em}\n\n{sm}"
            print(f"@@@@@  {msg}")
            QMessageBox.critical(self, "読込エラー", f"ファイルの読込に失敗しました: {e}")

    ########################################################
    def loadSettings(self) -> None:
        s = self._settings
        if s is None:
            return

        s.beginGroup("WinWorkCaseGen")

        self._lastDirDataOut = s.value("lastDirDataOut", "")

        oldWinPos = s.value("PosCaseGen", None)
        if oldWinPos is not None:
            self.restoreGeometry(oldWinPos)
        s.endGroup()

    ########################################################
    def saveSettings(self) -> None:
        s = self._settings
        if s is None:
            return

        s.beginGroup("WinWorkCaseGen")
        s.setValue("lastDirDataOut", self._lastDirDataOut)
        s.setValue("PosCaseGen", self.saveGeometry())
        s.endGroup()

    # endregion

    # region Events
    ########################################################
    def showEvent(self, event):
        self.onShow.emit()
        return super().showEvent(event)

    ########################################################
    def closeEvent(self, event):
        self.saveSettings()
        try:
            self._mdl.onChangeState.disconnect()
        except Exception:
            pass
        self.onClose.emit()

        return super().closeEvent(event)

    # endregion
