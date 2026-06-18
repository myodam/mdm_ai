"""동작 판정 서비스 계층.

라우터와 detector 사이에서 다음을 담당한다.
1. poseFrames 유효성 검사 (비어 있으면 INVALID_POSE_DATA)
2. missionType 에 맞는 detector 선택 (없으면 UNKNOWN_MISSION_TYPE)
3. detector 실행 및 결과(MissionCheckResponse) 반환

AI 서버는 missionType + poseFrames 만으로 판정한다.
storyId / sceneId 는 받지 않으며, scene-mission 매핑/검증은 백엔드 책임이다.
사용자 message / nextAction / nextSceneId 도 생성하지 않는다.
"""

from __future__ import annotations

from typing import Callable, Sequence

from app.core import constants
from app.detectors import (
    open_gourd_detector,
    protect_swallow_detector,
    receive_seed_detector,
)
from app.schemas.mission_schema import MissionCheckRequest, MissionCheckResponse
from app.schemas.pose_schema import PoseFrame

# missionType -> detector.detect 함수
DetectFn = Callable[[Sequence[PoseFrame]], MissionCheckResponse]

DETECTOR_REGISTRY: dict[str, DetectFn] = {
    constants.MISSION_PROTECT_SWALLOW: protect_swallow_detector.detect,
    constants.MISSION_RECEIVE_SEED: receive_seed_detector.detect,
    constants.MISSION_OPEN_GOURD: open_gourd_detector.detect,
}


def check_mission(request: MissionCheckRequest) -> MissionCheckResponse:
    # 1. poseFrames 유효성
    if not request.pose_frames:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_INVALID_POSE_DATA
        )

    # 2. missionType 기준 detector 선택
    detect = DETECTOR_REGISTRY.get(request.mission_type)
    if detect is None:
        # AI 서버가 지원하지 않는 missionType
        return MissionCheckResponse(
            success=False,
            score=0.0,
            error_code=constants.ERROR_UNKNOWN_MISSION_TYPE,
        )

    # 3. detector 실행
    return detect(request.pose_frames)
