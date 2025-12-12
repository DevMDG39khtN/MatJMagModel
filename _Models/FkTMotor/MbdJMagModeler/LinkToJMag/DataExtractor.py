from __future__ import annotations

import os
import re
from enum import Enum, auto
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


class SttExtract(Enum):
    Stop = auto()
    Continue = auto()
    Incomplete = auto()
    Extracted = auto()


class DataExtractor:
    _dPrms: dict[str, DesignParameter]

    datNames = [
        "Torque",
        "LineCurrent",
        "FEMCoilFlux",
        "TerminalVoltage",
        "VoltageDifference",
        # "FEMCoilInductance",
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

    # >>>>>> Skew 設定 #########
    ############################################
    @staticmethod
    # def isMultiSlice(s: jd.Study) -> list[float] | None:
    def isMultiSlice(
        s: jd.Study,
    ) -> tuple[list[float], int, float]:
        numCnds = s.NumConditions()
        tCnd: jd.Condition | None = None
        for i in range(numCnds):
            tCnd = s.GetCondition(i)
            if tCnd.GetType() == "複数断面":
                break

        # tCnd = s.GetCondition("MultiSlice")
        if not tCnd or not tCnd.IsValid():
            return ([], 0, 0.0)
        retNum = int(tCnd.GetValue("NumberOfSlices"))
        thSkew = tCnd.GetValue("SkewAngle")

        rets = np.array([float(retNum - 1) / 2 - i for i in range(retNum)]) * thSkew / (retNum - 1)

        dTbl: jd.DesignTable = s.GetDesignTable()
        npl = 1
        isp = False
        if dTbl.IsValid():
            id = dTbl.GetParameterIndex("nPole")
            if id >= 0:
                np0 = int(str(dTbl.GetValue(0, id)))
                if np0 > 0 and np0 % 2 == 0:
                    npl = np0 / 2
                    isp = True
        if not isp:
            print("@@@@@ Not have Pole Number Parameter")

        return (rets.tolist(), retNum, thSkew * float(npl))

    # <<<<< Skew 設定 ##########

    @staticmethod
    def getParmValues(
        tgt: jd.Study, prmNames: list[str], ntCases: int = 0
    ) -> dict[str, float | None]:
        """Get Parameter Values from JMag Study"""
        dTbl: jd.DesignTable = tgt.GetDesignTable()
        ret = {}
        for tpn in prmNames:
            if dTbl.HasEquation(tpn):
                # 方程式の値を取得
                id = dTbl.GetParameterIndex(tpn)
                ret[tpn] = dTbl.GetValue(ntCases, id)
            else:
                ret[tpn] = None

        return ret

    @staticmethod
    def getParams(tgt: jd.Study, dNams: list[str] | None = None) -> dict[str, DesignParameter]:
        dTbl: jd.DesignTable = tgt.GetDesignTable()
        np = dTbl.NumParameters()

        # 方程式抽出関数
        def getEquation(i: int) -> tuple[str, DesignParameter | None]:
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
            print(f">>>>> Set Parameter [Idx:{i:03}, prmIdx:{eqIdx:03}] Name:{eqName}")
            return eqName, DesignParameter(eq, eqIdx)

        prms = {nam: prm for nam, prm in [getEquation(i) for i in range(np)] if prm is not None}
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
        dPrmNames = ["Id", "Iq", "ThMOff"]
        sPrmNames = ["nPole", "nSpd"]
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
            vals = np.array([[src.GetValue(i, j) for j in range(nc)] for i in range(nr)])
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
                    if t0s.shape != vTms.shape or not np.allclose(t0s, vTms, 1e-6):
                        print(f"@@@@@ Time Data is not matched: {t0s.shape} != {vTms.shape}")
                        stt = False
                # 電流の場合は，UVW相データのみ選択
                fLst = [i for i, n in enumerate(dcns) if re.match("[UVW]-Phase", n)]
                if len(fLst) > 0:
                    dcns = [dcns[i] for i in fLst]
                    vals = vals[:, fLst]

                dest.setTimeData(nd, vals.T, dcns, unVal)  # 転置して格納
            else:
                if dest.axFreq is None:
                    dest.setFreqAxis([vTms, noStps], (["Hz", "No."], [unTime, ""]))
                else:
                    t0s = dest.axFreq.datas["Hz"]
                    if t0s.shape != vTms.shape or not np.allclose(t0s, vTms, 1e-6):
                        print(f"@@@@@ Freq Data is not matched: {t0s.shape} != {vTms.shape}")
                        stt = False
                dest.setFreqData(nd, vals.T, dcns, unVal)  # 転置して格納

            return stt

        def caseExtract(
            idxCaseTgt: int,
            wc: WorkCase,
            psi: StudyInfo,
            dPrms: dict[str, DesignParameter],
            sPrms: dict[str, DesignParameter],
            dTbl: jd.DesignTable,
            tStd: jd.Study,
            numSlice: int = 0,
        ) -> SttExtract:
            """各解析ケースのデータを取得する"""
            nonlocal num
            num += 1
            isStt = True

            if isStop is not None and isStop():
                print(">>>>>> return Each Extracting Data.")
                return SttExtract.Stop
            if onPrg is not None:
                onPrg(1)

            if wc.status == WorkStatus.Extracted:
                print(
                    f">>>>> Already Extracted [{wc.prmVals}] "
                    f"@ Case No. {wc.caseNo:4} / {idxCaseTgt:4}"
                )
                return SttExtract.Continue

            if not wc.StudyInfo or not wc.prjInfo:
                print(f"@@@@@ Not have a LinkInfo[{wc.status}] @  {wc.caseNo:3}:{wc.prmVals}")
                isStt = False
                return SttExtract.Continue
            p0 = wc.prjInfo.path if wc.prjInfo else ""
            p1 = psi.prjInfo.path if psi.prjInfo else ""
            if wc.studyName != psi.name or p0 != p1:
                print(f"@@@@@ Unmatch LinkInfo[{wc.status}] @  {wc.caseNo:3}:{wc.prmVals}")
                isStt = False
                return SttExtract.Continue
            if idxCaseTgt != wc.caseNo:
                print(f"@@@@@ CaseNo. is not matched: {wc.caseNo:04} -> {idxCaseTgt:04}")
                isStt = False
                return SttExtract.Continue

            print(f">>>>> Extracting Study: {wc.studyName}")
            pvs = [float(str(dTbl.GetValue(idxCaseTgt, d.dIdx))) for k, d in sPrms.items()]
            if len(pvs) < 2:
                print(f"@@@@@ Not have All Parameters: {len(sPrms)}")
                isStt = False
                return SttExtract.Continue
            fa = pvs[0] * pvs[1] / 120.0

            if len(dPrms) < len(dPrmNames):
                print(f"@@@@@ Not have All Parameters: {len(dPrms)}")
                isStt = False
                return SttExtract.Continue
            # ケースパラメータ値取得 文字列で返されるので注意
            pvs = [float(str(dTbl.GetValue(idxCaseTgt, dPrms[dn].dIdx))) for dn in dPrmNames]
            if not np.allclose(pvs, list(wc.prmVals), atol=1.0e-5, rtol=1.0e-3):
                print(f"@@@@@ Unmatched condition : {pvs}")
                ncCase = dTbl.NumCases()
                ncOld = idxCaseTgt
                for nc0 in range(ncCase):
                    pvs0 = [float(str(dTbl.GetValue(nc0, dPrms[dn].dIdx))) for dn in dPrmNames]
                    if np.allclose(pvs0, list(wc.prmVals), atol=1.0e-5, rtol=1.0e-3):
                        print(f">>>>>>> Found at Another Case : {pvs}")
                        idxCaseTgt = nc0
                        wc.caseNo = idxCaseTgt
                        break
                if idxCaseTgt == ncOld:
                    print(f"@@@@@ No Found Condition : {pvs}")
                    isStt = False
                    return SttExtract.Continue

            # ケースを選択し　必要ならばデータ読み込み
            tStd.SetCurrentCase(idxCaseTgt)  # 0 Origin
            cn = wc.caseNo + 1
            if not tStd.HasResult():
                print(f">>>>> No Result. Try to Read. @ CaseNo:{cn:4}")
                tStd.CheckForCaseResults()
                if not tStd.HasResult():
                    print(f"@@@@@ No Result. @ CaseNo:{cn:4}")
                    isStt = False
                    return SttExtract.Continue
                else:
                    print(">>>>>>>>>>> above Case Data Found !!!!!!")

                wc.status = WorkStatus.Analyzed
            rTbl = tStd.GetResultTable()

            def setResultData(
                rTblData: jd.ResultTableData,
                wc: WorkCase,
                isTime: bool = True,
                fa: float = 0.0,
            ) -> bool:
                """解析結果データを設定する"""
                if not rTblData.IsValid():
                    print(f"@@@@@@@@@@@@@@ Invalid DataSet  {mdtName:>30} @ CaseNo: {cn:4}")
                    return False
                return setData(rTblData, wc.data, isTime, fa)

            # 各解析結果（Step）
            # for i, mdtName in enumerate(DataExtractor.datNames):
            for mdtName in DataExtractor.datNames:
                print(f">>>>> Extracting JMag Time Data {mdtName:>30} @ CaseNo: {cn:4}")
                rTblData = rTbl.GetData(mdtName)  # ResultTable use
                isStt0 = setResultData(rTblData, wc, True, fa)
                isStt = isStt and isStt0
                # if i > 2:
                #     continue
                if mdtName in ("TerminalVoltage", "VoltageDifference") and numSlice > 0:
                    continue
                skWcs = list(wc.skewedDatas.values())
                # 断面設定時のSkewデータ取得
                for ns in range(numSlice):
                    rtSkData = rTbl.GetDataFromName(mdtName, f" <断面 {ns + 1}>")
                    print(f">>>>> ----- Skew[{ns + 1:3}] Time Data {mdtName:>30} @ CaseNo: {cn:4}")
                    isStt0 = setResultData(rtSkData, skWcs[ns], True, fa)
                    isStt = isStt and isStt0

            # 鉄損解析結果取得
            for mdtName in DataExtractor.irDatNames:
                print(f">>>>> Extracting JMag Freq Data {mdtName:>30} @ CaseNo: {cn:4}")
                rTblData = rTbl.GetData(mdtName)  # ResultTable use
                isStt0 = setResultData(rTblData, wc, False)
                isStt = isStt and isStt0
                skWcs = list(wc.skewedDatas.values())
                # 断面設定時のSkewデータ取得
                for ns in range(numSlice):
                    rtSkData = rTbl.GetDataFromName(mdtName, f" <断面 {ns + 1}>")
                    print(f">>>>> ----- Skew[{ns + 1:3}] Freq Data {mdtName:>30} @ CaseNo: {cn:4}")
                    isStt0 = setResultData(rtSkData, skWcs[ns], False)
                    isStt = isStt and isStt0
            wc.status = WorkStatus.Extracted if isStt else WorkStatus.InComplete
            print(f">>>>> Finish to extract data {wc.status.name}")
            return SttExtract.Extracted if isStt else SttExtract.Incomplete

        def eachExtract(
            rqDts: list[WorkCase],
            psi: StudyInfo,
            dPrms: dict[str, DesignParameter],
            sPrms: dict[str, DesignParameter],
            tStd: jd.Study,
        ) -> tuple[SttExtract, bool]:
            """各解析ケースのデータを取得する"""
            nonlocal num
            # 各解析ケースのデータ取得
            dTbl = tStd.GetDesignTable()
            ncCase = dTbl.NumCases()

            skThs, nSk, thSk = DataExtractor.isMultiSlice(tStd)
            nnn = len(rqDts) if nSk > 1 else sum([1 + w.nDivSkew for w in rqDts])

            if ncCase != nnn:
                print(f"@@@@@ Mismatch Case No: {len(rqDts)}/ {ncCase}")
                return (SttExtract.Continue, False)

            ncNo = 0
            isStt = True
            for wc in rqDts:
                num += 1
                if nSk > 0:
                    if not np.allclose(skThs, list(wc.skewedDatas.keys()), 1e-3, 1e-5):
                        print("@@@@@ Mismatch Skewed Data ")
                stt = caseExtract(ncNo, wc, psi, dPrms, sPrms, dTbl, tStd, nSk)
                isStt = isStt and (stt == SttExtract.Extracted)
                ncNo += 1
                if nSk == 0:
                    # 断面設定無時，skewData数から以降の解析ケース取得
                    for _, skWc in wc.skewedDatas.items():
                        stt = caseExtract(ncNo, skWc, psi, dPrms, sPrms, dTbl, tStd)
                        isStt = isStt and (stt == SttExtract.Extracted)
                        ncNo += 1
                        if stt == SttExtract.Stop:
                            break
                if stt == SttExtract.Stop:
                    print("******** Stop Extracting Data ********")
                    break

            print(f">>>>> Finish to extract data {wc.status.name}")
            return (stt, isStt)

        n = 0
        stt = False
        app = None
        if mdl.isAppOK:
            app = mdl._app

        nAppRst = 0
        for i, psi in enumerate(lnkInfos):
            if app is None:
                app = jd.designer.CreateApplication()  # type: ignore

            if isStop is not None and isStop():
                print(">>>>>> return Extracting Data.")
                return False
            tfn = psi.prjInfo.path if psi and psi.prjInfo else ""
            if not os.path.isfile(tfn):
                print(f"@@@@@ Not Found File: {os.path.basename(tfn)}")
                continue
            app.Load(tfn)
            tStd = app.GetStudy(psi.name)
            if tStd is None or not tStd.IsValid():
                ns = psi.prjInfo.name if psi.prjInfo else ""
                print(f"@@@@@ Not Found Study: {psi.name} @ {ns}")
                continue

            tpFn = psi.prjInfo.path if psi and psi.prjInfo else ""
            if not os.path.isfile(tpFn):
                print(f"@@@@@ Not Found Project: {os.path.basename(tpFn)}")
                continue
            rqDts = [wc for wc in rqDts0 if (wc.prjInfo.path if wc.prjInfo else "") == tpFn]
            nc0 = len([wc for wc in rqDts if wc.studyName != psi.name])
            nc1 = len([wc for wc in rqDts if wc.grpIdx == (i + 1)])
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

            stt, isStt = eachExtract(rqDts, psi, dPrms, sPrms, tStd)

            nAppRst = (nAppRst + 1) % 5
            if nAppRst == 0:
                app.Quit()
                app = None

            if stt == SttExtract.Stop:
                break
            pass

        if app is not None:
            bPath = mdl.BasePrjPath.Path
            app.Load(bPath)
        print(f">>>>> Finish to extract data: {n} cases")
        return isStt
