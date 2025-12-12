from __future__ import annotations

import copy
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import jmag.designer as jd
from PySide6.QtCore import QSettings


@dataclass(frozen=True)
class FileTimes:
    Created: datetime
    Updated: datetime
    Accessed: datetime


class JMagPrjFileInfo:
    __fnTimes = (os.path.getctime, os.path.getmtime, os.path.getatime)
    _basePrjPath: str
    # _idx: int
    _path: str
    _size: int
    _times: tuple[datetime, datetime, datetime]
    _uuid: str
    _hysUpdate: list[datetime]
    _hysAccess: list[datetime]
    _hysName: list[str]
    _hysPath: list[str]
    _hysSize: list[int]

    @classmethod
    def _getTimes(cls, path: str) -> tuple[datetime, ...]:
        po = Path(path)
        return tuple(
            datetime(*time.localtime(fn(po))[:6]) for fn in cls.__fnTimes
        )

    def __init__(
        self, path: str = "", bPath: str = "", isRecovery: bool = False
    ) -> None:
        # if not isRecovery:
        if path is not None and len(path) > 0 and not isRecovery:
            if not os.path.isfile(path):
                return

            po = Path(path)

            self._path = path
            self._basePrjPath = bPath
            self._size = os.path.getsize(path)
            self._times = (  # Updated, Accessed, Created
                datetime(*time.localtime(os.path.getmtime(po))[:6]),
                datetime(*time.localtime(os.path.getatime(po))[:6]),
                datetime(*time.localtime(os.path.getctime(po))[:6]),
            )

            self._uuid = ""

            self._hysUpdate = [self._times[0]]
            self._hysAccess = [self._times[1]]
            self._hysPath = [self._path]
            self._hysSize = [self._size]
            self._hysDirName = [os.path.dirname(path)]
            self._hysName = [os.path.basename(path)]
        else:
            self._path = path
            self._basePrjPath = bPath
            self._size = 0
            self._times = (datetime.now(), datetime.now(), datetime.now())
            self._uuid = ""
            self._hysUpdate = []
            self._hysAccess = []
            self._hysPath = []
            self._hysSize = []
            self._hysName = []
            self._hysDirName = []
        return

    def setUUID(self, app: jd.Application) -> bool:
        pPath = app.GetProjectPath()

        if not pPath:
            print("@@@@@ JMagDesigner is not loaded Project File.")
            return False
        if pPath != self._path:
            print("@@@@@ Mismatch loaded Project File.")
            return False
        self._uuid = app.GetUuid()
        return True

    def update(self, tPath: str) -> bool:
        if not os.path.isfile(self._path):
            print(f"@@@@@ Not Found: {self.name}")
            return False

        if self._path != tPath:
            self._hysPath.insert(0, self._path)
            self._path = tPath
            return True

        updFlgS = False

        nsz = os.path.getsize(self._path)
        if nsz != self._size:
            self._size = nsz
            self._hysSize.insert(0, self._size)
            updFlgS = True

        updFlgT = False
        nts: list[datetime] = []
        for i, t in enumerate(self._times):
            t0 = datetime(*time.localtime(self.__fnTimes[i](self._path))[:6])
            nts.append(t0)
            if i == 0 and t0 != t:
                print(f"@@@@@ {self.name} seems to be new file: {t} -> {t0}")
                return False
            else:
                if t0 != t:
                    updFlgT = True
        if updFlgT:
            self._times = (nts[0], nts[1], nts[2])
            if self._hysUpdate[0] != self._times[0]:
                self._hysUpdate.insert(0, self._times[0])
            if self._hysAccess[0] != self._times[1]:
                self._hysAccess.insert(0, self._times[1])
        return updFlgS and updFlgT

    @property
    def name(self) -> str:
        return os.path.basename(self._path) if os.path else ""

    @property
    def dirName(self) -> str:
        return os.path.dirname(self._path) if os.path else ""

    @property
    def path(self) -> str:
        return self._path

    @property
    def basePath(self) -> str:
        return self._basePrjPath

    @property
    def uuid(self) -> str:
        return self._uuid

    @uuid.setter
    def uuid(self, u: str) -> None:
        self._uuid = u
        return

    @property
    def size(self) -> int:
        return self._size

    @property
    def updTime(self) -> datetime:
        return self._times[0]

    @property
    def acsTime(self) -> datetime:
        return self._times[1]

    @property
    def crtTime(self) -> datetime:
        return self._times[2]

    def __setstate__(self, state: Any) -> None:
        for ss in state:
            self.__dict__[ss] = state[ss]
        if "_basePrjPath" not in self.__dict__:
            self._basePrjPath = ""
        return

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))
        return result

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, JMagPrjFileInfo):
            return False
        return self._path == o._path

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __repr__(self) -> str:
        # オブジェクト名を打つと返す
        bn = f"{os.path.basename(self._path):>50}"
        dn = f"{os.path.dirname(self._path)}"
        sn = f"{self._size / (1024**2):9.2f} Mb"
        tn = f"{self._times[0]}"
        return f"{bn}: {sn}/{tn} @ {dn}"

    def __str__(self) -> str:
        # 単体オブジェクトのprint で返す 　配列の場合，__repr__が呼ばれる
        bn = f"{os.path.basename(self._path)}"
        dn = f"{os.path.dirname(self._path)}"
        sn = f"{self._size / (1024**2)::9.2f} Mb"
        return (
            f"{bn} @ {dn}\n\t {sn}/Upd:{self._times[0]}"
            f", Use:{self._times[1]}, Ini:{self._times[2]}"
        )

    def saveSettings(self, s: QSettings | None) -> None:
        """JMagPrjFileInfoオブジェクトの設定を保存"""
        if s is None:
            return
        s.beginGroup("JMagPrjFileInfo")
        s.setValue("path", self._path)
        s.setValue("basePath", self._basePrjPath)
        s.setValue("size", self._size)
        s.setValue("uuid", self._uuid)
        # s.setValue("index", self._idx)
        s.beginGroup("times")
        s.setValue("updated", self._times[0].isoformat())
        s.setValue("accessed", self._times[1].isoformat())
        s.setValue("created", self._times[2].isoformat())
        s.endGroup()
        s.beginWriteArray("hysUpdated")
        for i, t in enumerate(self._hysUpdate):
            s.setArrayIndex(i)
            s.setValue("time", t.isoformat())
        s.endArray()
        s.beginWriteArray("hysAccess")
        for i, t in enumerate(self._hysAccess):
            s.setArrayIndex(i)
            s.setValue("time", t.isoformat())
        s.endArray()
        s.beginWriteArray("hysName")
        for i, t in enumerate(self._hysName):
            s.setArrayIndex(i)
            s.setValue("n", t)
        s.endArray()
        s.beginWriteArray("hysPath")
        for i, t in enumerate(self._hysPath):
            s.setArrayIndex(i)
            s.setValue("n", t)
        s.endArray()
        s.beginWriteArray("hysSize")
        for i, t in enumerate(self._hysSize):
            s.setArrayIndex(i)
            s.setValue("n", t)
        s.endArray()
        s.endGroup()

    def loadSettings(self, s: QSettings | None) -> None:
        """JMagPrjFileInfoオブジェクトの設定を読み込み"""
        if s is None:
            return
        s.beginGroup("JMagPrjFileInfo")
        self._path = s.value("path", "")
        self._basePrjPath = s.value("basePath", "")
        self._size = s.value("size", 0, int)
        self._uuid = s.value("uuid", "")
        s.beginGroup("times")
        t0 = s.value("updated", "")
        tt0 = datetime.fromisoformat(t0) if len(t0) > 0 else datetime.now()
        t1 = s.value("accessed", "")
        tt1 = datetime.fromisoformat(t1) if len(t1) > 0 else datetime.now()
        t2 = s.value("created", "")
        tt2 = datetime.fromisoformat(t2) if len(t2) > 0 else datetime.now()
        self._times = (tt0, tt1, tt2)
        s.endGroup()
        self._hysUpdate = []
        n = s.beginReadArray("hysUpdated")
        for i in range(n):
            s.setArrayIndex(i)
            t = s.value("time", "")
            self._hysUpdate.append(
                datetime.fromisoformat(t) if len(t) > 0 else datetime.now()
            )
        s.endArray()
        self._hysAccess = []
        n = s.beginReadArray("hysAccess")
        for i in range(n):
            s.setArrayIndex(i)
            t = s.value("time", "")
            self._hysAccess.append(
                datetime.fromisoformat(t) if len(t) > 0 else datetime.now()
            )
        s.endArray()
        self._hysName = []
        n = s.beginReadArray("hysName")
        for i in range(n):
            s.setArrayIndex(i)
            t = s.value("n", "")
            self._hysName.append(t)
        s.endArray()
        self._hysPath = []
        n = s.beginReadArray("hysPath")
        for i in range(n):
            s.setArrayIndex(i)
            t = s.value("n", "")
            self._hysPath.append(t)
        s.endArray()
        self._hysSize = []
        n = s.beginReadArray("hysSize")
        for i in range(n):
            s.setArrayIndex(i)
            t = s.value("n", 0, int)
            self._hysSize.append(t)
        s.endArray()
        s.endGroup()
        return

    def toDict(self) -> dict:
        """JMagPrjFileInfoオブジェクトを辞書形式に変換"""
        return {
            "path": self._path,
            "basePath": self._basePrjPath
            if "basePath" in self.__dict__
            else "",
            "size": self._size,
            "uuid": self._uuid,
            "times": {
                "updated": self._times[0].isoformat(),
                "accessed": self._times[1].isoformat(),
                "created": self._times[2].isoformat(),
            },
            "history": {
                "update": [t.isoformat() for t in self._hysUpdate],
                "access": [t.isoformat() for t in self._hysAccess],
                "path": self._hysPath,
                "size": self._hysSize,
                "name": self._hysName,
            },
        }

    @staticmethod
    def fromDict(
        data: dict, tgt: JMagPrjFileInfo | None = None
    ) -> JMagPrjFileInfo:
        """辞書形式のデータからJMagPrjFileInfoオブジェクトを生成"""
        if tgt is not None:
            obj = tgt
        else:
            if "basePath" in data:
                bPath = data["basePath"]
            else:
                bPath = ""

            obj = JMagPrjFileInfo(data["path"], bPath, True)

        obj._size = data["size"]
        obj._uuid = data["uuid"]
        # if "index" in data:
        #     obj._idx = data["index"]
        obj._times = (
            datetime.fromisoformat(data["times"]["updated"]),
            datetime.fromisoformat(data["times"]["accessed"]),
            datetime.fromisoformat(data["times"]["created"]),
        )
        obj._hysUpdate = [
            datetime.fromisoformat(t) for t in data["history"]["update"]
        ]
        obj._hysAccess = [
            datetime.fromisoformat(t) for t in data["history"]["access"]
        ]
        obj._hysPath = data["history"]["path"]
        obj._hysSize = data["history"]["size"]
        obj._hysName = data["history"]["name"]
        return obj

    def saveToJsonFile(self, file_path: str) -> None:
        """JMagPrjFileInfoオブジェクトをJSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.toDict(), f, indent=4, ensure_ascii=False)

    @staticmethod
    def loadFromJsonFile(file_path: str) -> JMagPrjFileInfo:
        """JSONファイルからJMagPrjFileInfoオブジェクトを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JMagPrjFileInfo.fromDict(data)
