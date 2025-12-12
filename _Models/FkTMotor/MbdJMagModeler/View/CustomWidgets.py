from __future__ import annotations

from typing import Union

import PySide6.QtGui as QtG
import PySide6.QtWidgets as QtW
from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt, Signal
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QLineEdit, QWidget

from Model.Numeric import NumericRange, NumVal

QtAf = Qt.AlignmentFlag
QtSp = QtW.QSizePolicy.Policy
QtIdR = Qt.ItemDataRole
QmIdx = Union[QModelIndex, QPersistentModelIndex]

_dvQtAf = QtAf.AlignVCenter | QtAf.AlignLeft
_tvQtSpP = (QtSp.Preferred, QtSp.Preferred)


class NumericValidator(QValidator):
    _tgt: NumericRange | NumVal

    def __init__(self, t: NumericRange | NumVal, p: QWidget | None = None):
        super().__init__(p)
        if isinstance(t, (NumericRange, NumVal)):
            self._tgt = t
        else:
            raise TypeError("Invalid target type for NumericValidator")

    def validate(self, txt: str, pos: int) -> tuple[QValidator.State, str, int]:
        if not txt:
            return QValidator.State.Intermediate, txt, pos
        if isinstance(self._tgt, NumVal):
            if self._tgt.isEnableText(txt):
                return QValidator.State.Acceptable, txt, pos
            else:
                return QValidator.State.Invalid, txt, pos
        elif isinstance(self._tgt, NumericRange):
            if bool(self._tgt.isEnableTextAll(txt)):
                return QValidator.State.Acceptable, txt, pos
            else:
                return QValidator.State.Invalid, txt, pos
        else:
            raise TypeError("Invalid target type for NumericValidator")


class ValEdit(QLineEdit):
    _lnkv: NumVal | NumericRange
    # _lstTxt: str | None

    def __init__(
        self,
        lnkv: NumVal | NumericRange,
        wf: int = 0,
        sp: tuple[QtSp, QtSp] = (QtSp.Fixed, QtSp.Fixed),
        af: QtAf = QtAf.AlignVCenter | QtAf.AlignRight,
        p: QWidget | None = None,
    ):
        super().__init__(p)
        self.setAlignment(af)
        self.setSizePolicy(sp[0], sp[1])
        if wf > 0:
            self.setFixedWidth(wf)
        self.setPlaceholderText("---")

        self._lnkv = lnkv
        self._validator = NumericValidator(self._lnkv)

        self.setText(lnkv.text)
        self.textChanged.connect(lambda txt: self._onTextChanged(txt))

        if lnkv is not None:
            self.editingFinished.connect(lambda: self._onTextUpdated(self.text()))
            self._lnkv.onValueChanged.connect(lambda txt: self.setText(txt))
            self.setText(self._lnkv.text)

        def disCon():
            try:
                self._lnkv.onValueChanged.disconnect()
            except Exception:
                pass

        self.destroyed.connect(lambda: disCon())
        return

    def closeEvent(self, event):
        try:
            self.textChanged.disconnect()
        except Exception:
            pass
        try:
            self.editingFinished.disconnect()
        except Exception:
            pass
        try:
            self._lnkv.onValueChanged.disconnect()
        except Exception:
            pass
        return super().closeEvent(event)

    def _onDataUpdated(self, txt: str):
        print(f">>>>>> onDataUpdated {txt}")
        if self.text() != txt:
            self.setText(txt)

    def _onTextUpdated(self, val: str):
        print(f">>>>>> onDataChanged {val}")

        state, _, _ = self._validator.validate(val, 0)
        if state == QValidator.State.Invalid:
            self.setText(self._lnkv.text)
            return
        if self._lnkv.text == val:
            return

        if state == QValidator.State.Acceptable:
            self._lnkv.text = val

    def _onTextChanged(self, txt: str):
        state, _, _ = self._validator.validate(txt, 0)
        if state == QValidator.State.Invalid:
            self.setStyleSheet("QLineEdit { background: #fcc; }")
        else:
            self.setStyleSheet("")


class ClickableLabel(QtW.QLabel):
    clicked = Signal()

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)

    def mousePressEvent(self, event: QtG.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
