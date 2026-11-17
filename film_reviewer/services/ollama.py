"""Nonblocking access to a locally running Ollama server."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


API_ROOT = "http://127.0.0.1:11434/api"
REWRITE_INSTRUCTION = (
    "Edit this personal film review for grammar, clarity, and flow. Preserve the "
    "writer's meaning, opinion, tone, film names, and language. Do not invent facts, "
    "add opinions, or change ratings. Return a JSON object with one field named "
    "review containing only the revised review text. Do not add an introduction."
)
REVIEW_FORMAT = {
    "type": "object",
    "properties": {"review": {"type": "string"}},
    "required": ["review"],
    "additionalProperties": False,
}
INTRO = (
    r"(?:sure[,!.]?\s*)?here(?: is|'s)\s+"
    r"(?:(?:a|an|the|your)\s+)?"
    r"(?:(?:new|another|revised|polished|improved|updated|alternative)\s+)?"
    r"(?:version|review|draft|take)"
    r"(?:\s+of\s+(?:your|the)\s+review)?"
)


def parse_model_names(raw: bytes) -> list[str]:
    payload = json.loads(raw)
    models = payload["models"]
    if not isinstance(models, list):
        raise ValueError("Invalid model list")
    return [item["name"] for item in models if isinstance(item, dict)
            and isinstance(item.get("name"), str) and item["name"].strip()]


def parse_rewrite(raw: bytes) -> str:
    content = json.loads(raw)["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Ollama returned an empty review")
    content = content.strip()
    try:
        structured = json.loads(content)
    except ValueError:
        structured = None
    if isinstance(structured, dict) and isinstance(structured.get("review"), str):
        content = structured["review"].strip()

    content = re.sub(rf"^{INTRO}\s*:\s*", "", content, count=1, flags=re.IGNORECASE)
    first_line, separator, remainder = content.partition("\n")
    if separator and re.fullmatch(rf"{INTRO}\s*[.!:]?", first_line.strip(), re.IGNORECASE):
        content = remainder.strip()
    if not content.strip():
        raise ValueError("Ollama returned an empty review")
    return content.strip()


def find_ollama_executable() -> str | None:
    candidates = [shutil.which("ollama")]
    if sys.platform == "darwin":
        candidates.extend((
            "/Applications/Ollama.app/Contents/Resources/ollama",
            str(Path.home() / "Applications/Ollama.app/Contents/Resources/ollama"),
        ))
    elif sys.platform == "win32":
        for folder in (os.getenv("LOCALAPPDATA"), os.getenv("ProgramFiles")):
            if folder:
                candidates.append(str(Path(folder) / "Ollama" / "ollama.exe"))
        if os.getenv("LOCALAPPDATA"):
            candidates.append(str(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe"))
    return next((path for path in candidates if path and Path(path).is_file()), None)


class OllamaClient(QObject):
    models_finished = pyqtSignal(object, str)
    rewrite_finished = pyqtSignal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)

    def start_server(self) -> bool:
        executable = find_ollama_executable()
        if executable is None:
            return False
        process = QProcess()
        process.setProgram(executable)
        process.setArguments(["serve"])
        process.setStandardOutputFile(QProcess.nullDevice())
        process.setStandardErrorFile(QProcess.nullDevice())
        return process.startDetached()

    def _finish(self, reply: QNetworkReply, callback) -> None:
        raw = bytes(reply.readAll())
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = ""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            error = reply.errorString()
        elif isinstance(status, int) and status >= 400:
            try:
                error = json.loads(raw).get("error", f"HTTP {status}")
            except (ValueError, AttributeError):
                error = f"HTTP {status}"
        callback(raw, error)
        reply.deleteLater()

    def list_models(self) -> None:
        request = QNetworkRequest(QUrl(f"{API_ROOT}/tags"))
        request.setTransferTimeout(10_000)
        reply = self.manager.get(request)

        def done(raw: bytes, error: str) -> None:
            if error:
                self.models_finished.emit([], error)
                return
            try:
                self.models_finished.emit(parse_model_names(raw), "")
            except (ValueError, TypeError, KeyError) as exc:
                self.models_finished.emit([], f"Invalid Ollama response: {exc}")

        reply.finished.connect(lambda: self._finish(reply, done))

    def rewrite(self, model: str, notes: str, previous_version: str | None = None) -> None:
        request = QNetworkRequest(QUrl(f"{API_ROOT}/chat"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(180_000)
        messages = [
            {"role": "system", "content": REWRITE_INSTRUCTION},
            {"role": "user", "content": notes},
        ]
        if previous_version:
            messages.append({
                "role": "user",
                "content": (
                    "Write another edit of my original review with noticeably different "
                    "wording and sentence structure. Keep the same meaning and tone. "
                    "Do not repeat this previous version:\n\n" + previous_version
                ),
            })
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "format": REVIEW_FORMAT,
            "options": {"temperature": 0.7 if previous_version else 0.2},
        }).encode("utf-8")
        reply = self.manager.post(request, payload)

        def done(raw: bytes, error: str) -> None:
            if error:
                self.rewrite_finished.emit("", error)
                return
            try:
                self.rewrite_finished.emit(parse_rewrite(raw), "")
            except (ValueError, TypeError, KeyError) as exc:
                self.rewrite_finished.emit("", f"Invalid Ollama response: {exc}")

        reply.finished.connect(lambda: self._finish(reply, done))
