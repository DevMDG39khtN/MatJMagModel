from __future__ import annotations

import json

from PySide6.QtCore import QObject, QSettings, Signal

from Model.Numeric import NumericRange, NumVal


class MdlMapDef(QObject):
    _tdCoil: NumVal
    _maxIa: NumVal
    _dIdq: NumVal
    _dFdq: NumVal
    _axTrqs: NumericRange
    _axNrpms: NumericRange
    _axVdcs: NumericRange
    _rLmtVdc: NumVal
    _isOvrMod: bool
    _nOrdFitMtl: NumVal

    onOvrModChanged = Signal(bool)

    ##### --------------------------------------------------
    def __init__(self, p: QObject | None = None) -> None:
        super().__init__(p)

        self._tdCoil = NumVal()
        self._maxIa = NumVal()
        self._dIdq = NumVal()
        self._dFdq = NumVal()
        self._axTrqs = NumericRange()
        self._axNrpms = NumericRange()
        self._axVdcs = NumericRange()
        self._rLmtVdc = NumVal()
        self._isOvrMod = False
        self._nOrdFitMtl = NumVal(isInt=True)

    ########################################################
    def setOvrMod(self, v: bool) -> None:
        self.isOvrMod = v

    ########################################################
    def toDict(self) -> dict[str, str]:
        """MdlMapDef オブジェクトを辞書形式に変換"""
        return {
            "tempCoil": self._tdCoil.toDict(),
            "maxIa": self._maxIa.toDict(),
            "dIdq": self._dIdq.toDict(),
            "dFdq": self._dFdq.toDict(),
            "axTrqs": self._axTrqs.toDict(),
            "axNrpms": self._axNrpms.toDict(),
            "axVdcs": self._axVdcs.toDict(),
            "rLmtVdc": self._rLmtVdc.toDict(),
            "isOvrMod": self.isOvrMod,
            "nOrdFitMtl": self.nOrdFitMtl.toDict(),
        }

    ########################################################
    @staticmethod
    def fromDict(data: dict[str, str], tgt: MdlMapDef = None) -> MdlMapDef:
        """辞書形式のデータから MdlMapDef オブジェクトを生成"""
        if tgt is not None:
            obj = tgt
        else:
            obj = MdlMapDef()
        NumVal.fromDict(data["tempCoil"], obj._tdCoil)
        NumVal.fromDict(data["maxIa"], obj._maxIa)
        NumVal.fromDict(data["dIdq"], obj._dIdq)
        NumVal.fromDict(data["dFdq"], obj._dFdq)
        NumericRange.fromDict(data["axTrqs"], obj._axTrqs)
        NumericRange.fromDict(data["axNrpms"], obj._axNrpms)
        NumericRange.fromDict(data["axVdcs"], obj._axVdcs)
        NumVal.fromDict(data["rLmtVdc"], obj._rLmtVdc)
        obj._isOvrMod = data["isOvrMod"]
        NumVal.fromDict(data["nOrdFitMtl"], obj._nOrdFitMtl)

        return obj

    ########################################################
    def loadFromJson(self, jst: str) -> None:
        if len(jst) == 0:
            return
        dic = json.loads(jst)
        self.fromDict(dic, self)

    ########################################################
    def saveToJson(self) -> str:
        dic = self.toDict()
        return json.dumps(dic, indent=2, ensure_ascii=False)

    ########################################################
    def loadToJsonFile(self, fpath: str) -> None:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data is not None:
                self.fromDict(data, self)

    ########################################################
    def saveToJsonFile(self, fpath: str) -> None:
        """辞書形式のデータを JSON ファイルに保存"""
        with open(fpath, "w", encoding="utf-8") as f:
            # json.dump(datas, f, ensure_ascii=False, indent=2)
            json.dump(self.toDict(), f, ensure_ascii=False, indent=2)

    def loadSettings(self, s: QSettings | None) -> None:
        if s is None:
            return
        s.beginGroup("MapDef")
        self._tdCoil.text = s.value("tempCoil", "", str)
        self._maxIa.text = s.value("maxIa", "", str)
        self._dIdq.text = s.value("dIdq", "", str)
        self._dFdq.text = s.value("dFdq", "", str)
        self._axTrqs.text = s.value("axTrqs", "", str)
        self._axNrpms.text = s.value("axNrpms", "", str)
        self._axVdcs.text = s.value("axVdcs", "", str)
        self._rLmtVdc.text = s.value("rLmtVdc", "", str)
        self._isOvrMod = s.value("isOvrMod", False, bool)
        self._nOrdFitMtl.text = s.value("nOrdFitMtl", "", str)
        s.endGroup()
        # mdi = s.value("MapDef", "", str)
        # self.loadFromJson(mdi)

    ########################################################
    def saveSettings(self, s: QSettings | None) -> None:
        if s is None:
            return
        s.beginGroup("MapDef")
        s.setValue("tempCoil", self._tdCoil.text)
        s.setValue("maxIa", self._maxIa.text)
        s.setValue("dIdq", self._dIdq.text)
        s.setValue("dFdq", self._dFdq.text)
        s.setValue("axTrqs", self._axTrqs.text)
        s.setValue("axNrpms", self._axNrpms.text)
        s.setValue("axVdcs", self._axVdcs.text)
        s.setValue("rLmtVdc", self._rLmtVdc.text)
        s.setValue("isOvrMod", self._isOvrMod)
        s.setValue("nOrdFitMtl", self._nOrdFitMtl.text)
        s.endGroup()

    # region Properties
    @property
    def tdCoil(self) -> NumVal:
        return self._tdCoil

    @property
    def maxIa(self) -> NumVal:
        return self._maxIa

    @property
    def dIdq(self) -> NumVal:
        return self._dIdq

    @property
    def dFdq(self) -> NumVal:
        return self._dFdq

    @property
    def axTrqs(self) -> NumericRange:
        return self._axTrqs

    @property
    def axNrpms(self) -> NumericRange:
        return self._axNrpms

    @property
    def axVdcs(self) -> NumericRange:
        return self._axVdcs

    @property
    def rLmtVdc(self) -> NumVal:
        return self._rLmtVdc

    @property
    def isOvrMod(self) -> bool:
        return self._isOvrMod

    @isOvrMod.setter
    def isOvrMod(self, v: bool) -> None:
        if self._isOvrMod != v:
            self._isOvrMod = v
            self.onOvrModChanged.emit(v)

    @property
    def nOrdFitMtl(self) -> NumVal:
        return self._nOrdFitMtl

    # endregion
