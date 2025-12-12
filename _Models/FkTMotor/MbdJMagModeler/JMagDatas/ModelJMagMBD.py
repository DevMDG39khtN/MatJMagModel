from __future__ import annotations

import math
import os
import re
import threading
import time
from typing import Callable, Optional

import jmag.designer as jd
from PySide6.QtCore import (
    QObject,
    QSettings,
    Signal,
    SignalInstance,
    Slot,
)
from PySide6.QtWidgets import QApplication

import LinkToJMag.DataExtractor as ext
from JMagDatas.WorkCase import (
    JMagPrjFileInfo,
    StudyInfo,
    WorkCase,
    WorkStatus,
)
from LinkToJMag.JMagDataSet import JMagDataSet, SetData
from LinkToMatlab.ModelData import MatCnvDat
from Model.MdlJMagAnlPrjGen import MdlJMagAnlPrjGen
from Model.MdlMapDef import MdlMapDef
from Model.MdlParameter import MdlParameter
from Model.MdlWorkCaseGen import MdlWorkCaseGen
from Model.MdlWorkCaseStore import MdlWorkCaseStore
from View.GuiDialogs import SttDialog


class FilePath:
    __path: str

    def __init__(self, path: str = "") -> None:
        self.__path = path

    @property
    def Path(self) -> str:
        return self.__path

    @property
    def Name(self) -> str:
        return os.path.basename(self.__path)

    @property
    def Dir(self) -> str:
        return os.path.dirname(self.__path)


