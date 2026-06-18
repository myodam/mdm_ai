"""Scene 2. 박씨 받기 - 한 손 들기 판정.

missionType: receive_seed  (참고: 흥부와 놀부 scene_002 — AI 는 missionType 만 사용)

판정 기준 (MediaPipe 는 y 가 작을수록 위쪽):
    leftHandRaised  = leftWrist.y  < leftShoulder.y  - margin
    rightHandRaised = rightWrist.y < rightShoulder.y - margin
성공: 한쪽 손이라도 어깨보다 충분히 위 + 해당 손목 visible.

errorCode 우선순위:
    어깨가 어느 프레임에서도 감지되지 않음        -> USER_NOT_DETECTED
    어깨는 보이나 손목이 어느 프레임에서도 안 보임 -> HAND_NOT_VISIBLE
"""

from __future__ import annotations

from typing import Sequence

from app.core import config, constants
from app.schemas.mission_schema import MissionCheckResponse
from app.schemas.pose_schema import PoseFrame
from app.utils.pose_utils import get_landmark, is_visible
from app.utils.score_utils import clamp_score, is_success

_SIDES = (
    (constants.LEFT_WRIST, constants.LEFT_SHOULDER),
    (constants.RIGHT_WRIST, constants.RIGHT_SHOULDER),
)


def _any_visible(pose_frames: Sequence[PoseFrame], name: str) -> bool:
    return any(is_visible(get_landmark(f, name)) for f in pose_frames)


def detect(pose_frames: Sequence[PoseFrame]) -> MissionCheckResponse:
    margin = config.RECEIVE_SEED_HAND_RAISE_MARGIN

    # 어깨/손목 가시성 기반 errorCode 판정
    shoulder_seen = _any_visible(pose_frames, constants.LEFT_SHOULDER) or _any_visible(
        pose_frames, constants.RIGHT_SHOULDER
    )
    wrist_seen = _any_visible(pose_frames, constants.LEFT_WRIST) or _any_visible(
        pose_frames, constants.RIGHT_WRIST
    )

    if not shoulder_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_USER_NOT_DETECTED
        )
    if not wrist_seen:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    # 모든 프레임 x 양손에서 "어깨 대비 손이 올라간 정도(raise)"의 최댓값 사용 (bestFrame)
    best_raise = None  # shoulder.y - wrist.y, 클수록 위로 든 것
    for frame in pose_frames:
        for wrist_name, shoulder_name in _SIDES:
            wrist = get_landmark(frame, wrist_name)
            shoulder = get_landmark(frame, shoulder_name)
            if not is_visible(wrist) or not is_visible(shoulder):
                continue
            raise_amount = shoulder.y - wrist.y
            if best_raise is None or raise_amount > best_raise:
                best_raise = raise_amount

    if best_raise is None:
        # 손목/어깨가 같은 프레임에서 함께 보인 적이 없음
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_HAND_NOT_VISIBLE
        )

    # raise == margin 에서 정확히 임계값(0.7)이 되도록 매핑 → is_success 와 일치
    score = clamp_score(config.SUCCESS_THRESHOLD + (best_raise - margin) * 1.5)
    success = is_success(score)
    reason_code = (
        constants.REASON_MISSION_SUCCESS
        if success
        else constants.REASON_HAND_NOT_RAISED
    )
    return MissionCheckResponse(success=success, score=score, reason_code=reason_code)
