"""skip_book detector 테스트 (책 넘기기, 동작형)."""

from app.core import constants
from app.detectors import skip_book_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(timestamp: float, rx: float, ry: float, wrist_vis: float = 0.92) -> PoseFrame:
    return PoseFrame(
        timestamp=timestamp,
        landmarks=PoseLandmarks(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            rightWrist=Landmark(x=rx, y=ry, visibility=wrist_vis),
        ),
    )


def test_sideways_sweep_success():
    # 오른손이 오른쪽(0.70)에서 왼쪽(0.38)으로 스윕 + 충분한 이동량
    frames = [
        _frame(0.0, 0.70, 0.58),
        _frame(1.0, 0.62, 0.50),
        _frame(2.0, 0.48, 0.46),
        _frame(3.0, 0.38, 0.52),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_up_down_only_book_not_turned():
    # 위아래로만 크게 움직이고 좌우 스윕은 거의 없음 → BOOK_NOT_TURNED
    frames = [
        _frame(0.0, 0.60, 0.40),
        _frame(1.0, 0.60, 0.60),
        _frame(2.0, 0.60, 0.40),
        _frame(3.0, 0.60, 0.60),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_BOOK_NOT_TURNED
    assert res.error_code is None


def test_barely_moves_movement_too_small():
    # 거의 정지 → MOVEMENT_TOO_SMALL
    frames = [
        _frame(0.0, 0.60, 0.50),
        _frame(1.0, 0.61, 0.50),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_MOVEMENT_TOO_SMALL
    assert res.error_code is None


def test_fewer_than_two_visible_frames_hand_not_visible():
    # 손목이 1개 프레임에서만 보임 → HAND_NOT_VISIBLE
    frames = [
        _frame(0.0, 0.70, 0.58, wrist_vis=0.92),
        _frame(1.0, 0.40, 0.50, wrist_vis=0.10),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE
    assert res.reason_code is None


def test_no_shoulder_user_not_detected():
    frames = [
        PoseFrame(
            timestamp=0.0,
            landmarks=PoseLandmarks(
                leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.1),
                rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.1),
                rightWrist=Landmark(x=0.70, y=0.58, visibility=0.9),
            ),
        ),
        PoseFrame(
            timestamp=1.0,
            landmarks=PoseLandmarks(
                leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.1),
                rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.1),
                rightWrist=Landmark(x=0.40, y=0.52, visibility=0.9),
            ),
        ),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_USER_NOT_DETECTED


def test_require_arc_success():
    # 좌우 스윕 + 세로 변화(곡선)까지 있으면 require_arc 에서도 성공
    frames = [
        _frame(0.0, 0.70, 0.58),
        _frame(1.0, 0.62, 0.46),
        _frame(2.0, 0.48, 0.46),
        _frame(3.0, 0.38, 0.52),
    ]
    res = skip_book_detector.detect(frames, require_arc=True)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS


def test_require_arc_flat_fails():
    # 좌우로는 충분히 움직이지만 세로 변화가 거의 없음 → require_arc 에서 실패
    frames = [
        _frame(0.0, 0.70, 0.50),
        _frame(1.0, 0.55, 0.50),
        _frame(2.0, 0.40, 0.50),
    ]
    res = skip_book_detector.detect(frames, require_arc=True)
    assert res.success is False
    assert res.reason_code == constants.REASON_BOOK_NOT_TURNED
