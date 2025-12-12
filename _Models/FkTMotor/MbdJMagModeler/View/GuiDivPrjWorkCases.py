from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal

# from typing import TYPE_CHECKING
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from Model.MdlJMagAnlPrjGen import DivStatus, MdlJMagAnlPrjGen
from Model.MdlWorkCaseGen import ItemExtGenWorkCase

QSP = QSizePolicy.Policy
QAF = Qt.AlignmentFlag


class GuiDivPrjWorkCases(QWidget):
    _css = """
QGroupBox {
    border: 2px solid black;
    border-radius: 10px;
    font: bold;
    padding: 5px;
    margin-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center; /* タイトルの位置を中央に設定 */
        padding: 0 3px; /* タイトルのパディングを設定 */
    }
"""
    __vPat = r"[+-]?\d+(\.\d*)?"  # 数値マッチ
    __rPat = rf"({__vPat})(:({__vPat})){{0,2}}"  # 数値範囲マッチ
    __tPat = rf"({__rPat})(,({__rPat}))*"  # 数値範囲リスト
    __mPat = rf"{__tPat}((;{__tPat})*);?"
    __mPat = r"\s*([1-9]\d*)\s*(,(\s*([1-9]\d*)\s*))*"
    __reo = re.compile(__mPat)

    def _chkText(self, txt: str) -> bool:
        return bool(self.__reo.fullmatch(txt))

    onGenAnlFile = Signal()

    _mdl: MdlJMagAnlPrjGen
    _validator: QIntValidator = QIntValidator(1, 200)

    def _setLayout(self):
        m = self._mdl

        self.setStyleSheet(self._css)

        lvb0 = QVBoxLayout(self)

        wgb0 = QGroupBox("Project Analysis Case Division", self)
        lvb0.addWidget(wgb0)
        wgl0 = QGridLayout(wgb0)
        self.setLayout(wgl0)

        wck0 = QCheckBox("電流条件分割", self)
        wgl0.addWidget(wck0, 0, 0, QAF.AlignVCenter)

        wCmb = QComboBox(self)
        wgl0.addWidget(wCmb, 0, 1, QAF.AlignVCenter)
        wCmb.addItems(["Id/Iq 分割数", "IaRms 分割数", "IaRms 指定"])
        wCmb.setCurrentIndex(0)

        wl0 = QLabel("分割数:")
        wgl0.addWidget(wl0, 0, 2, QAF.AlignVCenter)
        we0 = QLineEdit()
        wgl0.addWidget(we0, 0, 3, QAF.AlignVCenter)
        we0.setPlaceholderText("---")
        we0.setFixedWidth(60)
        we0.setSizePolicy(QSP.Fixed, QSP.Fixed)
        we0.setAlignment(QAF.AlignRight | QAF.AlignVCenter)

        def _onChangedTextDiv(s: str) -> None:
            if (
                self._validator.validate(s, 0)[0]
                == QIntValidator.State.Acceptable
            ):
                we0.setStyleSheet("")
            else:
                we0.setStyleSheet("QLineEdit { background: #fcc; }")

        we0.textChanged.connect(lambda s: _onChangedTextDiv(s))

        def _toSetDivNum(s: str) -> None:
            if (
                self._validator.validate(s, 0)[0]
                == QIntValidator.State.Acceptable
            ):
                self._mdl.numDivPrj = int(s)
            return

        we0.textEdited.connect(lambda s: _toSetDivNum(s))
        self._mdl.onChangedNumDiv.connect(
            lambda s: we0.setText(str(s) if s is not None and s > 0 else "")
        )
        if self._mdl.numDivPrj is not None and self._mdl.numDivPrj > 0:
            we0.setText(str(self._mdl.numDivPrj))

        wl1 = QLabel("IaRms:", alignment=QAF.AlignVCenter)
        wgl0.addWidget(wl1, 0, 2, QAF.AlignVCenter)
        wl1.setVisible(False)
        we1 = QLineEdit()
        wgl0.addWidget(we1, 0, 3, 1, 3, QAF.AlignVCenter)
        we1.setVisible(False)
        we1.setPlaceholderText("---")
        we1.setAlignment(QAF.AlignRight | QAF.AlignVCenter)
        we1.setSizePolicy(QSP.Expanding, QSP.Fixed)
        we1.setMinimumWidth(250)
        we1.setMaximumWidth(400)

        def _onChangedTextDivList(s: str) -> None:
            if ItemExtGenWorkCase.chkSetText(s):
                we1.setStyleSheet("")
            else:
                we1.setStyleSheet("QLineEdit { background: #fcc; }")

        we1.textChanged.connect(lambda s: _onChangedTextDivList(s))

        def _onChangedListDivList(s: str) -> None:
            if s is not None or len(s) > 0:
                if self._chkText(s):
                    d = [int(i) for i in re.sub(r"\s+", "", s).split(",")]
                    self._mdl.lstDivPrj = d
            return

        we1.textEdited.connect(lambda s: _onChangedListDivList(s))
        self._mdl.onChangedDivList.connect(
            lambda s: we1.setText(
                ", ".join([str(i) for i in s])
                if s is not None and len(s) > 0
                else ""
            )
        )

        wChk0 = QCheckBox("拡張分割", self)
        wgl0.addWidget(wChk0, 1, 2, 1, 2, QAF.AlignVCenter)
        wChk0.stateChanged.connect(
            lambda s: m.setIsExtSplitPrj(s == Qt.CheckState.Checked.value)
        )
        m.onChangedIsExtSplit.connect(lambda s: wChk0.setChecked(s))
        wChk0.setChecked(m.isExSplit)
        wChk0.setEnabled(m.isDivPrj)

        wChk1 = QCheckBox("界磁分割", self)
        wgl0.addWidget(wChk1, 1, 4, 1, 2, QAF.AlignVCenter)
        wChk1.stateChanged.connect(
            lambda s: m.setIsFwSplitPrj(s == Qt.CheckState.Checked.value)
        )
        m.onChangedIsFwSplit.connect(lambda s: wChk1.setChecked(s))
        wChk1.setChecked(m.isFwSplit)
        wChk1.setEnabled(m.isDivPrj)

        def _onSwitchSetDivPrj(stt: int):
            s0 = wck0.isChecked()
            s1 = DivStatus(stt)
            vStt = s1 != DivStatus.IaRmsVals
            wl0.setVisible(vStt and s0)
            we0.setVisible(vStt and s0)
            we0.setEnabled(vStt and s0)
            wl1.setVisible(not vStt and s0)
            we1.setVisible(not vStt and s0)
            we1.setEnabled(not vStt and s0)
            wChk0.setEnabled(s0)
            wChk1.setEnabled(s0)

            self._mdl.sttDivPrj = DivStatus(stt)
            return

        wCmb.currentIndexChanged.connect(lambda s: _onSwitchSetDivPrj(s))
        self._mdl.onChangedDivStt.connect(lambda s: wCmb.setCurrentIndex(s))
        wCmb.setCurrentIndex(int(self._mdl.sttDivPrj))

        def _onSetIsDivPrj(stt: bool):
            wCmb.setEnabled(stt)
            self._mdl.isDivPrj = stt
            _onSwitchSetDivPrj(wCmb.currentIndex())

        wck0.stateChanged.connect(
            lambda s: _onSetIsDivPrj(s == Qt.CheckState.Checked.value)
        )
        self._mdl.onChangedIsDivPrj.connect(lambda s: wck0.setChecked(s))
        wck0.setChecked(self._mdl.isDivPrj)

        d = self._mdl.lstDivPrj
        if d is not None and len(d) > 0:
            t = ", ".join([str(i) for i in d])
            we1.setText(t)

        wgl0.addItem(QSpacerItem(0, 0, QSP.MinimumExpanding, QSP.Fixed), 0, 6)

        _onSetIsDivPrj(wck0.isChecked())

    def __init__(self, m: MdlJMagAnlPrjGen, parent=None) -> None:
        super().__init__(parent)
        self._mdl = m
        self._setLayout()
