from __future__ import annotations

import os
import re
from typing import Callable, Optional

import jmag.designer as jd
import numpy as np

import JMagDatas.ModelJMagMBD as Model
from JMagDatas.JmagData import ExtractedMagDatas
from JMagDatas.WorkCase import StudyInfo, WorkCase, WorkStatus


class DesignParameter:
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


class DataExtractor:
    _dPrms: dict[str, DesignParameter]

    datNames = [
        "Torque",
        "LineCurrent",
        "FEMCoilFlux",
        "TerminalVoltage",
        "VoltageDifference",
        "FEMCoilInductance",
    ]
    irDatNames = [
        "IronLoss_IronLoss",
        "HysteresisLoss_IronLoss",
        "JouleLoss_IronLoss",
    ]

    _pNum: int
    _dPrms: dict[str, DesignParameter]

    def __init__(self, tgt: jd.Study | None) -> None:
        self._dPrms = {}
        self._pNum = 0

        if tgt is not None:
            self._dPrms = self.getParams(tgt)
        return

    @staticmethod
    def getParams(
        tgt: jd.Study, dNams: list[str] | None = None
    ) -> dict[str, DesignParameter]:
        dTbl: jd.DesignTable = tgt.GetDesignTable()
        np = dTbl.NumParameters()

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
                f">>>>> Set Parameter [Idx:{i:03}, "
                f"prmIdx:{eqIdx:03}] Name:{eqName}"
            )
            return eqName, DesignParameter(eq, eqIdx)

        prms = {
            nam: prm
            for nam, prm in [getEquation(i) for i in range(np)]
            if prm is not None
        }
        if dNams is not None:
            prms = {k: v for k, v in prms.items() if k in dNams}

        return prms

    @staticmethod
    def Extract(
        rqDts0: list[WorkCase],
        lnkInfos: list[StudyInfo],
        mdl: Model.ModelJMagMBD,
        onPrg: Optional[Callable[[int], None]] = None,
        isStop: Optional[Callable[[], bool]] = None,
    ) -> bool:
        dPrmNames = ["Id", "Iq"]
        sPrmNames = ["nP", "Nrpm"]
        num = 0

        def setData(
            src: jd.ResultTableData,
            dest: ExtractedMagDatas,
            isTime: bool = True,
            fa: float = 0.0,
        ) -> bool:
            nc = src.GetCols()
            nr = src.GetRows()
            nd = src.GetName().split(":", 1)[0].strip()
            nds = [s.strip() for s in nd.split(" ", 1)]
            if len(nds) > 1:
                dest.subName = nds[1]
            nd = nds[0]
            dcns = [src.GetColName(i) for i in range(nc)]
            noStps = np.array([src.GetStep(i) for i in range(nr)])

            # 軸データの設定
            # 単位文字列
            unTime: str = src.GetTimeUnit()
            unTheta: str = src.GetAngleUnit()
            unVal: str = src.GetValueUnit()

            vTms0 = np.array([[src.GetTime(i) for i in range(nr)]]).T
            vThms = np.array([[src.GetAngle(i) for i in range(nr)]]).T
            vals = np.array(
                [[src.GetValue(i, j) for j in range(nc)] for i in range(nr)]
            )
            vTms = vTms0 - vTms0[0]

            stt = True
            if isTime:
                if dest.axTime is None:
                    dest.setTimeAxis(
                        [vTms, vThms, noStps],
                        (["Time", "ThMec", "noStep"], [unTime, unTheta, ""]),
                        fa,
                    )
                else:
                    t0s = dest.axTime.datas["Time"]
                    if t0s.shape != vTms.shape or not np.allclose(
                        t0s, vTms, 1e-6
                    ):
                        print(
                            "@@@@@ Time Data is not matched: "
                            f"{t0s.shape} != {vTms.shape}"
                        )
                        stt = False
                # 電流の場合は，UVW相データのみ選択
                fLst = [
                    i for i, n in enumerate(dcns) if re.match("Coil [UVW]", n)
                ]
                if len(fLst) > 0:
                    dcns = [dcns[i] for i in fLst]
                    vals = vals[:, fLst]

                dest.setTimeData(nd, vals.T, dcns, unVal)  # 転置して格納
            else:
                if dest.axFreq is None:
                    dest.setFreqAxis(
                        [vTms, noStps], (["Hz", "No."], [unTime, ""])
                    )
                else:
                    t0s = dest.axFreq.datas["Hz"]
                    if t0s.shape != vTms.shape or not np.allclose(
                        t0s, vTms, 1e-6
                    ):
                        print(
                            "@@@@@ Freq Data is not matched:"
                            f" {t0s.shape} != {vTms.shape}"
                        )
                        stt = False
                dest.setFreqData(nd, vals.T, dcns, unVal)  # 転置して格納

            return stt

        def eachExtract(
            rqDts: list[WorkCase],
            psi: StudyInfo,
            dPrms: dict[str, DesignParameter],
            sPrms: dict[str, DesignParameter],
        ) -> bool:
            """各解析ケースのデータを取得する"""
            nonlocal num
            # 各解析ケースのデータ取得
            dTbl = tStd.GetDesignTable()
            ncCase = dTbl.NumCases()

            if ncCase != len(rqDts):
                print(f"@@@@@ Unmatch Case No: {len(rqDts)}/ {ncCase}")
                return False

            isStt = True
            for i, wc in enumerate(rqDts):
                num += 1
                if isStop is not None and isStop():
                    print(">>>>>> return Each Extracting Data.")
                    return False

                if wc.status == WorkStatus.Extracted:
                    print(
                        f">>>>> Already Extracted [{wc.prmVals}] "
                        f"@ Case No. {wc.caseNo:4} / {i + 1:4}"
                    )
                    continue

                if onPrg is not None:
                    onPrg(1)

                if not wc.StudyInfo or not wc.prjInfo:
                    print(
                        f"@@@@@ Not have a LinkInfo[{wc.status}] "
                        f"@  {wc.caseNo:3}:{wc.prmVals}"
                    )
                    isStt = False
                    continue
                if (
                    wc.studyName != psi.name
                    or wc.prjInfo.path != psi.prjInfo.path
                ):
                    print(
                        f"@@@@@ Unmatch LinkInfo[{wc.status}] "
                        f"@  {wc.caseNo:3}:{wc.prmVals}"
                    )
                    isStt = False
                    continue
                if i != wc.caseNo:
                    print(
                        f"@@@@@ CaseNo. is not matched: {wc.caseNo} -> {i + 1}"
                    )
                    isStt = False
                    continue

                print(f">>>>> Extracting Study: {wc.studyName}")
                pvs = [
                    float(dTbl.GetValue(i, d.dIdx)) for k, d in sPrms.items()
                ]
                if len(pvs) < 2:
                    print(f"@@@@@ Not have All Parameters: {len(sPrms)}")
                    isStt = False
                    continue
                fa = pvs[0] * pvs[1] / 120.0

                if len(dPrms) < len(dPrmNames):
                    print(f"@@@@@ Not have All Parameters: {len(dPrms)}")
                    isStt = False
                    continue
                # ケースパラメータ値取得 文字列で返されるので注意
                pvs = [
                    float(dTbl.GetValue(i, dPrms[dn].dIdx)) for dn in dPrmNames
                ]
                if not np.allclose(pvs, wc.prmVals, atol=1.0e-6):
                    print(f"@@@@@ Unmatched condition : {pvs}")
                    isStt = False
                    continue

                # ケースを選択し　必要ならばデータ読み込み
                tStd.SetCurrentCase(i)  # 0 Origin
                cn = wc.caseNo + 1
                if not tStd.HasResult():
                    print(f">>>>> No Result. Try to Read. @ CaseNo:{cn:4}")
                    tStd.CheckForCaseResults()
                    if not tStd.HasResult():
                        print(f"@@@@@ No Result. @ CaseNo:{cn:4}")
                        isStt = False
                        continue
                    else:
                        print(">>>>>>>>>>> above Case Data Found !!!!!!")

                    wc.status = WorkStatus.Analyzed
                rTbl = tStd.GetResultTable()
                # 各解析結果（Step）
                for mdtName in DataExtractor.datNames:
                    print(
                        f">>>>> Extracting JMag Time Data {mdtName:>30} "
                        f"@ CaseNo: {cn:4}"
                    )
                    rTblData = rTbl.GetData(mdtName)  # ResultTable use
                    if not rTblData.IsValid():
                        print(
                            f"@@@@@@@@@@@@@@ Invalid DataSet  {mdtName:>30} "
                            f"@ CaseNo: {cn:4}"
                        )
                        isStt = False
                        continue
                    if not setData(rTblData, wc.data, True, fa):
                        print(
                            f"@@@@@@@@@@@@@@ Fail to extract  {mdtName:>30} "
                            f"@ CaseNo: {cn:4}"
                        )
                        isStt = False
                        continue

                # 鉄損解析結果取得
                for mdtName in DataExtractor.irDatNames:
                    print(
                        f">>>>> Extracting JMag Freq Data {mdtName:>30} "
                        f"@ CaseNo: {cn:4}"
                    )
                    rTblData = rTbl.GetData(mdtName)  # ResultTable use
                    if not rTblData.IsValid():
                        print(
                            f"@@@@@@@@@@@@@@ Invalid DataSet  {mdtName:>30} "
                            f"@ CaseNo: {cn:4}"
                        )
                        isStt = False
                        continue
                    if not setData(rTblData, wc.data, False):
                        print(
                            f"@@@@@@@@@@@@@@ Fail to extract  {mdtName:>30} "
                            f"@ CaseNo: {cn:4}"
                        )
                        isStt = False
                        continue
                wc.status = WorkStatus.Extracted
                print(f">>>>> Finish to extract data {wc.status.name}")
            return isStt

        n = 0
        stt = False
        app = None
        if mdl.isAppOK:
            app = mdl._app

        nAppRst = 0
        if onPrg is not None:
            onPrg(0)
        for i, psi in enumerate(lnkInfos):
            if app is None:
                app = jd.designer.CreateApplication()

            if isStop is not None and isStop():
                print(">>>>>> return Extracting Data.")
                return False
            tfn = psi.prjInfo.path
            if not os.path.isfile(tfn):
                print(f"@@@@@ Not Found File: {os.path.basename(tfn)}")
                continue
            app.Load(tfn)
            tStd = app.GetStudy(psi.name)
            if tStd is None or not tStd.IsValid():
                print(
                    f"@@@@@ Not Found Study: {psi.name} @ {psi.prjInfo.name}"
                )
                continue

            rqDts = [
                wc
                for wc in rqDts0
                if wc.prjInfo.path == psi.prjInfo.path
                and wc.status == WorkStatus.Defined
            ]
            nc0 = sum([wc for wc in rqDts if wc.studyName != psi.name])
            nc1 = sum([wc for wc in rqDts if wc.grpIdx == (i + 1)])
            if nc0 > 0 or nc1 > 0:
                print(f"@@@@@ Not Extract All Items: {nc0} / {nc1}")
                continue
            rqDts = sorted(rqDts, key=lambda x: x.caseNo)
            nt = len(rqDts)
            n += nt

            print(f">>>>> Extracting Study: {psi.name}")
            sPrms = DataExtractor.getParams(tStd, sPrmNames)
            if len(sPrms) < 2:
                print(f"@@@@@ Not have All Parameters: {len(sPrms)}")
            dPrms = DataExtractor.getParams(tStd, dPrmNames)
            if len(dPrms) < len(dPrmNames):
                print(f"@@@@@ Not have All Parameters: {len(dPrms)}")

            if len(rqDts) == 0:
                print(f">>>>> No WorkCase to Extract @ {psi.name}")
                if onPrg is not None:
                    onPrg(0)
                continue
            stt = eachExtract(rqDts, psi, dPrms, sPrms)
            nAppRst = (nAppRst + 1) % 5
            if nAppRst == 0:
                app.Quit()
                app = None
            pass

        if app is not None:
            bPath = mdl.BasePrjPath.Path
            app.Load(bPath)
        print(f">>>>> Finish to extract data: {n} cases")
        return stt
