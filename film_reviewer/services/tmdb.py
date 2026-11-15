"""Asynchronous TMDB movie search and poster loading."""

from __future__ import annotations

import json

from PyQt6.QtCore import QObject, QUrl, QUrlQuery, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from ..models.movie import MovieDetails, MovieMatch


API_ROOT = "https://api.themoviedb.org/3"
POSTER_ROOT = "https://image.tmdb.org/t/p/w500"




def parse_search_results(payload: dict) -> list[MovieMatch]:
    matches = []
    for item in payload.get("results", [])[:8]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            continue
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        release_date = item.get("release_date") or ""
        year = release_date[:4] if isinstance(release_date, str) else ""
        matches.append(
            MovieMatch(
                id=item["id"],
                title=title.strip(),
                year=year,
                poster_path=item.get("poster_path") or "",
            )
        )
    return matches


def parse_movie_details(payload: dict) -> MovieDetails:
    crew = payload.get("credits", {}).get("crew", [])
    directors = [
        person.get("name", "")
        for person in crew
        if isinstance(person, dict) and person.get("job") == "Director"
    ]
    release_date = payload.get("release_date") or ""
    return MovieDetails(
        id=payload["id"],
        title=payload.get("title") or "Untitled film",
        year=release_date[:4] if isinstance(release_date, str) else "",
        director=", ".join(name for name in directors if name),
        poster_path=payload.get("poster_path") or "",
    )


class TmdbClient(QObject):
    search_finished = pyqtSignal(str, object, str)
    details_finished = pyqtSignal(int, object, str)
    poster_finished = pyqtSignal(int, bytes, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self.access_token = ""

    def set_access_token(self, token: str) -> None:
        self.access_token = token.strip()

    def _request(self, url: QUrl, callback) -> None:
        request = QNetworkRequest(url)
        request.setRawHeader(b"Accept", b"application/json")
        if self.access_token:
            request.setRawHeader(
                b"Authorization", f"Bearer {self.access_token}".encode("utf-8")
            )
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._finish(reply, callback))

    @staticmethod
    def _finish(reply: QNetworkReply, callback) -> None:
        raw = bytes(reply.readAll())
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = ""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            error = f"TMDB request failed: {reply.errorString()}"
        elif isinstance(status, int) and status >= 400:
            error = f"TMDB request failed (HTTP {status})"
        callback(raw, error)
        reply.deleteLater()

    def search(self, text: str) -> None:
        url = QUrl(f"{API_ROOT}/search/movie")
        query = QUrlQuery()
        query.addQueryItem("query", text)
        query.addQueryItem("include_adult", "false")
        url.setQuery(query)

        def done(raw: bytes, error: str) -> None:
            if error:
                self.search_finished.emit(text, [], error)
                return
            try:
                matches = parse_search_results(json.loads(raw))
            except (ValueError, TypeError, AttributeError) as exc:
                self.search_finished.emit(text, [], f"Invalid TMDB response: {exc}")
                return
            self.search_finished.emit(text, matches, "")

        self._request(url, done)

    def details(self, movie_id: int) -> None:
        url = QUrl(f"{API_ROOT}/movie/{movie_id}")
        query = QUrlQuery()
        query.addQueryItem("append_to_response", "credits")
        url.setQuery(query)

        def done(raw: bytes, error: str) -> None:
            if error:
                self.details_finished.emit(movie_id, None, error)
                return
            try:
                details = parse_movie_details(json.loads(raw))
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                self.details_finished.emit(movie_id, None, f"Invalid TMDB response: {exc}")
                return
            self.details_finished.emit(movie_id, details, "")

        self._request(url, done)

    def poster(self, movie_id: int, poster_path: str) -> None:
        if not poster_path.startswith("/"):
            self.poster_finished.emit(movie_id, b"", "Poster unavailable")
            return
        url = QUrl(f"{POSTER_ROOT}{poster_path}")
        request = QNetworkRequest(url)
        reply = self.manager.get(request)

        def done() -> None:
            raw = bytes(reply.readAll())
            error = "" if reply.error() == QNetworkReply.NetworkError.NoError else reply.errorString()
            self.poster_finished.emit(movie_id, raw, error)
            reply.deleteLater()

        reply.finished.connect(done)
