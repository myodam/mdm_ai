"""Scene 3. 박 타기 - 양팔 크게 벌리기 / 휘두르기 판정.

missionType: open_gourd  (참고: 흥부와 놀부 scene_003 — AI 는 missionType 만 사용)

기본(1안, 자세형, bestFrame):
    shoulderWidth = distance(leftShoulder, rightShoulder)
    wristWidth    = distance(leftWrist, rightWrist)
    성공: wristWidth > shoulderWidth * ratio
          AND leftWrist.x  < leftShoulder.x
          AND rightWrist.x > rightShoulder.x

선택(2안, 동작형): require_movement=True 일 때만 추가로
    totalArmMovement = totalMovement(leftWrist) + totalMovement(rightWrist)
    움직임이 임계값보다 작으면 MOVEMENT_TOO_SMALL.

MVP 기본값은 require_movement=False (자세만으로 판정).

errorCode 우선순위:
    어깨가 어느 프레임에서도 감지되지 않음             -> USER_NOT_DETECTED
    양손목/양어깨가 함께 보이는 프레임이 없음          -> HAND_NOT_VISIBLE
실패 reasonCode:
    양팔이 충분히 벌어지지 않음 -> ARMS_NOT_WIDE
    (require_movement) 움직임 부족 -> MOVEMENT_TOO_SMALL
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.core import config, constants
from app.schemas.mission_schema import MissionCheckResponse
from app.schemas.pose_schema import PoseFrame
from app.utils.geometry import calculate_distance, calculate_total_movement
from app.utils.pose_utils import get_landmark, is_visible
from app.utils.score_utils import clamp_score, is_success

logger = logging.getLogger("ai.detector.open_gourd")

_SCALE = 0.5  # ratio 가 임계값일 때 점수 0.7 이 되도록 하는 기울기


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def _frame_pose_metrics(frame: PoseFrame) -> tuple[float, float, float] | None:
    """양손목/양어깨가 모두 보이면 (score, wrist_width, shoulder_width) 반환, 아니면 None.

    좌우 손이 어깨 바깥으로 벌어지지 않았으면(orientation 실패) 0.7 미만으로 제한.
    """
    ls = get_landmark(frame, constants.LEFT_SHOULDER)
    rs = get_landmark(frame, constants.RIGHT_SHOULDER)
    lw = get_landmark(frame, constants.LEFT_WRIST)
    rw = get_landmark(frame, constants.RIGHT_WRIST)
    if not (is_visible(ls) and is_visible(rs) and is_visible(lw) and is_visible(rw)):
        return None

    shoulder_width = calculate_distance(ls, rs)
    wrist_width = calculate_distance(lw, rw)
    if shoulder_width <= 0:
        return 0.0, wrist_width, shoulder_width
    ratio = wrist_width / shoulder_width

    score = clamp_score(
        config.SUCCESS_THRESHOLD
        + (ratio - config.OPEN_GOURD_WRIST_WIDTH_RATIO) * _SCALE
    )

    # 손이 바깥으로 벌어진 방향(orientation)도 만족해야 성공으로 인정
    orientation_ok = lw.x < ls.x and rw.x > rs.x
    if not orientation_ok:
        score = min(score, config.SUCCESS_THRESHOLD - 0.01)
    return score, wrist_width, shoulder_width


def detect(
    pose_frames: Sequence[PoseFrame], require_movement: bool = False
) -> MissionCheckResponse:
    shoulder_seen = _any_visible(
        pose_frames, constants.LEFT_SHOULDER
    ) or _any_visible(pose_frames, constants.RIGHT_SHOULDER)
    if not shoulder_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )

    best = None  # (score, wrist_width, shoulder_width)
    for frame in pose_frames:
        metrics = _frame_pose_metrics(frame)
        if metrics is None:
            continue
        if best is None or metrics[0] > best[0]:
            best = metrics

    if best is None:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    best_score, wrist_width, shoulder_width = best
    movement = calculate_total_movement(
        pose_frames, constants.LEFT_WRIST
    ) + calculate_total_movement(pose_frames, constants.RIGHT_WRIST)
    logger.debug(
        "open_gourd wristWidth=%.3f shoulderWidth=%.3f movement=%.3f score=%.2f "
        "require_movement=%s",
        wrist_width,
        shoulder_width,
        movement,
        best_score,
        require_movement,
    )

    # 1. 자세(양팔 벌리기) 판정
    if not is_success(best_score):
        return MissionCheckResponse(
            success=False,
            score=best_score,
            reason_code=constants.REASON_ARMS_NOT_WIDE,
        )

    # 2. 선택적 움직임 판정 (require_movement=True 일 때만)
    if require_movement and movement < config.OPEN_GOURD_MOVEMENT_THRESHOLD:
        return MissionCheckResponse(
            success=False,
            score=best_score,
            reason_code=constants.REASON_MOVEMENT_TOO_SMALL,
        )

    return MissionCheckResponse(
        success=True, score=best_score, reason_code=constants.REASON_MISSION_SUCCESS
    )
