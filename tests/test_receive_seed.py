"""receive_seed detector 테스트 (두 손 모아 어깨 위)."""

from app.core import constants
from app.detectors import receive_seed_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(
    lw=(0.48, 0.24),
    rw=(0.52, 0.24),
    lw_vis: float = 0.92,
    rw_vis: float = 0.92,
    shoulder_vis: float = 0.97,
) -> PoseFrame:
    return PoseFrame(
        timestamp=0.0,
        landmarks=PoseLandmarks(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=shoulder_vis),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=shoulder_vis),
            leftWrist=Landmark(x=lw[0], y=lw[1], visibility=lw_vis),
            rightWrist=Landmark(x=rw[0], y=rw[1], visibility=rw_vis),
        ),
    )


def test_both_hands_up_together_success():
    # 두 손 모두 어깨 위(y=0.24 < 0.36) + 가까이(거리 0.04)
    res = receive_seed_detector.detect([_frame(lw=(0.48, 0.24), rw=(0.52, 0.24))])
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_hands_down_hand_not_raised():
    # 두 손이 어깨보다 아래 → HAND_NOT_RAISED
    res = receive_seed_detector.detect([_frame(lw=(0.48, 0.62), rw=(0.52, 0.62))])
    assert res.success is False
    assert res.reason_code == constants.REASON_HAND_NOT_RAISED


def test_one_hand_up_hand_not_raised():
    # 한 손만 올림(오른손 아래) → 성공 아님, HAND_NOT_RAISED
    res = receive_seed_detector.detect([_frame(lw=(0.48, 0.24), rw=(0.52, 0.62))])
    assert res.success is False
    assert res.reason_code == constants.REASON_HAND_NOT_RAISED


def test_raised_but_apart_hands_not_together():
    # 둘 다 어깨 위지만 멀리 떨어짐(거리 0.40) → HANDS_NOT_TOGETHER
    res = receive_seed_detector.detect([_frame(lw=(0.30, 0.24), rw=(0.70, 0.24))])
    assert res.success is False
    assert res.reason_code == constants.REASON_HANDS_NOT_TOGETHER


def test_one_wrist_invisible_hand_not_visible():
    # 오른손목이 안 보임 → 두 손 함께 보이는 프레임 없음 → HAND_NOT_VISIBLE
    res = receive_seed_detector.detect(
        [_frame(lw=(0.48, 0.24), rw=(0.52, 0.24), rw_vis=0.1)]
    )
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE


def test_no_shoulder_user_not_detected():
    res = receive_seed_detector.detect(
        [_frame(lw=(0.48, 0.24), rw=(0.52, 0.24), shoulder_vis=0.1)]
    )
    assert res.success is False
    assert res.error_code == constants.ERROR_USER_NOT_DETECTED


def test_best_frame_across_frames():
    # 첫 프레임 실패(손 내림), 둘째 프레임 성공(두 손 모아 위로)
    frames = [
        _frame(lw=(0.48, 0.62), rw=(0.52, 0.62)),
        _frame(lw=(0.48, 0.24), rw=(0.52, 0.24)),
    ]
    res = receive_seed_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
