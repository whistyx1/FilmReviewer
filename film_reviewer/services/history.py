"""Atomic JSON persistence for the user's saved reviews."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from ..models.saved_review import SavedReview


class HistoryStore:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            directory = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
            path = Path(directory) / "reviews.json"
        self.path = Path(path)

    def list_reviews(self) -> list[SavedReview]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Invalid history file")
        return [SavedReview.from_dict(item) for item in data]

    def save(self, review: SavedReview) -> None:
        reviews = [item for item in self.list_reviews() if item.id != review.id]
        self._write([review, *reviews])

    def delete(self, review_id: str) -> None:
        self._write([item for item in self.list_reviews() if item.id != review_id])

    def _write(self, reviews: list[SavedReview]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=".reviews-", suffix=".tmp", delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump([review.to_dict() for review in reviews], temporary, ensure_ascii=False, indent=2)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
