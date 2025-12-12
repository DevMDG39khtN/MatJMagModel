from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import QObject, SignalInstance
from PySide6.QtWidgets import QApplication, QMessageBox


############################################################
class SttDialog(Enum):
    Message = auto()
    Question = auto()
    Warning = auto()
    Error = auto()
    NoModeMsg = auto()


def showDialog(
    stt: SttDialog,
    msg: str,
    tit: str | None = None,
    onFined: SignalInstance = None,
    p: QObject = None,
) -> int | QMessageBox:
    """Show a message dialog based on the status."""
    if stt == SttDialog.Message:
        if not tit:
            tit = "Information"
        return showMsgDialog(msg, tit, onFined=onFined, p=p)
    elif stt == SttDialog.Question:
        if not tit:
            tit = "Question"
        return showSelDialog(msg, tit, onFined=onFined, p=p)
    elif stt == SttDialog.Warning:
        if not tit:
            tit = "Warning"
        return showWarnDialog(msg, tit, onFined=onFined, p=p)
    elif stt == SttDialog.NoModeMsg:
        if not tit:
            tit = "Information"
        return showMsgDialog(msg, tit, isMod=False, onFined=onFined, p=p)
    else:
        if not tit:
            tit = "Error"
        return showErrDialog(msg, tit, onFined=onFined, p=p)


def showMsgDialog(
    msg: str,
    tit: str = "Information",
    isMod: bool = True,
    onFined: SignalInstance = None,
    p: QObject = None,
) -> int | QMessageBox:
    btns = QMessageBox.StandardButton.Ok
    dBtn = btns
    dlg = QMessageBox(parent=p)
    dlg.setWindowTitle(tit)
    dlg.setText(msg)
    dlg.setModal(isMod)
    if isMod:
        dlg.setStandardButtons(btns)
        dlg.setDefaultButton(dBtn)
        dlg.setIcon(QMessageBox.Icon.Information)
        ret = dlg.exec()
        if onFined is not None:
            onFined.emit()
        return ret
    else:
        dlg.setIcon(QMessageBox.Icon.NoIcon)
        dlg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        dlg.show()
        QApplication.processEvents()
        return dlg


def showErrDialog(
    msg: str,
    tit: str = "Error",
    onFined: SignalInstance = None,
    p: QObject = None,
) -> int:
    dlg = QMessageBox(parent=p)
    dlg.setIcon(QMessageBox.Icon.Critical)
    dlg.setWindowTitle(tit)
    dlg.setText(msg)
    dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
    dlg.setDefaultButton(QMessageBox.StandardButton.Ok)
    ret = dlg.exec()
    if onFined is not None:
        onFined.emit()
    return ret


def showWarnDialog(
    msg: str,
    tit: str = "Warning",
    onFined: SignalInstance = None,
    p: QObject = None,
) -> int:
    dlg = QMessageBox(parent=p)
    dlg.setIcon(QMessageBox.Icon.Warning)
    dlg.setWindowTitle(tit)
    dlg.setText(msg)
    dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
    dlg.setDefaultButton(QMessageBox.StandardButton.Ok)
    ret = dlg.exec()
    if onFined is not None:
        onFined.emit()
    return ret


def showSelDialog(
    msg: str,
    tit: str = "Question",
    onFined: SignalInstance = None,
    p: QObject = None,
) -> int:
    btns = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    dBtn = QMessageBox.StandardButton.Yes
    dlg = QMessageBox(parent=p)
    dlg.setIcon(QMessageBox.Icon.Question)
    dlg.setWindowTitle(tit)
    dlg.setText(msg)
    dlg.setStandardButtons(btns)
    dlg.setDefaultButton(dBtn)

    ret = dlg.exec()
    if onFined is not None:
        onFined.emit()
    return ret
