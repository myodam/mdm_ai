"""Scene 2. 박씨 받기 - receive_seed 판정 (자세형, bestFrame).

missionType: receive_seed  (참고: 흥부와 놀부 scene_002 — AI 는 missionType 만 사용)

**두 손을 모아서 어깨 위로** 올려 박씨를 받는 동작.
한 손만 올리면 성공하지 않는다.

판정 기준 (MediaPipe 는 y 가 작을수록 위쪽):
    leftRaise  = leftShoulder.y  - leftWrist.y   (양수면 어깨 위)
    rightRaise = rightShoulder.y - rightWrist.y
    handDistance = distance(leftWrist, rightWrist)
성공: 두 손 모두 어깨 위(raise ≥ margin) AND 두 손이 모임(handDistance < 임계값).
    (각 임계값에서 점수가 0.7 → score≥0.7 과 동치)

errorCode:
    어깨가 어느 프레임에서도 감지 안 됨                 -> USER_NOT_DETECTED
    좌/우 손목이 함께 보이는 프레임이 없음              -> HAND_NOT_VISIBLE
실패 reasonCode:
    두 손이 충분히 올라가지 않음                        -> HAND_NOT_RAISED
    올렸지만 두 손이 모이지 않음                        -> HANDS_NOT_TOGETHER
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.core import config, constants
from app.schemas.mission_schema import MissionCheckResponse
from app.schemas.pose_schema import PoseFrame
from app.utils.geometry import calculate_distance
from app.utils.pose_utils import get_landmark, is_visible
from app.utils.score_utils import clamp_score, is_success

logger = logging.getLogger("ai.detector.receive_seed")

_RAISE_SCALE = 1.5
_TOGETHER_SCALE = 1.5


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def _frame_metrics(frame: PoseFrame) -> tuple[float, float, float] | None:
    """양손목/양어깨가 모두 보이면 (leftRaise, rightRaise, handDistance) 반환."""
    ls = get_landmark(frame, constants.LEFT_SHOULDER)
    rs = get_landmark(frame, constants.RIGHT_SHOULDER)
    lw = get_landmark(frame, constants.LEFT_WRIST)
    rw = get_landmark(frame, constants.RIGHT_WRIST)
    if not (is_visible(ls) and is_visible(rs) and is_visible(lw) and is_visible(rw)):
        return None
    left_raise = ls.y - lw.y
    right_raise = rs.y - rw.y
    hand_distance = calculate_distance(lw, rw)
    return left_raise, right_raise, hand_distance


def _score(left_raise: float, right_raise: float, hand_distance: float) -> float:
    margin = config.RECEIVE_SEED_HAND_RAISE_MARGIN
    left_score = config.SUCCESS_THRESHOLD + (left_raise - margin) * _RAISE_SCALE
    right_score = config.SUCCESS_THRESHOLD + (right_raise - margin) * _RAISE_SCALE
    together_score = config.SUCCESS_THRESHOLD + (
        config.RECEIVE_SEED_HAND_DISTANCE_THRESHOLD - hand_distance
    ) * _TOGETHER_SCALE
    return clamp_score(min(left_score, right_score, together_score))


def detect(pose_frames: Sequence[PoseFrame]) -> MissionCheckResponse:
    shoulder_seen = _any_visible(
        pose_frames, constants.LEFT_SHOULDER
    ) or _any_visible(pose_frames, constants.RIGHT_SHOULDER)
    if not shoulder_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )

    # 양손목/양어깨가 함께 보이는 프레임 중 점수 최댓값(bestFrame)
    best = None  # (score, left_raise, right_raise, hand_distance)
    for frame in pose_frames:
        metrics = _frame_metrics(frame)
        if metrics is None:
            continue
        left_raise, right_raise, hand_distance = metrics
        score = _score(left_raise, right_raise, hand_distance)
        if best is None or score > best[0]:
            best = (score, left_raise, right_raise, hand_distance)

    if best is None:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    score, left_raise, right_raise, hand_distance = best
    margin = config.RECEIVE_SEED_HAND_RAISE_MARGIN
    logger.debug(
        "receive_seed leftRaise=%.3f rightRaise=%.3f handDistance=%.3f score=%.2f",
        left_raise,
        right_raise,
        hand_distance,
        score,
    )

    if is_success(score):
        return MissionCheckResponse(
            success=True, score=score, reason_code=constants.REASON_MISSION_SUCCESS
        )

    # 실패 사유: 두 손이 덜 올라갔으면 우선 HAND_NOT_RAISED, 올렸는데 안 모이면 HANDS_NOT_TOGETHER
    if left_raise < margin or right_raise < margin:
        reason_code = constants.REASON_HAND_NOT_RAISED
    else:
        reason_code = constants.REASON_HANDS_NOT_TOGETHER
    return MissionCheckResponse(success=False, score=score, reason_code=reason_code)
