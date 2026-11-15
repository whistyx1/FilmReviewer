"""Subtle reflected light behind the review editor."""

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PyQt6.QtWidgets import QWidget


class BackgroundCanvas(QWidget):
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.rect()
        width = float(bounds.width())
        height = float(bounds.height())

        base = QLinearGradient(0, 0, width, height)
        base.setColorAt(0, QColor("#151916"))
        base.setColorAt(0.48, QColor("#101310"))
        base.setColorAt(1, QColor("#0B0E0C"))
        painter.fillRect(bounds, base)

        upper_glow = QRadialGradient(QPointF(width * 0.72, height * 0.08), width * 0.65)
        upper_glow.setColorAt(0, QColor(156, 185, 126, 26))
        upper_glow.setColorAt(0.4, QColor(130, 156, 118, 11))
        upper_glow.setColorAt(1, QColor(130, 156, 118, 0))
        painter.fillRect(bounds, upper_glow)

        lower_glow = QRadialGradient(QPointF(width * 0.14, height * 0.82), width * 0.7)
        lower_glow.setColorAt(0, QColor(140, 164, 131, 16))
        lower_glow.setColorAt(1, QColor(140, 164, 131, 0))
        painter.fillRect(bounds, lower_glow)

        reflection = QLinearGradient(width * 0.3, 0, width * 0.88, 0)
        reflection.setColorAt(0, QColor(255, 255, 255, 0))
        reflection.setColorAt(0.48, QColor(255, 255, 255, 7))
        reflection.setColorAt(0.55, QColor(255, 255, 255, 2))
        reflection.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(bounds, reflection)
        painter.end()
