"""점수 계산 / 성공 판정 유틸."""

from __future__ import annotations

from app.core import config


def clamp_score(score: float) -> float:
    """score 를 0~1 사이로 보정."""
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


def is_success(score: float, threshold: float = config.SUCCESS_THRESHOLD) -> bool:
    """score 가 성공 임계값 이상이면 True."""
    return score >= threshold
