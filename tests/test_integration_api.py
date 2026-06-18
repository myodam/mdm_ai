"""Step 8 - API 레벨 통합 테스트.

POST /internal/ai/missions/check 를 TestClient 로 호출해
3개 missionType 의 성공/실패와 예외 처리를 한 번에 검증한다.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CHECK_URL = "/internal/ai/missions/check"
ALLOWED_KEYS = {"success", "score", "reasonCode", "errorCode"}
FORBIDDEN_KEYS = {"message", "nextAction", "nextSceneId", "warningCode"}


def _post(body: dict) -> dict:
    res = client.post(CHECK_URL, json=body)
    assert res.status_code == 200, res.text
    data = res.json()
    # 응답 키는 정확히 4개 (금지 필드 미포함)
    assert set(data.keys()) == ALLOWED_KEYS
    assert not (set(data.keys()) & FORBIDDEN_KEYS)
    return data


def _req(scene_id: str, mission_type: str, frames: list) -> dict:
    return {
        "storyId": "heungbu_nolbu",
        "sceneId": scene_id,
        "missionType": mission_type,
        "captureDurationSec": 5,
        "sampleFps": 5,
        "poseFrames": frames,
    }


def _lm(x, y, v=0.95):
    return {"x": x, "y": y, "visibility": v}


# --- receive_seed ---
def test_receive_seed_success():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.40, 0.62), "rightWrist": _lm(0.64, 0.24)}}]
    data = _post(_req("scene_002", "receive_seed", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"
    assert data["errorCode"] is None


def test_receive_seed_fail():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.40, 0.62), "rightWrist": _lm(0.60, 0.62)}}]
    data = _post(_req("scene_002", "receive_seed", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "HAND_NOT_RAISED"


# --- protect_swallow ---
def test_protect_swallow_success():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
        "leftWrist": _lm(0.49, 0.57), "rightWrist": _lm(0.51, 0.57)}}]
    data = _post(_req("scene_001", "protect_swallow", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"


def test_protect_swallow_fail():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
        "leftWrist": _lm(0.30, 0.60), "rightWrist": _lm(0.70, 0.60)}}]
    data = _post(_req("scene_001", "protect_swallow", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "HANDS_TOO_FAR"


# --- open_gourd ---
def test_open_gourd_success():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
        "leftWrist": _lm(0.20, 0.46), "rightWrist": _lm(0.80, 0.46)}}]
    data = _post(_req("scene_003", "open_gourd", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"


def test_open_gourd_fail():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
        "leftWrist": _lm(0.48, 0.58), "rightWrist": _lm(0.52, 0.58)}}]
    data = _post(_req("scene_003", "open_gourd", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "ARMS_NOT_WIDE"


# --- 예외 처리 ---
def test_empty_pose_frames():
    data = _post(_req("scene_002", "receive_seed", []))
    assert data["success"] is False
    assert data["errorCode"] == "INVALID_POSE_DATA"


def test_missing_required_landmarks():
    # 어깨만 있고 손목이 전혀 없음 → 어깨는 감지되나 손 미감지 → HAND_NOT_VISIBLE
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36)}}]
    data = _post(_req("scene_002", "receive_seed", frames))
    assert data["success"] is False
    assert data["errorCode"] == "HAND_NOT_VISIBLE"


def test_mission_mismatch():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.40, 0.62), "rightWrist": _lm(0.64, 0.24)}}]
    # scene_001 은 protect_swallow 여야 하는데 receive_seed 전달
    data = _post(_req("scene_001", "receive_seed", frames))
    assert data["success"] is False
    assert data["errorCode"] == "MISSION_MISMATCH"


def test_unknown_mission_type():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.40, 0.62), "rightWrist": _lm(0.64, 0.24)}}]
    body = _req("scene_002", "unknown_mission", frames)
    data = _post(body)
    assert data["success"] is False
    assert data["errorCode"] == "MISSION_MISMATCH"


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "ai-server"}
