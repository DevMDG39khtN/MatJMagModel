from __future__ import annotations

import json
import math
from enum import Enum, IntEnum
from typing import Any

import numpy as np
import numpy.typing as npt


class PeriodType(IntEnum):
    FULL = 1
    HALF = 2
    DIV3 = 3
    DIV6 = 6


class DataType(Enum):
    TORQUE = "トルク"
    CURRENT = "回路の電流"
    FLUX = "コイルの鎖交磁束"
    VoltLine = "電位差"
    VOLT = "回路の電圧"


class AxisMagData:
    __names: list[str]
    __units: dict[str, str]
    __datas: dict[str, npt.NDArray[np.float64]]  # npt.NDArray[np.float64]
    __priStt: PeriodType | None
    __isTime: bool
    __fa: float

    def __init__(
        self,
        name: list[str],
        units: list[str],
        datas: list[npt.NDArray[np.float64]],
        fa: float = np.nan,
    ) -> None:
        self.__names = name
        self.__units = dict(zip(name, units))
        self.__datas = dict(zip(name, datas))
        self.__isTime = "Time" in name

        if self.__isTime:
            self.__fa = fa

            self.__priStt = PeriodType.FULL
            if self.__isTime:
                vth = np.max(self.theta)
                if vth < 120 - 1.0e-6:
                    self.__priStt = PeriodType.DIV6
                elif vth < 180 - 1.0e-6:
                    self.__priStt = PeriodType.DIV3
                elif vth < 360 - 1.0e-6:
                    self.__priStt = PeriodType.HALF
        else:
            self.__fa = math.nan
            self.__priStt = PeriodType.FULL

    @property
    def datas(self) -> dict[str, npt.NDArray[np.float64]]:
        return self.__datas

    @property
    def theta(self) -> npt.NDArray[np.float64] | float:
        if self.__isTime and not np.isnan(self.__fa):
            return self.__datas["Time"] * self.__fa * 360
        else:
            return np.nan

    @property
    def names(self) -> list[str]:
        return self.__names

    @property
    def units(self) -> dict[str, str]:
        return self.__units

    @property
    def freq(self) -> float:
        return self.__fa

    @property
    def periodType(self) -> PeriodType | None:
        return self.__priStt

    def __getstate__(self):
        return {k: self.__dict__[k] for k in self.__dict__}

    def __setstate__(self, state: Any) -> None:
        for sn in state:
            self.__dict__[sn] = state[sn]
        return

    def toDict(self) -> dict:
        """AxisMagDataオブジェクトを辞書形式に変換"""
        return {
            "names": self.__names,
            "units": self.__units,
            "datas": {
                k: v.tolist() for k, v in self.__datas.items()
            },  # NumPy配列をリストに変換
            "freq": self.__fa,
            "isTime": self.__isTime,
            "periodType": self.__priStt.name if self.__priStt else None,
        }

    @staticmethod
    def fromDict(data: dict | None) -> AxisMagData:
        """辞書形式のデータからAxisMagDataオブジェクトを生成"""
        names = data["names"]
        units = list(data["units"].values())
        datas = [np.array(v, dtype=np.float64) for v in data["datas"].values()]
        fa = data["freq"]
        obj = AxisMagData(names, units, datas, fa)
        obj.__isTime = data["isTime"]
        obj.__priStt = (
            PeriodType[data["periodType"]] if data["periodType"] else None
        )
        return obj

    def saveToJsonFile(self, file_path: str) -> None:
        """AxisMagDataオブジェクトをJSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def loadFromJsonFile(file_path: str) -> AxisMagData:
        """JSONファイルからAxisMagDataオブジェクトを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AxisMagData.fromDict(data)


class MagData:
    _dtype: str  #  JMag ResultTableから取得した名前（単位除去
    _unit: str
    _names: list[str]
    _data: npt.NDArray[np.float64]  # npt.NDArray[np.float64]

    def __init__(
        self,
        dt: str,
        data: npt.NDArray[np.float64],
        names: list[str],
        uname: str,
        isZdel=True,
    ) -> None:
        if data.shape[0] != len(names):
            print(
                f"@@@@@ Data and Names are not same length:{len(data):4}"
                f" <-> {len(names):4}"
            )

        self._dtype = dt
        self._data = data
        self._names = names
        self._unit = uname

    @property
    def dName(self) -> str:
        return self._dtype

    @property
    def uName(self) -> str:
        return self._unit

    @property
    def colNames(self) -> list[str]:
        return self._names

    @property
    def dataSize(self) -> npt.NDArray:
        return np.array(self._data.shape)

    @property
    def data(self) -> npt.NDArray[np.float64]:
        return self._data

    def toDict(self) -> dict:
        """MagDataオブジェクトを辞書形式に変換"""
        return {
            "dtype": self._dtype,
            "unit": self._unit,
            "names": self._names,
            "data": self._data.tolist(),  # NumPy配列をリストに変換
        }

    @staticmethod
    def fromDict(data: dict) -> MagData:
        """辞書形式のデータからMagDataオブジェクトを生成"""
        dtype = data["dtype"]
        unit = data["unit"]
        names = data["names"]
        array_data = np.array(
            data["data"], dtype=np.float64
        )  # リストをNumPy配列に変換
        return MagData(dtype, array_data, names, unit)

    def saveToJsonFile(self, file_path: str) -> None:
        """MagDataオブジェクトをJSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def loadFromJsonFile(file_path: str) -> MagData:
        """JSONファイルからMagDataオブジェクトを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MagData.fromDict(data)


