from __future__ import annotations

import re
from enum import IntEnum, auto
from typing import Callable

import numpy as np
from PySide6.QtCore import QObject, QSettings, Signal

from Model.Numeric import NumericRange, NumVal


class TypDefExtCase(IntEnum):
    Each = 0
    Both = auto()


class ItemExtGenWorkCase(QObject):
    """
    Id/Iq 正常動作外領域 条件生成
    """

    # region Attributes
    _type: TypDefExtCase
    _defId: str
    _defIq: str

    onValidChanged = Signal(bool)
    onTypeChanged = Signal(TypDefExtCase)
    onDefIdChanged = Signal(str)
    onDefIqChanged = Signal(str)
    # endregion

    # region Functions
    ##### Initializer #####
    def __init__(
        self,
        t: TypDefExtCase = TypDefExtCase.Each,
        id: str = "",
        iq: str = "",
        cb: Callable[[bool], None] | None = None,
    ):
        """
        Initialize ItemExtGenWorkCase instance.

        Parameters
        ----------
        t : TypDefExtCase, optional
            DefType, by default TypDefExtCase.Each
        id : str, optional
            Id Values Defs, by default ""
        iq : str, optional
            Iq Values, by default ""
        cb : Callable[[bool], None], optional
            _description_, by default None
        """
        super().__init__(None)
        self._type = t
        self._defId = id
        self._defIq = iq

        if cb is not None:
            self.onValidChanged.connect(cb)
        self.onValidChanged.connect(self._chkValid)
        return

    ########################################################
    def _dataList(self) -> tuple[list[float], list[float]]:
        """Get data list."""

        def _getAxList(txt: str) -> list[float]:
            """Get axis list by text decode"""
            if len(txt) == 0:
                return []
            axLst = []
            for dTxt in txt.split(";"):
                if len(dTxt) == 0:
                    continue
                rLst = []
                for eTxt in dTxt.split(","):
                    if len(eTxt) == 0:
                        continue
                    rTxs = eTxt.split(":")
                    nrt = len(rTxs)
                    if nrt == 1:
                        rLst.append(NumVal(rTxs[0]).value)
                    elif nrt == 2:
                        rvo = NumericRange(
                            NumVal(rTxs[0]), NumVal(rTxs[1]), NumVal()
                        )
                        rLst.extend(rvo.values)
                    elif nrt == 3:
                        rvo = NumericRange(
                            NumVal(rTxs[0]),
                            NumVal(rTxs[2]),
                            NumVal(rTxs[1]),
                        )
                        rLst.extend(rvo.valList)
                    else:
                        raise ValueError("Invalid Range")
                rs = sorted(np.unique(rLst).tolist())
                print(f">>> {rLst} \n--> {rs}")
                if len(rs) > 0:
                    axLst.append(rs)
            return axLst

        axVals0 = [_getAxList(re.sub(r"\s+", "", t)) for t in self.axDefText]
        if self.type == TypDefExtCase.Both and len(axVals0[1]) == 0:
            axVals0[1] = axVals0[0]
        axVals = (
            (axVals0[0], axVals0[1])
            if len(axVals0) > 1
            else (axVals0[0], axVals0[0])
        )
        return axVals

    # endregion

    __vPat = r"[+-]?\d+(\.\d*)?"  # 数値マッチ
    __rPat = rf"({__vPat})(:({__vPat})){{0,2}}"  # 数値範囲マッチ
    __tPat = rf"({__rPat})(,({__rPat}))*"  # 数値範囲リスト
    __mPat = rf"{__tPat}((;{__tPat})*);?"
    __reo = re.compile(__mPat)

    ########################################################
    ########################################################

    # region Class Members
    ########################################################

    @staticmethod
    def chkSetText(txt: str) -> bool:
        """Check if the text is a valid set text."""
        tTxt = re.sub(r"\s+", "", txt)  # remove spaces
        m = ItemExtGenWorkCase.__reo.fullmatch(tTxt)
        return bool(m)

    # endregion

    ########################################################
    ########################################################

    # region Serialize/Deserialize
    ########################################################
    def toDict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "type": self._type.name,
            "defId": self._defId,
            "defIq": self._defIq,
        }

    ########################################################
    @staticmethod
    def fromDict(d: dict[str, str]) -> ItemExtGenWorkCase:
        """Convert from dictionary."""
        t = TypDefExtCase[d["type"]]
        id = d["defId"]
        iq = d["defIq"]
        return ItemExtGenWorkCase(t, id, iq)

    ########################################################
    def loadSettings(self, s: QSettings | None = None) -> None:
        if s is None:
            return
        s.beginGroup("Data")
        self._type = TypDefExtCase[
            str(s.value("type", TypDefExtCase.Each.name, str))
        ]
        self._defId = str(s.value("defId", "", str))
        self._defIq = str(s.value("defIq", "", str))
        s.endGroup()

    ########################################################
    def saveSettings(self, s: QSettings | None = None) -> None:
        if s is None:
            return
        s.beginGroup("Data")
        s.setValue("type", self._type.name)
        s.setValue("defId", self._defId)
        s.setValue("defIq", self._defIq)
        s.endGroup()

    # endregion

    ########################################################
    ########################################################

    # region Properties
    ########################################################
    @property
    def axDefText(self) -> tuple[str, str]:
        """Get axis definition text."""
        if self._type == TypDefExtCase.Each:
            return (self._defId, self._defIq)
        else:
            return (self._defId, "")

    @property
    def isValid(self) -> bool:
        if self._type == TypDefExtCase.Each:
            stt = self.chkSetText(self._defId) and self.chkSetText(self._defIq)
        else:
            stt = self.chkSetText(self._defId)
        return stt

    ########################################################
    @property
    def type(self) -> TypDefExtCase:
        return self._type

    ########################################################
    @type.setter
    def type(self, t: TypDefExtCase):
        if self._type != t:
            self._type = t
            self.onTypeChanged.emit(self._type)
            self.onValidChanged.emit(lambda: self._chkValid())

    ### Id Gen Definition
    @property
    def defId(self) -> str:
        return self._defId

    ########################################################
    @defId.setter
    def defId(self, id: str):
        if self._defId != id:
            self._defId = id
            self.onDefIdChanged.emit(id)
            self.onValidChanged.emit(lambda: self._chkValid())

    ### Iq Gen Definition
    @property
    def defIq(self) -> str:
        return self._defIq

    ########################################################
    @defIq.setter
    def defIq(self, iq: str):
        if self._defIq != iq:
            self._defIq = iq
            self.onDefIqChanged.emit(iq)
            self.onValidChanged.emit(lambda: self._chkValid())

    ########################################################
    def _chkValid(self) -> bool:
        """Check definition validity. only use properties"""
        stt = len(self._defId) > 0
        if self._type == TypDefExtCase.Each:
            stt = stt and len(self._defIq) > 0
        return stt

    # endregion

    ########################################################
    ########################################################

    # region Special Functions

    ########################################################
    def __repr__(self):
        return (
            f"ItemExtGenWorkCase(Type:{self._type.name}{self.type}"
            f", def:{self.defId}/{self.defIq})"
        )

    # endregion
