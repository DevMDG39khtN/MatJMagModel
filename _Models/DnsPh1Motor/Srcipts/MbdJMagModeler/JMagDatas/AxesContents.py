from __future__ import annotations

from enum import IntEnum


class Axis2D(IntEnum):
    """Table 2D Axis Type"""

    CX = 0
    RY = 1


class AxisDQ(IntEnum):
    """Motor DQ Axis Type"""

    D = 0
    Q = 1


class AxisAC(IntEnum):
    """Motor AC Axis Type"""

    RMS = 0
    FW = 1


class MotAxes(IntEnum):
    """Motor Coordinate Axis Type"""

    DQ = 0
    AC = 1


class AxesDefs:
    """Motor Coordinate Axis Info. Definition"""

    @classmethod
    def _chkBaseName(cls, bName: str) -> tuple[str, str]:
        """Check the Base Name"""
        dqName = bName[0].upper()
        acName = bName
        return dqName, acName

    @classmethod
    def name(cls, m: MotAxes, sfx: str) -> str:
        """Get the Axis Name"""
        if m == MotAxes.DQ:
            return f"{sfx}d-{sfx}q"
        return f"{sfx}a-Fw"

    @classmethod
    def axisName(cls, m: MotAxes, ax: Axis2D, sfx: str, unit: str = "") -> str:
        """Get the Axis Name"""
        if m == MotAxes.DQ:
            if ax == Axis2D.CX:
                return f"{sfx}d"
            return f"{sfx}q"
        if ax == Axis2D.CX:
            return f"{sfx}a"
        return "Fw"
