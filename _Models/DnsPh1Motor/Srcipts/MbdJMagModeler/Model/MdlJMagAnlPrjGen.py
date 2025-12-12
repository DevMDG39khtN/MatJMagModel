from __future__ import annotations

import json
import threading
from enum import IntEnum

import numpy as np
from PySide6.QtCore import QObject, QSettings, Qt, Signal, SignalInstance, Slot
from PySide6.QtWidgets import QSizePolicy

from JMagDatas.WorkCase import WorkCase, WorkStatus
from Model.MdlWorkCaseGen import MdlWorkCaseGen

QSP = QSizePolicy.Policy
QAF = Qt.AlignmentFlag
uQRole = Qt.ItemDataRole


class DivStatus(IntEnum):
    IdIqNum = 0
    IaRmsNum = 1
    IaRmsVals = 2


class MdlJMagAnlPrjGen(QObject):
    _isDivPrj: bool
    _sttDivPrj: DivStatus
    _numDivPrj: int
    _lstDivPrj: list[int]
    _isExSplit: bool
    _isFwSplit: bool
    _isDoJob: bool

    # region Methods
    ########################################################
    def __init__(
        self,
        s: QSettings = None,
        p: QObject | None = None,
    ) -> None:
        super().__init__(p)

        self._isDivPrj = False
        self._sttDivPrj = DivStatus.IdIqNum
        self._numDivPrj = 0
        self._lstDivPrj = []
        self._isExSplit = True
        self._isFwSplit = True

        self._isDoJob = False

        return

    ########################################################
    def _genAnlPrjListIdIqNum(
        self,
        tgt0: list[WorkCase],
        fnUpd: SignalInstance[int] = None,
        stt: threading.Event | None = None,
    ) -> dict[str, list[list[WorkCase]]]:
        """分割プロジェクトのリストを生成"""
        # 分割プロジェクトのリストを生成
        eps = 1.0e-6

        n0 = len(tgt0)
        if n0 == 0:
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        tgt = sorted(
            [v for v in tgt0 if v.status == WorkStatus.Created],
            key=lambda v: (-v.valDQi[0], v.valDQi[1]),
        )

        n1 = len(tgt)
        if n1 == 0:
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}
        if stt is not None and stt.is_set():
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        tgtNA = np.array(tgt)

        if fnUpd is not None:
            fnUpd.emit(2)

        dNum = self.numDivPrj
        if self.isExSplit:
            flgInArea = np.array([not v.isExtArea for v in tgt])
            if self.isFwSplit:
                kns = ["Base", "ExtWkn", "ExtRng"]
                flgFwArea = np.array([v.valDQi[0] < eps for v in tgt])
                vs: list[list[WorkCase]] = [
                    np.concatenate(
                        [
                            tgtNA[flgInArea & flgFwArea],
                            tgtNA[flgInArea & ~flgFwArea],
                        ]
                    ).tolist(),
                    tgtNA[~flgInArea & flgFwArea].tolist(),
                    tgtNA[~flgInArea & ~flgFwArea].tolist(),
                ]
            else:
                kns = ["Base", "Ext"]
                vs: list[list[WorkCase]] = [
                    tgtNA[flgInArea].tolist(),
                    tgtNA[~flgInArea].tolist(),
                ]
        else:
            if self.isFwSplit:
                kns = ["Wkn", "Str"]
                flgFwArea = np.array([v.valDQi[0] < eps for v in tgt])
                vs: list[list[WorkCase]] = [
                    tgtNA[flgFwArea].tolist(),
                    tgtNA[~flgFwArea].tolist(),
                ]
            else:
                kns = [f"Div{dNum}"]
                vs = [tgt]

        if fnUpd is not None:
            fnUpd.emit(2)

        sDiv = {
            k: [v[i : i + dNum] for i in range(0, len(v), dNum)]
            for k, v in zip(kns, vs)
            if len(v) > 0
        }
        nDiv = [len(v) for v in sDiv.values()]
        num = sum([sum([len(vv) for vv in v]) for v in sDiv.values()])
        if num != len(tgt):
            print("分割プロジェクトのリスト生成エラー", num, len(tgt), nDiv)

        if fnUpd is not None:
            fnUpd.emit(2)

        return sDiv

    ########################################################
    def _genAnlPrjListIaRmsNum(
        self,
        tgt0: list[WorkCase],
        maxIa: float,
        fnUpd: SignalInstance[int] = None,
        stt: threading.Event | None = None,
    ) -> dict[str, list[list[WorkCase]]]:
        """分割プロジェクトのリストを生成"""
        eps = 1.0e-6

        n0 = len(tgt0)
        if n0 == 0:
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        tgt = sorted(
            [v for v in tgt0 if v.status == WorkStatus.Created],
            key=lambda v: (
                v.valACi[0],
                v.valACi[1] if v.valACi[1] > -eps else 360 - v.valACi[1],
            ),
        )

        n1 = len(tgt)
        if n1 == 0:
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        if stt is not None and stt.is_set():
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        if fnUpd is not None:
            fnUpd.emit(2)

        tgtNA = np.array(tgt)

        dNum = self.numDivPrj
        if self.isExSplit:
            if maxIa < eps:
                flgInArea = np.array([not v.isExtArea for v in tgt])
            else:
                flgInArea = np.array([v.valACi[0] < maxIa * 1.1 for v in tgt])

            if self.isFwSplit:
                kns = ["Base", "ExtWkn", "ExtRng"]
                flgFwArea = np.array([v.valDQi[0] < eps for v in tgt])
                if maxIa < eps:
                    vs: list[list[WorkCase]] = [
                        np.concatenate(
                            [
                                tgtNA[flgInArea & flgFwArea],
                                tgtNA[flgInArea & ~flgFwArea],
                            ]
                        ).tolist(),
                        tgtNA[~flgInArea & flgFwArea].tolist(),
                        tgtNA[~flgInArea & ~flgFwArea].tolist(),
                    ]
                else:
                    vs: list[list[WorkCase]] = [
                        tgtNA[flgInArea & flgFwArea].tolist(),
                        tgtNA[~flgInArea & flgFwArea].tolist(),
                        np.concatenate(
                            [
                                tgtNA[flgInArea & ~flgFwArea],
                                tgtNA[~flgInArea & ~flgFwArea],
                            ]
                        ).tolist(),
                    ]
            else:
                kns = ["Base", "Ext"]
                vs: list[list[WorkCase]] = [
                    tgtNA[flgInArea].tolist(),
                    tgtNA[~flgInArea].tolist(),
                ]
        else:
            if self.isFwSplit:
                kns = ["Wkn", "Str"]
                flgFwArea = np.array([v.valDQi[0] < eps for v in tgt])
                vs: list[list[WorkCase]] = [
                    tgtNA[flgFwArea].tolist(),
                    tgtNA[~flgFwArea].tolist(),
                ]
            else:
                kns = [f"Div{dNum}"]
                vs = [tgt]

        if fnUpd is not None:
            fnUpd.emit(2)

        sDiv = {
            f"{k}>>>Ia": [v[i : i + dNum] for i in range(0, len(v), dNum)]
            for k, v in zip(kns, vs)
            if len(v) > 0
        }

        nDiv = [len(v) for v in sDiv.values()]
        num = sum([sum([len(vv) for vv in v]) for v in sDiv.values()])
        if num != len(tgt):
            print("分割プロジェクトのリスト生成エラー", num, len(tgt), nDiv)

        if fnUpd is not None:
            fnUpd.emit(2)

        return sDiv

    ########################################################
    def _genAnlPrjListIaRmsVals(
        self,
        tgt0: list[WorkCase],
        maxIa: float,
        fnUpd: SignalInstance[int] = None,
        stt: threading.Event | None = None,
    ) -> dict[str, list[list[WorkCase]]]:
        """分割プロジェクトのリストを生成"""
        # 分割プロジェクトのリストを生成
        eps = 1.0e-6

        n0 = len(tgt0)
        if n0 == 0:
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        tgt = sorted(
            [v for v in tgt0 if v.status == WorkStatus.Created],
            key=lambda v: (
                v.valACi[0],
                v.valACi[1] if v.valACi[1] > -eps else 360 - v.valACi[1],
            ),
        )

        n1 = len(tgt)
        if n1 == 0:
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        if stt is not None and stt.is_set():
            if fnUpd is not None:
                fnUpd.emit(6)
            return {}

        if fnUpd is not None:
            fnUpd.emit(2)

        ias = np.array([v.valACi[0] for v in tgt])
        iaList = np.array(
            [-2 * eps] + [float(v) for v in self.lstDivPrj] + [np.inf],
            dtype=float,
        )
        ss = np.searchsorted(iaList, ias, side="right")

        tgtNA = np.array(tgt)

        if self.isExSplit:
            if maxIa < eps:
                flgInArea = np.array([not v.isExtArea for v in tgt])
            else:
                flgInArea = np.array([v.valACi[0] < maxIa * 1.1 for v in tgt])
            if self.isFwSplit:
                kns = ["Base", "ExtWkn", "ExtRng"]
                flgFwArea = np.array([v.valDQi[0] < eps for v in tgt])
                if maxIa < eps:
                    ids = [
                        flgInArea,
                        ~flgInArea & flgFwArea,
                        ~flgInArea & ~flgFwArea,
                    ]
                else:
                    ids = [
                        flgInArea & flgFwArea,
                        ~flgInArea & flgFwArea,
                        ~flgFwArea,
                    ]
            else:
                kns = ["Base", "Ext"]
                ids = [flgInArea, ~flgInArea]
        else:
            if self.isFwSplit:
                kns = ["Wkn", "Str"]
                flgFwArea = np.array([v.valDQi[0] < eps for v in tgt])
                ids = [flgFwArea, ~flgFwArea]
            else:
                kns = ["Div"]
                ids = [np.arange(len(tgtNA))]

        if fnUpd is not None:
            fnUpd.emit(2)

        kn = ",".join(str(v) for v in iaList[2:])

        sDiv = {
            f"{k}>>>Ia:{kn}": [
                lst
                for i in range(len(iaList) - 1)
                if len(lst := tgtNA[idv & (ss == i + 1)].tolist()) > 0
            ]
            for k, idv in zip(kns, ids)
            if len(idv) > 0
        }

        nDiv = [len(v) for v in sDiv.values()]
        num = sum([sum([len(vv) for vv in v]) for v in sDiv.values()])
        if num != len(tgt):
            print("分割プロジェクトのリスト生成エラー", num, len(tgt), nDiv)

        if fnUpd is not None:
            fnUpd.emit(2)

        return sDiv

    ########################################################
    def genAnlPrjList(
        self,
        tgt: list[WorkCase],
        maxIa: float = -1.0,
        fnUpd: SignalInstance[int] | None = None,
        stt: threading.Event | None = None,
    ) -> dict[str, list[list[WorkCase]]]:
        if self._isDivPrj:
            if self._sttDivPrj == DivStatus.IdIqNum:
                return self._genAnlPrjListIdIqNum(tgt, fnUpd, stt)
            elif self._sttDivPrj == DivStatus.IaRmsNum:
                return self._genAnlPrjListIaRmsNum(tgt, maxIa, fnUpd, stt)
            elif self._sttDivPrj == DivStatus.IaRmsVals:
                return self._genAnlPrjListIaRmsVals(tgt, maxIa, fnUpd, stt)

        rv = {"All": [tgt]}
        if fnUpd is not None:
            fnUpd.emit(len(tgt))
        return rv

    # endregion

    # region Serialize/Deserialize
    ########################################################
    def toDict(self) -> dict:
        """MdlWorkCaseGen オブジェクトを辞書形式に変換"""
        return {
            "isDivPrj": self._isDivPrj,
            "sttDivPrj": int(self._sttDivPrj),
            "numDivPrj": self._numDivPrj,
            "lstDivPrj": self._lstDivPrj,
            "isExSplit": self._isExSplit,
            "isFwSplit": self._isFwSplit,
            "isDoJob": self._isDoJob,
        }

    ########################################################
    @staticmethod
    def fromDict(
        data: dict,
        p: QObject,
        tgt: MdlJMagAnlPrjGen,
    ) -> MdlWorkCaseGen:
        if tgt is not None:
            obj = tgt
        else:
            obj = MdlJMagAnlPrjGen(p=p)

        obj.isDivPrj = data["isDivPrj"]
        obj.sttDivPrj = DivStatus(data["sttDivPrj"])
        obj.numDivPrj = data["numDivPrj"]
        obj.lstDivPrj = data["lstDivPrj"]
        obj.isExSplit = data["isExSplit"]
        obj.isFwSplit = data["isFwSplit"]
        obj.isDoJob = data.get("isDoJob", False)

        return obj

    ########################################################
    def importJson(self, txt: str) -> MdlJMagAnlPrjGen | None:
        dic = json.loads(txt)
        if dic is not None:
            return self.fromDict(dic, self.parent(), self)
        return None

    ########################################################
    def exportJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False, indent=2)

    ########################################################
    def loadSettings(self, s: QSettings = None) -> None:
        if s is None:
            return
        s.beginGroup("JMagPrjGen")
        dTxt = s.value("DataSet", "", str)
        if len(dTxt) > 0:
            self.importJson(dTxt)
        s.endGroup()

    ########################################################
    def saveSettings(self, s: QSettings = None) -> None:
        if s is None:
            return

        s.beginGroup("JMagPrjGen")
        s.setValue("DataSet", self.exportJson())
        s.endGroup()

    ########################################################
    def loadToJsonFile(self, fpath: str) -> None:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data is not None:
                self.fromDict(data, self.parent(), self)

    ########################################################
    def saveToJsonFile(self, fpath: str) -> None:
        """辞書形式のデータを JSON ファイルに保存"""
        with open(fpath, "w", encoding="utf-8") as f:
            # json.dump(datas, f, ensure_ascii=False, indent=2)
            json.dump(self.toDict(), f, ensure_ascii=False, indent=2)

    # endregion

    # region Signal
    ########################################################
    onChangedIsDivPrj = Signal(bool)
    onChangedDivStt = Signal(int)
    onChangedNumDiv = Signal(int)
    onChangedDivList = Signal(list)
    onChangedIsExtSplit = Signal(bool)
    onChangedIsFwSplit = Signal(bool)
    onChangedIsDoJob = Signal(bool)

    # endregion

    # region Slot
    ########################################################
    @Slot(bool)
    def setIsDivPrj(self, stt: bool) -> None:
        self.isDivPrj = stt

    @Slot(bool)
    def setIsExtSplitPrj(self, stt: bool) -> None:
        self.isExSplit = stt

    @Slot(bool)
    def setIsFwSplitPrj(self, stt: bool) -> None:
        self.isFwSplit = stt

    @Slot(bool)
    def setIsDoJob(self, stt: bool) -> None:
        self.isDoJob = stt

    ########################################################
    @Slot(int)
    def toSetDivStt(self, stt: int):
        self.sttDivPrj = DivStatus(stt)
        return

    ########################################################
    @Slot(int)
    def toSetNumDiv(self, num: int):
        self.numDivPrj = num
        return

    ########################################################
    @Slot(list)
    def toSetDivList(self, lst: list[int]):
        self.lstDivPrj = lst
        return

    # endregion

    # region Properties
    ########################################################
    @property
    def sttDivPrj(self) -> DivStatus:
        return self._sttDivPrj

    @sttDivPrj.setter
    def sttDivPrj(self, stt: DivStatus) -> None:
        if self._sttDivPrj == stt:
            return
        self._sttDivPrj = stt
        self.onChangedDivStt.emit(int(stt))

    ########################################################
    @property
    def numDivPrj(self) -> int:
        return self._numDivPrj

    @numDivPrj.setter
    def numDivPrj(self, num: int) -> None:
        if self._numDivPrj == num:
            return
        self._numDivPrj = num
        self.onChangedNumDiv.emit(self._numDivPrj)

    ########################################################
    @property
    def lstDivPrj(self) -> list[int]:
        return self._lstDivPrj

    @lstDivPrj.setter
    def lstDivPrj(self, lst: list[int]) -> None:
        if self._lstDivPrj == lst:
            return
        self._lstDivPrj.clear()
        self._lstDivPrj.extend(lst)
        self.onChangedDivList.emit(self._lstDivPrj)

    ########################################################
    @property
    def DivPrjStt(self) -> DivStatus:
        return self._sttDivPrj

    @DivPrjStt.setter
    def DivPrjStt(self, stt: DivStatus) -> None:
        if self._sttDivPrj == stt:
            return
        self._sttDivPrj = stt
        # self._mdl._isDivPrj = stt
        self.onChangedIsDivPrj.emit(stt == DivStatus.IdIqNum)

    ########################################################
    @property
    def isDivPrj(self) -> bool:
        return self._isDivPrj

    @isDivPrj.setter
    def isDivPrj(self, stt: bool) -> None:
        if self._isDivPrj == stt:
            return
        self._isDivPrj = stt
        self.onChangedIsDivPrj.emit(stt)

    ########################################################
    @property
    def isExSplit(self) -> bool:
        return self._isExSplit

    @isExSplit.setter
    def isExSplit(self, stt: bool) -> None:
        if self._isExSplit == stt:
            return
        self._isExSplit = stt
        self.onChangedIsExtSplit.emit(stt)

    ########################################################
    @property
    def isFwSplit(self) -> bool:
        return self._isFwSplit

    @isFwSplit.setter
    def isFwSplit(self, stt: bool) -> None:
        if self._isFwSplit == stt:
            return
        self._isFwSplit = stt
        self.onChangedIsFwSplit.emit(stt)

    ########################################################
    @property
    def isDoJob(self) -> bool:
        return self._isDoJob

    @isDoJob.setter
    def isDoJob(self, stt: bool) -> None:
        if self._isDoJob == stt:
            return
        self._isDoJob = stt
        self.onChangedIsDoJob.emit(stt)

    # endregion
