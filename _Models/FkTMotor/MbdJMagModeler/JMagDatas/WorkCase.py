from __future__ import annotations

import json
import math
from enum import Flag, IntEnum, auto
from math import atan2, cos, pi, sin, sqrt
from typing import Any

import numpy as np
from PySide6.QtCore import QSettings

from JMagDatas.AxesContents import Axis2D, AxisAC, AxisDQ, MotAxes
from JMagDatas.JmagData import ExtractedMagDatas
from LinkToJMag.JMagFileInfo import JMagPrjFileInfo


class LnkPrjStatus(Flag):
    """JMAG プロジェクトファイルの状態"""

    Normal = 0
    NoBaseFile = auto()
    NoBaseDir = auto()
    NoBasePath = NoBaseFile | NoBaseDir
    NoPrjFile = auto()
    NoPrjDir = auto()
    NoPrjPath = NoPrjFile | NoPrjDir
    NoStudy = auto()


class WorkStatus(IntEnum):
    NaN = -1
    Created = auto()
    Defined = auto()
    InComplete = auto()
    Analyzed = auto()
    Extracted = auto()


# @dataclass
class StudyInfo:
    idx: int
    name: str
    uuid: str
    prjInfo: JMagPrjFileInfo | None

    def __init__(
        self,
        name: str = "",
        uuid: str = "",
        prjInfo: JMagPrjFileInfo | None = None,
        idx: int = -1,
    ) -> None:
        self.name = name
        self.uuid = uuid
        self.prjInfo = prjInfo
        self.idx = idx

    def saveSettings(self, s: QSettings | None) -> None:
        """StudyInfoオブジェクトをQSettingsに保存"""
        if s is not None:
            s.beginGroup("StudyInfo")
            s.setValue("idx", self.idx)
            s.setValue("name", self.name)
            s.setValue("uuid", self.uuid)
            if self.prjInfo:
                self.prjInfo.saveSettings(s)
            s.endGroup()

    def loadSettings(self, s: QSettings | None) -> None:
        """QSettingsからStudyInfoオブジェクトを読み込み"""
        if s is None:
            return
        s.beginGroup("StudyInfo")
        self.idx = int(str(s.value("idx", -1, int)))
        self.name = str(s.value("name", ""))
        self.uuid = str(s.value("uuid", ""))
        self.prjInfo = JMagPrjFileInfo()
        self.prjInfo.loadSettings(s)
        s.endGroup()

        # if "JMagPrjFileInfo" in s.childGroups():
        #     self.prjInfo = JMagPrjFileInfo()
        #     self.prjInfo.loadSettings(s)
        # else:
        #     self.prjInfo = None

    def toDict(self) -> dict[str, Any]:
        """StudyInfoオブジェクトを辞書形式に変換"""
        return {
            "idx": self.idx,
            "name": self.name,
            "uuid": self.uuid,
            "prjInfo": self.prjInfo.toDict() if self.prjInfo else None,
        }

    @staticmethod
    def fromDict(data: dict[str, str], tgt: StudyInfo | None = None) -> StudyInfo:
        """辞書形式のデータからStudyInfoオブジェクトを生成"""
        if tgt is None:
            tgt = StudyInfo()
        tgt.idx = int(data.get("idx", -1))
        tgt.name = data.get("name", "")
        tgt.uuid = data.get("uuid", "")
        d0: str | dict = data.get("prjInfo", {})
        if d0 and len(d0) > 0 and isinstance(d0, dict):
            tgt.prjInfo = JMagPrjFileInfo.fromDict(d0)
        return tgt

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StudyInfo):
            return False
        return (
            self.name == other.name
            # and self.uuid == other.uuid
            and (self.prjInfo.path if self.prjInfo else "")
            == (other.prjInfo.path if other.prjInfo else "")
        )

    def __hash__(self):
        p = self.prjInfo.path if self.prjInfo else ""
        return hash((self.name, p))


