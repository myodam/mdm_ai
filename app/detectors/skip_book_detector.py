"""Scene 0. 책 넘기기 - skip_book 판정 (동작형).

missionType: skip_book  (참고: 흥부와 놀부 scene_000 — AI 는 missionType 만 사용)

UX 안내는 "왼손으로 책장을 넘겨주세요" 이지만, AI 는 **왼손에 고정하지 않는다.**
카메라 미러링 / MediaPipe 좌우 라벨 스왑 때문에 실제로 움직인 손이 rightWrist 로
잡힐 수 있으므로, **양손 중 가로 이동 폭(xRange)이 더 큰 손**을 책 넘긴 손으로 본다.

판정 방식 (선택손 = xRange 가 더 큰 손, 시간순 visible 프레임 기준):
    xRange        = max(x) - min(x)            # first-last 가 아닌 전체 범위
    totalMovement = Σ |x[t] - x[t-1]|          # 가로 누적 이동량
    yRange        = max(y) - min(y)            # 약한 곡선(보조 점수만)
방향(x 증가/감소)은 강제하지 않는다(미러링 대응).

성공: xRange ≥ X_RANGE AND totalMovement ≥ MOVEMENT (각 임계값에서 0.7 매핑 → score≥0.7)
    yRange 는 하드 게이트가 아니라 score 보조 요소.

errorCode:
    양손 모두 visible 프레임 < 2              -> HAND_NOT_VISIBLE
실패 reasonCode (우선순위):
    선택손 총 이동량 부족                      -> MOVEMENT_TOO_SMALL
    선택손 좌우 이동 폭 부족                   -> BOOK_NOT_TURNED
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

_X_SCALE = 1.5
_MOVE_SCALE = 1.5
_ARC_SCALE = 2.0  # yRange 보조 점수용 (게이트 아님)
_MIN_VISIBLE_FRAMES = 2


def _wrist_metrics(
    pose_frames: Sequence[PoseFrame], name: str
) -> tuple[int, float, float, float]:
    """한 손목의 (visible 프레임 수, xRange, totalMovement, yRange) 반환."""
    xs: list[float] = []
    ys: list[float] = []
    for frame in pose_frames:
        wrist = get_landmark(frame, name)
        if is_visible(wrist):
            xs.append(wrist.x)
            ys.append(wrist.y)
    if len(xs) < _MIN_VISIBLE_FRAMES:
        return len(xs), 0.0, 0.0, 0.0
    x_range = max(xs) - min(xs)
    y_range = max(ys) - min(ys)
    total_movement = sum(abs(xs[t] - xs[t - 1]) for t in range(1, len(xs)))
    return len(xs), x_range, total_movement, y_range


def detect(pose_frames: Sequence[PoseFrame]) -> MissionCheckResponse:
    left = _wrist_metrics(pose_frames, constants.LEFT_WRIST)
    right = _wrist_metrics(pose_frames, constants.RIGHT_WRIST)

    # 양손 모두 판정 가능한 프레임이 부족하면 손 미감지
    if left[0] < _MIN_VISIBLE_FRAMES and right[0] < _MIN_VISIBLE_FRAMES:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    # xRange 가 더 큰 손을 "책 넘긴 손"으로 선택 (왼손 고정 X)
    selected_name = "leftWrist" if left[1] >= right[1] else "rightWrist"
    _, x_range, total_movement, y_range = left if left[1] >= right[1] else right

    x_score = config.SUCCESS_THRESHOLD + (
        x_range - config.SKIP_BOOK_X_RANGE_THRESHOLD
    ) * _X_SCALE
    move_score = config.SUCCESS_THRESHOLD + (
        total_movement - config.SKIP_BOOK_MOVEMENT_THRESHOLD
    ) * _MOVE_SCALE
    # yRange 는 보조 "가점"만 (부족해도 감점/실패 없음, 곡선이 있으면 소폭 가산)
    arc_bonus = min(0.1, max(0.0, (y_range - config.SKIP_BOOK_ARC_THRESHOLD) * _ARC_SCALE))
    score = clamp_score(min(x_score, move_score) + arc_bonus)

    logger.debug(
        "skip_book selected=%s xRange=%.3f totalMovement=%.3f yRange=%.3f score=%.2f "
        "(left xR=%.3f mv=%.3f / right xR=%.3f mv=%.3f)",
        selected_name,
        x_range,
        total_movement,
        y_range,
        score,
        left[1],
        left[2],
        right[1],
        right[2],
    )

    if is_success(score):
        return MissionCheckResponse(
            success=True, score=score, reason_code=constants.REASON_MISSION_SUCCESS
        )

    # 실패 사유: 총 이동량 부족 우선, 그 다음 좌우 폭 부족
    if total_movement < config.SKIP_BOOK_MOVEMENT_THRESHOLD:
        reason_code = constants.REASON_MOVEMENT_TOO_SMALL
    else:
        reason_code = constants.REASON_BOOK_NOT_TURNED
    return MissionCheckResponse(success=False, score=score, reason_code=reason_code)
