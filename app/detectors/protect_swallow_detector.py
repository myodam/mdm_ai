"""Scene 1. 다친 제비 보호하기 - 두 손 모으기 판정.

storyId: heungbu_nolbu / sceneId: scene_001 / missionType: protect_swallow

판정 기준 (자세형, bestFrame):
    handDistance = distance(leftWrist, rightWrist)
    bodyCenterX  = (leftShoulder.x + rightShoulder.x) / 2
    handsCenterX = (leftWrist.x + rightWrist.x) / 2
    centerDiff   = abs(handsCenterX - bodyCenterX)
성공: handDistance < 거리 임계값 AND centerDiff < 중앙 임계값.

errorCode 우선순위:
    어깨가 어느 프레임에서도 감지되지 않음                  -> USER_NOT_DETECTED
    양손목이 함께 보이는 프레임이 하나도 없음              -> HAND_NOT_VISIBLE
실패 reasonCode:
    손 사이가 너무 멂      -> HANDS_TOO_FAR (우선)
    손이 몸 중앙에서 벗어남 -> HANDS_NOT_CENTERED
"""

from __future__ import annotations

from typing import Sequence

from app.core import config, constants
from app.schemas.mission_schema import MissionCheckResponse
from app.schemas.pose_schema import PoseFrame
from app.utils.geometry import calculate_distance
from app.utils.pose_utils import get_landmark, is_visible
from app.utils.score_utils import clamp_score, is_success

_SCALE = 1.5  # 임계값 경계에서 점수가 0.7 이 되도록 하는 기울기


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def _frame_metrics(frame: PoseFrame) -> tuple[float, float] | None:
    """양손목/양어깨가 모두 보이면 (handDistance, centerDiff) 반환, 아니면 None."""
    ls = get_landmark(frame, constants.LEFT_SHOULDER)
    rs = get_landmark(frame, constants.RIGHT_SHOULDER)
    lw = get_landmark(frame, constants.LEFT_WRIST)
    rw = get_landmark(frame, constants.RIGHT_WRIST)
    if not (is_visible(ls) and is_visible(rs) and is_visible(lw) and is_visible(rw)):
        return None
    hand_distance = calculate_distance(lw, rw)
    body_center_x = (ls.x + rs.x) / 2
    hands_center_x = (lw.x + rw.x) / 2
    center_diff = abs(hands_center_x - body_center_x)
    return hand_distance, center_diff


def _score(hand_distance: float, center_diff: float) -> float:
    dist_score = config.SUCCESS_THRESHOLD + (
        config.PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD - hand_distance
    ) * _SCALE
    center_score = config.SUCCESS_THRESHOLD + (
        config.PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD - center_diff
    ) * _SCALE
    return clamp_score(min(dist_score, center_score))


def detect(pose_frames: Sequence[PoseFrame]) -> MissionCheckResponse:
    shoulder_seen = _any_visible(
        pose_frames, constants.LEFT_SHOULDER
    ) or _any_visible(pose_frames, constants.RIGHT_SHOULDER)
    if not shoulder_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )

    # 양손목/양어깨가 함께 보이는 프레임 중 점수 최댓값(bestFrame) 선택
    best = None  # (score, hand_distance, center_diff)
    for frame in pose_frames:
        metrics = _frame_metrics(frame)
        if metrics is None:
            continue
        hand_distance, center_diff = metrics
        score = _score(hand_distance, center_diff)
        if best is None or score > best[0]:
            best = (score, hand_distance, center_diff)

    if best is None:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    score, hand_distance, center_diff = best
    if is_success(score):
        return MissionCheckResponse(
            success=True, score=score, reason_code=constants.REASON_MISSION_SUCCESS
        )

    # 실패 사유: 거리 우선, 다음 중앙 이탈
    if hand_distance >= config.PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD:
        reason_code = constants.REASON_HANDS_TOO_FAR
    else:
        reason_code = constants.REASON_HANDS_NOT_CENTERED
    return MissionCheckResponse(success=False, score=score, reason_code=reason_code)