class ExtractedMagDatas:
    __axTime: AxisMagData | None
    __axFreq: AxisMagData | None
    __timeDatas: dict[str, MagData]
    __freqDatas: dict[str, MagData]
    subName: str

    def __init__(self):
        self.__axTime = None
        self.__axFreq = None
        self.__timeDatas = dict()
        self.__freqDatas = dict()
        self.subName = ""

    def clear(self) -> None:
        self.__axTime = None
        self.__axFreq = None
        self.__timeDatas.clear()
        self.__freqDatas.clear()
        self.subName = ""

    def setTimeAxis(
        self,
        ds: list[npt.NDArray[np.float64]],
        ns: tuple[list[str], list[str]],
        fa: float = 1000 * 8 / 120,
    ) -> None:
        self.__axTime = AxisMagData(ns[0], ns[1], ds, fa)

    def setFreqAxis(
        self,
        ds: list[npt.NDArray[np.float64]],
        ns: tuple[list[str], list[str]],
    ) -> None:
        self.__axFreq = AxisMagData(ns[0], ns[1], ds)

    def setTimeData(
        self, n: str, d: npt.NDArray[np.float64], dns: list[str], un: str
    ) -> int:
        dt = MagData(n, d, dns, un)
        if n in self.__timeDatas:
            print(f"***** Data already Exist:{n}")
        self.__timeDatas[n] = dt
        return len(self.__timeDatas)

    def setFreqData(
        self, n: str, d: npt.NDArray[np.float64], dns: list[str], un: str
    ) -> int:
        dt = MagData(n, d, dns, un)
        if n in self.__timeDatas:
            print(f"***** Data already Exist:{n}")
        self.__freqDatas[n] = dt
        return len(self.__freqDatas)

    @property
    def axTime(self) -> AxisMagData | None:
        return self.__axTime

    @property
    def axFreq(self) -> AxisMagData | None:
        return self.__axFreq

    @property
    def times(self) -> npt.NDArray | float:
        if self.__axTime is not None:
            return self.__axTime.datas["Time"]
        return np.nan

    @property
    def thetas(self) -> npt.NDArray | float:
        return self.__axTime.theta if self.__axTime else np.nan

    @property
    def freqs(self) -> npt.NDArray | float:
        if self.__axFreq is None:
            return np.nan
        return self.__axFreq.datas["Hz"]

    @property
    def datStep(self) -> dict[str, MagData]:
        return self.__timeDatas

    @property
    def datFreq(self) -> dict[str, MagData]:
        return self.__freqDatas

    def __getstate__(self):
        return {k: self.__dict__[k] for k in self.__dict__}

    def __setstate__(self, state: Any) -> None:
        for sn in state:
            self.__dict__[sn] = state[sn]
        return

    def toDict(self) -> dict:
        """ExtractedMagDatasオブジェクトを辞書形式に変換"""
        return {
            "axTime": self.__axTime.toDict() if self.__axTime else None,
            "axFreq": self.__axFreq.toDict() if self.__axFreq else None,
            "timeDatas": {k: v.toDict() for k, v in self.__timeDatas.items()},
            "freqDatas": {k: v.toDict() for k, v in self.__freqDatas.items()},
            "subName": self.subName,
        }

    @staticmethod
    def fromDict(
        data: dict, tgt: ExtractedMagDatas | None = None
    ) -> ExtractedMagDatas:
        """辞書形式のデータからExtractedMagDatasオブジェクトを生成"""
        if tgt is not None:
            obj = tgt
        else:
            obj = ExtractedMagDatas()

        obj.__axTime = None
        if data["axTime"]:
            obj.__axTime = AxisMagData.fromDict(data["axTime"])
        obj.__axFreq = None
        if data["axFreq"]:
            obj.__axFreq = AxisMagData.fromDict(data["axFreq"])
        obj.__timeDatas.clear()
        obj.__timeDatas = {
            k: MagData.fromDict(v) if len(v) > 0 else {}
            for k, v in data["timeDatas"].items()
        }
        obj.__freqDatas.clear()
        obj.__freqDatas = {
            k: MagData.fromDict(v) if len(v) > 0 else {}
            for k, v in data["freqDatas"].items()
        }
        obj.subName = data["subName"]
        return obj

    # @staticmethod
    # def fromDict(
    #     data: dict[str, Any], tgt: ExtractedMagDatas | None = None
    # ) -> ExtractedMagDatas:
    #     """辞書形式のデータからExtractedMagDatasオブジェクトを生成"""
    #     if tgt is not None:
    #         obj = tgt
    #     else:
    #         obj = ExtractedMagDatas()
    #     obj.__axTime = (
    #         AxisMagData.fromDict(data["axTime"]) if data["axTime"] else None
    #     )
    #     obj.__axFreq = (
    #         AxisMagData.fromDict(data["axFreq"]) if data["axFreq"] else None
    #     )
    #     d = data.get("timeDatas", {})
    #     if len(d) > 0:
    #         d: dict[str, dict] = data["timeDatas"]
    #         obj.__timeDatas = {
    #             k: MagData.fromDict(v) for k, v in d.items() if len(v) > 0
    #         }
    #     else:
    #         obj.__timeDatas.clear()
    #     d = data.get("freqDatas", {})
    #     if len(d) > 0:
    #         d: dict[str, dict] = data["freqDatas"]
    #         obj.__freqDatas = {
    #             k: MagData.fromDict(v) for k, v in d.items() if len(v) > 0
    #         }
    #     else:
    #         obj.__freqDatas.clear()
    #     obj.subName = data["subName"]
    #     return obj

    def saveToJsonFile(self, file_path: str) -> None:
        """ExtractedMagDatasオブジェクトをJSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def loadFromJsonFile(file_path: str) -> ExtractedMagDatas:
        """JSONファイルからExtractedMagDatasオブジェクトを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ExtractedMagDatas.fromDict(data)
