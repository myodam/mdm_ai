"""skip_book detector 테스트.

양손 중 더 크게 움직인 손을 자동 선택해 좌우 스윕을 본다.
방향은 강제하지 않으며(미러링 대응), 전체 max-min xRange 를 사용한다.
"""

from app.core import constants
from app.detectors import skip_book_detector
from app.schemas.pose_schema import Landmark, PoseFrame, PoseLandmarks


def _frame(timestamp, left=None, right=None):
    lm = {
        "leftShoulder": Landmark(x=0.42, y=0.35, visibility=0.97),
        "rightShoulder": Landmark(x=0.58, y=0.35, visibility=0.97),
    }
    if left is not None:
        lm["leftWrist"] = Landmark(x=left[0], y=left[1], visibility=left[2] if len(left) > 2 else 0.92)
    if right is not None:
        lm["rightWrist"] = Landmark(x=right[0], y=right[1], visibility=right[2] if len(right) > 2 else 0.92)
    return PoseFrame(timestamp=timestamp, landmarks=PoseLandmarks(**lm))


def test_left_hand_sweep_success():
    # 왼손이 좌우로 크게 쓸기 (방향 무관)
    frames = [
        _frame(0.0, left=(0.30, 0.55)),
        _frame(1.0, left=(0.45, 0.50)),
        _frame(2.0, left=(0.60, 0.50)),
        _frame(3.0, left=(0.72, 0.56)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS
    assert res.score >= 0.7


def test_decreasing_direction_still_success():
    # x 감소 방향(미러링)이어도 성공해야 함 (방향 비강제)
    frames = [
        _frame(0.0, left=(0.72, 0.55)),
        _frame(1.0, left=(0.58, 0.50)),
        _frame(2.0, left=(0.44, 0.50)),
        _frame(3.0, left=(0.30, 0.56)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS


def test_right_hand_moves_left_fixed_success():
    # 왼손은 거의 고정, 오른손이 크게 움직임 → 오른손 자동 선택해서 성공
    frames = [
        _frame(0.0, left=(0.70, 0.85), right=(0.42, 0.60)),
        _frame(1.0, left=(0.70, 0.85), right=(0.55, 0.58)),
        _frame(2.0, left=(0.69, 0.85), right=(0.66, 0.60)),
        _frame(3.0, left=(0.70, 0.85), right=(0.60, 0.62)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS


def test_barely_moves_movement_too_small():
    frames = [
        _frame(0.0, left=(0.50, 0.50), right=(0.55, 0.50)),
        _frame(1.0, left=(0.51, 0.50), right=(0.55, 0.50)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_MOVEMENT_TOO_SMALL


def test_jitter_small_range_book_not_turned():
    # 좌우로 조금씩 떨어 총 이동량은 있으나 폭(xRange)이 작음 → BOOK_NOT_TURNED
    frames = [
        _frame(0.0, left=(0.50, 0.50)),
        _frame(1.0, left=(0.55, 0.50)),
        _frame(2.0, left=(0.50, 0.50)),
        _frame(3.0, left=(0.55, 0.50)),
        _frame(4.0, left=(0.50, 0.50)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.reason_code == constants.REASON_BOOK_NOT_TURNED


def test_yrange_zero_still_success():
    # 세로 변화가 거의 없어도(보조 점수) 가로 스윕만 충분하면 성공
    frames = [
        _frame(0.0, left=(0.30, 0.50)),
        _frame(1.0, left=(0.45, 0.50)),
        _frame(2.0, left=(0.60, 0.50)),
        _frame(3.0, left=(0.74, 0.50)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is True
    assert res.reason_code == constants.REASON_MISSION_SUCCESS


def test_no_wrist_visible_hand_not_visible():
    # 양손 모두 visible 프레임 < 2 (손목 미제공)
    frames = [_frame(0.0), _frame(1.0)]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE


def test_low_visibility_frames_filtered_hand_not_visible():
    # 손목이 들어오지만 visibility 낮아 모두 필터 → HAND_NOT_VISIBLE
    frames = [
        _frame(0.0, left=(0.30, 0.55, 0.2), right=(0.40, 0.60, 0.2)),
        _frame(1.0, left=(0.60, 0.50, 0.2), right=(0.55, 0.60, 0.2)),
    ]
    res = skip_book_detector.detect(frames)
    assert res.success is False
    assert res.error_code == constants.ERROR_HAND_NOT_VISIBLE
