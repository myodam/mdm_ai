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


def _req(mission_type: str, frames: list) -> dict:
    return {
        "missionType": mission_type,
        "captureDurationSec": 5,
        "sampleFps": 5,
        "poseFrames": frames,
    }


def _lm(x, y, v=0.95):
    return {"x": x, "y": y, "visibility": v}


# --- skip_book (양손 중 더 크게 움직인 손이 좌우로 쓸기, 방향 비강제) ---
def test_skip_book_success():
    frames = [
        {"timestamp": 0.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.30, 0.55)}},
        {"timestamp": 1.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.45, 0.50)}},
        {"timestamp": 2.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.60, 0.50)}},
        {"timestamp": 3.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.72, 0.56)}},
    ]
    data = _post(_req("skip_book", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"
    assert data["errorCode"] is None


def test_skip_book_fail():
    # 손이 거의 안 움직임 → MOVEMENT_TOO_SMALL
    frames = [
        {"timestamp": 0.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.50, 0.55), "rightWrist": _lm(0.55, 0.55)}},
        {"timestamp": 1.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.51, 0.55), "rightWrist": _lm(0.55, 0.55)}},
    ]
    data = _post(_req("skip_book", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "MOVEMENT_TOO_SMALL"


# --- receive_seed (두 손 모아 어깨 위) ---
def test_receive_seed_success():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.48, 0.24), "rightWrist": _lm(0.52, 0.24)}}]
    data = _post(_req("receive_seed", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"
    assert data["errorCode"] is None


def test_receive_seed_fail():
    # 두 손이 어깨 아래 → HAND_NOT_RAISED
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.48, 0.62), "rightWrist": _lm(0.52, 0.62)}}]
    data = _post(_req("receive_seed", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "HAND_NOT_RAISED"


# --- protect_swallow ---
def test_protect_swallow_success():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
        "leftWrist": _lm(0.49, 0.57), "rightWrist": _lm(0.51, 0.57)}}]
    data = _post(_req("protect_swallow", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"


def test_protect_swallow_fail():
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
        "leftWrist": _lm(0.30, 0.60), "rightWrist": _lm(0.70, 0.60)}}]
    data = _post(_req("protect_swallow", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "HANDS_TOO_FAR"


# --- open_gourd (박 썰기: 어깨 아래 + 같은 방향 좌우 이동) ---
def test_open_gourd_success():
    frames = [
        {"timestamp": 0.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.30, 0.60), "rightWrist": _lm(0.60, 0.60)}},
        {"timestamp": 1.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.48, 0.60), "rightWrist": _lm(0.78, 0.60)}},
        {"timestamp": 2.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.30, 0.60), "rightWrist": _lm(0.60, 0.60)}},
        {"timestamp": 3.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.48, 0.60), "rightWrist": _lm(0.78, 0.60)}},
    ]
    data = _post(_req("open_gourd", frames))
    assert data["success"] is True
    assert data["reasonCode"] == "MISSION_SUCCESS"


def test_open_gourd_fail():
    # 어깨 아래지만 거의 안 움직임 → MOVEMENT_TOO_SMALL
    frames = [
        {"timestamp": 0.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.30, 0.60), "rightWrist": _lm(0.60, 0.60)}},
        {"timestamp": 1.0, "landmarks": {
            "leftShoulder": _lm(0.42, 0.35), "rightShoulder": _lm(0.58, 0.35),
            "leftWrist": _lm(0.31, 0.61), "rightWrist": _lm(0.61, 0.61)}},
    ]
    data = _post(_req("open_gourd", frames))
    assert data["success"] is False
    assert data["reasonCode"] == "MOVEMENT_TOO_SMALL"


# --- 예외 처리 ---
def test_empty_pose_frames():
    data = _post(_req("receive_seed", []))
    assert data["success"] is False
    assert data["errorCode"] == "INVALID_POSE_DATA"


def test_missing_required_landmarks():
    # 어깨만 있고 손목이 전혀 없음 → 어깨는 감지되나 손 미감지 → HAND_NOT_VISIBLE
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36)}}]
    data = _post(_req("receive_seed", frames))
    assert data["success"] is False
    assert data["errorCode"] == "HAND_NOT_VISIBLE"


def test_unknown_mission_type():
    # detector registry 에 없는 missionType → UNKNOWN_MISSION_TYPE
    frames = [{"timestamp": 0.0, "landmarks": {
        "leftShoulder": _lm(0.42, 0.36), "rightShoulder": _lm(0.58, 0.36),
        "leftWrist": _lm(0.40, 0.62), "rightWrist": _lm(0.64, 0.24)}}]
    body = _req("unknown_mission", frames)
    data = _post(body)
    assert data["success"] is False
    assert data["errorCode"] == "UNKNOWN_MISSION_TYPE"


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "ai-server"}
