"""동작 판정 요청/응답 schema.

외부 JSON 은 camelCase, Python 내부는 snake_case 를 사용한다.
Pydantic alias 로 매핑하며, populate_by_name=True 로 두 방식 모두 허용한다.

응답에는 success / score / reasonCode / errorCode 4개 필드만 포함한다.
message / nextAction / nextSceneId / warningCode 는 절대 포함하지 않는다(백엔드 담당).
"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pose_schema import PoseFrame


class MissionCheckRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    story_id: str = Field(alias="storyId")
    scene_id: str = Field(alias="sceneId")
    mission_type: str = Field(alias="missionType")
    capture_duration_sec: float | None = Field(default=None, alias="captureDurationSec")
    sample_fps: float | None = Field(default=None, alias="sampleFps")
    pose_frames: list[PoseFrame] = Field(alias="poseFrames")


class MissionCheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    score: float
    reason_code: str | None = Field(default=None, alias="reasonCode")
    error_code: str | None = Field(default=None, alias="errorCode")