class ModelJMagMBD(QObject):
    _app: jd.Application
    __isLinked: bool
    _bPrjPath: FilePath
    _tgtStudy: jd.Study

    _mdlPrm: MdlParameter
    _mdlWCS: MdlWorkCaseStore
    _mdlWCG: MdlWorkCaseGen
    _mdlMgen: MdlMapDef
    _mdlGenJps: MdlJMagAnlPrjGen

    _listStdInfo: list[StudyInfo]

    _dirStore: str
    _nameMbdPrj: str
    _setStore: QSettings

    # ######################################
    onSwdLinkStatus = Signal(bool, bool)
    onSetOutPrjDir = Signal(Callable[[str], None])
    onChangeStudy = Signal(str)

    onPrjFileStatus = Signal(bool)  # プロジェクトファイルの状態
    onProcess = Signal(object)

    onShowMsg = Signal(SttDialog, str)

    def __init__(self, s: QSettings = None) -> None:
        super().__init__()
        self._dirStore: str = "D:/_CmnWk/_Devs/_MotorMBDs/_DataStore"
        self._app = None
        self._tgtStudy = None
        self.__isLinked = False
        self._bPrjPath = FilePath()
        self._listStdInfo = []
        self._listDataStore = []
        self._nameMbdPrj = "MotMBD"
        self._setStore = QSettings()
        self._mdlPrm = MdlParameter()
        self._mdlWCS = MdlWorkCaseStore()
        self._mdlWCG = MdlWorkCaseGen(self._mdlWCS)
        self._mdlMgen = MdlMapDef()
        self._mdlGenJps = MdlJMagAnlPrjGen(self._mdlWCS, self)

        def _updMaxIa(v: float) -> None:
            if self._mdlMgen.maxIa.text is None or self._mdlMgen.maxIa.text == "":
                self._mdlMgen.maxIa.setText(str(v))
            self._mdlWCG.maxIa.setText(str(v))

        self._mdlPrm.onMaxIaChanged.connect(lambda v: _updMaxIa(v))

        def _upTmpCoil(v: float) -> None:
            if self._mdlMgen.tdCoil.text is None or self._mdlMgen.tdCoil.text == "":
                self._mdlMgen.tdCoil.setText(str(v))

        self._mdlPrm.onTempCoilChanged.connect(lambda v: _upTmpCoil(v))

        if not os.path.isdir(self._dirStore):
            print("***** Invalid data store folder. {self._dirStore}")
            return

    # ######################################
    @Slot()
    def cnvJmagToMatlab(self) -> None:
        matObj = MatCnvDat()
        matObj.createModel(self._mdlWCS.dataList, self._mdlPrm, self._mdlMgen)
        pass

    @Slot()
    def extractData(
        self,
        onPrg: Optional[Callable[[int], None]] = None,
        onStop: Optional[Callable[[], bool]] = None,
    ) -> None:
        ext.DataExtractor.Extract(self._mdlWCS.dataList, self._listStdInfo, self, onPrg, onStop)

    @Slot(bool)
    def toChangeLinkStatus(self, tgt: bool) -> None:
        if tgt:
            self.linkApp(False)
        else:
            self.isLinked = False
            del self._app
            self._app = None

    @Slot(bool)
    def linkApp(self, isNew: bool = False) -> None:
        if self.isAppOK:
            self.onShowMsg.emit(SttDialog.Message, "Already linked to JMag-Designer.")
            return

        if isNew:
            self._app = jd.designer.CreateApplication()
        else:
            self._app = jd.designer.GetApplication()
        time.sleep(0.1)  # Wait for JMag to initialize
        self.isLinked = True

    @Slot()
    @property
    def isAppOK(self) -> bool:
        return self._app.IsValid() if self._app is not None else False

    def loadBasePrj(self) -> None:
        if not self.isAppOK:
            print("***** App link not connected.")
            self.isLinked = False
            return
        bPath = self.BasePrjPath.Path
        if os.path.isfile(bPath):
            self._app.Load(bPath)
        else:
            print(f"***** Invalid base project file: {bPath}")
        if not self.isAppOK:
            print("***** Invalid App")
        return

    def setTgtStudy(self, idx: int) -> None:
        if self._app is None or not self._app.IsValid():
            self.isLinked = False
            return
        if idx < 0 or idx >= self._app.NumStudies():
            return
        ts = self._app.GetStudy(idx)
        if ts is None or not ts.IsValid():
            print(f"***** Invalid Study. {ts}")
            return
        self.tgtStudy = ts
        return

    def chkLinkStatus(self, isMsgShow: bool = False) -> tuple[bool, str]:
        if self._app is None or not self._app.IsValid():
            if isMsgShow:
                self.onShowMsg.emit(SttDialog.Error, "No valid JMag-Designer.")
            return (False, self.BasePrjPath.Path)
        return (True, self.BasePrjPath.Path)

    def genAnlPrjFiles(
        self,
        tps: dict[str, list[list[WorkCase]]],
        tDir: str,
        fnUpd: SignalInstance[int] = None,
        stt: threading.Event | None = None,
    ) -> None:
        num = sum([sum([len(vv) for vv in v]) for v in tps.values()])
        if num == 0:
            print(f"***** No data to Generate all list. {num} / {len(self._mdlWCS.dataList)}")
            return
        tNum = sum([n for n in map(len, tps.values())])
        if len(tps) == 0:
            print("@@@@@@@@@@ No data to Generate all list.")
            return
        app = self._app
        bPath = self.BasePrjPath.Path
        fNam0, eNam = os.path.splitext(self.BasePrjPath.Name)

        nw = max(int(math.log10(tNum) + 1), 3)

        enDs = list(
            set([v.StudyInfo for v in self._mdlWCS.dataList if v.status >= WorkStatus.Defined])
        )
        self._listStdInfo.clear()
        self._listStdInfo.extend(sorted(enDs, key=lambda x: x.idx))
        ii = max(self._listStdInfo, key=lambda x: x.idx).idx + 1 if len(enDs) else 0
        # 解析jprojファイル作成
        nErr = 0

        app.ClearError()
        for k, v in tps.items():
            for i, vv in enumerate(v):
                if len(vv) == 0:
                    continue
                app.Load(bPath)
                app.SetCurrentStudy(0)
                tsName = app.GetCurrentStudy().GetName()
                # 解析プロジェクト名の設定
                niOff = 0
                if self._mdlPrm.isMultiSlice:  # 解析済と互換性を持たせるため
                    niOff = 10  # スライス数オフセット
                idn = str(ii + 1 + niOff).zfill(nw)  # 0埋め番号
                k = re.sub(r"\s+", "", k)
                if ">>>" not in k:
                    npNam = f"Mbd{idn}_{fNam0}_{k}.jproj"
                    nsNam = f"Mbd{idn} {tsName} {k}"
                else:
                    kk = k.split(">>>")
                    kks = kk[1].split(":")
                    if len(kks) == 1:
                        npNam = f"Mbd{idn}_{fNam0}_{kk[0]}_to_{kks[0]}{vv[-1].valACi[0]:.0f}A.jproj"
                        nsNam = f"Mbd{idn} {tsName} {kk[0]} to {kks[0]}:{vv[-1].valACi[0]:.1f}[A]"
                    else:
                        iav = kks[1].split(",")[i]
                        szIav = f"{float(iav):.0f}"
                        s0 = kk[0]
                        s1 = kks[0]
                        npNam = f"Mbd{idn}_{fNam0}_{s0}_to_{s1}{szIav}A.jproj"
                        nsNam = f"Mbd{idn} {tsName} {s0} to {s1}:{szIav}A"
                        # >>>>>>> FUKUTA 従来モデル用　互換
                        npNam = f"{re.sub(r'M000', rf'M{idn}', fNam0)}_to_{s1}{szIav}A.jproj"
                        nsNam = f"{re.sub(r'M000', rf'M{idn}', tsName)} to {s1}{szIav}A"
                        if self._mdlPrm.isMultiSlice:
                            npNam = f"{re.sub(r'M010', rf'M{idn}', fNam0)}_to_{s1}{szIav}A.jproj"
                            nsNam = f"{re.sub(r'M010', rf'M{idn}', tsName)} to {s1}{szIav}A"
                        # <<<<<<<<< FUKUTA 従来モデル用　互換

                tPath = os.path.join(tDir, npNam)
                ds: list[SetData] = []
                for twc in vv:
                    QApplication.processEvents()
                    if stt is not None and stt.is_set():
                        print("***** Cancel of genAnlPrjFiles.")
                        app.Load(bPath)
                        return
                    print(
                        f" Id:{twc.valDQi[0]:.1f}, Iq:{twc.valDQi[1]:.1f}"
                        f"   Ia:{twc.valACi[0]:.1f}, Fw:{twc.valACi[1]:.2f}"
                        f"    Skew:{len(twc.skewedDatas)}"
                    )
                    cds = SetData(twc.valDQi[0], twc.valDQi[1], 0.0)
                    cds.fPath = tPath
                    cds.sName = nsNam
                    ds.append(cds)
                    if not twc.isSlice:
                        tSds = twc.skewedDatas
                        print(f">>>>>>>>> Skew Num {len(tSds)}")
                        for th, swc in tSds.items():
                            cds2 = SetData(swc.valDQi[0], swc.valDQi[1], float(th))
                            cds2.fPath = tPath
                            cds2.sName = nsNam
                            ds.append(cds2)

                app.SaveAs(tPath)  # TODO: 既にファイルがあるか確認
                app.GetCurrentModel().DuplicateStudyName(tsName, nsNam, True)
                app.GetCurrentModel().DeleteStudy(tsName)
                ts = app.GetStudy(nsNam)
                tObj = JMagDataSet(ts)
                tObj.AddCase(ts, ds)
                QApplication.processEvents()

                app.Save()
                if app.HasError():
                    print(f"@@@@@@@@ JMag Has error : {app.GetLastMessage()}")
                    app.ClearError()
                    nErr += 1
                else:
                    sInfo = StudyInfo(nsNam, ts.GetUuid(), JMagPrjFileInfo(tPath, bPath), ii)
                    sInfo.prjInfo.isMultiSlice = ext.DataExtractor.isMultiSlice(ts)[1] > 1
                    self._listStdInfo.append(sInfo)
                    cid0 = 0
                    for _, twc in enumerate(vv):
                        twc.status = WorkStatus.Defined
                        twc.StudyInfo = sInfo
                        twc.caseNo = cid0
                        twc.grpIdx = ii
                        cid0 += 1
                        if not twc.isSlice:
                            tSds = twc.skewedDatas
                            print(f">>>>>>>>> Skew Num {len(tSds)}")
                            for _, swc in tSds.items():
                                swc.status = WorkStatus.Defined
                                swc.StudyInfo = sInfo
                                swc.caseNo = cid0
                                swc.grpIdx = ii
                                cid0 += 1

                if nErr > 10:
                    print("@@@@@@@@@@ Too many error. Stop.")
                    return

                if fnUpd is not None:
                    fnUpd.emit(len(vv))

                ii += 1

        app.Load(bPath)
        print(">>>>> End of genAnlPrjFile")

        app.Load(bPath)
        return

    def addAnalysisJob(
        self,
        fnUpd: SignalInstance[int] = None,
        stt: threading.Event | None = None,
    ) -> bool:
        app = self._app
        # 解析実行
        job: jd.Job = None
        flg = True
        fnUpd.emit(0)
        for i, p in enumerate(self._listStdInfo):
            if fnUpd is not None:
                fnUpd.emit(i)
            tgts = sorted(
                [w for w in self.wcList if w.status == WorkStatus.Defined and w.StudyInfo == p],
                key=lambda x: x.caseNo,
            )
            n0 = len(tgts)
            if n0 == 0:
                print("***** No defined WorkCase to set Analysis job :{p.name}")
                fnUpd.emit(0)
                continue
            QApplication.processEvents()
            if stt is not None and stt.is_set():
                print(f"***** Cancel of set Analysis job. :{p.name}")
                break
            pPath = p.prjInfo.path
            app.Load(pPath)
            tjs = app.GetStudy(p.name)
            if tjs is None or not tjs.IsValid():
                print(f"***** Invalid Study. {p.name} at {pPath}")
                flg = False
                continue
            job = tjs.CreateJob()
            print(f">>> {i}, Exec. Study:{p.name}\n\tpath:{pPath}")

            job.SetValue("Title", f"{p.name}")
            job.SetValue("Queued", True)
            job.SetValue("DeleteScratch", True)
            job.SetValue("PreProcessOnWrite", True)
            job.Submit(True)

            t0 = time.perf_counter()
            while time.perf_counter() - t0 < 5:
                QApplication.processEvents()
                time.sleep(0.01)

        return flg

    def getStudyLists(self) -> dict[int, str]:
        return {i: self._app.GetStudy(i).GetName() for i in range(self._app.NumStudies())}

    def getStudyNames(self) -> list[tuple[int, str]]:
        if self._app is None:
            self.isLinked = False
            return []
        elif not self._app.IsValid():
            self._app = None
            self.isLinked = False
            return []

        nS = self._app.NumStudies()
        return [(i, self._app.GetStudy(i).GetName()) for i in range(nS)]

    def saveToIni(self, s: QSettings, isFrcDatOut: bool = False) -> None:
        if s is None:
            return
        if self._mdlPrm is not None:
            self._mdlPrm.saveSettings(s)

        s.beginGroup("MbdJMagModel")
        s.setValue("BasePrjPath", self.BasePrjPath.Path)
        s.beginGroup("LinkFileInfo")
        s.remove("")
        s.endGroup()
        s.beginWriteArray("LinkFileInfo")
        for i, si in enumerate(self._listStdInfo):
            s.setArrayIndex(i)
            si.saveSettings(s)
        s.endArray()
        s.endGroup()

        if self._mdlWCG is not None:
            self._mdlWCG.saveSettings(s)
        if self._mdlGenJps is not None:
            self._mdlGenJps.saveSettings(s)
        if self._mdlMgen is not None:
            self._mdlMgen.saveSettings(s)
        if self._mdlWCS is not None:
            self._mdlWCS.saveSettings(s, isFrcDatOut)

    def loadFromIni(self, s: QSettings) -> None:
        if s is None:
            return

        s.beginGroup("MbdJMagModel")
        self._bPrjPath = FilePath(s.value("BasePrjPath", "", str))
        self._listStdInfo = []
        sz = s.beginReadArray("LinkFileInfo")
        for i in range(sz):
            s.setArrayIndex(i)
            si = StudyInfo()
            si.loadSettings(s)
            self._listStdInfo.append(si)
        s.endArray()
        s.endGroup()

        if self._mdlPrm is not None:
            self._mdlPrm.loadSettings(s)

        if self._mdlWCG is not None:
            self._mdlWCG.loadSettings(s)
        if self._mdlGenJps is not None:
            self._mdlGenJps.loadSettings(s)
        if self._mdlMgen is not None:
            self._mdlMgen.loadSettings(s)
        if self._mdlWCS is not None:
            self._mdlWCS.loadSettings(s)
        pass

    # region Properties

    @property
    def mdlWCG(self) -> MdlWorkCaseGen:
        return self._mdlWCG

    @property
    def mdlGenJps(self) -> MdlJMagAnlPrjGen:
        return self._mdlGenJps

    @property
    def tgtStudy(self) -> jd.Study:
        return self._tgtStudy

    @property
    def wcList(self) -> list[WorkCase]:
        return self._mdlWCS.dataList

    @tgtStudy.setter
    def tgtStudy(self, ts: jd.Study) -> None:
        if self._tgtStudy != ts:
            self._tgtStudy = ts
            if self._tgtStudy is None or not self._tgtStudy.IsValid():
                sn = "inValid"
            else:
                sn = ts.GetName()
                pm = self._mdlPrm
                vs = ext.DataExtractor.isMultiSlice(ts)
                if vs[1] > 1:
                    pm.isMultiSlice = True
                    pm.isSkewed = True
                    pm.nDivSkew = vs[1]
                    pm.thSkew = vs[2]
                else:
                    pm.isMultiSlice = False

            self.onChangeStudy.emit(sn)

    @property
    def isLinked(self) -> bool:
        return self.__isLinked

    @isLinked.setter
    def isLinked(self, stt: bool) -> None:
        if self.__isLinked != stt:
            s2 = False
            if self.__isLinked and self._app is not None and not self._app.IsValid():
                s2 = True
            self.__isLinked = stt
            if stt:
                print(f">>>> Link to JMag-Designer: {stt}")
            self.onSwdLinkStatus.emit(stt, s2)

    @property
    def BasePrjPath(self) -> FilePath:
        return self._bPrjPath

    @BasePrjPath.setter
    def BasePrjPath(self, path: FilePath) -> None:
        if path is not None and os.path.isfile(path.Path):
            if self._bPrjPath.Path != path.Path:
                self._bPrjPath = path
            return
        else:
            msg = f"Invalid JMag Project File and ignored:\n{path.Name}"
            self.onShowMsg.emit(SttDialog.Warning, msg)
            return

    @property
    def AppPrjPath(self) -> FilePath:
        if self.isAppOK:
            return FilePath(self._app.GetProjectPath())
        else:
            return FilePath()

    # endregion
