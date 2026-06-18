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

# Scene 1. protect_swallow
PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD: float = _get_float(
    "PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD", 0.18
)
PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD: float = _get_float(
    "PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD", 0.2
)

# Scene 2. receive_seed (두 손 모아 어깨 위)
RECEIVE_SEED_HAND_RAISE_MARGIN: float = _get_float(
    "RECEIVE_SEED_HAND_RAISE_MARGIN", 0.05
)
RECEIVE_SEED_HAND_DISTANCE_THRESHOLD: float = _get_float(
    "RECEIVE_SEED_HAND_DISTANCE_THRESHOLD", 0.20
)

# Scene 3. open_gourd (박 썰기: 양손이 어깨 아래에서 같은 방향으로 함께 좌우 이동)
OPEN_GOURD_MOVEMENT_THRESHOLD: float = _get_float(
    "OPEN_GOURD_MOVEMENT_THRESHOLD", 0.20  # 손목별 총 이동량
)
OPEN_GOURD_X_RANGE_THRESHOLD: float = _get_float(
    "OPEN_GOURD_X_RANGE_THRESHOLD", 0.12  # 손목별 좌우 이동 폭
)
OPEN_GOURD_CENTER_X_RANGE_THRESHOLD: float = _get_float(
    "OPEN_GOURD_CENTER_X_RANGE_THRESHOLD", 0.15  # 양손 중심의 좌우 이동 폭
)
OPEN_GOURD_SAME_DIRECTION_COUNT: int = _get_int(
    "OPEN_GOURD_SAME_DIRECTION_COUNT", 2  # 두 손이 같은 방향으로 움직인 구간 횟수
)

# Scene 0. skip_book (책 넘기기: 왼손이 오른쪽으로 한 번 곡선 스윕)
SKIP_BOOK_NET_X_THRESHOLD: float = _get_float("SKIP_BOOK_NET_X_THRESHOLD", 0.20)
SKIP_BOOK_X_MOVEMENT_THRESHOLD: float = _get_float(
    "SKIP_BOOK_X_MOVEMENT_THRESHOLD", 0.25
)
SKIP_BOOK_DIRECTION_RATIO_THRESHOLD: float = _get_float(
    "SKIP_BOOK_DIRECTION_RATIO_THRESHOLD", 0.6
)
SKIP_BOOK_ARC_THRESHOLD: float = _get_float("SKIP_BOOK_ARC_THRESHOLD", 0.05)
# 미러링으로 화면 좌→우가 x 감소면 -1 로 두어 netX 부호를 뒤집는다.
SKIP_BOOK_DIRECTION_SIGN: float = _get_float("SKIP_BOOK_DIRECTION_SIGN", 1.0)
