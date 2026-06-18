"""Step 6 - protect_swallow detector 테스트."""

from app.core import constants
from app.detectors import protect_swallow_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(**landmarks: Landmark) -> PoseFrame:
    return PoseFrame(timestamp=0.0, landmarks=PoseLandmarks(**landmarks))


def test_hands_close_center_success():
    # 두 손이 가깝고(0.02) 몸 중앙(0.5)에 모임 → 성공
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.98),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.49, y=0.57, visibility=0.93),
            rightWrist=Landmark(x=0.51, y=0.57, visibility=0.93),
        )
    ]
    res = protect_swallow_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_hands_too_far():
    # 손 사이 거리 큼(0.40) → HANDS_TOO_FAR
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.98),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.30, y=0.60, visibility=0.91),
            rightWrist=Landmark(x=0.70, y=0.60, visibility=0.91),
        )
    ]
    res = protect_swallow_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_HANDS_TOO_FAR
    assert res.error_code is None


def test_hands_not_centered():
    # 손은 가깝지만(0.02) 몸 중앙에서 크게 벗어남(centerDiff 0.35) → HANDS_NOT_CENTERED
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.98),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.84, y=0.50, visibility=0.91),
            rightWrist=Landmark(x=0.86, y=0.50, visibility=0.91),
        )
    ]
    res = protect_swallow_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_HANDS_NOT_CENTERED
    assert res.error_code is None


def test_low_wrist_visibility_hand_not_visible():
    # 어깨는 보이나 양손목 visibility 낮음 → HAND_NOT_VISIBLE
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.98),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.49, y=0.57, visibility=0.2),
            rightWrist=Landmark(x=0.51, y=0.57, visibility=0.1),
        )
    ]
    res = protect_swallow_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE
    assert res.reason_code is None


def test_no_shoulder_user_not_detected():
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.1),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.1),
            leftWrist=Landmark(x=0.49, y=0.57, visibility=0.9),
            rightWrist=Landmark(x=0.51, y=0.57, visibility=0.9),
        )
    ]
    res = protect_swallow_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_USER_NOT_DETECTED


def test_best_frame_across_frames():
    # 앞 프레임은 손이 멂(실패), 나중 프레임에서 두 손을 중앙에 모음(성공)
    # → bestFrame 기준으로 success true
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.98),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.30, y=0.60, visibility=0.91),
            rightWrist=Landmark(x=0.70, y=0.60, visibility=0.91),
        ),
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.98),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.49, y=0.57, visibility=0.93),
            rightWrist=Landmark(x=0.51, y=0.57, visibility=0.93),
        ),
    ]
    res = protect_swallow_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
