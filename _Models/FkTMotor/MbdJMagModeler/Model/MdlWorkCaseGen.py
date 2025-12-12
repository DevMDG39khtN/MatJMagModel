from __future__ import annotations

import json

import numpy as np
import numpy.typing as npt
from PySide6.QtCore import QObject, QSettings, Signal, Slot

from Model.BaseMdlWorkCaseGen import BaseMdlWorkCaseGen
from Model.ItemExtGenWorkCase import ItemExtGenWorkCase
from Model.MdlWorkCaseStore import MdlWorkCaseStore
from Model.Numeric import NumericRange, NumVal


class MdlWorkCaseGen(BaseMdlWorkCaseGen):
    _srcMdl: MdlWorkCaseStore

    _baseIdRange: NumericRange
    _baseIqRange: NumericRange
    _maxIa: NumVal
    _kMaxIa: NumVal
    _isReduce: bool
    # ._dList はBaseMdlWorkCaseGen で初期化

    # region Methods
    ########################################################
    def genCases(
        self,
        isMod=False,
        nDivSk: int = 0,
        thSk: float = 0.0,
        isSlice: bool = False,
    ) -> None:
        # get Ext. Id-Iq Axis Data List

        if not isMod:
            self._srcMdl.clrData()

        bIdq0 = np.array([wc.valDQi for wc in self._srcMdl.dataList])
        if len(bIdq0) == 0:
            bIdq0 = np.empty((0, 2))
        bIdqSets0 = self._genBaseIdIqSets(bIdq0)
        if len(bIdqSets0) == 0:
            bIdqSets0 = np.empty((0, 2))
        bIdq1 = np.vstack((bIdq0, bIdqSets0))
        eIdqSets0 = self._genExtIdIqSets(bIdq1)

        bIdqSets: list[tuple[float, float]] = list(map(tuple, bIdqSets0.tolist()))
        eIdqSets: list[tuple[float, float]] = list(map(tuple, eIdqSets0.tolist()))

        self._srcMdl.addIdqDatas(bIdqSets, eIdqSets, nDivSk, thSk, isSlice)
        return

    ########################################################
    def _genBaseIdIqSets(self, base: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        # ) -> list[tuple[float, float]]:
        vbAxIds = self._baseIdRange.valList
        vbAxIqs = self._baseIqRange.valList
        [mIds, mIqs] = np.meshgrid(vbAxIds, vbAxIqs)
        mIas: npt.NDArray[np.float64] = np.sqrt((mIds**2 + mIqs**2) / 3)
        if self._isReduce:
            kIa0 = self._kMaxIa.value
            kIa = float(kIa0) if kIa0 is not None else 1.0
            maxIa0 = self._maxIa.value
            maxIa = float(maxIa0) if maxIa0 is not None else 1.0
            lmtIa = kIa * maxIa

            ids = mIas > lmtIa
            ids[-1, 0] = False  # Remain on Corner Point

            mIds[ids] = np.nan
            mIqs[ids] = np.nan
        else:
            ids = np.zeros(mIas.shape, dtype=bool)

        mfs0 = np.stack((mIds[~ids].ravel(), mIqs[~ids].ravel())).T
        mfs = np.array(sorted(mfs0, key=lambda x: (x[0], x[1])))
        r = np.array(
            [
                v
                for i, v in enumerate(mfs)
                if not any(
                    np.all(
                        np.isclose(mfs[:i, :], v, rtol=1.0e-3, atol=1.0e-5),
                        axis=1,
                    )
                )
            ]
        )

        print(f">>>> Base Idq Sets Defined: {len(r)} / rejected {mIds.size - len(r)}")
        if base.size == 0:
            return r
        else:
            fr = ~np.any(
                np.all(np.isclose(r[:, None, :], base[None, :, :]), axis=-1),
                axis=1,
            )
            rr = r
            r = rr[fr]
            # ret: list[tuple[float, float]] = list(map(tuple, r.tolist()))
            return r

    ########################################################
    def _genExtIdIqSets(self, base: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        # ) -> list[tuple[float, float]]:
        axs = self.extAxDataLists
        exSets0 = np.empty((0, 2), dtype=float)
        for ax0 in axs:
            for axd in ax0[0]:
                for axq in ax0[1]:
                    [mIds, mIqs] = np.meshgrid(axd, axq)
                    ex0 = np.stack([mIds.ravel(), mIqs.ravel()]).T
                    exSets0 = np.vstack((exSets0, ex0))

        exSets1 = np.array(sorted(exSets0, key=lambda x: (x[0], x[1])))
        exSets2 = np.array(
            [
                v
                for i, v in enumerate(exSets1)
                if not any(
                    np.all(
                        np.isclose(exSets1[:i, :], v, rtol=1.0e-3, atol=1.0e-5),
                        axis=1,
                    )
                )
            ]
        )

        if base.size == 0:
            exSets = exSets2
        else:
            if exSets2.size > 1:
                fr = ~np.any(
                    np.all(
                        np.isclose(exSets2[:, None, :], base[None, :, :]),
                        axis=-1,
                    ),
                    axis=1,
                )
                exSets = exSets2[fr]
            else:
                exSets = exSets2
            if exSets.size < 2:
                exSets = np.empty((0, 2), dtype=float)
        print(f">>>> Ext Idq Sets Removed Dup.: {len(exSets)} <- {len(exSets0)}")
        # ret: list[tuple[float, float]] = list(map(tuple, exSets.tolist()))
        return exSets

    ########################################################
    def __init__(
        self,
        m: MdlWorkCaseStore,
        p: QObject | None = None,
    ) -> None:
        super().__init__(p)
        self._srcMdl = m

        self._baseIdRange = NumericRange(NumVal(), NumVal(), NumVal())
        self._baseIqRange = NumericRange(NumVal(), NumVal(), NumVal())
        self._maxIa = NumVal()
        self._kMaxIa = NumVal()
        self._isReduce = False

        # self._dList はBaseMdlWorkCaseGen で初期化

        return

    # endregion

    # region Serialize/Deserialize
    ########################################################
    def toDict(self) -> dict:
        """MdlWorkCaseGen オブジェクトを辞書形式に変換"""
        return {
            "baseData": {
                "baseIdRange": self._baseIdRange.toDict(),
                "baseIqRange": self._baseIqRange.toDict(),
                "maxIa": self._maxIa.toDict(),
                "kMaxIa": self._kMaxIa.toDict(),
                "isReduce": self._isReduce,
            },
            "extData": [ed.toDict() for ed in self._dList],
        }

    ########################################################
    def _setBaseData(self, data: dict) -> None:
        nro = NumericRange.fromDict(data["baseIdRange"])
        self._baseIdRange.min.text = nro.min.text
        self._baseIdRange.max.text = nro.max.text
        self._baseIdRange.step.text = nro.step.text
        nro = NumericRange.fromDict(data["baseIqRange"])
        self._baseIqRange.min.text = nro.min.text
        self._baseIqRange.max.text = nro.max.text
        self._baseIqRange.step.text = nro.step.text
        nro = NumVal.fromDict(data["maxIa"])
        self._maxIa.text = nro.text
        self._maxIa = NumVal.fromDict(data["maxIa"])
        nro = NumVal.fromDict(data["kMaxIa"])
        self._kMaxIa.text = nro.text
        self.isReduce = data["isReduce"]

    ########################################################
    @staticmethod
    def fromDict(
        data: dict,
        mdl: MdlWorkCaseStore,
        p: QObject,
        tgt: MdlWorkCaseGen | None = None,
    ) -> MdlWorkCaseGen:
        if tgt is not None:
            obj = tgt
        else:
            if p is None:
                raise Exception("WorkCaseGen. Creator needs WorkCaseStore.")
            obj = MdlWorkCaseGen(mdl, p)

        """辞書形式のデータから MdlWorkCaseGen オブジェクトを生成"""
        obj._setBaseData(data["baseData"])
        ndList = [ItemExtGenWorkCase.fromDict(d) for d in data["extData"]]
        obj.beginResetModel()
        obj._dList.clear()
        obj._dList.extend(ndList)
        obj.endResetModel()
        obj.layoutChanged.emit()
        return obj

    ########################################################
    def importJson(self, txt: str) -> MdlWorkCaseGen | None:
        dic = json.loads(txt)
        if dic is not None:
            return self.fromDict(dic, self._srcMdl, self.parent(), self)
        return None

    ########################################################
    def exportJson(self) -> str:
        return json.dumps(self.toDict(), ensure_ascii=False, indent=2)

    ########################################################
    def loadToJsonFile(self, fpath: str) -> None:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data is not None:
                self.fromDict(data, self._srcMdl, self.parent(), tgt=self)

    ########################################################
    def saveToJsonFile(self, fpath: str) -> None:
        """辞書形式のデータを JSON ファイルに保存"""
        with open(fpath, "w", encoding="utf-8") as f:
            # json.dump(datas, f, ensure_ascii=False, indent=2)
            json.dump(self.toDict(), f, ensure_ascii=False, indent=2)

    ########################################################
    def loadSettings(self, s: QSettings | None = None) -> None:
        if s is None:
            return
        s.beginGroup("WorkCaseGen")

        s.beginGroup("Base")
        s.beginGroup("IdRange")
        self._baseIdRange.loadSettings(s)
        s.endGroup()
        s.beginGroup("IqRange")
        self._baseIqRange.loadSettings(s)
        s.endGroup()
        s.beginGroup("MaxIa")
        self._maxIa.loadSettings(s)
        s.endGroup()
        s.beginGroup("kMaxIa")
        self._kMaxIa.loadSettings(s)
        s.endGroup()
        self._isReduce = bool(s.value("isReduce", False, bool))
        s.endGroup()

        s.beginGroup("ExtArea")
        n = s.beginReadArray("Items")
        self._dList.clear()
        for i in range(n):
            s.setArrayIndex(i)
            d = ItemExtGenWorkCase()
            d.loadSettings(s)
            self._dList.append(d)
        s.endArray()
        s.endGroup()

        s.endGroup()

    ########################################################
    def saveSettings(self, s: QSettings | None = None) -> None:
        if s is None:
            return
        s.beginGroup("WorkCaseGen")
        s.remove("")

        s.beginGroup("Base")
        s.beginGroup("IdRange")
        self._baseIdRange.saveSettings(s)
        s.endGroup()
        s.beginGroup("IqRange")
        self._baseIqRange.saveSettings(s)
        s.endGroup()
        s.beginGroup("MaxIa")
        self._maxIa.saveSettings(s)
        s.endGroup()
        s.beginGroup("kMaxIa")
        self._kMaxIa.saveSettings(s)
        s.endGroup()
        s.setValue("isReduce", self._isReduce)
        s.endGroup()

        s.beginGroup("ExtArea")
        s.beginWriteArray("Items", len(self._dList))
        for i, d in enumerate(self._dList):
            s.setArrayIndex(i)
            d.saveSettings(s)
        s.endArray()
        s.endGroup()

        s.endGroup()

    # endregion

    # region Slot
    ########################################################
    @Slot(float)
    def upDataMaxIa(self, v: str):
        self._maxIa.text = v

    # region Properties

    ########################################################
    @property
    def extAxDataLists(self) -> list[tuple[list[float], list[float]]]:
        ret = [d._dataList() for d in self._dList if d.isValid]
        return ret

    ########################################################
    @property
    def srcWCSMdl(self) -> MdlWorkCaseStore:
        return self._srcMdl

    ########################################################
    @property
    def baseIdRange(self) -> NumericRange:
        return self._baseIdRange

    ########################################################
    @property
    def baseIqRange(self) -> NumericRange:
        return self._baseIqRange

    ########################################################
    @property
    def maxIa(self) -> NumVal:
        return self._maxIa

    ########################################################
    @property
    def kMaxIa(self) -> NumVal:
        return self._kMaxIa

    ########################################################
    @property
    def isReduce(self) -> bool:
        return self._isReduce

    onChangeState = Signal(bool)

    ########################################################
    @isReduce.setter
    def isReduce(self, stt: bool) -> None:
        if self._isReduce == stt:
            return
        self._isReduce = stt
        self.onChangeState.emit(self._isReduce)

    # endregion
