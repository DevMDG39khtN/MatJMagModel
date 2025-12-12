from __future__ import annotations

import os
import time
from typing import List

from PySide6.QtCore import QSettings, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
)

from JMagDatas.ModelJMagMBD import FilePath, ModelJMagMBD
from JMagDatas.WorkCase import WorkStatus
from View.CustomWidgets import ValEdit
from View.GuiDialogs import SttDialog, showDialog
from View.WinJMagAnlPrjGen import WinJMagAnlPrjGen
from View.WinMbdMapGenerator import WinMbdMapGenerator

QSP = QSizePolicy.Policy
QAF = Qt.AlignmentFlag


class FileStatusDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)


class FileNameCombo(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSP.Fixed, QSP.Fixed)
        self.setFixedWidth(400)

    def showPopup(self):
        for i in range(self.count()):
            item = self.itemData(i)
            if isinstance(item, FilePath):
                # print(f"Item {i}: {item.Path}")
                pass
        super().showPopup()


class GuiMbdSetting(QGroupBox):
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
    "QPushButton {padding-left: 1px; adding-right: 1px;}"
"""

    onReqJMagLnk = Signal()
    onShowCaseGen = Signal()
    onExtractFinished = Signal()
    _onSwJMagPrj = Signal(list)

    __settings: QSettings
    __fileHistory: List[FilePath]
    __tgtPath: FilePath
    __selector: QComboBox
    __selectBtn: QPushButton
    __tgtFolder: QLabel
    _wStudyName: QComboBox
    _lastPath: str
    _mdl: ModelJMagMBD

    _wmg: WinMbdMapGenerator | None
    _wgp: WinJMagAnlPrjGen | None

    _extCancel: bool

    def __init__(self, m: ModelJMagMBD, settings: QSettings, parent=None) -> None:
        self._mdl = m
        self.__settings = settings
        self.__fileHistory = []
        self.__tgtPath = None
        self._lastPath = ""
        self._wmg = None
        self._wgp = None
        self._extCancel = False

        super().__init__("Base JMag Project File", parent)
        self.__setLayout()
        self.__setBehavior()
        self._mdl._mdlPrm.isMultiSlice = False

        self._mdl.onShowMsg.connect(lambda t, msg: showDialog(t, msg, p=self))

    def __setSkewLayout(self) -> QVBoxLayout:
        pMdl = self._mdl._mdlPrm

        p0 = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        qpf = QSizePolicy.Policy.Fixed

        lv0 = QVBoxLayout()
        lh0 = QHBoxLayout()
        lv0.addLayout(lh0)

        lh0.addItem(QSpacerItem(15, 1, qpf, qpf))
        cs0 = QCheckBox("Skew")
        lh0.addWidget(cs0)

        ta = QLabel("/")
        lh0.addWidget(ta)

        cs1 = QCheckBox("MultiSlice")
        lh0.addWidget(cs1)
        cs1.setEnabled(False)

        lh1 = QHBoxLayout()
        lv0.addLayout(lh1)
        ts0 = QLabel("Angle:")
        ts0.setAlignment(p0)
        lh1.addWidget(ts0)
        es0 = ValEdit(pMdl.lnkThSkew, wf=50)
        lh1.addWidget(es0)
        ts1 = QLabel("/")
        ts1.setAlignment(p0)
        lh1.addWidget(ts1)
        ts2 = QLabel("Div.:")
        ts2.setAlignment(p0)
        lh1.addWidget(ts2)
        es1 = ValEdit(pMdl.lnkNDivSkew, wf=25)
        lh1.addWidget(es1)

        def _set0(s: bool):
            pMdl.isSkewed = s

        cs0.stateChanged.connect(lambda s: _set0(s == Qt.CheckState.Checked.value))

        def _onSkewChanged(s: bool) -> None:
            cs0.setChecked(s)
            print(f"*** Skew Changed to {s} <- {pMdl.isSkewed}")
            if not pMdl.isMultiSlice:
                es0.setEnabled(s)
                es1.setEnabled(s)

        cs0.setChecked(pMdl.isSkewed)

        pMdl.lnkIsSkew.onValueChanged.connect(lambda s: _onSkewChanged(s))

        def _set1(s: bool):
            pMdl.isMultiSlice = s

        cs1.stateChanged.connect(lambda s: _set1(s == Qt.CheckState.Checked.value))

        def _onMltSlcChanged(s: bool) -> None:
            print(f"*** Multi-Slice Changed to {s} <- {pMdl.isMultiSlice}")
            cs1.setEnabled(True)
            cs1.setChecked(s)
            cs1.setEnabled(False)
            if s:
                cs0.setChecked(s)
            cs0.setEnabled(not s)
            es0.setEnabled(not s)
            es1.setEnabled(not s)
            # self.ChangeSkewStatus()

        pMdl.lnkIsMultiSlice.onValueChanged.connect(lambda s: _onMltSlcChanged(s))
        pMdl._onAllUpdate()

        pMdl.lnkIsMultiSlice.onValueChanged.emit(pMdl.isMultiSlice)
        pMdl.lnkIsSkew.onValueChanged.emit(pMdl.isSkewed)

        return lv0

    # region GuiFileSelector Layout
    def __setLayout(self):
        m = self._mdl

        ts = self.style()
        self.setStyleSheet(self._css)
        self.setSizePolicy(QSP.Preferred, QSP.Fixed)

        gLyt = QGridLayout(self)
        self.setLayout(gLyt)

        fLbl = QLabel("Name:", self)
        gLyt.addWidget(fLbl, 0, 0)
        fLbl.setSizePolicy(QSP.Fixed, QSP.Fixed)

        fCmb = QComboBox(self)
        fCmb.setSizePolicy(QSP.Expanding, QSP.Fixed)
        fCmb.setMinimumWidth(300)

        self.__selector = fCmb
        gLyt.addWidget(fCmb, 0, 2)
        icn = ts.standardIcon(QStyle.StandardPixmap.SP_FileDialogStart)
        fBtn = QPushButton("", self)
        gLyt.addWidget(fBtn, 0, 3)
        fBtn.setIcon(icn)
        fBtn.setToolTip("Select JMag Base Project File")
        fBtn.setSizePolicy(QSP.Fixed, QSP.Fixed)
        self.__selectBtn = fBtn

        wConBtn = QPushButton("条件", self)
        gLyt.addWidget(wConBtn, 0, 4)
        wConBtn.setFixedWidth(55)
        wConBtn.setSizePolicy(QSP.Fixed, QSP.Fixed)
        wConBtn.clicked.connect(lambda: self.onShowCaseGen.emit())
        wConBtn.setIcon(ts.standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))

        # Link To JMag Application
        wLnkBtn = QPushButton("JMag", self)
        wConBtn.setFixedWidth(55)
        gLyt.addWidget(wLnkBtn, 0, 5)
        wLnkBtn.setSizePolicy(QSP.Fixed, QSP.Fixed)
        wLnkBtn.setToolTip("Link to JMag Project")
        ic1 = ts.standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        ic2 = ts.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        ic1g = ts.standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton)
        wLnkBtn.setIcon(ic1g)

        wLnkBtn.clicked.connect(lambda: self._mdl.toChangeLinkStatus(not self._mdl.isLinked))

        wGenBtn = QPushButton("生成", self)
        gLyt.addWidget(wGenBtn, 0, 6)
        wGenBtn.setFixedWidth(55)

        def _showGenAnlPrj():
            if self._wgp is None:
                self._wgp = WinJMagAnlPrjGen(self._mdl.mdlGenJps, self._mdl, self.__settings, self)
                self._wgp.onDataChanged.connect(lambda: self._mdl._mdlWCS.layoutChanged.emit())
                self._wgp.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

                def _onDestroyed():
                    self._wgp = None

                self._wgp.destroyed.connect(lambda: _onDestroyed())
                self._wgp.show()
            else:
                self._wgp.raise_()
                self._wgp.activateWindow()

        wGenBtn.clicked.connect(lambda: _showGenAnlPrj())

        wGenBtn.setToolTip("Create JMag Analysis Project")
        wGenBtn.setEnabled(False)
        wGenBtn.setSizePolicy(QSP.Fixed, QSP.Fixed)
        wGenBtn.setIcon(ts.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))

        wExtBtn = QPushButton("抽出", self)
        wExtBtn.setEnabled(False)
        wExtBtn.setFixedWidth(55)
        gLyt.addWidget(wExtBtn, 0, 7)
        wExtBtn.setIcon(ts.standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))

        def _onExtData():
            msg = "JMag解析結果を抽出しますか？"
            dBtn = QMessageBox.StandardButton.No
            btn = QMessageBox.StandardButton.Yes | dBtn

            ret = QMessageBox.information(self, "Extract JMag Analysis", msg, btn, dBtn)
            if ret != QMessageBox.StandardButton.Yes:
                return

            total = sum(
                1 + (len(wc.skewedDatas) if not self._mdl._mdlPrm.isMultiSlice else 0)
                for wc in self._mdl._mdlWCS.dataList
                if wc.status == WorkStatus.Defined
            )

            dlg = QProgressDialog("抽出中...", "Cancel", 0, total, self)
            dlg.setWindowTitle("進捗")
            dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
            dlg.setAutoClose(False)
            dlg.setAutoReset(False)
            dlg.setValue(0)
            dlg.show()
            QApplication.processEvents()
            time.sleep(0.1)  # 少し待つ

            self._extCancel = False

            def onProgress(val: int):
                n = dlg.value()
                if val == 0:
                    if n <= 0:
                        dlg.setValue(0)
                    QApplication.processEvents()
                    return
                dlg.setValue(n + val)
                # 必要ならQApplication.processEvents()を呼ぶ

            def isCanceled():
                return dlg.wasCanceled()

            try:
                self._mdl.extractData(onProgress, isCanceled)

            except Exception as e:
                import traceback

                em = str(e)
                sm = traceback.format_exc()
                msg = f"実行エラー:{em}\n\n{sm}"
                self._mdl.isLinked = self._mdl.isAppOK
                print(f"@@@@@ Error in Data Extracting:{msg}")
                showDialog(SttDialog.Error, msg, p=self)
            finally:
                print(">>>>> End Process in Data Extracting")
                dlg.close()
                self._mdl._mdlWCS.layoutChanged.emit()
            return

        wExtBtn.clicked.connect(lambda: _onExtData())

        btn = QPushButton("Map", self)
        btn.setFixedWidth(55)
        gLyt.addWidget(btn, 0, 8)
        btn.setIcon(ts.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        btn.clicked.connect(lambda: self._showGenMbdMap())

        ### 2行目
        dLbl = QLabel("Dir:", self)
        dLbl.setSizePolicy(QSP.Fixed, QSP.Fixed)
        gLyt.addWidget(dLbl, 1, 0)

        dNm = QLabel("---", self)
        dNm.setFrameStyle(QFrame.Shape.Box.value | QFrame.Shadow.Sunken.value)
        dNm.setSizePolicy(QSP.Minimum, QSP.Fixed)
        gLyt.addWidget(dNm, 1, 1, 1, 5)
        self.__tgtFolder = dNm

        ### 3行目
        dLbl = QLabel("Study:", self)
        dLbl.setSizePolicy(QSP.Fixed, QSP.Fixed)
        gLyt.addWidget(dLbl, 2, 0)

        # Studyリスト対応時の処理

        dsn = QComboBox(self)

        def _onSwPrj(sLst: list[int, str]) -> None:
            sns = [s[1] for s in sLst]
            dsn.clear()
            dsn.addItems(sns)
            dsn.setCurrentIndex(0)

        self._onSwJMagPrj.connect(lambda sls: _onSwPrj(sls))
        gLyt.addWidget(dsn, 2, 1, 1, 5)
        self._wStudyName = dsn
        dsn.setEnabled(False)
        dsn.setPlaceholderText(">>>>> Not Link to JMag")
        dsn.currentIndexChanged.connect(lambda i: self._mdl.setTgtStudy(i))

        def _setLnkStatus(stt: bool, ss: bool):
            if stt:
                wLnkBtn.setIcon(ic1)
                wGenBtn.setEnabled(True)
                wExtBtn.setEnabled(True)
                dsn.setEnabled(True)
                self.setTgtFile(m.BasePrjPath)
            else:
                wGenBtn.setEnabled(False)
                if ss:
                    wLnkBtn.setIcon(ic2)
                else:
                    wLnkBtn.setIcon(ic1g)

                wExtBtn.setEnabled(False)
                dsn.setEnabled(False)

        m.onSwdLinkStatus.connect(lambda s, ss: _setLnkStatus(s, ss))

        skl = self.__setSkewLayout()
        wFrm = QFrame(self)
        wFrm.setFrameShape(QFrame.Shape.StyledPanel)
        wFrm.setLayout(skl)
        gLyt.addWidget(wFrm, 1, 6, 2, 3)

        gLyt.setColumnStretch(1, 0)
        gLyt.setColumnStretch(2, 1)
        gLyt.setColumnStretch(0, 0)
        gLyt.setColumnStretch(6, 0)
        gLyt.setColumnStretch(7, 0)
        gLyt.setColumnStretch(8, 0)
        return

    def _showGenMbdMap(self):
        if self._wmg is None:
            self._wmg = WinMbdMapGenerator(self._mdl._mdlMgen, self._mdl, self.__settings, self)

            self._wmg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

            def _onClose():
                self._wmg = None

            self._wmg.destroyed.connect(lambda: _onClose())
            self._wmg.show()
        else:
            self._wmg.raise_()
            self._wmg.activateWindow()

    def __setBehavior(self):
        self.__selectBtn.clicked.connect(self._selectFile)

        fn = self.__selector
        for h in self.__fileHistory:
            fn.addItem(h.Name, h)
        fn.currentIndexChanged.connect(self.Selection)

    # endregion

    def Selection(self) -> None:
        id = self.__selector.currentIndex()
        tp: FilePath = self.__selector.currentData()
        print(f"File Selection To [{id}]-({tp.Name})")
        if self.__tgtPath is None or self.__tgtPath.Path != tp.Path:
            self.__tgtFolder.setText(tp.Dir)
            self.__tgtPath = tp
            self._lastPath = tp.Path

            self.__selector.currentIndexChanged.disconnect(self.Selection)
            self.__fileHistory.remove(tp)
            self.__selector.removeItem(id)
            self.__fileHistory.insert(0, tp)
            self.__selector.insertItem(0, tp.Name, tp)
            self.__selector.setCurrentIndex(0)
            self.__selector.currentIndexChanged.connect(self.Selection)

        self.setTgtFile(tp)
        print(f"!!!!! File Selected Fired: {tp.Path}")

    def _selectFile(self):
        """
        Select JMag Project File Dialog
        """
        _fdExts = [
            "JMag (*.jproj)",
            "All Files (*)",
        ]
        options = QFileDialog.Options()
        selFp, selExts = QFileDialog.getOpenFileName(
            None,
            "Select JMag Project File",
            os.path.dirname(self._lastPath),
            ";;".join(_fdExts),
            _fdExts[0],
            options,
        )

        if len(selFp) <= 0:
            return

        fn = FilePath(selFp)
        self.setTgtFile(fn)

    @Slot(FilePath)
    def setTgtFile(self, fn: FilePath) -> None:
        """
        Set JMag Project File

        Parameters
        ----------
        fn : FilePath
            Target FilePath
        """
        m = self._mdl

        m.BasePrjPath = fn
        if m.isAppOK:
            aPath = m.AppPrjPath
            if aPath.Path != m.BasePrjPath.Path:
                if len(aPath.Path) > 0:
                    msg = f"Change to {m.BasePrjPath.Name}"
                    msg += f"\n  from  {aPath.Name}"
                    btn = QMessageBox.StandardButton.Ok
                    QMessageBox.information(self, "Change JMag Project", msg, btn, btn)
                m.loadBasePrj()

            ls = self._mdl.getStudyNames()
            if len(ls) > 0:
                self._wStudyName.clear()
                self._wStudyName.addItems([s[1] for s in ls])
                self._wStudyName.setCurrentIndex(0)

        ps = [hp.Path for hp in self.__fileHistory]
        if len(ps) > 0 and fn.Path == ps[0]:
            return
        self.__selector.currentIndexChanged.disconnect(self.Selection)
        if fn.Path in ps:
            id = ps.index(fn.Path)
            del self.__fileHistory[id]
            self.__selector.removeItem(id)
        self.__fileHistory.insert(0, fn)
        self.__selector.insertItem(0, fn.Name, fn)
        # 10を超えると古いものから削除
        self.__fileHistory = self.__fileHistory[:10]
        nc = self.__selector.count()
        while nc > 10:
            self.__selector.removeItem(nc - 1)
            nc = self.__selector.count()
        self.__selector.setCurrentIndex(-1)
        self.__selector.currentIndexChanged.connect(self.Selection)
        self.__selector.setCurrentIndex(0)
        self.__tgtFolder.setText(fn.Dir)
        if self.__tgtPath.Path != fn.Path:
            self._lastPath = self.__tgtPath.Path
        self.__tgtPath = fn

    @Slot(str)
    def setStudyName(self, sn: str) -> None:
        if self._wStudyName is not None and len(sn) > 0 and sn != "inValid":
            self._wStudyName.setEnabled(True)
            n = -1
            for i in range(self._wStudyName.count()):
                sn0 = self._wStudyName.itemText(i)
                if sn0 == sn:
                    n = i
                    break
            if n < 0:
                print(f"@@@@@ Study Name Not Found: {sn}")

            self._wStudyName.setCurrentIndex(n)
        else:
            self._wStudyName.clear()
            self._wStudyName.setEnabled(False)

    @Slot()
    def ChangeSkewStatus(self) -> None:
        pm = self._mdl._mdlPrm
        wcm = self._mdl._mdlWCS
        if len(wcm.dataList) == 0:
            return
        w0 = wcm.dataList[0]
        fSk0 = w0.hasSkew
        fSk1 = w0.isSlice
        if pm.isSkewed == fSk0 and pm.isMultiSlice == fSk1:
            return

        skStt = (
            pm.nDivSkew if pm.isSkewed else 0,
            pm.thSkew / pm.nP * 2 if pm.isSkewed else 0.0,
            pm.isMultiSlice,
        )
        wcm = self._mdl._mdlWCS
        if any(wc.status >= WorkStatus.Defined for wc in wcm.dataList):
            msg = "Skew変更時,全ての条件を初期化します\nAre you OK？"
            ret = showDialog(SttDialog.Question, msg, p=self)
            if ret != QMessageBox.StandardButton.Yes:
                if pm.isSkewed != fSk0:
                    pm.isSkewed = fSk0
                if pm.isMultiSlice != fSk1:
                    pm.isMultiSlice = fSk1
                return
            wcm.ChangeSkewStatus(skStt)
            print(">>>> Skew 条件が変更されました")
            return

    # region Setting Area
    def loadSettings(self, s: QSettings = None) -> None:
        if s is None:
            s = self.__settings
        if s is None:
            return

        s.beginGroup("FileSelector")

        self.__fileHistory = []
        sz = s.beginReadArray("History")
        for i in range(sz):
            s.setArrayIndex(i)
            p = s.value("Path")
            if p is not None and len(p) > 0:
                self.__fileHistory.append(FilePath(p))
        s.endArray()

        s.endGroup()
        # FilePath History ComboBox Item の復元
        self.__selector.clear()
        for hp in self.__fileHistory:
            self.__selector.addItem(hp.Name, hp)
        self.__selector.setCurrentIndex(0)

        return

    def saveSettings(self, s: QSettings = None) -> None:
        if s is None:
            s = self.__settings
        if s is None:
            return

        s.beginGroup("FileSelector")
        s.setValue("LastPath", self._lastPath)
        s.beginGroup("History")
        s.remove("")
        s.endGroup()
        s.beginWriteArray("History")
        for i, hp in enumerate(self.__fileHistory):
            pstr = hp.Path
            if len(pstr) > 0:
                s.setArrayIndex(i)
                s.setValue("Path", pstr)
        s.endArray()
        s.endGroup()

    # endregion

    # region Properties
    @property
    def FileName(self) -> str:
        return self.__tgtPath.Name

    @property
    def Folder(self) -> str:
        return self.__tgtPath.Dir

    @property
    def Path(self) -> str:
        return self.__tgtPath.Path

    # endregion

    # region Events
    def closeEvent(self, event):
        self.saveSettings()
        return super().closeEvent(event)

    # endregion
