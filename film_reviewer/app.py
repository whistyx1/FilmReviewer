"""Application entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.theme import STYLESHEET


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
