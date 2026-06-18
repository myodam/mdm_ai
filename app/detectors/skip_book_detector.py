"""Scene 0. 책 넘기기 - skip_book 판정 (동작형).

missionType: skip_book  (참고: 흥부와 놀부 scene_000 — AI 는 missionType 만 사용)

오른손으로 책장을 넘기듯 옆으로 움직였는지를 본다.
한 순간의 자세(bestFrame)가 아니라, 여러 poseFrame 에 걸친 rightWrist 의
이동 궤적을 분석하는 동작형 미션이다.

판정 항목:
    xRange    = max(rightWrist.x) - min(rightWrist.x)   # 좌우 스윕 폭
    movement  = totalMovement(rightWrist over poseFrames) # 전체 이동량
    yRange    = max(rightWrist.y) - min(rightWrist.y)    # 세로 곡선 (선택)

성공(기본): xRange >= X_RANGE_THRESHOLD AND movement >= MOVEMENT_THRESHOLD
    → score 가 두 임계값에서 정확히 0.7 이 되도록 매핑하므로 score >= 0.7 과 동치.

require_arc=True 일 때만 yRange >= ARC_THRESHOLD 도 함께 요구(선택). 기본은 False.
방향(좌/우)은 강제하지 않는다(미러링·화면 방향 이슈).

errorCode 우선순위:
    어깨가 어느 프레임에서도 감지되지 않음           -> USER_NOT_DETECTED
    rightWrist 가 visible 한 프레임이 2개 미만        -> HAND_NOT_VISIBLE
실패 reasonCode:
    전체 이동량 부족  -> MOVEMENT_TOO_SMALL
    좌우 스윕 부족    -> BOOK_NOT_TURNED
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

logger = logging.getLogger("ai.detector.skip_book")

_X_SCALE = 1.5
_MOVE_SCALE = 1.5
_ARC_SCALE = 2.5
_MIN_VISIBLE_FRAMES = 2


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def detect(
    pose_frames: Sequence[PoseFrame], require_arc: bool = False
) -> MissionCheckResponse:
    # 1. 사람 감지 (어깨)
    shoulder_seen = _any_visible(
        pose_frames, constants.RIGHT_SHOULDER
    ) or _any_visible(pose_frames, constants.LEFT_SHOULDER)
    if not shoulder_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )

    # 2. rightWrist 가 보이는 프레임 모으기
    wrists = []
    for frame in pose_frames:
        wrist = get_landmark(frame, constants.RIGHT_WRIST)
        if is_visible(wrist):
            wrists.append(wrist)
    if len(wrists) < _MIN_VISIBLE_FRAMES:
        # 궤적을 판단하기에 충분한 프레임이 없음
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    # 3. 지표 계산
    xs = [w.x for w in wrists]
    ys = [w.y for w in wrists]
    x_range = max(xs) - min(xs)
    y_range = max(ys) - min(ys)
    movement = calculate_total_movement(pose_frames, constants.RIGHT_WRIST)

    # 4. score 매핑 (임계값에서 정확히 0.7)
    x_score = config.SUCCESS_THRESHOLD + (
        x_range - config.SKIP_BOOK_X_RANGE_THRESHOLD
    ) * _X_SCALE
    move_score = config.SUCCESS_THRESHOLD + (
        movement - config.SKIP_BOOK_MOVEMENT_THRESHOLD
    ) * _MOVE_SCALE
    components = [x_score, move_score]
    if require_arc:
        arc_score = config.SUCCESS_THRESHOLD + (
            y_range - config.SKIP_BOOK_ARC_THRESHOLD
        ) * _ARC_SCALE
        components.append(arc_score)
    score = clamp_score(min(components))

    logger.debug(
        "skip_book visibleFrames=%d xRange=%.3f movement=%.3f yRange=%.3f "
        "xScore=%.2f movementScore=%.2f finalScore=%.2f require_arc=%s",
        len(wrists),
        x_range,
        movement,
        y_range,
        x_score,
        move_score,
        score,
        require_arc,
    )

    if is_success(score):
        return MissionCheckResponse(
            success=True, score=score, reason_code=constants.REASON_MISSION_SUCCESS
        )

    # 5. 실패 사유: 전체 이동량 부족 우선, 다음 좌우 스윕 부족
    if movement < config.SKIP_BOOK_MOVEMENT_THRESHOLD:
        reason_code = constants.REASON_MOVEMENT_TOO_SMALL
    else:
        reason_code = constants.REASON_BOOK_NOT_TURNED
    return MissionCheckResponse(success=False, score=score, reason_code=reason_code)
