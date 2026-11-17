"""Main Film Reviewer window and movie search interaction."""

from __future__ import annotations

import os
import base64
from datetime import datetime
from uuid import uuid4

from PyQt6.QtCore import QCoreApplication, QElapsedTimer, QSettings, QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QBoxLayout, QDialog, QFrame, QHBoxLayout, QInputDialog, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QScrollArea, QTextEdit, QPushButton, QVBoxLayout, QWidget

from ..models.movie import MovieDetails, MovieMatch
from ..models.rating import calculate_rating
from ..models.review import format_review, tidy_notes
from ..models.saved_review import SavedReview
from ..services.history import HistoryStore
from ..services.ollama import OllamaClient
from ..services.tmdb import TmdbClient
from .background import BackgroundCanvas
from .history import HistoryDialog
from .metrics import METRICS, RatingPanel
from .theme import LIME, SAGE
from .widgets import lbl, panel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Film Reviewer")
        self.resize(1100, 920)
        self.setMinimumSize(770, 620)
        QCoreApplication.setOrganizationName("FilmReviewer")
        QCoreApplication.setApplicationName("FilmReviewer")
        self.settings = QSettings("FilmReviewer", "FilmReviewer")
        self.history_store = HistoryStore()
        self.tmdb = TmdbClient(self)
        self.ollama = OllamaClient(self)
        self.tmdb.set_access_token(
            str(os.getenv("TMDB_READ_ACCESS_TOKEN") or self.settings.value("tmdb_access_token", ""))
        )
        self.selected_movie_id: int | None = None
        self.selected_year = ""
        self.poster_data = b""
        self.current_review_id: str | None = None
        self.brushed_notes: str | None = None
        self.ollama_version_active = False
        self.pending_notes: str | None = None
        self.pending_previous_version: str | None = None
        self.ollama_start_timer = QElapsedTimer()
        self.ollama_retry_timer = QTimer(self)
        self.ollama_retry_timer.setSingleShot(True)
        self.ollama_retry_timer.setInterval(1_000)
        self.ollama_retry_timer.timeout.connect(self._retry_ollama_models)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(350)
        self.search_timer.timeout.connect(self._search_movie)
        self.tmdb.search_finished.connect(self._show_search_results)
        self.tmdb.details_finished.connect(self._show_details)
        self.tmdb.poster_finished.connect(self._show_poster)
        self.ollama.models_finished.connect(self._ollama_models_finished)
        self.ollama.rewrite_finished.connect(self._ollama_rewrite_finished)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll)
        page = BackgroundCanvas()
        page.setObjectName("page")
        scroll.setWidget(page)
        body = QVBoxLayout(page)
        body.setContentsMargins(35, 28, 35, 45)
        body.setSpacing(20)
        self._topbar(body)
        self._film_header(body)
        self._ratings(body)
        self._score(body)
        self._review(body)
        attribution = lbl(
            "This product uses the TMDB API but is not endorsed or certified by TMDB.",
            "attribution",
        )
        attribution.setAlignment(Qt.AlignmentFlag.AlignRight)
        body.addWidget(attribution)
        body.addStretch()
        self._apply_responsive_layout()

        for metric in self.first_panel.metrics + self.second_panel.metrics:
            metric.changed.connect(self._update_score)
        self.title_input.textEdited.connect(self._title_edited)
        self.title_input.textChanged.connect(self._update_preview)
        self.director_input.textChanged.connect(self._update_preview)
        self.notes_input.textChanged.connect(self._notes_changed)
        self._update_score()
        self._update_preview()
        self._update_api_button()
        self.last_saved_state = self._draft_state()

    def _topbar(self, body: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.addWidget(lbl("Film Reviewer", "brand"))
        row.addStretch()
        self.new_button = QPushButton("New review")
        self.new_button.setObjectName("quietButton")
        self.new_button.clicked.connect(self._new_review)
        row.addWidget(self.new_button)
        self.history_button = QPushButton("History")
        self.history_button.setObjectName("quietButton")
        self.history_button.clicked.connect(self._open_history)
        row.addWidget(self.history_button)
        body.addLayout(row)

    def _film_header(self, body: QVBoxLayout) -> None:
        search_row = QHBoxLayout()
        search_row.setSpacing(15)
        self.title_input = QLineEdit()
        self.title_input.setObjectName("titleInput")
        self.title_input.setPlaceholderText("Search for a film or enter its title…")
        search_row.addWidget(self.title_input, 1)
        self.api_button = QPushButton()
        self.api_button.setObjectName("quietButton")
        self.api_button.clicked.connect(self._connect_tmdb)
        search_row.addWidget(self.api_button)
        body.addLayout(search_row)
        self.suggestions = QListWidget()
        self.suggestions.setObjectName("suggestions")
        self.suggestions.setMaximumHeight(150)
        self.suggestions.hide()
        self.suggestions.itemClicked.connect(self._select_movie)
        body.addWidget(self.suggestions)
        self.search_status = lbl("", "hint")
        body.addWidget(self.search_status)

    def _ratings(self, body: QVBoxLayout) -> None:
        hero = QHBoxLayout()
        self.hero_layout = hero
        hero.setSpacing(22)
        self.poster = lbl("POSTER", "poster")
        self.poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster.setFixedSize(225, 335)
        hero.addWidget(self.poster, alignment=Qt.AlignmentFlag.AlignTop)
        right = QVBoxLayout()
        right.setSpacing(14)
        self.display_title = lbl("Choose a film", "displayTitle")
        self.display_title.setWordWrap(True)
        right.addWidget(self.display_title)
        director_row = QHBoxLayout()
        director_row.setSpacing(7)
        director_row.addWidget(lbl("Directed by", "directorLead"))
        self.director_input = QLineEdit()
        self.director_input.setObjectName("directorInput")
        self.director_input.setPlaceholderText("enter director")
        director_row.addWidget(self.director_input, 1)
        right.addLayout(director_row)
        self.first_panel = RatingPanel(METRICS[:5], LIME)
        self.second_panel = RatingPanel(METRICS[5:], SAGE)
        right.addWidget(self.first_panel)
        right.addWidget(self.second_panel)
        hero.addLayout(right, 1)
        body.addLayout(hero)

    def _score(self, body: QVBoxLayout) -> None:
        frame = panel("scorePanel")
        row = QHBoxLayout(frame)
        self.score_layout = row
        row.setContentsMargins(0, 20, 0, 19)
        row.setSpacing(28)
        math = QVBoxLayout()
        math.setSpacing(13)
        self.first_math = lbl("", "mathLine")
        self.second_math = lbl("", "mathLine")
        self.first_math.setStyleSheet(f"color: {LIME};")
        self.second_math.setStyleSheet(f"color: {SAGE};")
        for color, line in ((LIME, self.first_math), (SAGE, self.second_math)):
            line_row = QHBoxLayout()
            square = lbl("", "colorSquare")
            square.setFixedSize(12, 12)
            square.setStyleSheet(f"background: {color}; border-radius: 3px;")
            line_row.addWidget(square)
            line_row.addWidget(line)
            line_row.addStretch()
            math.addLayout(line_row)
        row.addLayout(math, 1)
        divider = panel("verticalDivider")
        self.score_divider = divider
        divider.setFixedSize(1, 72)
        row.addWidget(divider)
        total = QVBoxLayout()
        total.setSpacing(1)
        self.total_math = lbl("", "totalMath")
        total.addWidget(self.total_math, alignment=Qt.AlignmentFlag.AlignRight)
        self.final_score = lbl("", "finalScore")
        total.addWidget(self.final_score, alignment=Qt.AlignmentFlag.AlignRight)
        row.addLayout(total)
        body.addWidget(frame)

    def _review(self, body: QVBoxLayout) -> None:
        frame = panel("reviewPanel")
        columns = QHBoxLayout(frame)
        self.review_layout = columns
        columns.setContentsMargins(0, 20, 0, 8)
        columns.setSpacing(35)
        notes = QVBoxLayout()
        notes.addWidget(lbl("Notes", "sectionTitle"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Your thoughts about the film…")
        self.notes_input.setMinimumHeight(140)
        notes.addWidget(self.notes_input, 1)
        brush_actions = QHBoxLayout()
        self.brush_button = QPushButton("Brush up with Ollama")
        self.brush_button.setObjectName("accentButton")
        self.brush_button.setEnabled(False)
        self.brush_button.clicked.connect(self._brush_up_review)
        brush_actions.addWidget(self.brush_button)
        self.cleanup_button = QPushButton("Basic cleanup")
        self.cleanup_button.setObjectName("quietButton")
        self.cleanup_button.setEnabled(False)
        self.cleanup_button.clicked.connect(self._basic_cleanup)
        brush_actions.addWidget(self.cleanup_button)
        brush_actions.addStretch()
        notes.addLayout(brush_actions)
        self.original_button = QPushButton("Use original notes")
        self.original_button.setObjectName("quietButton")
        self.original_button.clicked.connect(self._use_original_notes)
        self.original_button.hide()
        notes.addWidget(self.original_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.brush_status = lbl("", "hint")
        self.brush_status.setWordWrap(True)
        notes.addWidget(self.brush_status)
        columns.addLayout(notes, 1)
        divider = panel("verticalDivider")
        self.review_divider = divider
        divider.setFixedWidth(1)
        columns.addWidget(divider)
        preview = QVBoxLayout()
        preview.setSpacing(8)
        preview.addWidget(lbl("Review preview", "sectionTitle"))
        self.preview_card = panel("previewCard")
        preview_content = QVBoxLayout(self.preview_card)
        preview_content.setContentsMargins(18, 17, 18, 18)
        preview_content.setSpacing(7)
        self.preview_title = lbl("Untitled film", "previewTitle")
        self.preview_director = lbl("Director not entered", "hint")
        self.preview_score = lbl("", "previewScore")
        self.preview_notes = lbl("", "previewNotes")
        self.preview_notes.setWordWrap(True)
        preview_content.addWidget(self.preview_title)
        preview_content.addWidget(self.preview_director)
        preview_content.addWidget(self.preview_score)
        line = panel("previewDivider")
        line.setFixedHeight(1)
        preview_content.addWidget(line)
        self.preview_stars = []
        for name, _ in METRICS:
            metric_row = QHBoxLayout()
            metric_row.setSpacing(8)
            metric_row.addWidget(lbl(name, "previewMetricName"))
            metric_row.addStretch()
            stars = lbl("", "previewStars")
            stars.setAlignment(Qt.AlignmentFlag.AlignRight)
            metric_row.addWidget(stars)
            preview_content.addLayout(metric_row)
            self.preview_stars.append(stars)
        self.notes_divider = panel("previewDivider")
        self.notes_divider.setFixedHeight(1)
        preview_content.addWidget(self.notes_divider)
        preview_content.addWidget(self.preview_notes)
        preview.addWidget(self.preview_card)
        copy_actions = QHBoxLayout()
        self.save_button = QPushButton("Save review")
        self.save_button.setObjectName("accentButton")
        self.save_button.clicked.connect(self._save_review)
        copy_actions.addWidget(self.save_button)
        self.copy_text_button = QPushButton("Copy text")
        self.copy_image_button = QPushButton("Copy image")
        for button in (self.copy_text_button, self.copy_image_button):
            button.setObjectName("quietButton")
            copy_actions.addWidget(button)
        self.copy_text_button.clicked.connect(self._copy_text)
        self.copy_image_button.clicked.connect(self._copy_image)
        preview.addLayout(copy_actions)
        self.copy_status = lbl("", "hint")
        preview.addWidget(self.copy_status)
        preview.addStretch()
        columns.addLayout(preview, 1)
        body.addWidget(frame)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "review_layout"):
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        narrow = self.width() < 930
        direction = QBoxLayout.Direction.TopToBottom if narrow else QBoxLayout.Direction.LeftToRight
        self.hero_layout.setDirection(direction)
        self.score_layout.setDirection(direction)
        self.review_layout.setDirection(direction)
        if narrow:
            self.poster.setFixedSize(118, 177)
        else:
            self.poster.setFixedSize(225, 335)
        self.score_divider.setVisible(not narrow)
        self.review_divider.setVisible(not narrow)

    def _update_score(self) -> None:
        first = [metric.value for metric in self.first_panel.metrics]
        second = [metric.value for metric in self.second_panel.metrics]
        result = calculate_rating(first, second)
        self.first_math.setText(f"({' + '.join(map(str, first))}) → {result.first}/40")
        self.second_math.setText(
            f"({second[0]} × 3) + ({second[1]} × 2) + {second[2]} → {result.second}/60"
        )
        self.total_math.setText(f"{result.first} + {result.second} =")
        self.final_score.setText(f"{result.total}/100")
        self.preview_score.setText(f"{result.total}/100")
        for row, stars in zip(self.first_panel.metrics + self.second_panel.metrics, self.preview_stars):
            stars.setText(f"{'★' * row.value}  {row.value}/10")

    def _update_preview(self) -> None:
        title = self.title_input.text().strip()
        display = f"{title} ({self.selected_year})" if title and self.selected_year else title
        self.display_title.setText(display or "Choose a film")
        self.preview_title.setText(display or "Untitled film")
        self.preview_director.setText(self.director_input.text().strip() or "Director not entered")
        notes = self._effective_notes()
        self.preview_notes.setText(notes)
        self.preview_notes.setVisible(bool(notes))
        self.notes_divider.setVisible(bool(notes))

    def _effective_notes(self) -> str:
        return self.brushed_notes if self.brushed_notes is not None else self.notes_input.toPlainText().strip()

    def _notes_changed(self) -> None:
        self.brushed_notes = None
        self._set_ollama_retry(False)
        has_notes = bool(self.notes_input.toPlainText().strip())
        self.brush_button.setEnabled(has_notes and self.pending_notes is None)
        self.cleanup_button.setEnabled(has_notes and self.pending_notes is None)
        self.original_button.hide()
        self.brush_status.clear()
        self._update_preview()

    def _brush_up_review(self) -> None:
        original = self.notes_input.toPlainText().strip()
        if not original or self.pending_notes is not None:
            return
        self.pending_notes = original
        self.pending_previous_version = self.brushed_notes if self.ollama_version_active else None
        self.ollama_retry_timer.stop()
        self.ollama_start_timer.invalidate()
        self.brush_button.setEnabled(False)
        self.cleanup_button.setEnabled(False)
        self.brush_status.setText("Checking local Ollama models…")
        self.ollama.list_models()

    def _ollama_models_finished(self, models: list[str], error: str) -> None:
        if self.pending_notes is None:
            return
        if error:
            if error.startswith("Invalid Ollama response:"):
                self._ollama_failed(error)
                return
            if not self.ollama_start_timer.isValid():
                if not self.ollama.start_server():
                    self._ollama_failed("Could not start Ollama. Open the Ollama app, then try again.")
                    return
                self.ollama_start_timer.start()
            if self.ollama_start_timer.elapsed() < 15_000:
                self.brush_status.setText("Starting local Ollama…")
                self.ollama_retry_timer.start()
                return
            self._ollama_failed("Ollama did not start in time. Open the Ollama app, then try again.")
            return
        self.ollama_retry_timer.stop()
        self.ollama_start_timer.invalidate()
        if not models:
            self._ollama_failed("No Ollama model is installed. Run: ollama pull gemma3:1b")
            return
        saved = str(self.settings.value("ollama_model", ""))
        if self.pending_previous_version is not None and saved in models:
            model = saved
        elif len(models) == 1:
            model = models[0]
        else:
            model, accepted = QInputDialog.getItem(
                self, "Choose Ollama model", "Model for review editing:", models,
                models.index(saved) if saved in models else 0, False,
            )
            if not accepted:
                self._ollama_failed("Ollama model selection cancelled.")
                return
        self.settings.setValue("ollama_model", model)
        self.brush_status.setText(
            f"Trying another version with {model}…"
            if self.pending_previous_version is not None else f"Brushing up with {model}…"
        )
        self.ollama.rewrite(model, self.pending_notes, self.pending_previous_version)

    def _retry_ollama_models(self) -> None:
        if self.pending_notes is not None and self.ollama_start_timer.isValid():
            self.ollama.list_models()

    def _ollama_rewrite_finished(self, rewritten: str, error: str) -> None:
        original = self.pending_notes
        self.pending_notes = None
        self.pending_previous_version = None
        self.brush_button.setEnabled(bool(self.notes_input.toPlainText().strip()))
        self.cleanup_button.setEnabled(bool(self.notes_input.toPlainText().strip()))
        if original is None:
            return
        if error:
            self.brush_status.setText(f"Ollama could not brush up the review: {error}")
            return
        if self.notes_input.toPlainText().strip() != original:
            self.brush_status.setText("Notes changed while Ollama was working. Try again.")
            return
        self._apply_brushed_notes(rewritten, "Ollama")

    def _ollama_failed(self, message: str) -> None:
        self.pending_notes = None
        self.pending_previous_version = None
        self.ollama_retry_timer.stop()
        self.ollama_start_timer.invalidate()
        self.brush_button.setEnabled(bool(self.notes_input.toPlainText().strip()))
        self.cleanup_button.setEnabled(bool(self.notes_input.toPlainText().strip()))
        self.brush_status.setText(message)

    def _basic_cleanup(self) -> None:
        original = self.notes_input.toPlainText().strip()
        cleaned = tidy_notes(original)
        if not cleaned or cleaned == original:
            self.brush_status.setText("Your notes are already tidy.")
            return
        self._apply_brushed_notes(cleaned, "Basic cleanup")

    def _apply_brushed_notes(self, text: str, source: str) -> None:
        self.brushed_notes = text
        self._set_ollama_retry(source == "Ollama")
        self.original_button.show()
        self.brush_status.setText(f"Preview uses {source} text. Your original notes are unchanged.")
        self._update_preview()

    def _use_original_notes(self) -> None:
        self.brushed_notes = None
        self._set_ollama_retry(False)
        self.original_button.hide()
        self.brush_status.setText("Showing your original notes.")
        self._update_preview()

    def _set_ollama_retry(self, enabled: bool) -> None:
        self.ollama_version_active = enabled
        self.brush_button.setText("Try another version" if enabled else "Brush up with Ollama")

    def _formatted_review(self) -> str:
        metrics = [(row.name, row.value) for row in self.first_panel.metrics + self.second_panel.metrics]
        result = calculate_rating(
            [row.value for row in self.first_panel.metrics],
            [row.value for row in self.second_panel.metrics],
        )
        return format_review(
            self.title_input.text(), self.selected_year, self.director_input.text(),
            result.total, metrics, self._effective_notes(),
        )

    def _copy_text(self) -> None:
        QApplication.clipboard().setText(self._formatted_review())
        self.copy_status.setText("Formatted review copied as text.")

    def _copy_image(self) -> None:
        QApplication.clipboard().setPixmap(self.preview_card.grab())
        self.copy_status.setText("Review card copied as an image.")

    def _draft_state(self) -> tuple:
        scores = tuple(row.value for row in self.first_panel.metrics + self.second_panel.metrics)
        return (
            self.title_input.text().strip(), self.selected_year,
            self.director_input.text().strip(), self.selected_movie_id,
            scores, self.notes_input.toPlainText(), self.brushed_notes, self.poster_data,
        )

    def _save_review(self) -> bool:
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.information(self, "Film title needed", "Enter a film title before saving.")
            return False
        review = SavedReview(
            id=self.current_review_id or str(uuid4()),
            saved_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            title=title, year=self.selected_year,
            director=self.director_input.text().strip(),
            movie_id=self.selected_movie_id,
            scores=tuple(row.value for row in self.first_panel.metrics + self.second_panel.metrics),
            notes=self.notes_input.toPlainText(), brushed_notes=self.brushed_notes,
            poster_data=base64.b64encode(self.poster_data).decode("ascii"),
        )
        try:
            self.history_store.save(review)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            QMessageBox.warning(self, "Save failed", f"Could not save this review: {exc}")
            return False
        self.current_review_id = review.id
        self.last_saved_state = self._draft_state()
        self.copy_status.setText("Review saved to local history.")
        return True

    def _confirm_discard(self) -> bool:
        if self._draft_state() == self.last_saved_state:
            return True
        if self._draft_state()[0] == "" and not self.notes_input.toPlainText().strip() and all(
            row.value == 5 for row in self.first_panel.metrics + self.second_panel.metrics
        ):
            return True
        answer = QMessageBox.question(
            self, "Unsaved changes", "Discard changes to the current review?",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Discard

    def _new_review(self) -> None:
        if not self._confirm_discard():
            return
        self.search_timer.stop()
        self.suggestions.hide()
        self.selected_movie_id = None
        self.selected_year = ""
        self.poster_data = b""
        self.current_review_id = None
        self.pending_notes = None
        self.pending_previous_version = None
        self.ollama_retry_timer.stop()
        self.ollama_start_timer.invalidate()
        self.brushed_notes = None
        self._set_ollama_retry(False)
        self.title_input.clear()
        self.director_input.clear()
        self.notes_input.clear()
        self.poster.clear()
        self.poster.setText("POSTER")
        for row in self.first_panel.metrics + self.second_panel.metrics:
            row.slider.setValue(5)
        self.original_button.hide()
        self.brush_status.clear()
        self.copy_status.clear()
        self._update_preview()
        self._update_api_button()
        self.last_saved_state = self._draft_state()

    def _open_history(self) -> None:
        try:
            dialog = HistoryDialog(self.history_store, self)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            QMessageBox.warning(self, "History error", f"Could not open review history: {exc}")
            return
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_review is not None:
            if self._confirm_discard():
                self._load_review(dialog.selected_review)

    def _load_review(self, review: SavedReview) -> None:
        self.search_timer.stop()
        self.suggestions.hide()
        self.current_review_id = review.id
        self.selected_movie_id = review.movie_id
        self.selected_year = review.year
        self.pending_notes = None
        self.pending_previous_version = None
        self.ollama_retry_timer.stop()
        self.ollama_start_timer.invalidate()
        self.title_input.setText(review.title)
        self.director_input.setText(review.director)
        for row, value in zip(self.first_panel.metrics + self.second_panel.metrics, review.scores):
            row.slider.setValue(value)
        self.notes_input.setPlainText(review.notes)
        self.brushed_notes = review.brushed_notes
        self._set_ollama_retry(review.brushed_notes is not None)
        self.original_button.setVisible(review.brushed_notes is not None)
        self.brush_status.setText("Showing saved brushed-up text. Original notes are unchanged." if review.brushed_notes is not None else "")
        try:
            self.poster_data = base64.b64decode(review.poster_data, validate=True)
        except ValueError:
            self.poster_data = b""
        pixmap = QPixmap()
        if self.poster_data and pixmap.loadFromData(self.poster_data):
            self.poster.setText("")
            self.poster.setPixmap(pixmap.scaled(
                self.poster.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            self.poster.clear()
            self.poster.setText("POSTER")
        self._update_preview()
        self.copy_status.setText("Saved review opened. Save again to update it.")
        self.last_saved_state = self._draft_state()

    def _update_api_button(self) -> None:
        connected = bool(self.tmdb.access_token)
        self.api_button.setText("TMDB connected" if connected else "Connect TMDB")
        self.search_status.setText(
            "Search powered by TMDB. You can also enter details manually."
            if connected else "Connect TMDB to search films and load posters automatically."
        )

    def _connect_tmdb(self) -> None:
        token, accepted = QInputDialog.getText(
            self, "Connect TMDB", "Paste your TMDB API Read Access Token:",
            QLineEdit.EchoMode.Password,
        )
        if accepted and token.strip():
            self.settings.setValue("tmdb_access_token", token.strip())
            self.tmdb.set_access_token(token)
            self._update_api_button()

    def _title_edited(self, title: str) -> None:
        self.search_timer.stop()
        self.suggestions.hide()
        if self.selected_movie_id is not None:
            self.selected_movie_id = None
            self.selected_year = ""
            self.poster_data = b""
            self.poster.clear()
            self.poster.setText("POSTER")
            self.director_input.clear()
            self._update_preview()
        if len(title.strip()) < 2:
            self.search_status.setText("Type at least two letters to search.")
        elif not self.tmdb.access_token:
            self.search_status.setText("Connect TMDB to search films and load posters automatically.")
        else:
            self.search_status.setText("Searching…")
            self.search_timer.start()

    def _search_movie(self) -> None:
        title = self.title_input.text().strip()
        if len(title) >= 2:
            self.tmdb.search(title)

    def _show_search_results(self, query: str, results: list[MovieMatch], error: str) -> None:
        if self.selected_movie_id is not None or query != self.title_input.text().strip():
            return
        self.suggestions.clear()
        if error:
            self.search_status.setText(error)
            return
        if not results:
            self.search_status.setText("No films found. You can enter the details manually.")
            return
        for movie in results:
            item = QListWidgetItem(movie.display_name)
            item.setData(Qt.ItemDataRole.UserRole, movie)
            self.suggestions.addItem(item)
        self.suggestions.show()
        self.search_status.setText("Choose the film you meant.")

    def _select_movie(self, item: QListWidgetItem) -> None:
        movie: MovieMatch = item.data(Qt.ItemDataRole.UserRole)
        self.selected_movie_id = movie.id
        self.selected_year = movie.year
        self.title_input.setText(movie.title)
        self.director_input.clear()
        self.suggestions.hide()
        self.search_status.setText("Loading film details…")
        self.tmdb.details(movie.id)
        self.poster.clear()
        self.poster.setText("POSTER")
        self.poster_data = b""

    def _show_details(self, movie_id: int, movie: MovieDetails | None, error: str) -> None:
        if movie_id != self.selected_movie_id:
            return
        if error or movie is None:
            self.search_status.setText(error or "Film details unavailable.")
            return
        self.title_input.setText(movie.title)
        self.selected_year = movie.year
        self._update_preview()
        self.director_input.setText(movie.director)
        self.search_status.setText(f"{movie.year} · Film details from TMDB" if movie.year else "Film details from TMDB")
        if movie.poster_path:
            self.tmdb.poster(movie.id, movie.poster_path)
        else:
            self.poster.setText("NO POSTER")

    def _show_poster(self, movie_id: int, data: bytes, error: str) -> None:
        if movie_id != self.selected_movie_id:
            return
        pixmap = QPixmap()
        if error or not pixmap.loadFromData(data):
            self.poster_data = b""
            self.poster.setText("NO POSTER")
            return
        self.poster_data = data
        self.poster.setText("")
        self.poster.setPixmap(pixmap.scaled(
            self.poster.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
