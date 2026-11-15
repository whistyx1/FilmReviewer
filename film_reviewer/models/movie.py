"""Movie data returned by the film search service."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MovieMatch:
    id: int
    title: str
    year: str
    poster_path: str

    @property
    def display_name(self) -> str:
        return f"{self.title}  ·  {self.year}" if self.year else self.title


@dataclass(frozen=True)
class MovieDetails:
    id: int
    title: str
    year: str
    director: str
    poster_path: str
