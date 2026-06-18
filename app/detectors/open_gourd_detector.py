"""Scene 3. 박 타기 - open_gourd 판정 (동작형).

missionType: open_gourd  (참고: 흥부와 놀부 scene_003 — AI 는 missionType 만 사용)

**양손을 어느 정도 벌린 상태에서 왼손·오른손이 같은 방향으로 함께 좌우로 움직이며
박을 써는 동작**. (서로 반대 방향이 아니라, 두 손이 함께 쓱싹쓱싹 이동)
poseFrames 전체에서 양손목의 이동량/방향을 보는 동작형 미션.

성공 조건:
    양손 visible, 각 visible 프레임 >= 2
    leftWrist.y > leftShoulder.y  AND  rightWrist.y > rightShoulder.y   (어깨보다 아래)
    leftWristMovement >= MOVE  AND  rightWristMovement >= MOVE
    leftWristXRange  >= X_RANGE AND  rightWristXRange  >= X_RANGE
    handsCenterXRange >= CENTER_X_RANGE
    sameDirectionCount >= SAME_DIR_COUNT   (두 손이 같은 방향으로 움직인 구간 수)
    (각 임계값에서 점수 0.7 → score>=0.7 과 동치)

errorCode:
    어깨가 어느 프레임에서도 감지 안 됨        -> USER_NOT_DETECTED
    좌/우 손목 visible 프레임 < 2             -> HAND_NOT_VISIBLE
실패 reasonCode (우선순위):
    손이 어깨보다 높음                        -> HAND_POSITION_TOO_HIGH
    양손 움직임/가로폭 부족                   -> MOVEMENT_TOO_SMALL
    중심 좌우이동/같은방향 구간 부족          -> SAWING_MOTION_TOO_SMALL
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.core import config, constants
from app.schemas.mission_schema import MissionCheckResponse
from app.schemas.pose_schema import PoseFrame
from app.utils.geometry import calculate_total_movement
from app.utils.pose_utils import get_landmark, is_visible
from app.utils.score_utils import clamp_score, is_success

logger = logging.getLogger("ai.detector.open_gourd")

_MOVE_SCALE = 1.5
_X_RANGE_SCALE = 1.5
_CENTER_SCALE = 1.5
_SAME_DIR_SCALE = 0.15
_POSITION_SCALE = 1.5
_MIN_VISIBLE_FRAMES = 2


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def _visible_xs(pose_frames: Sequence[PoseFrame], name: str) -> list[float]:
    return [
        lm.x
        for f in pose_frames
        if is_visible(lm := get_landmark(f, name))  # noqa: F841
    ]


def _below_margin(
    pose_frames: Sequence[PoseFrame], wrist_name: str, shoulder_name: str
) -> float:
    """어깨 대비 손목이 아래로 내려간 평균 정도(wrist.y - shoulder.y). 양수면 어깨 아래."""
    diffs = []
    for f in pose_frames:
        w = get_landmark(f, wrist_name)
        s = get_landmark(f, shoulder_name)
        if is_visible(w) and is_visible(s):
            diffs.append(w.y - s.y)
    if not diffs:
        return 0.0
    return sum(diffs) / len(diffs)


def detect(pose_frames: Sequence[PoseFrame]) -> MissionCheckResponse:
    # 1. 사람 감지 (어깨)
    if not (
        _any_visible(pose_frames, constants.LEFT_SHOULDER)
        or _any_visible(pose_frames, constants.RIGHT_SHOULDER)
    ):
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )

    # 2. 양손목 visible 프레임 수
    left_xs = _visible_xs(pose_frames, constants.LEFT_WRIST)
    right_xs = _visible_xs(pose_frames, constants.RIGHT_WRIST)
    if len(left_xs) < _MIN_VISIBLE_FRAMES or len(right_xs) < _MIN_VISIBLE_FRAMES:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    # 3. 지표 계산
    left_movement = calculate_total_movement(pose_frames, constants.LEFT_WRIST)
    right_movement = calculate_total_movement(pose_frames, constants.RIGHT_WRIST)
    left_x_range = max(left_xs) - min(left_xs)
    right_x_range = max(right_xs) - min(right_xs)

    # 어깨보다 아래(허리 근사): 두 손 중 더 위에 있는 쪽 기준
    left_below = _below_margin(
        pose_frames, constants.LEFT_WRIST, constants.LEFT_SHOULDER
    )
    right_below = _below_margin(
        pose_frames, constants.RIGHT_WRIST, constants.RIGHT_SHOULDER
    )
    position_margin = min(left_below, right_below)

    # 양손이 함께 보이는 프레임에서 중심 좌우이동 + 같은방향 구간 수
    centers_x: list[float] = []
    same_direction_count = 0
    prev_lx = prev_rx = None
    for f in pose_frames:
        lw = get_landmark(f, constants.LEFT_WRIST)
        rw = get_landmark(f, constants.RIGHT_WRIST)
        if is_visible(lw) and is_visible(rw):
            centers_x.append((lw.x + rw.x) / 2)
            if prev_lx is not None:
                if (lw.x - prev_lx) * (rw.x - prev_rx) > 0:
                    same_direction_count += 1
            prev_lx, prev_rx = lw.x, rw.x
        else:
            prev_lx = prev_rx = None  # 가시성 끊기면 델타 연결 안 함
    hands_center_x_range = (max(centers_x) - min(centers_x)) if centers_x else 0.0

    # 4. score 매핑 (각 임계값에서 0.7)
    left_move_score = config.SUCCESS_THRESHOLD + (
        left_movement - config.OPEN_GOURD_MOVEMENT_THRESHOLD
    ) * _MOVE_SCALE
    right_move_score = config.SUCCESS_THRESHOLD + (
        right_movement - config.OPEN_GOURD_MOVEMENT_THRESHOLD
    ) * _MOVE_SCALE
    left_x_score = config.SUCCESS_THRESHOLD + (
        left_x_range - config.OPEN_GOURD_X_RANGE_THRESHOLD
    ) * _X_RANGE_SCALE
    right_x_score = config.SUCCESS_THRESHOLD + (
        right_x_range - config.OPEN_GOURD_X_RANGE_THRESHOLD
    ) * _X_RANGE_SCALE
    center_score = config.SUCCESS_THRESHOLD + (
        hands_center_x_range - config.OPEN_GOURD_CENTER_X_RANGE_THRESHOLD
    ) * _CENTER_SCALE
    same_dir_score = config.SUCCESS_THRESHOLD + (
        same_direction_count - config.OPEN_GOURD_SAME_DIRECTION_COUNT
    ) * _SAME_DIR_SCALE
    position_score = config.SUCCESS_THRESHOLD + position_margin * _POSITION_SCALE
    score = clamp_score(
        min(
            left_move_score,
            right_move_score,
            left_x_score,
            right_x_score,
            center_score,
            same_dir_score,
            position_score,
        )
    )

    logger.debug(
        "open_gourd leftMove=%.3f rightMove=%.3f leftXRange=%.3f rightXRange=%.3f "
        "centerXRange=%.3f sameDirCount=%d positionMargin=%.3f score=%.2f",
        left_movement,
        right_movement,
        left_x_range,
        right_x_range,
        hands_center_x_range,
        same_direction_count,
        position_margin,
        score,
    )

    if is_success(score):
        return MissionCheckResponse(
            success=True, score=score, reason_code=constants.REASON_MISSION_SUCCESS
        )

    # 5. 실패 사유 우선순위: 위치 → 움직임/가로폭 → 중심이동/같은방향
    if position_margin <= 0:
        reason_code = constants.REASON_HAND_POSITION_TOO_HIGH
    elif (
        left_movement < config.OPEN_GOURD_MOVEMENT_THRESHOLD
        or right_movement < config.OPEN_GOURD_MOVEMENT_THRESHOLD
        or left_x_range < config.OPEN_GOURD_X_RANGE_THRESHOLD
        or right_x_range < config.OPEN_GOURD_X_RANGE_THRESHOLD
    ):
        reason_code = constants.REASON_MOVEMENT_TOO_SMALL
    else:
        reason_code = constants.REASON_SAWING_MOTION_TOO_SMALL
    return MissionCheckResponse(success=False, score=score, reason_code=reason_code)
