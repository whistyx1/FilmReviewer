"""Rating controls and metric explanations."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget

from .theme import SURFACE
from .widgets import lbl


METRICS = (
    ("Story & characters", "How engaging and coherent are the plot, dialogue, and characters?"),
    ("Acting", "How convincing and expressive are the performances?"),
    ("Cinematography & visuals", "How well do framing, lighting, color, and visual design serve the film?"),
    ("Pacing & editing", "Does the film flow well, with scenes and cuts given the right amount of time?"),
    ("Sound & music", "How well do the score, sound design, and dialogue mix support the film?"),
    ("Enjoyment", "How much did you enjoy watching the film overall?"),
    ("Emotional impact", "How strongly did the film make you feel or connect with its story?"),
    ("Lasting impression", "How much do you expect this film to stay with you?"),
)


class Metric(QWidget):
    changed = pyqtSignal()

    def __init__(self, name: str, description: str, color: str) -> None:
        super().__init__()
        self.name = name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        name_label = lbl(name, "metricName")
        name_label.setFixedWidth(218)
        layout.addWidget(name_label)
        help_button = QPushButton("?")
        help_button.setObjectName("helpButton")
        help_button.setFixedSize(21, 21)
        help_button.setToolTip(description)
        help_button.setAccessibleName(f"About {name}")
        help_button.clicked.connect(lambda: QMessageBox.information(self, name, description))
        layout.addWidget(help_button)
        self.value_label = lbl("5", "metricValue")
        self.value_label.setStyleSheet(f"color: {color};")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setFixedSize(38, 30)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 10)
        self.slider.setValue(5)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(1)
        self.slider.setAccessibleName(name)
        self.slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: #393E35; height: 6px; border-radius: 3px; }}"
            f"QSlider::sub-page:horizontal {{ background: {color}; border-radius: 3px; }}"
            f"QSlider::add-page:horizontal {{ background: #393E35; border-radius: 3px; }}"
            f"QSlider::handle:horizontal {{ background: {color}; border: 2px solid {SURFACE}; "
            "width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }"
        )
        self.slider.valueChanged.connect(self._changed)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)

    @property
    def value(self) -> int:
        return self.slider.value()

    def _changed(self, value: int) -> None:
        self.value_label.setText(str(value))
        self.changed.emit()


class RatingPanel(QFrame):
    def __init__(self, definitions: tuple, color: str) -> None:
        super().__init__()
        self.setObjectName("ratingPanel")
        self.setStyleSheet(
            "QFrame#ratingPanel { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #252C23, stop:0.22 #1D231C, stop:1 #171B17); "
            f"border: 1px solid {color}; "
            "border-radius: 11px; }"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 9)
        shadow.setColor(QColor(0, 0, 0, 95))
        self.setGraphicsEffect(shadow)
        rows = QVBoxLayout(self)
        rows.setContentsMargins(23, 17, 23, 17)
        rows.setSpacing(10)
        self.metrics = [Metric(name, info, color) for name, info in definitions]
        for metric in self.metrics:
            rows.addWidget(metric)
