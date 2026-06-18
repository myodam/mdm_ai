"""Step 2 - schema 검증 테스트."""

import pytest
from pydantic import ValidationError

from app.schemas.mission_schema import MissionCheckRequest, MissionCheckResponse


def _valid_request_dict() -> dict:
    return {
        "missionType": "receive_seed",
        "captureDurationSec": 5,
        "sampleFps": 5,
        "poseFrames": [
            {
                "timestamp": 0.0,
                "landmarks": {
                    "leftShoulder": {"x": 0.42, "y": 0.36, "visibility": 0.97},
                    "rightShoulder": {"x": 0.58, "y": 0.36, "visibility": 0.97},
                    "leftWrist": {"x": 0.40, "y": 0.62, "visibility": 0.90},
                    "rightWrist": {"x": 0.64, "y": 0.24, "visibility": 0.92},
                },
            }
        ],
    }


def test_valid_request_passes_and_maps_camel_to_snake():
    req = MissionCheckRequest.model_validate(_valid_request_dict())
    assert req.mission_type == "receive_seed"
    assert req.capture_duration_sec == 5
    assert req.sample_fps == 5
    assert len(req.pose_frames) == 1
    # 좌표 접근 확인
    frame = req.pose_frames[0]
    assert frame.landmarks.rightWrist.y == 0.24


def test_missing_required_field_raises_validation_error():
    data = _valid_request_dict()
    del data["missionType"]
    with pytest.raises(ValidationError):
        MissionCheckRequest.model_validate(data)


def test_missing_pose_frames_raises_validation_error():
    data = _valid_request_dict()
    del data["poseFrames"]
    with pytest.raises(ValidationError):
        MissionCheckRequest.model_validate(data)


def test_response_serializes_camelcase_and_only_four_fields():
    resp = MissionCheckResponse(success=True, score=0.91, reason_code="MISSION_SUCCESS")
    dumped = resp.model_dump(by_alias=True)
    assert dumped == {
        "success": True,
        "score": 0.91,
        "reasonCode": "MISSION_SUCCESS",
        "errorCode": None,
    }
    # 금지 필드 미포함 확인
    for forbidden in ("message", "nextAction", "nextSceneId", "warningCode"):
        assert forbidden not in dumped


def test_response_error_case():
    resp = MissionCheckResponse(success=False, score=0.0, error_code="HAND_NOT_VISIBLE")
    dumped = resp.model_dump(by_alias=True)
    assert dumped["success"] is False
    assert dumped["reasonCode"] is None
    assert dumped["errorCode"] == "HAND_NOT_VISIBLE"
