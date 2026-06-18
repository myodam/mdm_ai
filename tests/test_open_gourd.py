"""Step 7 - open_gourd detector 테스트."""

from app.core import constants
from app.detectors import open_gourd_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(timestamp: float = 0.0, **landmarks: Landmark) -> PoseFrame:
    return PoseFrame(timestamp=timestamp, landmarks=PoseLandmarks(**landmarks))


def _wide_frame(timestamp: float = 0.0) -> PoseFrame:
    # 어깨폭 0.16, 손목폭 0.60 → ratio 3.75, 손이 어깨 바깥으로 벌어짐
    return _frame(
        timestamp,
        leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
        rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
        leftWrist=Landmark(x=0.20, y=0.46, visibility=0.91),
        rightWrist=Landmark(x=0.80, y=0.46, visibility=0.91),
    )


def test_arms_wide_success():
    res = open_gourd_detector.detect([_wide_frame()])
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
    assert res.score >= 0.7


def test_arms_narrow_arms_not_wide():
    # 손목이 거의 모여 있음 → ARMS_NOT_WIDE
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.48, y=0.58, visibility=0.91),
            rightWrist=Landmark(x=0.52, y=0.58, visibility=0.91),
        )
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_ARMS_NOT_WIDE
    assert res.error_code is None


def test_movement_too_small_when_required():
    # 자세는 충분히 벌어졌지만 두 프레임이 동일 → 이동량 0
    frames = [_wide_frame(0.0), _wide_frame(2.0)]
    res = open_gourd_detector.detect(frames, require_movement=True)
    assert res.success is False
    assert res.reason_code == constants.REASON_MOVEMENT_TOO_SMALL
    assert res.error_code is None


def test_movement_ok_when_required_success():
    # 휘두르듯 손목이 프레임마다 크게 움직임 (양손 각각 0.6 이동 → 합 1.2 > 0.4)
    def f(ts, lx, rx):
        return _frame(
            ts,
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=lx, y=0.46, visibility=0.91),
            rightWrist=Landmark(x=rx, y=0.46, visibility=0.91),
        )

    # frame0 은 양팔 충분히 벌어진 자세(bestFrame), 이후 좌우로 휘두름
    frames = [f(0.0, 0.10, 0.90), f(1.0, 0.40, 0.60), f(2.0, 0.10, 0.90)]
    res = open_gourd_detector.detect(frames, require_movement=True)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS


def test_low_wrist_visibility_hand_not_visible():
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.20, y=0.46, visibility=0.2),
            rightWrist=Landmark(x=0.80, y=0.46, visibility=0.1),
        )
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE
    assert res.reason_code is None


def test_best_frame_across_frames():
    # 앞 프레임은 손목이 좁음(실패), 나중 프레임에서 양팔을 충분히 벌림(성공)
    # → bestFrame 기준으로 success true
    frames = [
        _frame(
            leftShoulder=Landmark(x=0.42, y=0.35, visibility=0.97),
            rightShoulder=Landmark(x=0.58, y=0.35, visibility=0.97),
            leftWrist=Landmark(x=0.48, y=0.58, visibility=0.91),
            rightWrist=Landmark(x=0.52, y=0.58, visibility=0.91),
        ),
        _wide_frame(2.0),
    ]
    res = open_gourd_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.error_code is None
