from __future__ import annotations

from enum import IntEnum, auto
from math import atan2, cos, degrees, radians, sin, sqrt

from JMagDatas.AxesContents import AxisAC, AxisDQ, MotAxes
from LinkToJMag.JMagFileInfo import JMagPrjFileInfo


class CaseStatus(IntEnum):
    NaN = -1
    Created = auto()
    Defined = auto()
    InComplete = auto()
    Analyzed = auto()
    Extracted = auto()


class JMagCaseSet:
    _mode: MotAxes
    _vals: tuple[float, float]
    _status: CaseStatus
    _linkPrj: JMagPrjFileInfo | None

    def __init__(
        self, vals: tuple[float, float], mode: MotAxes = MotAxes.DQ
    ) -> None:
        self._mode = mode
        self._vals = vals
        self._status = CaseStatus.Created
        self._linkPrj = None

    @property
    def mode(self) -> MotAxes:
        return self._mode

    @property
    def valIdIq(self) -> dict[AxisDQ, float]:
        if self._mode == MotAxes.DQ:
            return {AxisDQ.D: self._vals[0], AxisDQ.Q: self._vals[1]}
        else:
            return self.CnvIaFwToIdq(self._vals)

    @property
    def valIaFw(self) -> dict[AxisAC, float]:
        if self._mode == MotAxes.DQ:
            return self.CnvIdqToIaFw(self._vals)
        else:
            return {AxisAC.RMS: self._vals[0], AxisAC.FW: self._vals[1]}

    @staticmethod
    def CnvIdqToIaFw(vals: tuple[float, float]) -> dict[AxisAC, float]:
        Id = vals[0]
        Iq = vals[1]
        Ia = sqrt(Id * Id + Iq * Iq)
        Fw = degrees(atan2(-Id, Iq))
        return {AxisAC.RMS: Ia, AxisAC.FW: Fw}

    @staticmethod
    def CnvIaFwToIdq(vals: tuple[float, float]) -> dict[AxisDQ, float]:
        Ia = vals[0]
        Fw = vals[1]
        Id = Ia * sin(-radians(Fw))
        Iq = Ia * cos(-radians(Fw))
        return {AxisDQ.D: Id, AxisDQ.Q: Iq}
