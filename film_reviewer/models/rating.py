"""Whole-number 40/60 film rating calculation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RatingResult:
    first: int
    second: int
    total: int


def calculate_rating(first: Sequence[int], second: Sequence[int]) -> RatingResult:
    if len(first) != 5 or len(second) != 3:
        raise ValueError("Expected five first-group and three second-group scores")
    if any(value < 1 or value > 10 for value in (*first, *second)):
        raise ValueError("Each metric must be scored from 1 to 10")
    first_score = (sum(first) * 4 + 2) // 5
    second_score = second[0] * 3 + second[1] * 2 + second[2]
    return RatingResult(first_score, second_score, first_score + second_score)
