"""Browse, inspect, and open saved reviews."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
)

from ..models.review import format_review
from ..models.saved_review import SavedReview
from ..services.history import HistoryStore
from .metrics import METRICS
from .widgets import lbl


class HistoryDialog(QDialog):
    def __init__(self, store: HistoryStore, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.selected_review: SavedReview | None = None
        self.reviews = store.list_reviews()
        self.setWindowTitle("Review history")
        self.resize(770, 510)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        layout.addWidget(lbl("Review history", "sectionTitle"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find a film…")
        self.search.textChanged.connect(self._populate)
        layout.addWidget(self.search)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("historyList")
        self.list_widget.currentItemChanged.connect(self._show_selected)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self._open())
        columns.addWidget(self.list_widget, 2)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Select a review to see its details.")
        columns.addWidget(self.preview, 3)
        layout.addLayout(columns, 1)

        actions = QHBoxLayout()
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("quietButton")
        self.delete_button.clicked.connect(self._delete)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        close_button = QPushButton("Close")
        close_button.setObjectName("quietButton")
        close_button.clicked.connect(self.reject)
        actions.addWidget(close_button)
        self.open_button = QPushButton("Open review")
        self.open_button.setObjectName("accentButton")
        self.open_button.clicked.connect(self._open)
        actions.addWidget(self.open_button)
        layout.addLayout(actions)
        self._populate()

    def _populate(self) -> None:
        query = self.search.text().strip().casefold()
        self.list_widget.clear()
        for review in self.reviews:
            if query not in f"{review.title} {review.year} {review.director}".casefold():
                continue
            date = review.saved_at[:10]
            heading = f"{review.title} ({review.year})" if review.year else review.title
            item = QListWidgetItem(f"{heading}\n{review.total_score}/100  ·  {date}")
            item.setData(Qt.ItemDataRole.UserRole, review)
            self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
        else:
            self.preview.clear()
            self.open_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    def _show_selected(self) -> None:
        review = self._current_review()
        self.open_button.setEnabled(review is not None)
        self.delete_button.setEnabled(review is not None)
        if review is None:
            self.preview.clear()
            return
        metrics = [(name, score) for (name, _), score in zip(METRICS, review.scores)]
        text = format_review(
            review.title, review.year, review.director,
            review.total_score, metrics,
            review.brushed_notes if review.brushed_notes is not None else review.notes,
        )
        self.preview.setPlainText(text)

    def _current_review(self) -> SavedReview | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _open(self) -> None:
        self.selected_review = self._current_review()
        if self.selected_review is not None:
            self.accept()

    def _delete(self) -> None:
        review = self._current_review()
        if review is None:
            return
        answer = QMessageBox.question(
            self, "Delete review", f"Delete the saved review for {review.title}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.delete(review.id)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            QMessageBox.warning(self, "History error", f"Could not delete the review: {exc}")
            return
        self.reviews = [item for item in self.reviews if item.id != review.id]
        self._populate()
