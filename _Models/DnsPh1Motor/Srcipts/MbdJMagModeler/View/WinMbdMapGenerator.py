from __future__ import annotations

import os.path as path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

import JMagDatas.ModelJMagMBD as jdt
from Model.MdlMapDef import MdlMapDef
from View.CustomWidgets import ValEdit


class WinMbdMapGenerator(QWidget):
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
"""
    onFinished = Signal()
    onShow = Signal()

    # region Attribute Type Hints
    _mdl: MdlMapDef
    _dMdl: jdt.ModelJMagMBD
    _settings: QSettings | None
    _lastDirPrj: str
    # end region

    ########################################################
    def loadSettings(self, s: QSettings | None) -> None:
        if s is not None:
            s.beginGroup("MapGen")
            self._lastDirPrj = s.value("lastDirPrj", "", str)
            self.restoreGeometry(s.value("WinMapGen"))
            s.endGroup()

    ########################################################
    def saveSettings(self, s: QSettings | None) -> None:
        if s is not None:
            s.beginGroup("MapGen")
            s.setValue("lastDirPrj", self._lastDirPrj)
            s.setValue("WinMapGen", self.saveGeometry())
            s.endGroup()

    ########################################################
    def showEvent(self, event) -> None:
        """ウィンドウが表示されたときに呼び出される"""
        self.onShow.emit()
        super().showEvent(event)

    ################################1########################
    def closeEvent(self, event):
        self.saveSettings(self._settings)
        try:
            self._mdl.onOvrModChanged.disconnect()
        except Exception:
            pass
        aws: list[ValEdit] = self.findChildren(ValEdit)
        for w in aws:
            w.close()
        return super().closeEvent(event)

    ##### --------------------------------------------------
    def __init__(
        self,
        m: MdlMapDef,
        dm: jdt.ModelJMagMBD,
        s: QSettings | None = None,
        p=None,
    ) -> None:
        super().__init__(p)
        self.setWindowTitle("Control Map Generator")
        self.setWindowFlag(Qt.WindowType.Window)

        self._mdl = m
        self._dMdl = dm
        self._settings = s

        self._lastDirPrj = ""

        self.loadSettings(s)
        self._iniLayout()
        self.setStyleSheet(self._css)
        self.setFixedSize(self.sizeHint())

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    ########################################################
    def _iniLayout(self) -> None:
        """ウィンドウのレイアウトを設定する"""
        p = self.parent()
        m = self._mdl

        lhb = QHBoxLayout()
        self.setLayout(lhb)

        sp0 = QSizePolicy.Policy.Fixed
        sp1 = QSizePolicy.Policy.Preferred

        self.setSizePolicy(sp0, sp0)

        alf0 = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        alf1 = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        alf2 = Qt.AlignmentFlag.AlignCenter

        gbs = QGroupBox("解析マップ設定")
        lhb.addWidget(gbs)
        lg0 = QGridLayout()
        gbs.setLayout(lg0)
        lg0.addWidget(QLabel("Map Step幅"), 0, 0, 1, 2, alf2)
        lg0.addWidget(QLabel("電流 [A]: "), 1, 0, alf0)
        lg0.addWidget(ValEdit(m.dIdq, 50), 1, 1, alf1)
        lg0.addWidget(QLabel("磁束 [Wb] : "), 2, 0, alf0)
        lg0.addWidget(ValEdit(m.dFdq, 50), 2, 1, alf1)

        gbm = QGroupBox("Torque Map Range")
        lhb.addWidget(gbm)
        lg1 = QGridLayout()
        gbm.setLayout(lg1)
        lg1.addWidget(QLabel("トルク [Nm] : ", p), 0, 0, alf0)
        lg1.addWidget(QLabel("回転数 [rpm] : ", p), 1, 0, alf0)
        lg1.addWidget(QLabel("DC電圧 [V] : ", p), 2, 0, alf0)

        edv0 = ValEdit(m.axTrqs, 150, p=self)
        lg1.addWidget(edv0, 0, 1, alf1)
        edv1 = ValEdit(m._axNrpms, 150, p=self)
        lg1.addWidget(edv1, 1, 1, alf1)
        edv2 = ValEdit(m._axVdcs, 150, p=self)
        lg1.addWidget(edv2, 2, 1, alf1)
        lg1.addItem(QSpacerItem(20, 5, sp0, sp0), 0, 2)
        lg1.addWidget(QLabel("最大電流 [A]:"), 0, 3, alf0)
        eda = ValEdit(m.maxIa, 50, p=self)
        eda.setReadOnly(True)
        eda.setEnabled(False)
        lg1.addWidget(eda, 0, 4, alf1)
        lg1.addWidget(QLabel("Coil温度 [°C]:"), 0, 5, alf0)
        edb = ValEdit(m.tdCoil, 50, p=self)
        edb.setReadOnly(True)
        edb.setEnabled(False)
        lg1.addWidget(edb, 0, 6, alf1)
        cb0 = QCheckBox("過変調電圧限界")
        cb0.setChecked(m.isOvrMod)
        ss = Qt.CheckState.Checked.value
        cb0.stateChanged.connect(lambda s: m.setOvrMod(s == ss))
        m.onOvrModChanged.connect(lambda s: cb0.setChecked(s))
        lg1.addWidget(cb0, 1, 3, 1, 2, alf1)
        lg1.addWidget(QLabel("飽和電圧制限率:"), 1, 5, alf0)
        lg1.addWidget(ValEdit(m.rLmtVdc, 50, p=self), 1, 6, alf1)

        lg2 = QGridLayout()
        lg1.addLayout(lg2, 2, 3, 1, 2)
        lg2.addWidget(QLabel("最大トルクFit次数:"), 0, 1, alf0)
        lg2.addWidget(ValEdit(m.nOrdFitMtl, 35, p=self), 0, 2, alf1)

        btn = QPushButton("変換")
        lg1.addWidget(btn, 2, 5, 1, 2, alf2)

        def cnvToMatlabModel():
            """Convert JMag model to Matlab format."""
            btn.setEnabled(False)
            QApplication.processEvents()
            self._dMdl.cnvJmagToMatlab()
            self.onFinished.emit()
            btn.setEnabled(True)
            QApplication.processEvents()

        btn.clicked.connect(lambda: cnvToMatlabModel())
        lg1.addItem(QSpacerItem(0, 0, sp1, sp0), 0, 7)

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
        menu.exec_(self.mapToGlobal(pos))

    # region SerDes Data
    __filters = ["Data File(*.mmg)", "All Files (*)"]

    ########################################################
    def _saveJsonData(self) -> None:
        fName, flt = QFileDialog.getSaveFileName(
            self,
            "Save Gen Anl Prj JSon Data",
            self._lastDirPrj,
            ";;".join(self.__filters),
            self.__filters[0],
            options=QFileDialog.Options(),
        )
        if len(fName) == 0:
            return

        self._lastDirPrj = path.dirname(fName)

        try:
            self._mdl.saveToJsonFile(fName)
        except Exception as e:
            QMessageBox.critical(
                self, "保存エラー", f"ファイルの保存に失敗しました: {e}"
            )

    ########################################################
    def _loadJsonData(self, isZipped: bool = False):
        fName, sFil = QFileDialog.getOpenFileName(
            self,
            "Load Gen AnlPrj JSON Data",
            self._lastDirPrj,
            ";;".join(self.__filters),
            self.__filters[0],
            options=QFileDialog.Options(),
        )

        if len(fName) == 0:
            return

        self._lastDirPrj = path.dirname(fName)

        try:
            self._mdl.loadToJsonFile(fName)
        except Exception as e:
            QMessageBox.critical(
                self, "保存エラー", f"ファイルの読込に失敗しました: {e}"
            )

    # endregion
