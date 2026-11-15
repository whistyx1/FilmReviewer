"""Small widget helpers shared by the interface."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel


def lbl(value: str = "", role: str = "") -> QLabel:
    widget = QLabel()
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setText(value)
    if role:
        widget.setObjectName(role)
    return widget


def panel(role: str) -> QFrame:
    widget = QFrame()
    widget.setObjectName(role)
    return widget
