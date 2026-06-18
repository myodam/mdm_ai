"""좌표 계산 유틸.

Landmark(또는 .x/.y 속성을 가진 객체) 기반의 거리/이동량 계산.
"""

from __future__ import annotations

import math
from typing import Iterable

from app.schemas.pose_schema import Landmark, PoseFrame


def calculate_distance(point_a: Landmark, point_b: Landmark) -> float:
    """두 점 사이의 유클리드 거리."""
    return math.hypot(point_a.x - point_b.x, point_a.y - point_b.y)


def calculate_angle(point_a: Landmark, point_b: Landmark, point_c: Landmark) -> float:
    """point_b 를 꼭짓점으로 하는 각도(도 단위, 0~180)."""
    ax, ay = point_a.x - point_b.x, point_a.y - point_b.y
    cx, cy = point_c.x - point_b.x, point_c.y - point_b.y
    dot = ax * cx + ay * cy
    mag = math.hypot(ax, ay) * math.hypot(cx, cy)
    if mag == 0:
        return 0.0
    cos_v = max(-1.0, min(1.0, dot / mag))
    return math.degrees(math.acos(cos_v))


def calculate_total_movement(
    frames: Iterable[PoseFrame], landmark_name: str
) -> float:
    """프레임 시퀀스에서 특정 landmark 의 누적 이동량.

    연속한 두 프레임 모두에 해당 landmark 가 존재할 때만 거리를 누적한다.
    """
    total = 0.0
    prev: Landmark | None = None
    for frame in frames:
        current = getattr(frame.landmarks, landmark_name, None)
        if current is not None and prev is not None:
            total += calculate_distance(prev, current)
        if current is not None:
            prev = current
    return total
