from __future__ import annotations

import inspect
import json
from math import sqrt
from typing import get_type_hints

from PySide6.QtCore import QObject, QSettings, Signal

from Model.Numeric import NumVal, boolVal


class MdlParameter(QObject):
    _nP: int | None
    _maxIa: float | None
    _nParaCoil: int | None
    _RaM: float | None
    _tmpAtRa: float
    _mdlNrpm: float
    # >>>>>> Skew 設定 #########
    _isSkewed: boolVal
    _thSkew: NumVal
    _nDivSkew: NumVal
    _isMultiSlice: boolVal
    # <<<<< Skew 設定 ##########

    onValueChanged = Signal(str, str)
    onChkStateChanged = Signal(str, bool)
    onStatusChanged = Signal(bool)
    onMaxIdqChanged = Signal(float)
    onMaxIaChanged = Signal(float)
    onTempCoilChanged = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self._nP = None
        self._maxIa = None
        self._nParaCoil = None
        self._RaM = None
        self._tmpAtRa = None
        self._mdlNrpm = None

        # >>>>>> Skew 設定 #########
        self._isSkewed = boolVal(False)
        self._thSkew = NumVal()
        self._nDivSkew = NumVal(isInt=True)
        self._isMultiSlice = boolVal(False)
        # <<<<< Skew 設定 ##########

    def update(self) -> None:
        for pn, typ in self.getPrmTypes().items():
            if isinstance(typ, bool):
                self.onChkStateChanged.emit(pn, getattr(self, pn))
            else:
                v = getattr(self, pn)
                if pn == "RaM":
                    sv = str(round(v, 4))
                else:
                    sv = str(v)
                self.onValueChanged.emit(pn, sv)
        self.onMaxIdqChanged.emit(self.maxIdq)

    def _chkStatus(self) -> bool:
        return all(getattr(self, pn) is not None for pn in self.getPrmTypes())

    @classmethod
    def getPrmTypes(cls) -> dict[str, type]:
        mps = {
            n: get_type_hints(o.fset).get("v", None)
            for n, o in inspect.getmembers(cls)
            if isinstance(o, property) and o.fset is not None
        }
        return mps

    ########################################################
    def _onAllUpdate(self) -> None:
        self.onValueChanged.emit("nP", str(self._nP))
        self.onMaxIaChanged.emit(self._maxIa)
        self.onValueChanged.emit("maxIa", str(self._maxIa))
        self.onMaxIdqChanged.emit(self.maxIdq)
        self.onValueChanged.emit("nParaCoil", str(self.nParaCoil))
        self.onTempCoilChanged.emit(self._tmpAtRa)
        self.onValueChanged.emit("tmpAtRa", str(self._tmpAtRa))
        self.onValueChanged.emit("RaM", str(round(self.RaM, 4)))
        self.onValueChanged.emit("mdlNrpm", str(round(self._mdlNrpm, 4)))
        self._isSkewed.onValueChanged.emit(self._isSkewed.val)
        self._isMultiSlice.onValueChanged.emit(self._isMultiSlice.val)
        self._thSkew.onValueChanged.emit(self._thSkew.text)
        self._nDivSkew.onValueChanged.emit(self._nDivSkew.text)
        self.onStatusChanged.emit(self._chkStatus())
        return

    def loadSettings(self, s: QSettings = None) -> None:
        if s is None:
            return
        s.beginGroup("ModelParameter")
        self._nP = s.value("nP", 8, int)
        self._maxIa = s.value("maxIa", 0.0, float)
        self._nParaCoil = s.value("nParaCoil", 1, int)
        self._RaM = s.value("RaM", 0.0, float)
        self._tmpAtRa = s.value("tmpAtRa", 20.0, float)
        self._mdlNrpm = s.value("mdlNrpm", 0.0, float)
        self._isSkewed.val = s.value("isSkewed", False, bool)
        self._isMultiSlice.val = s.value("isMultiSlice", False, bool)
        self._thSkew.text = s.value("thSkew", "", str)
        self._nDivSkew.text = s.value("nDivSkew", "", str)
        s.endGroup()

        self._onAllUpdate()
        return

    def saveSettings(self, s: QSettings) -> None:
        if s is None:
            return

        s.beginGroup("ModelParameter")
        s.remove("")
        s.endGroup()

        s.beginGroup("ModelParameter")
        s.setValue("nP", self._nP)
        s.setValue("maxIa", self._maxIa)
        s.setValue("nParaCoil", self._nParaCoil)
        s.setValue("RaM", self._RaM)
        s.setValue("tmpAtRa", self._tmpAtRa)
        s.setValue("mdlNrpm", self._mdlNrpm)
        s.setValue("isSkewed", self._isSkewed.val)
        s.setValue("isMultiSlice", self._isMultiSlice.val)
        s.setValue("thSkew", self._thSkew.text)
        s.setValue("nDivSkew", self._nDivSkew.text)
        s.endGroup()
        return

    # region Ser-Deserialize
    ########################################################
    def toDict(self) -> dict[str, int | float]:
        return {
            "nP": self.nP,
            "maxIa": self.maxIa,
            "nParaCoil": self.nParaCoil,
            "RaM": self.RaM,
            "tmpAtRa": self.tmpAtRa,
            "mdlNrpm": self.mdlNrpm,
            "isSkewed": self.lnkIsSkew.toDict(),
            "isMultiSlice": self.lnkIsMultiSlice.toDict(),
            "thSkew": self.lnkThSkew.toDict(),
            "nDivSkew": self.lnkNDivSkew.toDict(),
        }

    ########################################################
    @staticmethod
    def fromDict(d: dict[str, int | float], mp: MdlParameter) -> MdlParameter:
        """Create an instance of MdlParameter from a dictionary."""
        pvs = {
            "nP": d.get("nP"),
            "maxIa": d.get("maxIa"),
            "nParaCoil": d.get("nParaCoil"),
            "RaM": d.get("RaM"),
            "tmpAtRa": d.get("tmpAtRa"),
            "mdlNrpm": d.get("mdlNrpm"),
        }
        if mp is None:
            mp = MdlParameter()

        mp._nP = pvs["nP"]
        mp._maxIa = pvs["maxIa"]
        mp._nParaCoil = pvs["nParaCoil"]
        mp._RaM = pvs["RaM"]
        mp._tmpAtRa = pvs["tmpAtRa"]
        mp._mdlNrpm = pvs["mdlNrpm"]
        mp.lnkIsSkew.fromDict(d.get("isSkewed", {}), mp.lnkIsSkew)
        mp.lnkIsMultiSlice.fromDict(d.get("isMultiSlice", {}), mp.lnkIsMultiSlice)
        mp.lnkThSkew.fromDict(d.get("thSkew", {}), mp.lnkThSkew)
        mp.lnkNDivSkew.fromDict(d.get("nDivSkew", {}), mp.lnkNDivSkew)
        return mp

    ########################################################
    def importJson(self, dTxt: str | None) -> None:
        if dTxt is None:
            return
        try:
            d = json.loads(dTxt)
            self.fromDict(d)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    ########################################################
    def exportJson(self) -> str:
        return json.dumps(self.toDict(), indent=2, ensure_ascii=False)

    # endregion

    # region Properties
    ########################################################
    @property
    def nP(self) -> int:
        return self._nP

    @nP.setter
    def nP(self, v: int) -> None:
        n = "nP"
        if v != self._nP:
            if v is None or v % 2 != 0:
                raise ValueError("nP must be even.")
            self._nP = v
            self.onValueChanged.emit(n, str(v))
            self.onStatusChanged.emit(self._chkStatus())

    ########################################################
    @property
    def maxIa(self) -> float:
        return self._maxIa

    @maxIa.setter
    def maxIa(self, v: float):
        n = "maxIa"
        if v != self._maxIa:
            self._maxIa = v
            self.onMaxIaChanged.emit(v)
            self.onValueChanged.emit(n, str(v))
            self.onMaxIdqChanged.emit(self.maxIdq)
            self.onStatusChanged.emit(self._chkStatus())

    @property
    def maxIdq(self) -> float:
        return sqrt(3) * self._maxIa if self._maxIa is not None else None

    ########################################################
    @property
    def nParaCoil(self) -> int:
        return self._nParaCoil

    @nParaCoil.setter
    def nParaCoil(self, v: int):
        n = "nParaCoil"
        if v != self._nParaCoil:
            self._nParaCoil = v
            self.onValueChanged.emit(n, str(v))
            self.onStatusChanged.emit(self._chkStatus())

    ########################################################
    @property
    def RaM(self) -> float:
        return self._RaM if self._RaM is not None else 0.0

    @RaM.setter
    def RaM(self, v: float) -> None:
        n = "RaM"
        if v != self._RaM:
            self._RaM = v
            self.onValueChanged.emit(n, str(round(v, 4)))
            self.onStatusChanged.emit(self._chkStatus())

    ########################################################
    @property
    def tmpAtRa(self) -> float:
        return self._tmpAtRa if self._tmpAtRa is not None else 0.0

    @tmpAtRa.setter
    def tmpAtRa(self, v: float) -> None:
        n = "tmpAtRa"
        if v != self._tmpAtRa:
            self._tmpAtRa = v
            self.onTempCoilChanged.emit(v)
            self.onValueChanged.emit(n, str(round(v, 4)))
            self.onStatusChanged.emit(self._chkStatus())

    ########################################################
    @property
    def mdlNrpm(self) -> float:
        return self._mdlNrpm if self._mdlNrpm is not None else 0.0

    @mdlNrpm.setter
    def mdlNrpm(self, v: float) -> None:
        n = "mdlNrpm"
        if v != self._mdlNrpm:
            self._mdlNrpm = v
            self.onValueChanged.emit(n, str(round(v, 4)))
            self.onStatusChanged.emit(self._chkStatus())

    ########################################################
    @property
    def vP(self) -> float:
        return float(self._nP) if self._nP is not None else 0.0

    @property
    def Ra(self) -> float:
        return self._RaM / 1000.0 if self._RaM is not None else 0.0

    # >>>>>> Skew 設定 #########
    ########################################################
    @property
    def isSkewed(self) -> bool:
        return self._isSkewed.val

    @isSkewed.setter
    def isSkewed(self, v: bool) -> None:
        self._isSkewed.val = v

    @property
    def lnkIsSkew(self) -> boolVal:
        return self._isSkewed

    ########################################################
    @property
    def thSkew(self) -> float:
        return self._thSkew.value

    @thSkew.setter
    def thSkew(self, v: float) -> None:
        self._thSkew.value = v

    @property
    def lnkThSkew(self) -> NumVal:
        return self._thSkew

    ########################################################
    @property
    def nDivSkew(self) -> int:
        return self._nDivSkew.value

    @nDivSkew.setter
    def nDivSkew(self, v: int) -> None:
        self._nDivSkew.value = v

    @property
    def lnkNDivSkew(self) -> NumVal:
        return self._nDivSkew

    ########################################################
    @property
    def isMultiSlice(self) -> bool:
        return self._isMultiSlice.val

    @isMultiSlice.setter
    def isMultiSlice(self, v: bool) -> None:
        self._isMultiSlice.val = v

    @property
    def lnkIsMultiSlice(self) -> boolVal:
        return self._isMultiSlice

    # <<<<< Skew 設定 ##########
    # endregion
