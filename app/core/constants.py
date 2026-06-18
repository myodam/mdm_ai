"""상수 정의.

AI 서버는 사용자 메시지를 관리하지 않는다.
또한 storyId / sceneId 도 받지 않으며, scene-mission 매핑/검증은 백엔드 책임이다.
따라서 missionType / reasonCode / errorCode 만 상수로 관리한다.
"""

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
# UNKNOWN_MISSION_TYPE 는 detector registry 에 없는 missionType 이 들어온 경우.
# AI_SERVER_ERROR 는 백엔드가 AI 호출 실패를 감지했을 때 사용 (AI 서버가 직접 반환하지 않음).
ERROR_USER_NOT_DETECTED = "USER_NOT_DETECTED"
ERROR_HAND_NOT_VISIBLE = "HAND_NOT_VISIBLE"
ERROR_INVALID_POSE_DATA = "INVALID_POSE_DATA"
ERROR_UNKNOWN_MISSION_TYPE = "UNKNOWN_MISSION_TYPE"

# --- 주요 랜드마크 이름 ---
LEFT_SHOULDER = "leftShoulder"
RIGHT_SHOULDER = "rightShoulder"
LEFT_ELBOW = "leftElbow"
RIGHT_ELBOW = "rightElbow"
LEFT_WRIST = "leftWrist"
RIGHT_WRIST = "rightWrist"
NOSE = "nose"
