"""A review snapshot kept in local history."""

from __future__ import annotations

from dataclasses import dataclass

from .rating import calculate_rating


@dataclass(frozen=True)
class SavedReview:
    id: str
    saved_at: str
    title: str
    year: str
    director: str
    movie_id: int | None
    scores: tuple[int, ...]
    notes: str
    brushed_notes: str | None
    poster_data: str

    @property
    def total_score(self) -> int:
        return calculate_rating(self.scores[:5], self.scores[5:]).total

    @classmethod
    def from_dict(cls, data: dict) -> "SavedReview":
        scores = tuple(data["scores"])
        if len(scores) != 8 or any(type(value) is not int or not 1 <= value <= 10 for value in scores):
            raise ValueError("Invalid review scores")
        if not isinstance(data["title"], str) or not data["title"].strip():
            raise ValueError("Invalid review title")
        return cls(
            id=str(data["id"]), saved_at=str(data["saved_at"]),
            title=data["title"], year=str(data["year"]),
            director=str(data["director"]), movie_id=data["movie_id"],
            scores=scores, notes=str(data["notes"]),
            brushed_notes=data["brushed_notes"], poster_data=str(data["poster_data"]),
        )

    def to_dict(self) -> dict:
        return {**self.__dict__, "scores": list(self.scores)}
