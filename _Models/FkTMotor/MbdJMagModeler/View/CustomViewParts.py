import PySide6.QtGui as QtG
import PySide6.QtWidgets as QtW
from PySide6.QtCore import Qt, Signal

QtAf = Qt.AlignmentFlag
QtSp = QtW.QSizePolicy.Policy

_dvQtAf = QtAf.AlignVCenter | QtAf.AlignLeft
_tvQtSpP = (QtSp.Preferred, QtSp.Preferred)


class CfLineEdit(QtW.QLineEdit):
    def __init__(
        self,
        text: str = "",
        af: QtAf = _dvQtAf,
        ise: bool = False,
        isro: bool = False,
        wf: int = 0,
        parent=None,
    ):
        super().__init__(text, parent)
        self.setAlignment(af)
        self.setEnabled(ise)
        self.setReadOnly(isro)
        self.setSizePolicy(QtSp.Fixed, QtSp.Fixed)
        if wf > 0:
            self.setFixedWidth(wf)


class ClickableLabel(QtW.QLabel):
    clicked = Signal()

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)

    def mousePressEvent(self, event: QtG.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CLabel(QtW.QLabel):
    def __init__(
        self,
        text: str = "",
        af: QtAf = _dvQtAf,
        sps: QtSp = _tvQtSpP,
        parent=None,
    ):
        super().__init__(text, parent)
        self.setAlignment(af)
        self.setSizePolicy(sps[0], sps[1])
