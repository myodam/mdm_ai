"""MediaPipe 포즈 좌표 schema.

외부 JSON 은 camelCase (leftShoulder, rightWrist ...) 를 그대로 사용한다.
landmark 이름 자체가 camelCase 이므로 PoseLandmarks 는 필드명을 camelCase 로 둔다.
"""

from pydantic import BaseModel, ConfigDict, Field


class Landmark(BaseModel):
    """단일 관절 좌표. x, y 는 0~1 정규화, y 가 작을수록 화면 위쪽."""

    x: float
    y: float
    visibility: float | None = None


class PoseLandmarks(BaseModel):
    """한 프레임의 주요 관절 모음.

    Unity 가 보내는 7개 주요 좌표만 명시한다.
    그 외 MediaPipe 랜드마크가 추가로 와도 무시한다(extra="ignore").
    모든 필드는 선택값이며, 없으면 None 으로 처리한다.
    """

    model_config = ConfigDict(extra="ignore")

    leftShoulder: Landmark | None = None
    rightShoulder: Landmark | None = None
    leftElbow: Landmark | None = None
    rightElbow: Landmark | None = None
    leftWrist: Landmark | None = None
    rightWrist: Landmark | None = None
    nose: Landmark | None = None


class PoseFrame(BaseModel):
    """미션 수행 중 수집된 한 프레임."""

    timestamp: float
    landmarks: PoseLandmarks
