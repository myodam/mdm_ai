"""Step 3 - 공통 유틸 테스트."""

from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks
from app.utils.geometry import calculate_distance, calculate_total_movement
from app.utils.pose_utils import (
    find_best_frame,
    get_landmark,
    has_required_landmarks,
    is_visible,
)
from app.utils.score_utils import clamp_score, is_success


def _frame(timestamp: float, **landmarks: Landmark) -> PoseFrame:
    return PoseFrame(timestamp=timestamp, landmarks=PoseLandmarks(**landmarks))


def test_calculate_distance():
    a = Landmark(x=0.0, y=0.0)
    b = Landmark(x=3.0, y=4.0)
    assert calculate_distance(a, b) == 5.0


def test_calculate_total_movement():
    frames = [
        _frame(0.0, leftWrist=Landmark(x=0.0, y=0.0)),
        _frame(1.0, leftWrist=Landmark(x=0.0, y=0.1)),
        _frame(2.0, leftWrist=Landmark(x=0.0, y=0.3)),
    ]
    # 0.1 + 0.2 = 0.3
    assert abs(calculate_total_movement(frames, "leftWrist") - 0.3) < 1e-9


def test_is_visible_threshold():
    assert is_visible(Landmark(x=0.5, y=0.5, visibility=0.9)) is True
    assert is_visible(Landmark(x=0.5, y=0.5, visibility=0.3)) is False
    # visibility 가 None 이면 보이는 것으로 간주
    assert is_visible(Landmark(x=0.5, y=0.5)) is True
    # landmark 자체가 없으면 False
    assert is_visible(None) is False


def test_has_required_landmarks():
    frame = _frame(
        0.0,
        leftWrist=Landmark(x=0.4, y=0.6),
        rightWrist=Landmark(x=0.6, y=0.6),
    )
    assert has_required_landmarks(frame, ["leftWrist", "rightWrist"]) is True
    assert has_required_landmarks(frame, ["leftWrist", "leftShoulder"]) is False


def test_get_landmark():
    frame = _frame(0.0, nose=Landmark(x=0.5, y=0.2))
    assert get_landmark(frame, "nose").y == 0.2
    assert get_landmark(frame, "leftWrist") is None


def test_find_best_frame():
    frames = [
        _frame(0.0, leftWrist=Landmark(x=0.0, y=0.9)),
        _frame(1.0, leftWrist=Landmark(x=0.0, y=0.1)),
    ]
    # y 가 작을수록 점수 높게 주는 스코어 함수
    best, score = find_best_frame(
        frames, lambda f: 1.0 - get_landmark(f, "leftWrist").y
    )
    assert best.timestamp == 1.0
    assert abs(score - 0.9) < 1e-9


def test_find_best_frame_empty():
    best, score = find_best_frame([], lambda f: 1.0)
    assert best is None
    assert score == 0.0


def test_clamp_score():
    assert clamp_score(-0.5) == 0.0
    assert clamp_score(1.5) == 1.0
    assert clamp_score(0.42) == 0.42


def test_is_success():
    assert is_success(0.7) is True
    assert is_success(0.69) is False
    assert is_success(0.5, threshold=0.4) is True
