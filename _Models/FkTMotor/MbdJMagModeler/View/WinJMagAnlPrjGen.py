from __future__ import annotations

import os
import threading
import time
from os import path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

import JMagDatas.ModelJMagMBD as MdlJmg
from JMagDatas.WorkCase import WorkStatus
from Model.MdlJMagAnlPrjGen import DivStatus, MdlJMagAnlPrjGen
from View.CustomWidgets import QtAf
from View.GuiDialogs import SttDialog, showDialog
from View.GuiDivPrjWorkCases import GuiDivPrjWorkCases


class WinJMagAnlPrjGen(QWidget):
    _linkedGuis: dict[str, QWidget]
    _mdl: MdlJMagAnlPrjGen
    _dMdl: MdlJmg.ModelJMagMBD
    _settings: QSettings | None
    _lastDirPrjOut: str | None
    _lastPathBasePrj: str | None
    _lastDirSetOut: str | None

    onClose = Signal()
    onUpdated = Signal(int)
    onFinished = Signal()
    onShowErrMsg = Signal(str, str)
    onDataChanged = Signal()
    onJobUpdated = Signal(int)
    onJobCreated = Signal()
    onShow = Signal()

    def __init__(
        self,
        mdl: MdlJMagAnlPrjGen,
        dMdl: MdlJmg.ModelJMagMBD,
        s: QSettings,
        p: QWidget = None,
    ):
        super().__init__(p)

        self.setWindowTitle("JMag Analysis Projects Generator")
        self.setWindowFlag(Qt.WindowType.Window)

        self._mdl = mdl
        self._dMdl = dMdl
        self._settings = s
        self._lastDirPrjOut = ""
        self._lastPathBasePrj = ""
        self._lastDirSetOut = ""

        self.__evtGenPrj = threading.Event()
        self.__evtGenJob = threading.Event()

        self.loadSettings()

        lv0 = QVBoxLayout()
        self.setLayout(lv0)

        lv0.addWidget(GuiDivPrjWorkCases(mdl, self), QtAf.AlignCenter)

        lh0 = QHBoxLayout()
        lv0.addLayout(lh0)

        btn = QPushButton("解析Prj. 生成")
        lh0.addWidget(btn, QtAf.AlignCenter)

        lh0.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        acb = QCheckBox("生成後解析実行", self)
        lh0.addWidget(acb, QtAf.AlignCenter)
        acb.stateChanged.connect(lambda s: mdl.setIsDoJob(s == Qt.CheckState.Checked.value))
        mdl.onChangedIsDoJob.connect(lambda s: acb.setChecked(s))

        lh0.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))

        bDoAnal = QPushButton("解析実行")
        lh0.addWidget(bDoAnal, QtAf.AlignCenter)

        def _genExe(btn: QPushButton, doBtn: QPushButton) -> None:
            self.generator(btn)
            if self._mdl.isDoJob:
                self._createAnlJob(doBtn)
            return

        btn.clicked.connect(lambda: _genExe(btn, bDoAnal))

        bDoAnal.clicked.connect(lambda: self._createAnlJob(bDoAnal))

        self.onShowErrMsg.connect(lambda msg, tit: showDialog(SttDialog.Error, msg, tit, p=self))

        oss = self._mdl.sttDivPrj
        self._mdl.sttDivPrj = DivStatus.IaRmsVals
        QApplication.processEvents()
        self.setFixedSize(self.sizeHint())
        self._mdl.sttDivPrj = oss

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        return

    def generator(self, btn: QPushButton) -> None:
        bPath = self._dMdl.BasePrjPath.Path
        if bPath != self._lastPathBasePrj or not os.path.isdir(self._lastDirPrjOut):
            bDir = os.path.dirname(bPath)
        else:
            bDir = self._lastDirPrjOut
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        dlg.setOption(QFileDialog.Option.ShowDirsOnly, False)  # ファイルも表示
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dlg.setDirectory(bDir)
        dlg.setNameFilter("JMag (*.jproj);;All Files (*)")
        nRet = dlg.exec()
        if nRet == 0:
            return

        tDir = dlg.selectedFiles()[0]
        self._lastDirPrjOut = tDir
        self._lastPathBasePrj = bPath

        tgt = self._dMdl.wcList
        n = len([w for w in tgt if w.status == WorkStatus.Created]) + 6
        dlg = QProgressDialog("Create JMag Analysis Project File ...", "Cancel", 0, n, self)
        dlg.setWindowTitle("Generate Jprojs")
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setAutoClose(False)  # ← これでキャンセル時も閉じない
        dlg.setAutoReset(False)  # ← これで値リセットもしない
        dlg.setValue(0)
        dlg.show()
        QApplication.processEvents()
        time.sleep(0.1)  # Wait for show

        self._isCanceled = False

        self.nmDlg: QMessageBox = None
        self.__isDoGen = False

        def prgCancel() -> None:
            if not self.__isDoGen:
                return
            self._isCanceled = True
            self.__evtGenPrj.set()
            self.nmDlg = showDialog(SttDialog.NoModeMsg, "Cancel中です.", p=dlg)
            self.nmDlg.show()

        dlg.canceled.connect(lambda: prgCancel())

        def prgUpd(n: int) -> None:
            n0 = dlg.value()
            if n == 0:
                if n0 < 0:
                    dlg.setValue(0)
                QApplication.processEvents()
                return

            dlg.setValue(n0 + n)

            return

        try:
            self.onUpdated.disconnect()
        except Exception:
            pass
        self.onUpdated.connect(lambda n: prgUpd(n))

        def prgFin() -> None:
            print(">>>>> End Process in generating project list Request")
            self.__isDoGen = False
            if self.nmDlg is not None:
                self.nmDlg.accept()
                QApplication.processEvents()
                self.nmDlg = None
            dlg.close()
            btn.setEnabled(True)
            self._dMdl._mdlWCS.layoutChanged.emit()
            self.onDataChanged.emit()
            try:
                self.onFinished.disconnect()
            except Exception:
                pass
            return

        def wrkPrc(evt: threading.Event) -> None:
            try:
                print(">>>>> Start Process in generating project list Request")
                tLists = self._mdl.genAnlPrjList(tgt, self._dMdl._mdlPrm.maxIa, self.onUpdated, evt)
                QApplication.processEvents()
                evt.clear()
                self._dMdl.genAnlPrjFiles(tLists, tDir, self.onUpdated, evt)
            except Exception as e:
                import traceback

                em = str(e)
                sm = traceback.format_exc()
                msg = f"実行エラー:{em}\n\n{sm}"
                print(f"@@@@@ Error in generating project list:{msg}")
                showDialog(SttDialog.Error, msg, p=self)
                self._dMdl.isLinked = self._dMdl.isAppOK
            finally:
                self.onFinished.emit()
                QApplication.processEvents()
                print("<<<<< End in generating project list")
            return

        try:
            self.__isDoGen = True
            self.onFinished.connect(lambda: prgFin())
            self.__evtGenPrj.clear()
            btn.setEnabled(False)
            wrkPrc(self.__evtGenPrj)

        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"実行エラー:{em}\n\n{sm}"
            print(f"@@@@@ Error in start generating project list:{msg}")
            showDialog(SttDialog.Error, msg, p=self)
            self._dMdl.isLinked = self._dMdl.isAppOK
        finally:
            print(">>>>> End Process in generating project list Request")
            if self.nmDlg is not None:
                self.nmDlg.accept()
                self.nmDlg = None
            dlg.close()
            btn.setEnabled(True)
            self._dMdl._mdlWCS.layoutChanged.emit()
            try:
                self.onFinished.disconnect()
            except Exception:
                pass
        return

    def _createAnlJob(self, btn: QPushButton) -> None:
        if not self._dMdl.isLinked:
            QMessageBox.critical(self, "JMag Link Fail", "Conf  irm. or Relink.")
            return

        n = len(self._dMdl._listStdInfo)
        # region Job Process Dialog
        dlg = QProgressDialog("Create JMag Analysis Job on JMAG App ...", "Cancel", 0, n, self)
        dlg.setWindowTitle("Create JMag Analysis Job")
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setAutoClose(False)  # ← これでキャンセル時も閉じない
        dlg.setAutoReset(False)  # ← これで値リセットもしない
        dlg.setValue(0)
        dlg.show()
        QApplication.processEvents()
        time.sleep(0.1)  # Wait for show

        self._isJobCanceled = False
        self.__njDlg: QMessageBox = None
        self.__isDoJob = False

        def prgCancel() -> None:
            if not self.__isDoJob:
                return
            self._isJobCanceled = True
            self.__evtGenJob.set()
            self.__njDlg = showDialog(SttDialog.NoModeMsg, "Cancel中です.", p=dlg)
            self.__njDlg.show()

        dlg.canceled.connect(lambda: prgCancel())

        def prgUpd(n: int) -> None:
            n0 = dlg.value()
            if n == 0:
                if n0 < 0:
                    dlg.setValue(0)
                QApplication.processEvents()
                return

            dlg.setValue(n0 + n)
            return

        try:
            self.onJobUpdated.disconnect()
        except Exception:
            pass
        self.onJobUpdated.connect(lambda n: prgUpd(n))

        def prgFin() -> None:
            print(">>>>> End Process in Analysis Job Creation Request")
            self.__isDoJob = False
            if self.__njDlg is not None:
                self.__njDlg.accept()
                QApplication.processEvents()
                self.__njDlg = None
            dlg.close()
            btn.setEnabled(True)
            return

        # endregion
        def wrkPrc(evt: threading.Event) -> None:
            try:
                self.__isDoJob = True
                print(">>>>> Start Process in Analysis Job Creation Request")
                QApplication.processEvents()
                evt.clear()
                self._dMdl.addAnalysisJob(self.onJobUpdated, evt)
            except Exception as e:
                import traceback

                em = str(e)
                sm = traceback.format_exc()
                msg = f"実行エラー:{em}\n\n{sm}"
                print(f"@@@@@ Error in Analysis Job Creation:{msg}")
                showDialog(SttDialog.Error, msg, p=self)
                self._dMdl.isLinked = self._dMdl.isAppOK
            finally:
                self.onJobCreated.emit()
                QApplication.processEvents()
                print("<<<<< End Analysis Job Creation")
            return

        try:
            self.onJobCreated.connect(lambda: prgFin())
            btn.setEnabled(False)
            self.__evtGenJob.clear()
            wrkPrc(self.__evtGenJob)
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"実行エラー:{em}\n\n{sm}"
            self._dMdl.isLinked = self._dMdl.isAppOK
            print(f"@@@@@ Error in start Analysis Job Creation:{msg}")
            showDialog(SttDialog.Error, msg, p=self)
        finally:
            print(">>>>> End Process Analysis Job Creation")
            dlg.close()
            btn.setEnabled(True)
            try:
                self.onJobCreated.disconnect()
            except Exception:
                pass
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
        menu.exec_(self.mapToGlobal(pos))

    ########################################################

    # region SerDes Data
    __filters = ["Data File(*.pjg)", "All Files (*)"]

    ########################################################
    def _saveJsonData(self) -> None:
        fName, flt = QFileDialog.getSaveFileName(
            self,
            "Save Gen Anl Prj JSon Data",
            self._lastDirSetOut,
            ";;".join(self.__filters),
            self.__filters[0],
            options=QFileDialog.Options(),
        )
        if len(fName) == 0:
            return

        self._lastDirSetOut = path.dirname(fName)

        try:
            self._mdl.saveToJsonFile(fName)
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"保存エラー:{em}\n\n{sm}"
            print(f"@@@@@ Error in saving JSON data: {msg}")
            QMessageBox.critical(self, "保存エラー", f"ファイルの保存に失敗しました: {e}")

    ########################################################
    def _loadJsonData(self, isZipped: bool = False):
        fName, sFil = QFileDialog.getOpenFileName(
            self,
            "Load Gen AnlPrj JSON Data",
            self._lastDirSetOut,
            ";;".join(self.__filters),
            self.__filters[0],
            options=QFileDialog.Options(),
        )

        if len(fName) == 0:
            return

        self._lastDirSetOut = path.dirname(fName)

        try:
            self._mdl.loadToJsonFile(fName)
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"読込エラー:{em}\n\n{sm}"
            print(f"@@@@@ Error in loading JSON data: {msg}")
            QMessageBox.critical(self, "読込エラー", f"ファイルの読込に失敗しました: {msg}")

    ########################################################
    def loadSettings(self) -> None:
        s = self._settings
        s.beginGroup("WinJMagPrjGen")
        self._lastDirPrjOut = s.value("lastDirDataOut", "")
        self._lastPathBasePrj = s.value("lastPathBasePrj", "")
        self._lastDirSetOut = s.value("lastDirSetOut", "")
        oldWinPos = s.value("PosCaseGen", None)
        if oldWinPos is not None:
            self.restoreGeometry(oldWinPos)
        s.endGroup()

    ########################################################
    def saveSettings(self) -> None:
        s = self._settings

        if s is None:
            return
        s.beginGroup("WinJMagPrjGen")
        s.setValue("lastDirDataOut", self._lastDirPrjOut)
        s.setValue("lastPathBasePrj", self._lastPathBasePrj)
        s.setValue("lastDirSetOut", self._lastDirSetOut)
        s.setValue("PosPrjGen", self.saveGeometry())
        s.endGroup()

    # endregion

    # region Events
    ########################################################
    def showEvent(self, event):
        self.onShow.emit()
        return super().showEvent(event)

    ########################################################
    def closeEvent(self, event):
        try:
            self._mdl.onChangedDivStt.disconnect()
        except Exception:
            pass
        try:
            self._mdl.onChangedNumDiv.disconnect()
        except Exception:
            pass
        try:
            self._mdl.onChangedDivList.disconnect()
        except Exception:
            pass
        try:
            self._mdl.onChangedIsDivPrj.disconnect()
        except Exception:
            pass
        try:
            self._mdl.onChangedIsExtSplit.disconnect()
        except Exception:
            pass
        try:
            self._mdl.onChangedIsFwSplit.disconnect()
        except Exception:
            pass
        try:
            self._mdl.onChangedIsDoJob.disconnect()
        except Exception:
            pass
        self.saveSettings()
        self.onClose.emit()

        return super().closeEvent(event)

    # endregion
