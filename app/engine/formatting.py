from __future__ import annotations


SCORE_DECIMALS = 4


def round_score(value: float | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), SCORE_DECIMALS)
