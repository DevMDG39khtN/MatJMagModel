from __future__ import annotations

import os
import shutil

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from JMagDatas.ModelJMagMBD import ModelJMagMBD
from Model.MdlWorkCaseStore import MdlWorkCaseStore
from View.GuiDialogs import SttDialog, showDialog
from View.GuiMbdSetting import GuiMbdSetting
from View.GuiModelParameter import GuiModelParameter
from View.GuiPlotWorkSetsArea import GuiPlotWorkSetsArea
from View.GuiTableWorkCases import GuiTableWorkCases
from View.WinCaseGenerator import WinCaseGenerator

QSP = QSizePolicy.Policy
QAF = Qt.AlignmentFlag


class GuiMainWidget(QWidget):
    """JMag MBD  MODEL GUI"""

    _settings: QSettings
    _defMdl: MdlWorkCaseStore
    _jMagModel: ModelJMagMBD
    __plotArea: GuiPlotWorkSetsArea
    __guiBase: GuiMbdSetting

    _lastDirOut: str
    __wcg: WinCaseGenerator | None

    def __init__(self, s: QSettings, parent=None):
        super().__init__(parent)

        self._jMagModel = ModelJMagMBD()
        tMdl = self._jMagModel
        self._settings = s

        self._lastDirOut = ""
        if self._settings is not None:
            self._lastDirOut = self._settings.value(
                "LastDirPrjDataOut", "", str
            )

        dlg = showDialog(SttDialog.NoModeMsg, "データ読込中 ...", p=self)
        QApplication.processEvents()
        tMdl.loadFromIni(s)
        QApplication.processEvents()
        dlg.accept()

        lv0 = QVBoxLayout(self)
        self.setLayout(lv0)
        lh0 = QHBoxLayout()
        lv0.addLayout(lh0)

        w0a = GuiModelParameter(tMdl._mdlPrm, self._settings)
        lh0.addWidget(w0a, alignment=Qt.AlignmentFlag.AlignCenter)

        lh0 = QHBoxLayout()
        lv0.addLayout(lh0)

        m = tMdl._mdlWCS
        self._defMdl = m
        wTwc = GuiTableWorkCases(m, self._jMagModel, self._settings)
        lh0.addWidget(wTwc)
        self.__wcg = None

        def _showCaseGen():
            """WinCaseGenerator 表示"""

            def _clearWin():
                self.__wcg = None
                return

            if self.__wcg is None:
                self.__wcg = WinCaseGenerator(
                    tMdl.mdlWCG, self._settings, wTwc
                )
                self.__wcg.onShow.connect(
                    lambda: tMdl.mdlWCG.maxIa.setText(str(tMdl._mdlPrm.maxIa))
                )
                wcg = self.__wcg
                wcg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
                wcg.destroyed.connect(lambda: _clearWin())
                wcg.show()
            else:
                self.__wcg.raise_()
                self.__wcg.activateWindow()

        wTwc.onShowCaseGen.connect(lambda: _showCaseGen())

        lva = QVBoxLayout()
        lh0.addLayout(lva)

        wfs = GuiMbdSetting(self._jMagModel, s)
        lva.addWidget(wfs)

        wfs.onReqJMagLnk.connect(lambda: self._jMagModel.linkApp())
        wfs.onShowCaseGen.connect(lambda: _showCaseGen())
        self._jMagModel.onChangeStudy.connect(wfs.setStudyName)
        lv1 = lva
        self.__guiBase = wfs

        wa1 = GuiPlotWorkSetsArea(m)
        self.__plotArea = wa1
        tMdl._mdlPrm.onMaxIdqChanged.connect(lambda v: wa1.toMaxIaFromIdq(v))
        lv1.addWidget(wa1)

        wfs.loadSettings()
        tMdl._mdlPrm.onMaxIdqChanged.emit(tMdl._mdlPrm.maxIdq)
        tMdl._mdlWCS.resetDataModified()
        return

    ############################################################

    _fdExts = [
        "MdbProject (*.ini)",
        "All Files (*)",
    ]

    def loadFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "ファイルを開く",
            self._lastDirOut,
            ";;".join(self._fdExts),
            options=options,
        )
        if fileName:
            try:
                self._lastDirOut = os.path.dirname(fileName)
                qs = QSettings(fileName, QSettings.Format.IniFormat)
                dlg = showDialog(
                    SttDialog.NoModeMsg, "データ読込中 ...", p=self
                )
                QApplication.processEvents()
                self.__guiBase.loadSettings(qs)
                self._jMagModel.loadFromIni(qs)
                dlg.accept()
                QApplication.processEvents()
                if len(self._jMagModel._mdlWCS.dataList) > 0:
                    self.__plotArea.plotDQ()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "読み込みエラー",
                    f"ファイルの読み込みに失敗しました: {e}",
                )

    def saveFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "ファイルを保存",
            self._lastDirOut,
            ";;".join(self._fdExts),
            options=options,
        )
        if fileName:
            try:
                self._lastDirOut = os.path.dirname(fileName)
                qs = QSettings(fileName, QSettings.Format.IniFormat)
                dlg = showDialog(
                    SttDialog.NoModeMsg, "データ保存中 ...", p=self
                )
                QApplication.processEvents()
                self.__guiBase.saveSettings(qs)
                self._jMagModel.saveToIni(qs, True)
                dlg.accept()
                QApplication.processEvents()
            except Exception as e:
                QMessageBox.critical(
                    self, "保存エラー", f"ファイルの保存に失敗しました: {e}"
                )

    @property
    def InModel(self) -> MdlWorkCaseStore:
        return self._defMdl

    def closeEvent(self, event):
        if not MainWindow.isReset:
            dlg = showDialog(SttDialog.NoModeMsg, "データ保存中 ...", p=self)
            QApplication.processEvents()
            if self._settings is not None:
                self._settings.setValue("LastDirPrjDataOut", self._lastDirOut)
            self.__guiBase.saveSettings(self._settings)
            self._jMagModel.saveToIni(self._settings)
            dlg.accept()
            QApplication.processEvents()
        super().closeEvent(event)

    ############################################################


