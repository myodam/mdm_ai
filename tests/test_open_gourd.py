"""open_gourd detector 테스트 (박 썰기: 어깨 아래 + 같은 방향 좌우 이동)."""

from app.core import constants
from app.detectors import open_gourd_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(
    timestamp: float,
    lx: float,
    rx: float,
    ly: float = 0.60,
    ry: float = 0.60,
    lw_vis: float = 0.92,
    rw_vis: float = 0.92,
    shoulder_vis: float = 0.97,
) -> PoseFrame:
    return PoseFrame(
        timestamp=timestamp,
        landmarks=PoseLandmarks(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=shoulder_vis),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=shoulder_vis),
            leftWrist=Landmark(x=lx, y=ly, visibility=lw_vis),
            rightWrist=Landmark(x=rx, y=ry, visibility=rw_vis),
        ),
    )


def _sawing_same_direction():
    # 두 손이 함께 좌우로 이동(같은 방향), 어깨 아래
    return [
        _frame(0.0, 0.30, 0.60),
        _frame(1.0, 0.48, 0.78),
        _frame(2.0, 0.30, 0.60),
        _frame(3.0, 0.48, 0.78),
    ]


def test_sawing_same_direction_success():
    res = open_gourd_detector.detect(_sawing_same_direction())
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_hands_too_high():
    # 손이 어깨보다 위(y < shoulder.y) → HAND_POSITION_TOO_HIGH
    frames = [
        _frame(0.0, 0.30, 0.60, ly=0.20, ry=0.20),
        _frame(1.0, 0.48, 0.78, ly=0.20, ry=0.20),
        _frame(2.0, 0.30, 0.60, ly=0.20, ry=0.20),
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_HAND_POSITION_TOO_HIGH


def test_barely_moves_movement_too_small():
    # 어깨 아래지만 거의 안 움직임 → MOVEMENT_TOO_SMALL
    frames = [
        _frame(0.0, 0.30, 0.60),
        _frame(1.0, 0.31, 0.61),
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_MOVEMENT_TOO_SMALL


def test_opposite_direction_sawing_too_small():
    # 양손이 서로 반대 방향(중심 고정, 같은방향 구간 없음) → SAWING_MOTION_TOO_SMALL
    frames = [
        _frame(0.0, 0.30, 0.75),
        _frame(1.0, 0.45, 0.60),
        _frame(2.0, 0.30, 0.75),
        _frame(3.0, 0.45, 0.60),
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_SAWING_MOTION_TOO_SMALL


def test_one_wrist_invisible_hand_not_visible():
    frames = [
        _frame(0.0, 0.30, 0.60, rw_vis=0.1),
        _frame(1.0, 0.48, 0.78, rw_vis=0.1),
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE


def test_no_shoulder_user_not_detected():
    frames = [
        _frame(0.0, 0.30, 0.60, shoulder_vis=0.1),
        _frame(1.0, 0.48, 0.78, shoulder_vis=0.1),
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_USER_NOT_DETECTED
