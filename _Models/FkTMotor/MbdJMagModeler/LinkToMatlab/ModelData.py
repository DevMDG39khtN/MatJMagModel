from __future__ import annotations

import matlab
import matlab.engine as me  # type: ignore
import numpy as np
import numpy.typing as npt

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
    def createModel(self, tgt: list[WorkCase], prm: MdlParameter, defMap: MdlMapDef) -> None:
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
            mMap = mo.MapDefinition(  # type: ignore
                np.array((dm.dIdq.value, dm.dFdq.value)),
                (dm.axTrqs.values, dm.axNrpms.values, dm.axVdcs.values),
                np.array((dm.maxIa.value, dm.tdCoil.value)),
                dm.rLmtVdc.value,
                dm.isOvrMod,
                dm.nOrdFitMtl.value,
            )
            mo.workspace["defMap"] = mMap  # type: ignore

            d0 = tgt[0].data
            isSlice = tgt[0].isSlice
            hasSkew = tgt[0].hasSkew
            # データの初期データでsizeを設定 Case毎に変わるのは想定しない
            ids = np.array([d.valDQi for d in tgt])
            idC = mo.IndexDQ(ids.T)  # type: ignore
            if not d0.axTime:
                print("***** No Time Axis Data in WorkCase")
                return
            tAx = mo.AxisTime(  # type: ignore
                d0.axTime.datas["Time"], d0.axTime.freq
            )  # 時間軸
            fAx = mo.AxisFreq(d0.axFreq.datas["Hz"]) if d0.axFreq else None  # type: ignore # 周波数軸
            mPrm = mo.ModelParms(  # type: ignore
                float(prm.nP),
                prm.Ra,
                prm.maxIa,
                float(prm.nParaCoil),
                prm.mdlNrpm,
                prm.tmpAtRa,
            )

            mDst = mo.MotorModel(idC, tAx, fAx, mPrm, mMap, isSlice)  # type: ignore

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

            fnSetDataDomain = (mo.pySetTimeDataAtCase, mo.pySetFreqDataAtCase)  # type: ignore

            for ddIdx, ddName in enumerate(dataDomainName):
                kvNames = tvNames[ddName]  # 時間軸・周波数 データ名辞書
                for dNam in tNames[ddName]:  # dNam : 各データ名選択
                    print(f"++++++ {dNam} @ {ddName}  +++++++++++++++++++")
                    # 解析ケース毎　データマップテーブル作成
                    dd00 = (tgt[0].data.datStep, tgt[0].data.datFreq)[ddIdx]
                    if dNam not in dd00:
                        print(f"***** Base Data:[{dNam}] not found in [{ddName}]")
                        continue
                    # サイズ設定
                    dd0: MagData = dd00[dNam]  # MagData class
                    sz = tuple(dd0.dataSize.tolist() + [len(tgt)])
                    mData = np.empty(sz)
                    # Skew Dataのサイズ設定
                    thSks = list(tgt[0].skewedDatas.keys())
                    skDatas: dict[float, npt.NDArray[np.float64]] = {}
                    ncd = 0
                    for ks, ds in tgt[0].skewedDatas.items():
                        ds00 = (ds.data.datStep, ds.data.datFreq)[ddIdx]
                        if dNam not in ds00:
                            ncd += 1
                            # print("***** No Skewed Data at 0 Idx")
                            # skDatas[ks] = np.empty(sz)  # MagData class
                        else:
                            ds0 = ds00[dNam]  # MagData class
                            sz = tuple(ds0.dataSize.tolist() + [len(tgt)])
                            skDatas[ks] = np.empty(sz)  # MagData class
                    if ncd > 0:
                        print(f"***** No Skewed Data at 0 Idx: {ncd} / {len(thSks)}")

                    # データを mData にコピー
                    nskNG = 0
                    for i, d in enumerate(tgt):  # list[WorkCase]
                        # データの取得
                        tDat0 = (d.data.datStep, d.data.datFreq)[ddIdx]
                        if dNam not in tDat0:
                            print("***** No Base Data at id:[{i:04}]")
                            continue

                        tDat = tDat0[dNam]  # MagData class
                        mData[:, :, i] = tDat.data
                        # Skew Data
                        nsk1 = len(d.skewedDatas)
                        nks0 = len(skDatas)
                        if nsk1 != nks0:
                            # print(f"***** Mismatch Skew num. {nsk1}/{nks0}")
                            nskNG += 1
                            continue
                        skk = zip(d.skewedDatas.items(), skDatas.items())
                        for si0, thSkDs in enumerate(skk):
                            thSk = thSkDs[0][0]  # Skew angle
                            dSk = thSkDs[0][1]
                            thSk0 = thSkDs[1][0]
                            mSkData = thSkDs[1][1]  # Skewed MagData
                            tSkDat0s = (dSk.data.datStep, dSk.data.datFreq)
                            tSkDat = tSkDat0s[ddIdx][dNam]
                            if mSkData is None:
                                print(f"***** No Predefined Data @ [{si0:02}]")
                                continue
                            if not np.isclose(thSk, thSk0, rtol=1e-3, atol=1e-4):
                                inf0 = f"{thSk:.4f}/{thSk0:.4f} @ [{si0:02}]"
                                print(f"***** Mismatch Skew {inf0}")
                                continue
                            thSkDs[1][1][:, :, i] = tSkDat.data  # 更新
                        pass
                    ns = kvNames[dNam]
                    cns = dd0.colNames
                    # Matlab mDst 内の作成した Mag/LossData(ModelData) を返す
                    mMgd = fnSetDataDomain[ddIdx](mDst, ns, mData, cns)
                    if nskNG > 0:
                        print(f"***** some Mismatch Skew. [{nskNG:03}]{len(skDatas)}/{len(thSks)}")

                    if len(skDatas) == 0:
                        continue
                    mo.SetSkewedDataPy(  # type: ignore
                        mMgd, list(skDatas.keys()), list(skDatas.values())
                    )
                    pass
                pass
            pass
            mo.workspace["mMotData"] = mDst  # type: ignore

            skId = 0
            if not hasSkew or isSlice:
                skId = matlab.double([])

            MdlTrqMap, MdlFluxMap = mo.MappingModel(mDst, skId, nargout=2)  # type: ignore
            mo.workspace["MdlTrqMap"] = MdlTrqMap  # type: ignore
            mo.workspace["MdlFluxMap"] = MdlFluxMap  # type: ignore

            CntTrqReqMap, CntFdqDcpMap, CntLdqDMap, CntLdqSMap = mo.MappingController(
                mDst, skId, nargout=4
            )  # type: ignore
            mo.workspace["CntTrqReqMap"] = CntTrqReqMap  # type: ignore
            mo.workspace["CntFdqDcpMap"] = CntFdqDcpMap  # type: ignore
            mo.workspace["CntLdqDMap"] = CntLdqDMap  # type: ignore
            mo.workspace["CntLdqSMap"] = CntLdqSMap  # type: ignore
        except Exception as e:
            import traceback

            em = str(e)
            sm = traceback.format_exc()
            msg = f"実行エラー:{em}\n\n{sm}"
            print(f"***** Error in MATLAB processing: {msg}")
        finally:
            if mo:
                mo.quit()  # type: ignore # MATLABエンジンを終了
        print(">>>>> converting Data & creating Mbd Map Finished.\n\n")

        return
