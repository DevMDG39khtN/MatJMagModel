"""モデルパラメータ設定画面"""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from Model.MdlParameter import MdlParameter


# ##################################
class GuiModelParameter(QWidget):
    """Model Parameter Setting View"""

    _css = """
QGroupBox {
    border: 2px solid black;
    border-radius: 10px;
    margin-top: 8px;
    padding: 0px;
    font: bold;
    }

QGroupBox::title {
    subcontrol-position: top left; /* タイトルの位置を調整 */
    left: 10px; /* タイトルの位置を調整 */
    top: -8px; /* タイトルの位置を調整 */
    padding: 0 3px;}
#ParamLayout {
    border: 1px solid black;
}
"""
    _settings: QSettings | None
    _prmTypes: dict[str, type]
    _editList: dict[str, QLineEdit]
    _checkList: dict[str, QCheckBox]

    # ##################################
    def onValueSet(self, pn: str, v: str) -> None:
        if pn in list(self._editList.keys()):
            self._editList[pn].setText(v)
        else:
            print(f"@@@ No defined Editable Parameter {pn}")

    # ##################################
    def onCheckSet(self, pn: str, v: bool) -> None:
        if pn in list(self._checkList.keys()):
            self._checkList[pn].setChecked(v)
        else:
            print(f"@@@ No defined Editable Parameter {pn}")

    # ##################################
    def onChkChanged(self, pn: str, state):
        if pn in list(self._checkList.keys()):
            setattr(self._model, pn, state == Qt.CheckState.Checked.value)
            self._checkList[pn].setChecked(state)
        else:
            print(f"@@@ No defined Checkable Parameter {pn}")

    # ##################################
    @Slot(str, str)
    def onValueEdited(self, pn: str, vs: str) -> None:
        if pn in self._prmTypes:
            if vs is None or len(vs) == 0:
                print(f"@@@ Parameter[{pn}] Value Text is null")
            else:
                typ = self._prmTypes[pn]
                if typ is int:
                    setattr(self._model, pn, int(vs))
                elif typ is float:
                    setattr(self._model, pn, float(vs))
                else:
                    print(f"@@@ Parameter[{pn}] is not int or float {typ}")
                    return
        else:
            print(f"@@@ No defined Parameter {pn}")

    # ##################################
    @Slot(str, int)
    def onIntChanged(self, pn: str, v: int) -> None:
        setattr(self._model, pn, v)
        print(f"***Param {pn} is changed to {getattr(self._model, pn)}\n")

    # ##################################
    @Slot(str, float)
    def onFloatChanged(self, pn: str, v: float) -> None:
        setattr(self._model, pn, v)
        print(f"***Param {pn} is changed to {getattr(self._model, pn)}\n")

    # ##################################
    @Slot(float)
    def onMaxIdqChanged(self, tgt: QLabel, v: float) -> None:
        if v is not None:
            tgt.setText(f"({v:.3f} A)")
        else:
            tgt.setText("(***)")

    # ##################################
    def _iniViewParam(self) -> QHBoxLayout:
        p0 = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        pn0 = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        qpf = QSizePolicy.Policy.Fixed

        lh0 = QHBoxLayout()
        t0 = QLabel("極数：")
        t0.setAlignment(p0)
        lh0.addWidget(t0)
        t0.setSizePolicy(qpf, qpf)
        # データ
        e0 = QLineEdit("---")
        lh0.addWidget(e0)
        e0.setAlignment(pn0)
        e0.setMinimumWidth(50)
        e0.setMaximumWidth(50)
        e0.editingFinished.connect(lambda: self.onValueEdited("nP", e0.text()))
        self._editList["nP"] = e0

        lh0.addItem(QSpacerItem(20, 20, qpf, qpf))

        # 002 Max Current
        t1a = QLabel("最大電流：")
        t1a.setAlignment(p0)
        lh0.addWidget(t1a)

        e1 = QLineEdit("---")
        e1.setAlignment(pn0)
        lh0.addWidget(e1)
        e1.setMinimumWidth(50)
        e1.setMaximumWidth(50)
        e1.editingFinished.connect(lambda: self.onValueEdited("maxIa", e1.text()))
        self._editList["maxIa"] = e1

        t1b = QLabel("[Arms]")
        t1b.setAlignment(p0)
        lh0.addWidget(t1b)
        t1c = QLabel("---")
        t1c.setAlignment(p0)
        lh0.addWidget(t1c)
        t1c.setMinimumWidth(30)
        t1c.setMaximumWidth(100)
        t1c.setObjectName("maxIdq")
        self._model.onMaxIdqChanged.connect(lambda v: self.onMaxIdqChanged(t1c, v))

        lh0.addItem(QSpacerItem(10, 10, qpf, qpf))

        t2a = QLabel("並列コイル数：")
        t2a.setAlignment(p0)
        lh0.addWidget(t2a)

        e2a = QLineEdit("***")
        e2a.setAlignment(pn0)
        lh0.addWidget(e2a)
        e2a.setFixedWidth(25)
        e2a.editingFinished.connect(lambda: self.onValueEdited("nParaCoil", e2a.text()))
        self._editList["nParaCoil"] = e2a

        lh0.addItem(QSpacerItem(10, 10, qpf, qpf))

        t2c = QLabel("コイル抵抗：")
        t2c.setAlignment(p0)

        e3 = QLineEdit()
        e3.setPlaceholderText("---")
        e3.setAlignment(pn0)
        e3.setFixedWidth(60)
        e3.editingFinished.connect(lambda: self.onValueEdited("RaM", e3.text()))
        self._editList["RaM"] = e3

        t2d = QLabel("[mOhm]")
        t2d.setAlignment(p0)
        t2e = QLabel("/")
        t2e.setAlignment(p0)

        e4 = QLineEdit()
        e4.setPlaceholderText("---")
        e4.setAlignment(pn0)
        e4.setFixedWidth(50)
        e4.editingFinished.connect(lambda: self.onValueEdited("tmpAtRa", e4.text()))
        self._editList["tmpAtRa"] = e4

        t2f = QLabel("[℃]")
        t2f.setAlignment(p0)

        lh0.addWidget(t2c)
        lh0.addWidget(e3)
        lh0.addWidget(t2d)
        lh0.addWidget(t2e)
        lh0.addWidget(e4)
        lh0.addWidget(t2f)

        lh0.addItem(QSpacerItem(5, 10, qpf, qpf))

        t2g = QLabel("回転数：")
        t2g.setAlignment(p0)

        e5 = QLineEdit()
        e5.setPlaceholderText("---")
        e5.setAlignment(pn0)
        e5.setFixedWidth(50)
        e5.editingFinished.connect(lambda: self.onValueEdited("mdlNrpm", e5.text()))
        self._editList["mdlNrpm"] = e5

        t2h = QLabel("[Nrpm]")
        t2h.setAlignment(p0)

        lh0.addWidget(t2g)
        lh0.addWidget(e5)
        lh0.addWidget(t2h)

        return lh0

    def _iniView(self) -> None:
        gb = QGroupBox("Model Parameter")
        lh0 = QHBoxLayout()
        gb.setLayout(lh0)
        l0 = self._iniViewParam()
        lh0.addLayout(l0)
        sp = QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        lh0.addItem(sp)

        gb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        gb.setStyleSheet(self._css)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(gb)

    def loadSettings(self, s: QSettings | None = None) -> None:
        if s is None:
            s = self._settings
        if s is None:
            return
        s.beginGroup("ModelParameter")
        s.endGroup()

    def saveSettings(self, s: QSettings | None = None) -> None:
        m = self._model
        if s is None:
            s = self._settings
        if s is None:
            return
        s.beginGroup("ModelParameter")
        s.endGroup()

    def __init__(self, m: MdlParameter, set: QSettings | None = None, parent=None) -> None:
        super().__init__(parent)
        if m is None:
            m = MdlParameter()
        self._model = m

        self._editList = {}
        self._checkList = {}
        self._settings = set
        self._prmTypes = MdlParameter.getPrmTypes()

        self._iniView()

        self._model.onValueChanged.connect(self.onValueSet)
        self._model.onChkStateChanged.connect(self.onCheckSet)
        self.loadSettings(self._settings)
        self._model.update()
        self._model._onAllUpdate()

    def closeEvent(self, event):
        self.saveSettings(self._settings)
        return super().closeEvent(event)


