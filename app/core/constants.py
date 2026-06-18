"""상수 정의.

AI 서버는 사용자 메시지를 관리하지 않는다.
storyId / sceneId / missionType / reasonCode / errorCode 와
장면-미션 매핑만 상수로 관리한다.
"""

# --- Story ---
STORY_HEUNGBU_NOLBU = "heungbu_nolbu"

# --- Scene ---
SCENE_001 = "scene_001"
SCENE_002 = "scene_002"
SCENE_003 = "scene_003"

# --- Mission ---
MISSION_PROTECT_SWALLOW = "protect_swallow"
MISSION_RECEIVE_SEED = "receive_seed"
MISSION_OPEN_GOURD = "open_gourd"

# --- reasonCode (동작은 감지됐으나 성공/부족 판정) ---
REASON_MISSION_SUCCESS = "MISSION_SUCCESS"
REASON_LOW_SCORE = "LOW_SCORE"
REASON_HANDS_TOO_FAR = "HANDS_TOO_FAR"
REASON_HANDS_NOT_CENTERED = "HANDS_NOT_CENTERED"
REASON_HAND_NOT_RAISED = "HAND_NOT_RAISED"
REASON_ARMS_NOT_WIDE = "ARMS_NOT_WIDE"
REASON_MOVEMENT_TOO_SMALL = "MOVEMENT_TOO_SMALL"

# --- errorCode (판정 자체가 불가능한 경우) ---
# AI 서버가 직접 반환하는 것: USER_NOT_DETECTED / HAND_NOT_VISIBLE / INVALID_POSE_DATA
# MISSION_MISMATCH 는 기본적으로 백엔드 담당이나, AI 서버에서도 방어적으로 사용 가능.
# AI_SERVER_ERROR 는 백엔드가 AI 호출 실패를 감지했을 때 사용 (AI 서버가 직접 반환하지 않음).
ERROR_USER_NOT_DETECTED = "USER_NOT_DETECTED"
ERROR_HAND_NOT_VISIBLE = "HAND_NOT_VISIBLE"
ERROR_INVALID_POSE_DATA = "INVALID_POSE_DATA"
ERROR_MISSION_MISMATCH = "MISSION_MISMATCH"

# --- 장면-미션 매핑 (storyId -> sceneId -> missionType) ---
MISSION_BY_SCENE = {
    STORY_HEUNGBU_NOLBU: {
        SCENE_001: MISSION_PROTECT_SWALLOW,
        SCENE_002: MISSION_RECEIVE_SEED,
        SCENE_003: MISSION_OPEN_GOURD,
    }
}

# --- 주요 랜드마크 이름 ---
LEFT_SHOULDER = "leftShoulder"
RIGHT_SHOULDER = "rightShoulder"
LEFT_ELBOW = "leftElbow"
RIGHT_ELBOW = "rightElbow"
LEFT_WRIST = "leftWrist"
RIGHT_WRIST = "rightWrist"
NOSE = "nose"
