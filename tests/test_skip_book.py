"""skip_book detector 테스트 (왼손이 오른쪽으로 한 번 곡선 스윕)."""

from app.core import constants
from app.detectors import skip_book_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(timestamp: float, lx: float, ly: float, wrist_vis: float = 0.92) -> PoseFrame:
    return PoseFrame(
        timestamp=timestamp,
        landmarks=PoseLandmarks(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=lx, y=ly, visibility=wrist_vis),
        ),
    )


def test_left_to_right_sweep_success():
    # 왼손 x 가 증가(왼→오른쪽), 한 방향, 약간의 y 곡선
    frames = [
        _frame(0.0, 0.30, 0.55),
        _frame(1.0, 0.45, 0.50),
        _frame(2.0, 0.60, 0.50),
        _frame(3.0, 0.72, 0.56),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_wrong_direction_book_not_turned():
    # 충분히 움직였지만 왼쪽으로 이동(오른쪽 도달 부족) → BOOK_NOT_TURNED
    frames = [
        _frame(0.0, 0.70, 0.55),
        _frame(1.0, 0.55, 0.50),
        _frame(2.0, 0.40, 0.50),
        _frame(3.0, 0.30, 0.56),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_BOOK_NOT_TURNED


def test_zigzag_book_not_turned():
    # 많이 움직이지만 한 방향이 아님(net 부족) → BOOK_NOT_TURNED
    frames = [
        _frame(0.0, 0.40, 0.55),
        _frame(1.0, 0.60, 0.50),
        _frame(2.0, 0.40, 0.50),
        _frame(3.0, 0.50, 0.56),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_BOOK_NOT_TURNED


def test_barely_moves_movement_too_small():
    frames = [
        _frame(0.0, 0.50, 0.50),
        _frame(1.0, 0.51, 0.50),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_MOVEMENT_TOO_SMALL


def test_fewer_than_two_visible_frames_hand_not_visible():
    frames = [
        _frame(0.0, 0.30, 0.55, wrist_vis=0.92),
        _frame(1.0, 0.70, 0.55, wrist_vis=0.10),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE


def test_no_shoulder_user_not_detected():
    frames = [
        PoseFrame(
            timestamp=0.0,
            landmarks=PoseLandmarks(
                leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.1),
                rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.1),
                leftWrist=Landmark(x=0.30, y=0.55, visibility=0.9),
            ),
        ),
        PoseFrame(
            timestamp=1.0,
            landmarks=PoseLandmarks(
                leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.1),
                rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.1),
                leftWrist=Landmark(x=0.70, y=0.55, visibility=0.9),
            ),
        ),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_USER_NOT_DETECTED


def test_mirrored_direction_sign(monkeypatch):
    # SIGN=-1 이면 x 감소(화면상 오른쪽)도 성공으로 인정
    monkeypatch.setattr(skip_book_detector.config, "SKIP_BOOK_DIRECTION_SIGN", -1.0)
    frames = [
        _frame(0.0, 0.72, 0.55),
        _frame(1.0, 0.60, 0.50),
        _frame(2.0, 0.45, 0.50),
        _frame(3.0, 0.30, 0.56),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
