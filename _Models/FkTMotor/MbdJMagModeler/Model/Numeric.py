from __future__ import annotations

import json
import re
from decimal import Decimal

import numpy as np
from PySide6.QtCore import QObject, QSettings, Signal, Slot


class NumVal(QObject):
    __vPatf = r"0|([+-]?\d+(\.\d*)?)"  # 数値マッチ
    __vPatfe = (
        r"\s*(0|([+-]?[1-9]\d*))(?P<eDig>\.\d+([eE](?P<eIdx>[+-]?\d+))?)?\s*"
    )
    __vPati = r"\s*(0|([+-]?[1-9]\d*))\s*"
    __rof = re.compile(__vPatf)
    __rofe = re.compile(__vPatfe)
    __roi = re.compile(__vPati)

    def isEnableText(self, s: str) -> re.Match:
        if not self._isInt:
            stt = NumVal.__rofe.fullmatch(s)
        else:
            stt = NumVal.__roi.fullmatch(s)
        return stt

    _isInt: bool
    _txt: str
    onValueChanged = Signal(str)

    def __init__(
        self, val: str | float | int | None = None, isInt=False
    ) -> None:
        super().__init__(None)
        self._isInt = isInt
        if val is not None:
            if isinstance(val, (float, int)):
                val = str(val)
            elif not isinstance(val, str):
                raise TypeError("val must be str, float or int")
        self._txt = val

    @Slot(str)
    def setText(self, txt: str) -> None:
        self.text = txt

    @property
    def text(self) -> str:
        return self._txt

    @text.setter
    def text(self, txt: str) -> None:
        if self._txt == txt:
            return
        if txt is None or len(txt) == 0:
            self._txt = ""
        else:
            m = self.isEnableText(txt)
            if m is None:
                raise ValueError(f"Invalid numeric text value: {txt}")
            d = Decimal(txt)
            self._txt = str(
                d.quantize(Decimal(1))
                if d == d.to_integral_value()
                else d.normalize()
            )
        self.onValueChanged.emit(self._txt)

    @property
    def value(self) -> float | int | None:
        try:
            if self._txt is None or len(self._txt) == 0:
                return None
            elif not self._isInt:
                return float(Decimal(self._txt).normalize())
            else:
                return int(Decimal(self._txt).normalize())
        except ValueError:
            return None

    @value.setter
    def value(self, val: float | int) -> None:
        if isinstance(val, (float, int)):
            self.text = str(val)
        else:
            raise TypeError("val must be float or int")

    def toDict(self) -> dict:
        """NumVal オブジェクトを辞書形式に変換"""
        return {
            "tval": self._txt,
            "isInt": self._isInt,
        }

    @staticmethod
    def fromDict(data: dict, tgt: NumVal = None) -> NumVal:
        """辞書形式のデータから NumVal オブジェクトを生成"""
        if tgt is not None:
            obj = tgt
        else:
            obj = NumVal()
        if not isinstance(data, dict):
            return None
        if "txt" in data:
            obj.text = data["txt"]
        elif "tval" in data:
            vTxt = data["tval"]
            obj.text = vTxt
        isInt = False if "isInt" not in data else data["isInt"]
        obj._isInt = isInt
        obj.onValueChanged.emit(obj._txt)
        return obj

    def loadSettings(self, s: QSettings) -> None:
        """QSettings から値を読み込む"""
        if s is None:
            return
        s.beginGroup("NumVal")
        self._txt = s.value("text", "", str)
        self._isInt = s.value("isInt", False, bool)
        self.onValueChanged.emit(self._txt)
        s.endGroup()

    def saveSettings(self, s: QSettings) -> None:
        """QSettings に値を保存する"""
        if s is None:
            return
        s.beginGroup("NumVal")
        s.setValue("text", self._txt)
        s.setValue("isInt", self._isInt)
        s.endGroup()


class boolVal(QObject):
    _val: bool
    onValueChanged = Signal(bool)

    def __init__(self, val: bool = False, p: QObject = None) -> None:
        super().__init__(p)
        self._val = val

    @property
    def val(self) -> bool:
        return self._val

    @val.setter
    def val(self, val: bool) -> None:
        if self._val == val:
            return
        self._val = val
        self.onValueChanged.emit(self._val)

    def importJson(self, dTxt: str) -> None:
        """JSON形式の文字列から値を設定"""
        try:
            data = json.loads(dTxt)
            if isinstance(data, dict) and "val" in data:
                boolVal.fromDict(data, self)
            else:
                raise ValueError("Invalid JSON format for boolVal")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {dTxt}") from e

    def exportJson(self) -> str:
        """boolVal オブジェクトを JSON 形式の文字列に変換"""
        return json.dumps({"val": self._val}, indent=2, ensure_ascii=False)

    def toDict(self) -> dict:
        """boolVal オブジェクトを辞書形式に変換"""
        return {
            "val": self._val,
        }

    @staticmethod
    def fromDict(data: dict, tgt: boolVal = None) -> boolVal:
        """辞書形式のデータから boolVal オブジェクトを生成"""
        if tgt is not None:
            obj = tgt
        else:
            obj = boolVal()
        if not isinstance(data, dict):
            return None
        if "val" in data:
            obj.val = data["val"]
        obj.onValueChanged.emit(obj._val)
        return obj

    def loadSettings(self, s: QSettings) -> None:
        """QSettings から値を読み込む"""
        if s is None:
            return
        s.beginGroup("BoolVal")
        self._val = s.value("val", False, bool)
        s.endGroup()
        self.onValueChanged.emit(self._val)

    def saveSettings(self, s: QSettings) -> None:
        """QSettings に値を保存する"""
        if s is None:
            return
        s.beginGroup("BoolVal")
        s.setValue("val", self._val)
        s.endGroup()


