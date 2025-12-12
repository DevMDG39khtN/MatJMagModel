from __future__ import annotations

import math
from dataclasses import dataclass
from math import atan2, pi, sqrt

import jmag.designer as jd
import numpy as np
import numpy.typing as npt

from JMagDatas.WorkCase import WorkStatus


@dataclass
class JMagDesignParameter:
    name: str
    value: float
    dName: str
    dIdx: int
    isEqu: bool
    isGeo: bool
    info: str
    expr: str

    def __init__(self, oeq: jd.ParametricEquation, idx: int) -> None:
        self.name = oeq.GetName()
        self.value = oeq.GetValue()
        self.dName = oeq.GetDisplayName()
        self.info = oeq.GetDescription()
        self.isEqu = oeq.GetType() == 1
        self.expr = oeq.GetExpression()
        self.isGeo = oeq.GetModeling()
        self.dIdx = idx
        #  # Helpにはあるが，Python環境では存在しない
        # self.dIdx = oeq.GetDisplayIndex()


class SetData:
    pNames: list[str] = ["Id", "Iq", "ThMOff"]
    dIdqs: tuple[float, float]
    dIaFw: tuple[float, float]
    status: WorkStatus
    noCase: int
    sName: str
    fPath: str
    vals: dict[str, float]
    # >>>>>> FUKUTA 向け Skew 設定 #########
    dSthSkew: float
    # <<<<< FUKUTA 向け Skew 設定 ##########

    def __init__(self, vId: float, vIq: float, vThSk: float = 0.0):
        self.dSthSkew = vThSk

        self.dIdqs = (vId, vIq)
        vIa = sqrt((vId * vId + vIq * vIq) / 3)
        vFw = atan2(-vId, vIq) / pi * 180
        self.dIaFw = (vIa, vFw)
        self.status = WorkStatus.Created

        self.vals = {
            self.pNames[0]: vId,
            self.pNames[1]: vIq,
            self.pNames[2]: vThSk,
        }

        self.noCase = -1
        self.sName = ""
        self.fPath = ""

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        s0: str = f"[{self.noCase:04}] [{self.status.name:>8}]"
        s1: str = f"({self.dIdqs[0]:7.1f}, {self.dIdqs[1]:7.1f}, off:{self.dSthSkew:8.4f})"
        s2: str = f"({self.dIaFw[0]:8.2f}, Fw:{self.dIaFw[1]:8.3f})"
        return f"{s0} {s1} {s2}"


class JMagDataSet:
    pNames: list[str] = ["Id", "Iq", "IaRms", "Fw"]

    prmIdNo: list[int]

    datColNames: dict[str, list[str]]

    times: npt.NDArray[np.float64]
    angle: npt.NDArray[np.float64]
    datas: npt.NDArray[np.float64]

    params: dict[str, JMagDesignParameter]

    def __init__(self, tStudy: jd.Study) -> None:
        dTbl = tStudy.GetDesignTable()
        self._getPrms(dTbl)
        return

    def AddCase(self, tStudy: jd.Study, tData: list[SetData]) -> int:
        tgt = tData

        if len(tgt) < 1:
            print("@@@@@ No Data")
            return -1

        dTbl = tStudy.GetDesignTable()

        nc = dTbl.NumCases()
        nca = len(tgt) - nc
        dTbl.AddCases(nca)

        for i, sd in enumerate(tgt):
            cid = i
            for dn in sd.vals:
                v = sd.vals[dn]
                if dn not in self.params:
                    print(f"@@@@@ No Parameter: {dn}")
                    return -1
                otp = self.params[dn]
                npv = otp.dIdx
                cvn = dTbl.GetVariableName(npv)
                if cvn != dn:
                    print(f"@@@@@ Not Match: {dn} != {cvn}")
                    return -1
                if isinstance(v, str):
                    print(f"@@@@@ Not a Number: {v} @ {dn}")
                    return -1
                print(
                    f">>>>> Set Parameter [{dn:>8}]: {v:10.4f}  @ Case:{i:04}"
                )
                dTbl.SetValue(cid, npv, v)
                v0s = dTbl.GetValue(cid, npv)
                v0 = float(v0s)
                if not math.isclose(v, v0, abs_tol=1e-3):
                    print(
                        "@@@@@ Not Match Parameter Value: "
                        f"{v:10.4f} != {v0:10.4f}"
                    )
                    return -1
            sd.noCase = i
            sd.status = WorkStatus.Defined
        return 0

    def _getPrms(self, dTbl: jd.DesignTable) -> None:
        self.params = {}
        nPrms = dTbl.NumParameters()

        # 方程式抽出関数
        def getEquation(i: int) -> tuple[str, jd.ParametricEquation | None]:
            if not dTbl.ParameterTypeName(i) == "Equation":
                print(f"@@@@@ No Equation @ Idx:[{i:4}]")
                return "", None
            nam: str = dTbl.GetVariableName(i)
            if not dTbl.HasEquation(nam):
                print(f"@@@@@ Not have a Equation: [Idx:{i:4}] Name:{nam}")
                return "", None

            eq = dTbl.GetEquation(nam)
            eqName = eq.GetName()
            eqIdx = dTbl.GetParameterIndex(eqName)
            print(
                ">>>>> Set Parameter "
                f"[Idx:{i:03}, prmIdx:{eqIdx:03}] Name:{eqName}"
            )
            return eqName, JMagDesignParameter(eq, eqIdx)

        self.params = {
            nam: prm
            for nam, prm in [getEquation(i) for i in range(nPrms)]
            if prm is not None
        }

        print(f">>>>> Get Parameter {len(self.params):03}\n")
        return 0
