from __future__ import annotations

# import logging
import matlab.engine as me  # type: ignore
import numpy as np

# from logging import FileHandler, Formatter, StreamHandler, getLogger
from JMagDatas.JmagData import MagData
from JMagDatas.WorkCase import WorkCase
from Model.MdlMapDef import MdlMapDef
from Model.MdlParameter import MdlParameter


class MatCnvDat:
    eng: me.MatlabEngine | me.FutureResult | None

    dDims = ["time", "spec", "Iq,", "Id"]

    def __init__(self):
        return

    ###########################################################################
    def createModel(
        self, tgt: list[WorkCase], prm: MdlParameter, defMap: MdlMapDef
    ) -> None:
        if not me.find_matlab():
            print("******* No MATLAB instances found")
            self.eng = None
            return
        else:
            self.eng = me.connect_matlab()
            print(">>>>>>> Connected to MATLAB <<<<<<<")
        try:
            mo = self.eng
            if mo is None:
                print("***** InValid Matlab Object.")
                return

            if len(tgt) <= 0:
                print("***** WorkCase Data is zero. No execution")
                return

            print(f">>>>> converting Data :[{len(tgt):5}] <<<<<<")

            # map軸の作成  出てきたId, Iq の全てを重複を削除して抽出
            vIds0, vIqs0 = zip(*[td.valDQi for td in tgt])

            dm = defMap
            mMap = mo.MapDefinition(
                np.array((dm.dIdq.value, dm.dFdq.value)),
                (dm.axTrqs.values, dm.axNrpms.values, dm.axVdcs.values),
                np.array((dm.maxIa.value, dm.tdCoil.value)),
                dm.rLmtVdc.value,
                dm.isOvrMod,
                dm.nOrdFitMtl.value,
            )
            mo.workspace["defMap"] = mMap

            d0 = tgt[0].data
            # データの初期データでsizeを設定 Case毎に変わるのは想定しない
            ids = np.array([d.valDQi for d in tgt])
            idC = mo.IndexDQ(ids.T)
            tAx = mo.AxisTime(
                d0.axTime.datas["Time"], d0.axTime.freq
            )  # 時間軸
            fAx = mo.AxisFreq(d0.axFreq.datas["Hz"])  # 周波数軸
            mPrm = mo.ModelParms(
                float(prm.nP),
                prm.Ra,
                prm.maxIa,
                float(prm.nParaCoil),
                prm.mdlNrpm,
                prm.tmpAtRa,
            )

            mDst = mo.MotorModel(idC, tAx, fAx, mPrm, mMap)

            # 時間軸，周波数軸の順に処理
            dataDomainName = ("TimeData", "FreqData")

            # 名前：データ名
            tNames = {
                k: ns
                for k, ns in zip(
                    dataDomainName,
                    (WorkCase.datIDNames, WorkCase.irDatIDNames),
                )
            }  # 日本語データ名
            tvNames = {
                k: nds
                for k, nds in zip(
                    dataDomainName,
                    (WorkCase.ddDnKeyToID, WorkCase.dlDnKeyToID),
                )
            }

            fnSetDataDomain = (mo.pySetTimeDataAtCase, mo.pySetFreqDataAtCase)

            for ddIdx, ddName in enumerate(dataDomainName):
                kvNames = tvNames[ddName]  # 時間軸・周波数 データ名辞書
                for dNam in tNames[ddName]:  # dNam : 各データ名選択
                    print(f"++++++ {dNam} @ {ddName}  +++++++++++++++++++")
                    # 解析ケース毎　データマップテーブル作成
                    dd00 = (tgt[0].data.datStep, tgt[0].data.datFreq)[ddIdx]
                    if dNam not in dd00:
                        print(
                            f"***** Base Data:[{dNam}] not found in [{ddName}]"
                        )
                        continue
                    # サイズ設定
                    dd0: MagData = dd00[dNam]  # MagData class
                    sz = tuple(dd0.dataSize.tolist() + [len(tgt)])
                    mData = np.empty(sz)
                    # データを mData にコピー
                    for i, d in enumerate(tgt):  # list[WorkCase]
                        # データの取得
                        tDat0 = (d.data.datStep, d.data.datFreq)[ddIdx]
                        if dNam not in tDat0:
                            print(
                                f"***** Data:[{dNam}] not found in [{ddName}]"
                            )
                            continue

                        tDat = tDat0[dNam]  # MagData class
                        mData[:, :, i] = tDat.data
                        pass
                    ns = kvNames[dNam]
                    cns = dd0.colNames
                    # Matlab mDst 内の作成した Mag/LossData(ModelData) を返す
                    fnSetDataDomain[ddIdx](mDst, ns, mData, cns)
                    pass
                pass
            pass
            mo.workspace["mMotData"] = mDst

            MdlTrqMap, MdlFluxMap = mo.MappingModel(mDst, nargout=2)
            mo.workspace["MdlTrqMap"] = MdlTrqMap
            mo.workspace["MdlFluxMap"] = MdlFluxMap

            CntTrqReqMap, CntFdqDcpMap, CntLdqDMap, CntLdqSMap = (
                mo.MappingController(mDst, nargout=4)
            )
            mo.workspace["CntTrqReqMap"] = CntTrqReqMap
            mo.workspace["CntFdqDcpMap"] = CntFdqDcpMap
            mo.workspace["CntLdqDMap"] = CntLdqDMap
            mo.workspace["CntLdqSMap"] = CntLdqSMap
        except Exception as e:
            print(f"***** Error in MATLAB processing: {e}")
        finally:
            mo.quit()  # MATLABエンジンを終了
        print(">>>>> converting Data & creating Mbd Map Finished.")

        return