class IntVal(QObject):
    __vPat = r"\s*(0|([+-]?[1-9]\d*))\s*"
    __ro = re.compile(__vPat)

    # _val: int | None
    _txt: str | None
    onValueChanged = Signal(str)

    def isEnableText(self, s: str) -> bool:
        return bool(IntVal.__ro.fullmatch(s))

    def __init__(self, val: str | int | None = None) -> None:
        super().__init__(None)
        if val is not None:
            if isinstance(val, int):
                val = str(val)
            elif not isinstance(val, str):
                raise TypeError("val must be str or int")
        self._txt = val

    @Slot(str)
    def setText(self, txt: str) -> None:
        self.text = txt

    @property
    def text(self) -> str:
        return self._txt

    @text.setter
    def text(self, txt: str) -> None:
        if self._txt == txt:
            return
        if txt is None or len(txt) == 0:
            self._txt = None
        else:
            m = self.isEnableText(txt)
            if m is None:
                raise ValueError(f"Invalid numeric text value: {txt}")
            d = Decimal(txt)
            self._txt = str(
                d.quantize(Decimal(1))
                if d == d.to_integral_value()
                else d.normalize()
            )
        self.onValueChanged.emit(self._txt)

    @property
    def value(self) -> float | int | None:
        try:
            if self._txt is None:
                return None
            elif not self._isInt:
                return float(Decimal(self._txt).normalize())
            else:
                return int(Decimal(self._txt).normalize())
        except ValueError:
            return None

    @value.setter
    def value(self, val: float | int) -> None:
        if isinstance(val, (float, int)):
            self.text = str(val)
        else:
            raise TypeError("val must be float or int")

    def toDict(self) -> dict:
        """NumVal オブジェクトを辞書形式に変換"""
        return {
            "tval": self._txt,
            "isInt": self._isInt,
        }

    @staticmethod
    def fromDict(data: dict, tgt: NumVal = None) -> NumVal:
        """辞書形式のデータから NumVal オブジェクトを生成"""
        if tgt is not None:
            obj = tgt
        else:
            obj = NumVal()
        if not isinstance(data, dict):
            return None
        if "txt" in data:
            obj.text = data["txt"]
        elif "tval" in data:
            vTxt = data["tval"]
            obj.text = vTxt
        isInt = False if "isInt" not in data else data["isInt"]
        obj._isInt = isInt
        return obj

    def loadSettings(self, s: QSettings) -> None:
        """QSettings から値を読み込む"""
        if s is None:
            return
        s.beginGroup("IntVal")
        self._txt = s.value("val", None, str)
        s.endGroup()

    def saveSettings(self, s: QSettings) -> None:
        """QSettings に値を保存する"""
        if s is None:
            return
        s.beginGroup("IntVal")
        s.setValue("val", self._txt)
        s.endGroup()


