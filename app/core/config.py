"""서버 설정 및 동작 판정 임계값.

값은 .env 로 덮어쓸 수 있으며, Unity 실제 테스트 후 조정 가능하다.
"""

import os


def _get_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# 공통 성공/가시성 임계값
SUCCESS_THRESHOLD: float = _get_float("SUCCESS_THRESHOLD", 0.7)
VISIBILITY_THRESHOLD: float = _get_float("VISIBILITY_THRESHOLD", 0.6)

# 기본 수집 설정
DEFAULT_CAPTURE_DURATION_SEC: int = _get_int("DEFAULT_CAPTURE_DURATION_SEC", 5)
DEFAULT_SAMPLE_FPS: int = _get_int("DEFAULT_SAMPLE_FPS", 5)

# Scene 1. protect_swallow
PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD: float = _get_float(
    "PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD", 0.18
)
PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD: float = _get_float(
    "PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD", 0.2
)

# Scene 2. receive_seed
RECEIVE_SEED_HAND_RAISE_MARGIN: float = _get_float(
    "RECEIVE_SEED_HAND_RAISE_MARGIN", 0.05
)

# Scene 3. open_gourd
OPEN_GOURD_WRIST_WIDTH_RATIO: float = _get_float("OPEN_GOURD_WRIST_WIDTH_RATIO", 1.6)
OPEN_GOURD_MOVEMENT_THRESHOLD: float = _get_float(
    "OPEN_GOURD_MOVEMENT_THRESHOLD", 0.4
)
