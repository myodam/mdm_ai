"""동작 판정 서비스 계층.

라우터와 detector 사이에서 다음을 담당한다.
1. poseFrames 유효성 검사 (비어 있으면 INVALID_POSE_DATA)
2. storyId / sceneId / missionType 조합 방어적 검증 (불일치 시 MISSION_MISMATCH)
3. missionType 에 맞는 detector 선택 및 실행
4. detector 결과(MissionCheckResponse) 반환

MISSION_MISMATCH 1차 검증은 백엔드 담당이지만, AI 서버에서도 방어적으로 확인한다.
사용자 message / nextAction / nextSceneId 는 생성하지 않는다.
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


def _is_valid_combination(story_id: str, scene_id: str, mission_type: str) -> bool:
    scenes = constants.MISSION_BY_SCENE.get(story_id)
    if scenes is None:
        return False
    return scenes.get(scene_id) == mission_type


def check_mission(request: MissionCheckRequest) -> MissionCheckResponse:
    # 1. poseFrames 유효성
    if not request.pose_frames:
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_INVALID_POSE_DATA
        )

    # 2. storyId / sceneId / missionType 조합 방어적 검증
    if not _is_valid_combination(
        request.story_id, request.scene_id, request.mission_type
    ):
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_MISSION_MISMATCH
        )

    # 3. detector 선택
    detect = DETECTOR_REGISTRY.get(request.mission_type)
    if detect is None:
        # 매핑은 맞지만 아직 미구현 missionType 등 → 방어적으로 MISSION_MISMATCH
        return MissionCheckResponse(
            success=False, score=0.0, error_code=constants.ERROR_MISSION_MISMATCH
        )

    # 4. detector 실행
    return detect(request.pose_frames)
