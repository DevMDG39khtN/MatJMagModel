from __future__ import annotations

from math import sqrt

import matplotlib
import matplotlib.patches
import matplotlib.pyplot as plt
from matplotlib.collections import PathCollection

matplotlib.use("QtAgg")

import matplotlib.patches as patches
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from JMagDatas.AxesContents import Axis2D, MotAxes
from JMagDatas.WorkCase import WorkCase, WorkStatus
from Model.MdlWorkCaseStore import MdlWorkCaseStore

plt.ion()

matplotlib.set_loglevel("warning")


class CnvPlotDefinedIdqArea(FigureCanvasQTAgg):
    _axes: Axes
    _fig: Figure
    _pDatas: list[PathCollection]

    def __init__(
        self,
        width: int = 5,
        height: int = 4,
        dpi: int = 300,
        fig: Figure | None = None,
        parent: QWidget | None = None,
    ):
        self._pDatas = [None for _ in range(5)]
        if fig is None:
            fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self._fig = fig
        self._axes = fig.add_subplot(1, 1, 1)
        fig.tight_layout()

    def plotDQ0(self, data, xAxis, yAxis):
        self._axes.set_title("Idq", fontsize=20)  # グラフタイトル
        self._axes.set_xlabel("d-Axis")
        self._axes.set_ylabel("q-Axis")

    def plotDQ(
        self,
        xd: list[float],
        yd: list[float],
        ecs: list[str],
        fcs: list[str],
        lws: list[float],
        maxIa: float | None = 600.0,
    ):
        for ax in self._fig.get_axes():
            self._fig.delaxes(ax)

        self._axes = self._fig.add_subplot(1, 1, 1)

        self._axes.cla()
        self._axes.relim()
        self._axes.invert_xaxis()
        self._axes.set_aspect("equal")
        self._axes.axhline(0, lw=1, c="k")
        self._axes.axvline(0, lw=1, c="k")
        self._axes.grid(True)
        if maxIa is not None:
            rad = sqrt(3) * maxIa
            c = patches.Arc(
                xy=(0.0, 0.0),
                theta1=90.0,
                theta2=180.0,
                width=2 * rad,
                height=2 * rad,
                ec="m",
                lw=2,
                transform=self._axes.transData,
            )
            self._axes.add_patch(c)

        self._pDatas[0] = self._axes.scatter(
            # xd, yd, facecolors="none", edgecolors="r", lw=2, s=30
            xd,
            yd,
            facecolors=fcs,
            edgecolors=ecs,
            lw=lws,
            s=30,
        )

        self._axes.set_title("Id-Iq Input Sets", fontsize=20)  # グラフタイトル
        self._axes.set_xlabel("d-Axis")
        self._axes.set_ylabel("q-Axis")

        self._fig.tight_layout()
        self._axes.autoscale(enable=True, axis="both", tight=None)
        self._axes.autoscale_view()
        self.draw()

        pass


class GuiPlotWorkSetsArea(QWidget):
    _pltCnvs: CnvPlotDefinedIdqArea
    _model: MdlWorkCaseStore

    def __init__(
        self, mdl: MdlWorkCaseStore, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._model = mdl
        layout = QVBoxLayout()
        self.setLayout(layout)
        pltCnvs = CnvPlotDefinedIdqArea(width=5, height=4, dpi=100)
        self._pltCnvs = pltCnvs
        toolbar: NavigationToolbar = NavigationToolbar(pltCnvs, self)
        layout.addWidget(pltCnvs)
        layout.addWidget(toolbar)

        mdl.onPlotRequested.connect(lambda: self.plotDQ())
        QTimer.singleShot(0, self.plotDQ)

    _maxIa: float = 600.0

    @property
    def maxIa(self) -> float:
        return self._maxIa

    @maxIa.setter
    def maxIa(self, v: float):
        if self._maxIa != v:
            self._maxIa = v
            self.plotDQ()

    @Slot(float)
    def toMaxIaFromIdq(self, v: float):
        v = v / sqrt(3)
        self.maxIa = v

    @Slot()
    def plotDQ(self):
        dList: list[WorkCase] = self._model.dataList
        xd = [d.vals[MotAxes.DQ][Axis2D.CX] for d in dList]
        yd = [d.vals[MotAxes.DQ][Axis2D.RY] for d in dList]
        fcs = ["blue" if not d.isExtArea else "c" for d in dList]
        ecs = [
            "blue"
            if not d.isExtArea and d.status >= WorkStatus.Defined
            else "c"
            if d.isExtArea and d.status >= WorkStatus.Defined
            else "red"
            if d.status <= WorkStatus.Defined and not d.isExtArea
            else "m"
            for d in dList
        ]
        fcs = [
            "blue"
            if not d.isExtArea and d.status >= WorkStatus.Extracted
            else "c"
            if d.isExtArea and d.status >= WorkStatus.Extracted
            else "none"
            for d in dList
        ]
        lws = [2 if d.status > WorkStatus.Created else 1 for d in dList]
        cnvs: CnvPlotDefinedIdqArea = self._pltCnvs
        cnvs.plotDQ(xd, yd, ecs, fcs, lws, self._maxIa)
