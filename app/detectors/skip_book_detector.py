"""Scene 0. 책 넘기기 - skip_book 판정 (동작형).

missionType: skip_book  (참고: 흥부와 놀부 scene_000 — AI 는 missionType 만 사용)

왼손(leftWrist)으로 책장을 **오른쪽 방향으로 한 번 곡선처럼** 넘기는 동작.
여러 poseFrame 에 걸친 leftWrist 의 가로 이동 궤적을 분석한다.

판정 항목 (시간순 visible leftWrist 기준):
    netX          = (마지막.x - 처음.x) * DIRECTION_SIGN   # 오른쪽이면 +
    totalXMovement= Σ |x[t] - x[t-1]|                      # 총 가로 이동량
    directionRatio= |netX| / totalXMovement                # 1에 가까울수록 한 방향
    yRange        = max(y) - min(y)                         # 약간의 곡선(세로 변화)

성공: netX≥NET_X AND totalXMovement≥X_MOVE AND directionRatio≥DIR_RATIO AND yRange≥ARC
    (각 임계값에서 점수가 0.7 이 되도록 매핑 → score≥0.7 과 동치)

미러링 주의: 화면 좌→우가 x 감소면 .env SKIP_BOOK_DIRECTION_SIGN=-1 로 뒤집는다.

errorCode:
    어깨가 어느 프레임에서도 감지 안 됨        -> USER_NOT_DETECTED
    leftWrist visible 프레임 < 2              -> HAND_NOT_VISIBLE
실패 reasonCode:
    총 이동량 부족                            -> MOVEMENT_TOO_SMALL
    오른쪽 도달/방향/곡선 부족                -> BOOK_NOT_TURNED
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.core import config, constants
from app.schemas.mission_schema import MissionCheckResponse
from app.schemas.pose_schema import PoseFrame
from app.utils.pose_utils import get_landmark, is_visible
from app.utils.score_utils import clamp_score, is_success

logger = logging.getLogger("ai.detector.skip_book")

_NET_SCALE = 1.5
_MOVE_SCALE = 1.5
_DIR_SCALE = 0.5
_ARC_SCALE = 2.0
_MIN_VISIBLE_FRAMES = 2


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def detect(pose_frames: Sequence[PoseFrame]) -> MissionCheckResponse:
    # 1. 사람 감지 (어깨)
    shoulder_seen = _any_visible(
        pose_frames, constants.LEFT_SHOULDER
    ) or _any_visible(pose_frames, constants.RIGHT_SHOULDER)
    if not shoulder_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )

    # 2. 시간순으로 보이는 leftWrist 모으기
    xs: list[float] = []
    ys: list[float] = []
    for frame in pose_frames:
        wrist = get_landmark(frame, constants.LEFT_WRIST)
        if is_visible(wrist):
            xs.append(wrist.x)
            ys.append(wrist.y)
    if len(xs) < _MIN_VISIBLE_FRAMES:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    # 3. 지표 계산
    net_x = (xs[-1] - xs[0]) * config.SKIP_BOOK_DIRECTION_SIGN
    total_x_movement = sum(abs(xs[t] - xs[t - 1]) for t in range(1, len(xs)))
    direction_ratio = abs(net_x) / total_x_movement if total_x_movement > 0 else 0.0
    y_range = max(ys) - min(ys)

    # 4. score 매핑 (각 임계값에서 0.7)
    net_score = config.SUCCESS_THRESHOLD + (
        net_x - config.SKIP_BOOK_NET_X_THRESHOLD
    ) * _NET_SCALE
    move_score = config.SUCCESS_THRESHOLD + (
        total_x_movement - config.SKIP_BOOK_X_MOVEMENT_THRESHOLD
    ) * _MOVE_SCALE
    dir_score = config.SUCCESS_THRESHOLD + (
        direction_ratio - config.SKIP_BOOK_DIRECTION_RATIO_THRESHOLD
    ) * _DIR_SCALE
    arc_score = config.SUCCESS_THRESHOLD + (
        y_range - config.SKIP_BOOK_ARC_THRESHOLD
    ) * _ARC_SCALE
    score = clamp_score(min(net_score, move_score, dir_score, arc_score))

    logger.debug(
        "skip_book visibleFrames=%d netX=%.3f totalXMovement=%.3f directionRatio=%.2f "
        "yRange=%.3f score=%.2f",
        len(xs),
        net_x,
        total_x_movement,
        direction_ratio,
        y_range,
        score,
    )

    if is_success(score):
        return MissionCheckResponse(
            success=True, score=score, reason_code=constants.REASON_MISSION_SUCCESS
        )

    # 5. 실패 사유: 총 이동량 부족 우선, 그 외(방향/도달/곡선)는 BOOK_NOT_TURNED
    if total_x_movement < config.SKIP_BOOK_X_MOVEMENT_THRESHOLD:
        reason_code = constants.REASON_MOVEMENT_TOO_SMALL
    else:
        reason_code = constants.REASON_BOOK_NOT_TURNED
    return MissionCheckResponse(success=False, score=score, reason_code=reason_code)