# ##################################
class GuiBtnSetCurrent(QPushButton):
    _type: int
    _uiType: QComboBox

    SetType = Signal(int)

    # ----------------------------------------
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.clicked.connect(self.onClicked)

        ly = QHBoxLayout(self)

        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(0)

        cb = QComboBox(self)
        cb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        cb.addItems(["新規作成", "追加", "クリア"])
        cb.currentIndexChanged.connect(self.onSetTypeChanged)
        cb.activated.connect(self.onUiTypeActivated)
        self.SetType.connect(lambda i: cb.setCurrentIndex(i))
        ly.addWidget(cb)
        ly.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        p = cb.sizeHint()
        self.setFixedSize(p.width() + 15, p.height() + 2)

        self._uiType = cb
        self._type = cb.currentIndex()
        if self._type == -1:
            self.Type = 0

    # ----------------------------------------
    @property
    def Type(self) -> int:
        return self._type

    @Type.setter
    def Type(self, i: int) -> None:
        self._type = i
        self.SetType.emit(i)

    # ----------------------------------------
    def _onTypeChanged(self, i: int) -> None:
        pass

    # ----------------------------------------
    def onUiTypeActivated(self, i: int) -> None:
        print(f"Set type activated to {i}")
        self.Type = i

    # ----------------------------------------
    def onSetTypeChanged(self, i: int) -> None:
        self._type = i
        print(f"Set type changed to {i}")

    # ----------------------------------------
    def onClicked(self) -> None:
        print("電流設定ボタンが押されました。")

    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
