from __future__ import annotations

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from Model.MdlWorkCaseGen import MdlWorkCaseGen
from View.CustomViewParts import QtAf, QtSp
from View.CustomWidgets import ValEdit

p1 = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
p2 = Qt.AlignmentFlag.AlignCenter


class GuiBaseCaseGenSets(QGroupBox):
    _mdl: MdlWorkCaseGen

    def __init__(
        self,
        m: MdlWorkCaseGen,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("基本領域設定", parent)

        self._mdl = m

        w = self
        w.setSizePolicy(QtSp.Fixed, QtSp.Fixed)

        lv0 = QVBoxLayout(w)
        w.setLayout(lv0)

        lg0 = QGridLayout()
        lv0.addLayout(lg0)
        lg0.addWidget(QLabel("Min."), 0, 0, 1, 3, alignment=p2)
        lg0.addWidget(QLabel("Max."), 0, 5, alignment=p2)
        lg0.addWidget(QLabel("Step."), 0, 8, alignment=p2)

        lg0.addWidget(QLabel("Id:"), 1, 0)

        lg0.addWidget(ValEdit(m.baseIdRange.min, wf=60), 1, 1)
        lg0.addWidget(QLabel("[A]"), 1, 2)

        lg0.addWidget(QLabel(" / "), 1, 3)
        lg0.addWidget(QLabel(" "), 1, 4)
        lg0.addWidget(ValEdit(m.baseIdRange.max, wf=60), 1, 5)

        lg0.addWidget(QLabel("[A]"), 1, 6)

        lg0.addWidget(QLabel(" / "), 1, 7)
        lg0.addWidget(ValEdit(m.baseIdRange.step, wf=60), 1, 8)
        lg0.addWidget(QLabel("[A]"), 1, 9)

        lg0.addWidget(QLabel("Iq:"), 2, 0)
        lg0.addWidget(ValEdit(m.baseIqRange.min, wf=60), 2, 1)
        lg0.addWidget(QLabel("[A]"), 2, 2)

        lg0.addWidget(QLabel(" / "), 2, 3)
        lg0.addWidget(QLabel(""), 2, 4)
        lg0.addWidget(ValEdit(m.baseIqRange.max, wf=60), 2, 5)
        lg0.addWidget(QLabel("[A]"), 2, 6)

        lg0.addWidget(QLabel(" / "), 2, 7)
        lg0.addWidget(ValEdit(m.baseIqRange.step, wf=60), 2, 8)
        lg0.addWidget(QLabel("[A]"), 2, 9)

        # Reduce Range
        lg0.addWidget(QLabel("maxIa:"), 1, 10)
        te0 = ValEdit(m.maxIa, wf=60)
        te0.setReadOnly(True)
        te0.setEnabled(False)
        lg0.addWidget(te0, 1, 11)
        lg0.addWidget(QLabel("Arms"), 1, 12)
        lg0.addWidget(
            QLabel("x :"), 2, 10, alignment=QtAf.AlignRight | QtAf.AlignVCenter
        )
        te1 = ValEdit(m.kMaxIa, wf=60)
        te1.setEnabled(False)
        lg0.addWidget(te1, 2, 11)

        def _onChangeState(s: Qt.CheckState) -> None:
            stt = s == Qt.CheckState.Checked.value
            te1.setEnabled(stt)
            m.isReduce = stt

        cb0 = QCheckBox("Reduce")
        cb0.stateChanged.connect(lambda s: _onChangeState(s))
        m.onChangeState.connect(
            lambda s: cb0.setCheckState(
                Qt.CheckState.Checked if s else Qt.CheckState.Unchecked
            )
        )
        cb0.setChecked(m.isReduce)
        lg0.addWidget(cb0, 0, 10, 1, 3, QtAf.AlignCenter)

        return
