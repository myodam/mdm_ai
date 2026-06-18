"""AI 판정 중 발생할 수 있는 예외.

AI 서버는 사용자 메시지를 만들지 않으므로, 예외는 errorCode 값만 담는다.
service 계층에서 이 예외를 잡아 MissionCheckResponse(errorCode=...) 로 변환한다.

AI_SERVER_ERROR 는 AI 서버가 직접 반환하지 않는다.
(백엔드가 AI 호출 실패를 감지했을 때 사용하는 코드)
"""

from __future__ import annotations

from app.core import constants


class MissionError(Exception):
    """AI 판정 예외 베이스. error_code 를 보유한다."""

    error_code: str = constants.ERROR_INVALID_POSE_DATA

    def __init__(self, error_code: str | None = None) -> None:
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.error_code)


class InvalidPoseDataError(MissionError):
    """poseFrames 가 비었거나 필수 좌표 구조가 잘못된 경우."""

    error_code = constants.ERROR_INVALID_POSE_DATA


class UserNotDetectedError(MissionError):
    """주요 관절(어깨 등)이 거의 감지되지 않는 경우."""

    error_code = constants.ERROR_USER_NOT_DETECTED


class HandNotVisibleError(MissionError):
    """손목 좌표가 없거나 visibility 가 기준보다 낮은 경우."""

    error_code = constants.ERROR_HAND_NOT_VISIBLE


class MissionMismatchError(MissionError):
    """storyId / sceneId / missionType 조합이 맞지 않는 경우(방어적 검증)."""

    error_code = constants.ERROR_MISSION_MISMATCH