class MainWindow(QMainWindow):
    """Motor Mbd Setting View"""

    isReset: bool = False
    _settings: QSettings
    _defMdl: MdlWorkCaseStore

    def Reset(self) -> None:
        msg = "結果はすべて削除されます\n  よろしいですか？"
        dBtn = QMessageBox.StandardButton.Cancel
        btn = QMessageBox.StandardButton.Yes | dBtn

        ret = QMessageBox.information(self, "Reset Project", msg, btn, dBtn)
        if ret != QMessageBox.StandardButton.Yes:
            return

        spf = self._settings.fileName()
        spd = os.path.dirname(spf)
        if not os.path.isdir(spd):
            os.makedirs(spd, exist_ok=True)
        if os.path.isfile(spf):
            sdf = spf + ".bakRst"
            shutil.copyfile(spf, sdf)
        self._settings.clear()
        self._settings.sync()
        MainWindow.isReset = True
        self.close()

        return

    def __init__(self, parent=None):
        super().__init__(parent)
        MainWindow.isReset = False

        self._settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "JMagMotorModel",
            "JMagMotorModelSettings",
        )
        self.setMaximumWidth(1800)
        self.setMaximumHeight(950)

        oldWinPos = self._settings.value("MainWinPos")
        if oldWinPos is not None:
            self.restoreGeometry(oldWinPos)

        w = GuiMainWidget(self._settings, self)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("ファイル")
        newAction = QAction("新規作成", self)
        newAction.triggered.connect(lambda: self.Reset())
        fileMenu.addAction(newAction)
        fileMenu.addSeparator()

        loadAction = QAction("読込", self)
        loadAction.triggered.connect(w.loadFile)
        fileMenu.addAction(loadAction)
        self.la = loadAction
        saveAction = QAction("保存", self)
        self.sa = loadAction
        saveAction.triggered.connect(w.saveFile)
        fileMenu.addAction(saveAction)

        fileMenu.addSeparator()

        exitAction = QAction("終了", self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        self.setWindowTitle("JMAG Motor Model")
        self.setCentralWidget(w)
        self._defMdl = w.InModel

    def closeEvent(self, event):
        """Save Main Window State"""
        self._settings.setValue("MainWinPos", self.saveGeometry())
        if not MainWindow.isReset:
            aws: list[QWidget] = self.findChildren(QWidget)
            for w in aws:
                w.close()
        super().closeEvent(event)

    @property
    def InModel(self) -> MdlWorkCaseStore:
        return self._defMdl
