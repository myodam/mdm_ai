"""poseFrames / landmark 처리 유틸."""

from __future__ import annotations

from typing import Callable, Sequence

from app.core import config
from app.schemas.pose_schema import Landmark, PoseFrame


def get_landmark(frame: PoseFrame, landmark_name: str) -> Landmark | None:
    """프레임에서 특정 landmark 를 가져온다. 없으면 None."""
    return getattr(frame.landmarks, landmark_name, None)


def has_required_landmarks(frame: PoseFrame, required_names: Sequence[str]) -> bool:
    """프레임에 필수 landmark 들이 모두 존재하는지 확인."""
    return all(get_landmark(frame, name) is not None for name in required_names)


def is_visible(
    landmark: Landmark | None, threshold: float = config.VISIBILITY_THRESHOLD
) -> bool:
    """landmark 가 존재하고 visibility 가 기준 이상인지 확인.

    visibility 가 None 이면 (값이 안 온 경우) 보이는 것으로 간주한다.
    """
    if landmark is None:
        return False
    if landmark.visibility is None:
        return True
    return landmark.visibility >= threshold


def find_best_frame(
    pose_frames: Sequence[PoseFrame],
    scoring_function: Callable[[PoseFrame], float],
) -> tuple[PoseFrame | None, float]:
    """각 프레임 점수를 계산해 가장 높은 (frame, score) 를 반환.

    자세형 미션에서 흔들림을 보정하기 위해 사용한다.
    프레임이 없으면 (None, 0.0).
    """
    best_frame: PoseFrame | None = None
    best_score = -1.0
    for frame in pose_frames:
        score = scoring_function(frame)
        if score > best_score:
            best_score = score
            best_frame = frame
    if best_frame is None:
        return None, 0.0
    return best_frame, best_score