class WorkCase:
    """JMAG 各ケースデータラッパ"""

    prmNames: dict[MotAxes, tuple[str, str]] = {
        MotAxes.DQ: ("Id", "Iq"),
        MotAxes.AC: ("IaReq", "FwReq"),
    }
    skpNames: tuple[str, str] = ("ThMOff", "FwOff")

    datNames0 = [
        "Torque",
        "LineCurrent",
        "FEMCoilFlux",
        "TerminalVoltage",
        "VoltageDifference",
        "FEMCoilInductance",
    ]
    irDatNames0 = [
        "IronLoss_IronLoss",
        "HysteresisLoss_IronLoss",
        "JouleLoss_IronLoss",
    ]

    datIDNames = [
        "トルク",
        "回路の電流",
        "コイルの鎖交磁束",
        "回路の電圧",
        "電位差",
        "FEMコイルのインダクタンス",
    ]
    irDatIDNames = [
        "鉄損(鉄損条件)",
        "ヒステリシス損失(鉄損条件)",
        "ジュール損失(鉄損条件)",
    ]

    ddDnKeyToID = {k: v for k, v in zip(datIDNames, datNames0)}
    dlDnKeyToID = {k: v for k, v in zip(irDatIDNames, irDatNames0)}

    _mode: MotAxes
    _status: WorkStatus
    _vals: dict[MotAxes, dict[Axis2D, float]]  # 電流条件値
    _data: ExtractedMagDatas  # 解析結果
    _cIdx: int  # Case Index
    _gIdx: int  # Group Index StudyInfoに定義すべき
    _lnkInfo: StudyInfo | None
    _isExtArea: bool  # 電流拡張領域
    _idx: int  # WorkCase Index
    _pfStatus: LnkPrjStatus  # プロジェクトファイルの状態
    # >>>>>> FUKUTA 向け Skew 設定 #########
    _thSkew: float  # Skew Angle
    _skewedDatas: dict[float, WorkCase]
    _isSlice: bool  # スライス解析かどうか
    # <<<<< FUKUTA 向け Skew 設定 ##########

    def __init__(
        self,
        val: tuple[float, float],
        mode: MotAxes = MotAxes.DQ,
        stt: WorkStatus = WorkStatus.Created,
        lnks: tuple[int, StudyInfo] | None = None,
        # ケース番号, Study名
        gIdx: int = -1,
        isExA: bool = False,
        idx: int = -1,
        # >>>>>> FUKUTA 向け Skew 設定 #########
        thOff: float = 0.0,
        # Skew Angle
        thSkew: float = 0.0,
        nDivSkew: int = 0,
        isSlice: bool = False,
        # <<<<< FUKUTA 向け Skew 設定 ##########
    ) -> None:
        self._mode = mode  # 電流軸
        self._status = stt  # 解析状態
        self._data = ExtractedMagDatas()  # 解析結果
        # >>>>>> Skew 設定 #########
        self._thSkew = thOff
        self._skewedDatas = {}
        self._isSlice = isSlice  # スライス解析かどうか
        # <<<<< Skew 設定 ##########

        # 定義モードによりデータ変換
        if mode == MotAxes.DQ:
            vals = (val, self.CnvDQToAC(val))
        else:
            vals = (self.CnvACToDQ(val), val)
        self._vals = {  # 設定解析電流値 Id, Iq, Ia, Fw の順
            m: {t: v for t, v in zip(Axis2D, vs)} for m, vs in zip(MotAxes, vals)
        }

        self._gIdx = gIdx
        if lnks is None:
            lnks = (-1, StudyInfo("", "", None))
        self._cIdx = lnks[0]
        self._lnkInfo = lnks[1]

        self._isExtArea = isExA

        self._idx = idx

        self._pfStatus = LnkPrjStatus.Normal

        if math.isclose(thSkew, 0.0, abs_tol=1e-3) or nDivSkew <= 1:
            return

        vsr = thSkew / 2
        for th in np.linspace(vsr, -vsr, nDivSkew):
            self._skewedDatas[th] = WorkCase(
                val=val,
                mode=mode,
                stt=stt,
                lnks=lnks,
                gIdx=gIdx,
                isExA=isExA,
                idx=idx,
                thOff=th,
            )
        return

    def ChangeSkewStatus(self, stt: tuple[int, float, bool]) -> None:
        isSl = stt[2]
        nSk = stt[0]
        self._isSlice = isSl
        if nSk > 0:
            self._skewedDatas.clear()
            skv = stt[1] / 2
            if not math.isclose(skv, 0.0, abs_tol=1e-3):
                return
            for th in np.linspace(skv, -skv, nSk):
                self._skewedDatas[th] = WorkCase(
                    val=self.val,
                    mode=self.mode,
                    stt=self.status,
                    lnks=(self._cIdx, self._lnkInfo),
                    gIdx=self._gIdx,
                    isExA=self._isExtArea,
                    idx=self._idx,
                    thOff=th,
                )
        return

    def RemoveCase(self, w: WorkCase) -> int:
        return 0

    def isSameEnv(self, sn: str, pif: JMagPrjFileInfo) -> bool:
        p0 = self._lnkInfo.prjInfo.path if (self._lnkInfo and self._lnkInfo.prjInfo) else ""
        p1 = pif.path if pif else ""
        n0 = self._lnkInfo.name if self._lnkInfo else ""
        return p0 == p1 and n0 == sn

    def _setVals(self, val: tuple[float, float], mode: MotAxes | None = None) -> None:
        """電流値を設定"""
        if mode is None:
            mode = self._mode
        # 定義モードによりデータ変換
        if mode == MotAxes.DQ:
            vals = (val, self.CnvDQToAC(val))
        else:
            vals = (self.CnvACToDQ(val), val)
        self._vals = {  # 設定解析電流値 Id, Iq, Ia, Fw の順
            m: {t: v for t, v in zip(Axis2D, vs)} for m, vs in zip(MotAxes, vals)
        }

    # region Properties

    @property
    def data(self) -> ExtractedMagDatas:
        return self._data

    @property
    def mode(self) -> MotAxes:
        return self._mode

    @property
    def status(self) -> WorkStatus:
        return self._status

    @status.setter
    def status(self, stt: WorkStatus) -> None:
        self._status = stt

    @property
    def prmVals(self) -> tuple[float, float, float]:
        v = self.valDQi if self._mode == MotAxes.DQ else self.valACi
        vs = v + (self._thSkew,)
        return vs

    @property
    def val(self) -> tuple[float, float]:
        return self.valDQi if self._mode == MotAxes.DQ else self.valACi

    @property
    def vals(self) -> tuple[tuple[float, ...], ...]:
        # return [list(v.values()) for v in self._vals.values()]
        return tuple(tuple([vv for vv in v.values()]) for v in self._vals.values())

    @property
    def valDQ(self) -> dict[AxisDQ, float]:
        return {m: v for m, v in zip(AxisDQ, self._vals[MotAxes.DQ])}

    @property
    def valAC(self) -> dict[AxisAC, float]:
        return {m: v for m, v in zip(AxisAC, self._vals[MotAxes.AC])}

    @property
    def valDQi(self) -> tuple[float, float]:
        return (
            self._vals[MotAxes.DQ][Axis2D.CX],
            self._vals[MotAxes.DQ][Axis2D.RY],
        )

    @valDQi.setter
    def valDQi(self, vs: tuple[float, float]) -> None:
        vv = self.CnvDQToAC(vs)
        for m in Axis2D:
            self._vals[MotAxes.DQ][m] = vs[int(m)]
            self._vals[MotAxes.AC][m] = vv[int(m)]

    @property
    def valACi(self) -> tuple[float, float]:
        return (
            self._vals[MotAxes.AC][Axis2D.CX],
            self._vals[MotAxes.AC][Axis2D.RY],
        )

    @valACi.setter
    def valACi(self, vs: tuple[float, float]) -> None:
        vv = self.CnvACToDQ(vs)
        for m in Axis2D:
            self._vals[MotAxes.DQ][m] = vv[int(m)]
            self._vals[MotAxes.AC][m] = vs[int(m)]

    @property
    def caseNo(self) -> int:
        return self._cIdx

    @caseNo.setter
    def caseNo(self, cNo: int) -> None:
        self._cIdx = cNo
        return

    @property
    def studyName(self) -> str:
        return self._lnkInfo.name if self._lnkInfo else ""

    @studyName.setter
    def studyName(self, nm: str) -> None:
        if not self._lnkInfo:
            self._lnkInfo = StudyInfo(nm, "", None)
        else:
            self._lnkInfo.name = nm
        return

    @property
    def prjInfo(self) -> JMagPrjFileInfo | None:
        return self._lnkInfo.prjInfo if self._lnkInfo else None

    @prjInfo.setter
    def prjInfo(self, lnk: JMagPrjFileInfo | None) -> None:
        if not self._lnkInfo:
            self._lnkInfo = StudyInfo("", "", lnk)
        else:
            self._lnkInfo.prjInfo = lnk
        return

    @property
    def StudyInfo(self) -> StudyInfo | None:
        return self._lnkInfo

    @StudyInfo.setter
    def StudyInfo(self, si: StudyInfo) -> None:
        self._lnkInfo = si

    @property
    def grpIdx(self) -> int:
        return self._gIdx

    @grpIdx.setter
    def grpIdx(self, gIdx: int) -> None:
        self._gIdx = gIdx

    @property
    def caseInfo(self) -> str:
        return (
            f"{self._cIdx:04} @ {self._lnkInfo.name} "
            if self._lnkInfo
            else f"{self._cIdx:04} @ No Link"
        )

    @property
    def isExtArea(self) -> bool:
        return self._isExtArea

    @property
    def index(self) -> int:
        """WorkCase Index"""
        return self._idx

    @index.setter
    def index(self, idx: int) -> None:
        """WorkCase Index"""
        self._idx = idx
        return

    @property
    def lnkStatus(self) -> LnkPrjStatus:
        return self._pfStatus

    @lnkStatus.setter
    def lnkStatus(self, st: LnkPrjStatus) -> None:
        self._pfStatus = st
        return

    @property
    def isLinked(self) -> bool:
        return self._pfStatus == LnkPrjStatus.Normal

    # >>>>>> Skew 設定 #########
    @property
    def thOffSkew(self) -> float:
        """Skewオフセット角度"""
        return self._thSkew

    @property
    def skewedDatas(self) -> dict[float, WorkCase]:
        """Skew分割されたデータ"""
        return self._skewedDatas

    @property
    def hasSkew(self) -> bool:
        """Skew分割があるかどうか"""
        return len(self._skewedDatas) > 0

    @property
    def nDivSkew(self) -> int:
        """Skew分割数"""
        return len(self._skewedDatas)

    @property
    def isSlice(self) -> bool:
        """断面解析かどうか"""
        return self._isSlice

    # <<<<< Skew 設定 ##########

    # endregion

    # region Static Methods
    @staticmethod
    def CnvDQToAC(vs: tuple[float, float]) -> tuple[float, float]:
        Id = vs[0]
        Iq = vs[1]
        Ia = sqrt((Id * Id + Iq * Iq) / 3)
        Fw = atan2(-Id, Iq) / pi * 180
        return Ia, Fw

    @staticmethod
    def CnvACToDQ(vs: tuple[float, float]) -> tuple[float, float]:
        Ia = vs[0]
        Fw = vs[1] / 180 * pi
        Id = sqrt(3) * Ia * sin(-Fw)
        Iq = sqrt(3) * Ia * cos(-Fw)
        return Id, Iq

    @staticmethod
    def RadToDeg(v: float) -> float:
        return v / pi * 180

    @staticmethod
    def DegToRad(v: float) -> float:
        return v / 180 * pi

    # endregion

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, WorkCase):
            return False

        return bool(np.isclose(self.prmVals, o.prmVals, atol=1e-4).all())

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __str__(self) -> str:
        s = ""
        for i, m in enumerate(MotAxes):
            s += f"{m.name:>3} -"
            for j, n in enumerate(Axis2D):
                if m == MotAxes.DQ:
                    mm: AxisDQ | AxisAC = AxisDQ(n)
                else:
                    mm = AxisAC(n)
                s += f"{mm.name:>3}:{self._vals[m][n]}"
                if j == 0:
                    s += " , "

            if i == 0:
                s += " / "
        return s

    def __repr__(self) -> str:
        s = self.__str__()
        s += f" [{self._status.name:>10}]"
        s += f" ({len(self._data.datStep):3} / {len(self._data.datFreq):3})"
        if self._lnkInfo:
            s += f" {self._cIdx:4} @ {self._lnkInfo.name}"
        return s

    def toDict(self) -> dict[str, Any]:
        """WorkCaseオブジェクトを辞書形式に変換"""
        return {
            "mode": self._mode.name,
            "status": self._status.name,
            "val": self.val,
            "caseNo": self._cIdx,
            "grpIdx": self._gIdx,
            "prjInfo": self._lnkInfo.toDict() if self._lnkInfo else {},
            "isExtArea": self.isExtArea,
            "index": self._idx if "_idx" in self.__dict__ else -1,
            "pfStatus": self._pfStatus.name,
            "data": self._data.toDict(),
            "isSlice": self._isSlice,
            "thSkew": float(self._thSkew),
            "skewedDatas": {th: skWc.toDict() for th, skWc in self._skewedDatas.items()},
        }

    @staticmethod
    def fromDict(data: dict, tgt: WorkCase | None = None) -> WorkCase:
        m = MotAxes[data.get("mode", MotAxes.DQ.name)]
        v = tuple(data.get("val", [0.0, 0.0]))
        if tgt is None:
            tgt = WorkCase(val=v, mode=m)
        else:
            tgt._setVals(v, m)
        """辞書形式のデータからWorkCaseオブジェクトを生成"""
        tgt._status = WorkStatus[data["status"]]

        tgt._data = ExtractedMagDatas.fromDict(data.get("data", ExtractedMagDatas().toDict()))
        tgt._cIdx = data["caseNo"]
        tgt._gIdx = data["grpIdx"]

        StudyInfo.fromDict(data.get("prjInfo", StudyInfo().toDict()), tgt._lnkInfo)
        tgt._isExtArea = data.get("isExtArea", False)
        tgt._idx = data.get("index", -1)
        tgt._pfStatus = LnkPrjStatus[data.get("pfStatus", LnkPrjStatus.Normal.name)]
        # >>>>>> Skew 設定 #########
        tgt._isSlice = data.get("isSlice", False)
        tgt._thSkew = float(data.get("thSkew", 0.0))
        tgt._skewedDatas = {
            float(th): WorkCase.fromDict(skWc) for th, skWc in data.get("skewedDatas", {}).items()
        }
        # <<<<< Skew 設定 ##########

        return tgt

    def saveToJsonFile(self, file_path: str) -> None:
        """WorkCaseオブジェクトをJSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def loadFromJsonFile(file_path: str) -> WorkCase:
        """JSONファイルからWorkCaseオブジェクトを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WorkCase.fromDict(data)

    # endregion
