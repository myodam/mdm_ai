"""Step 4 - receive_seed detector 테스트."""

from app.core import constants
from app.detectors import receive_seed_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(**landmarks: Landmark) -> PoseFrame:
    return PoseFrame(timestamp=0.0, landmarks=PoseLandmarks(**landmarks))


def test_one_hand_raised_success():
    # 오른손목 y(0.24) < 오른어깨 y(0.36) - 0.05 → 성공
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=0.97),
            leftWrist=Landmark(x=0.40, y=0.62, visibility=0.90),
            rightWrist=Landmark(x=0.64, y=0.24, visibility=0.92),
        )
    ]
    res = receive_seed_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_both_hands_down_fail():
    # 양손 모두 어깨보다 아래 → 실패, HAND_NOT_RAISED
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=0.97),
            leftWrist=Landmark(x=0.40, y=0.62, visibility=0.90),
            rightWrist=Landmark(x=0.60, y=0.62, visibility=0.90),
        )
    ]
    res = receive_seed_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_HAND_NOT_RAISED
    assert res.error_code is None


def test_low_wrist_visibility_hand_not_visible():
    # 어깨는 보이지만 양손목 visibility 낮음 → HAND_NOT_VISIBLE
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=0.97),
            leftWrist=Landmark(x=0.40, y=0.24, visibility=0.2),
            rightWrist=Landmark(x=0.64, y=0.24, visibility=0.1),
        )
    ]
    res = receive_seed_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE
    assert res.reason_code is None


def test_no_shoulder_user_not_detected():
    # 어깨/손목 모두 visibility 낮음 → 사람 미감지 우선
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=0.1),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=0.1),
            leftWrist=Landmark(x=0.40, y=0.62, visibility=0.1),
            rightWrist=Landmark(x=0.60, y=0.62, visibility=0.1),
        )
    ]
    res = receive_seed_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_USER_NOT_DETECTED


def test_best_frame_across_frames():
    # 첫 프레임은 손 내림, 두번째 프레임에서 손 듦 → bestFrame 기준 성공
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=0.97),
            leftWrist=Landmark(x=0.40, y=0.62, visibility=0.90),
            rightWrist=Landmark(x=0.60, y=0.62, visibility=0.90),
        ),
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.36, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.36, visibility=0.97),
            leftWrist=Landmark(x=0.40, y=0.62, visibility=0.90),
            rightWrist=Landmark(x=0.64, y=0.20, visibility=0.92),
        ),
    ]
    res = receive_seed_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
