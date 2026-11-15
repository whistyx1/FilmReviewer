"""Plain-text review export shared by the preview and clipboard actions."""

from __future__ import annotations

import re
from collections.abc import Sequence


def tidy_notes(text: str) -> str:
    """Make small, predictable edits without rewriting the author's meaning."""
    paragraphs = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n").strip())
    cleaned = []
    for paragraph in paragraphs:
        lines = [re.sub(r"[ \t]+", " ", line.strip()) for line in paragraph.splitlines()]
        compact = " ".join(line for line in lines if line)
        compact = re.sub(r"\s+([,.;:!?])", r"\1", compact)
        compact = re.sub(r"([,;:!?])(?=[A-Za-zА-Яа-яЁё])", r"\1 ", compact)
        compact = re.sub(
            r"(^|[.!?]\s+)([A-Za-zА-Яа-яЁё])",
            lambda match: match.group(1) + match.group(2).upper(),
            compact,
        )
        if compact:
            cleaned.append(compact)
    return "\n\n".join(cleaned)


def format_review(
    title: str,
    year: str,
    director: str,
    total_score: int,
    metrics: Sequence[tuple[str, int]],
    notes: str = "",
) -> str:
    heading = title.strip() or "Untitled film"
    if year.strip():
        heading += f" ({year.strip()})"
    lines = [heading]
    if director.strip():
        lines.append(f"Directed by {director.strip()}")
    lines.extend((f"{total_score}/100", ""))
    for name, score in metrics:
        lines.append(f"{name}: {'★' * score} {score}/10")
    if notes.strip():
        lines.extend(("", notes.strip()))
    return "\n".join(lines)
