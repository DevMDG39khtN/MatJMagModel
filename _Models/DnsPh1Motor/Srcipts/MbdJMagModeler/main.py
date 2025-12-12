import sys

from PySide6.QtWidgets import QApplication

from View.WinMain import MainWindow


def main():
    app = QApplication([])
    while True:
        w = MainWindow()
        w.show()
        stt = app.exec()
        w.deleteLater()
        if not MainWindow.isReset:
            break

    sys.exit(stt)


if __name__ == "__main__":
    main()