class NumericRange(QObject):
    _min: NumVal
    _max: NumVal
    _step: NumVal

    __vPatf = r"0|([+-]?\d+(\.\d*)?)"  # 数値マッチ
    __lPatf = rf"({__vPatf})(:({__vPatf})){{0,2}}"
    __ro = re.compile(__lPatf)
    __rs = re.compile(__vPatf)

    onValueChanged: Signal = Signal(str)

    def isEnableTextAll(self, s: str) -> bool:
        """数値範囲文字列が有効かどうかを判定する"""
        m = self.__ro.fullmatch(s)
        return bool(m)

    def isEnableTextVal(self, s: str) -> bool:
        """数値文字列が有効かどうかを判定する"""
        m = self.__rs.fullmatch(s)
        return bool(m)

    def __init__(
        self,
        min: NumVal | float | int | str | None = None,
        max: NumVal | float | int | str | None = None,
        step: NumVal | float | int | str | None = None,
        isInt: bool = False,
    ) -> None:
        super().__init__()
        if min is None:
            min = NumVal()
        if max is None:
            max = NumVal()
        if step is None:
            step = NumVal()

        if isinstance(min, str):
            if not self.isEnableTextAll(min):
                raise ValueError(f"Invalid numeric text value: {min}")
            vs = min.split(":")
            if len(vs) == 3:
                min = vs[0]
                step = vs[1]
                max = vs[2]
            elif len(vs) == 2:
                min = vs[0]
                step = None
                max = vs[1]
            else:
                raise ValueError(f"Invalid range text: {min}")
        vs = []
        for v in (min, max, step):
            if v is None:
                v = NumVal()
            if not isinstance(v, NumVal):
                if isinstance(v, str):
                    if self.isEnableTextVal(v):
                        v = NumVal(v, isInt)
                    else:
                        raise ValueError(f"Invalid numeric text value: {v}")
                elif not isinstance(v, (float, int)):
                    raise TypeError(
                        "min, max and step must be NumVal or float or int"
                    )
                v = NumVal(v, isInt)
            vs.append(v)
        min, max, step = tuple(vs)
        self._min = min
        self._max = max
        self._step = step

        for vv in (self._min, self._max, self._step):
            vv.onValueChanged.connect(
                lambda _: self.onValueChanged.emit(self.text)
            )

        return

    @property
    def values(self) -> np.ndarray:
        """Return a list of values in the range."""
        if self._step.value is None:
            stv = 1.0 if self._max.value > self._min.value else -1.0
        else:
            stv = self._step.value

        return np.arange(
            self._min.value,
            self._max.value + stv * 0.5,
            stv,
        )

    @property
    def valList(self) -> list[float | int]:
        return self.values.tolist()

    def chkStatus(self) -> bool:
        if self._min.value is None or self._max.value is None:
            return False
        if self._min.value > self._max.value:
            if self._step is not None and self._step.value >= 0:
                return False
        else:
            if self._step is not None and self._step.value <= 0:
                return False
        return True

    @property
    def min(self) -> NumVal:
        return self._min

    @property
    def max(self) -> NumVal:
        return self._max

    @property
    def step(self) -> NumVal:
        return self._step

    @property
    def text(self) -> str:
        ts = []
        m = self._min.text
        if m is None or len(m) == 0:
            return ""
        ts.append(m)
        m = self.step.text
        if m is not None and len(m) > 0:
            ts.append(m)
        m = self.max.text
        if m is None or len(m) == 0:
            return ""
        ts.append(m)
        return ":".join(ts)

    @text.setter
    def text(self, t: str):
        """文字列を分解して min, step, max を設定"""
        if t is None or len(t) == 0:
            for v in (self._min, self._step, self._max):
                v.text = None
            return
        ts = re.sub(r"\s+", "", t).split(":")

        if len(ts) == 3:
            self._min.text = ts[0]
            self._step.text = ts[1]
            self._max.text = ts[2]
        elif len(ts) == 2:
            self._min.text = ts[0]
            self._max.text = ts[1]
            self._step.text = None
        else:
            raise ValueError(f"Invalid range text: {t}")

    def toDict(self, isText=False) -> dict:
        if not isText:
            """NumericRange オブジェクトを辞書形式に変換"""
            return {
                "min": self._min.toDict(),
                "max": self._max.toDict(),
                "step": self._step.toDict(),
            }
        else:
            return self.text

    @staticmethod
    def fromDict(
        data: dict | str, tgt: NumericRange | None = None
    ) -> NumericRange:
        if tgt is not None:
            obj = tgt
        else:
            obj = NumericRange()
        if isinstance(data, str):
            data = data.split(":")
            if len(data) <= 3:
                obj.min.text = data[0]
                obj.max.text = data[1]
                if len(data) == 3:
                    obj.step.text = data[2]
            else:
                raise ValueError(f"Invalid range text: {data}")
        else:
            """辞書形式のデータから NumericRange オブジェクトを生成"""
            NumVal.fromDict(data["min"], obj.min)
            NumVal.fromDict(data["max"], obj.max)
            NumVal.fromDict(data["step"], obj.step)
        return obj

    ########################################################
    def loadSettings(self, s: QSettings = None) -> None:
        if s is None:
            return
        s.beginGroup("NumRange")

        s.beginGroup("Min")
        self._min.loadSettings(s)
        s.endGroup()

        s.beginGroup("Max")
        self._max.loadSettings(s)
        s.endGroup()

        s.beginGroup("Step")
        self._step.loadSettings(s)
        s.endGroup()

        s.endGroup()

    ########################################################
    def saveSettings(self, s: QSettings = None) -> None:
        if s is None:
            return
        s.beginGroup("NumRange")

        s.beginGroup("Min")
        self._min.saveSettings(s)
        s.endGroup()

        s.beginGroup("Max")
        self._max.saveSettings(s)
        s.endGroup()

        s.beginGroup("Step")
        self._step.saveSettings(s)
        s.endGroup()

        s.endGroup()

    def __str__(self) -> str:
        return self.text
