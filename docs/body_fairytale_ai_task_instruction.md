# 몸으로 넘기는 전래동화 - AI 파트 작업 지시서

## 1. 작업 목적

이 문서는 **몸으로 넘기는 전래동화 - 흥부와 놀부 MVP**에서 Claude가 **AI 서버 파트만** 구현할 수 있도록 작업 범위를 명확히 정의한 문서입니다.

이번 프로젝트의 전체 구조는 다음과 같습니다.

```text
Unity
→ Backend
→ AI Server(FastAPI)
→ Backend
→ Unity
```

Claude는 이 중에서 **AI Server(FastAPI)** 영역만 작업합니다.

Unity, Backend, DB, 화면 전환, 사용자 메시지 생성 로직은 Claude의 작업 범위가 아닙니다.

---

## 2. Claude 작업 범위

Claude가 작업해야 하는 범위는 다음과 같습니다.

```text
1. FastAPI 기반 AI 서버 구현
2. /health API 구현
3. /internal/ai/missions/check API 구현
4. MediaPipe poseFrames 요청 schema 구현
5. success / score / reasonCode / errorCode 응답 schema 구현
6. missionType에 따른 detector 분기 구현
7. protect_swallow 동작 판정 구현
8. receive_seed 동작 판정 구현
9. open_gourd 동작 판정 구현
10. 좌표 계산 유틸 함수 구현
11. visibility, score, bestFrame 계산 로직 구현
12. detector별 단위 테스트 작성
```

Claude는 **AI 서버가 백엔드로부터 받은 poseFrames를 분석해서 동작 성공 여부를 판단하는 로직**만 구현합니다.

---

## 3. Claude가 작업하지 말아야 할 범위

Claude는 다음 기능을 구현하지 않습니다.

```text
1. Unity 화면 구현
2. Unity MediaPipe 연동 코드
3. Unity 장면 전환 코드
4. Backend API 구현
5. Backend DB 저장 로직
6. 사용자 message 생성 로직
7. nextAction 생성 로직
8. nextSceneId 생성 로직
9. warningCode 생성 로직
10. 로그인 / 회원가입 기능
11. 사용자별 진행 상태 관리
12. WebSocket 실시간 스트리밍
13. 실제 딥러닝 모델 학습
```

특히 아래 값들은 AI 서버에서 만들지 않습니다.

```text
message
nextAction
nextSceneId
warningCode
```

위 값들은 모두 Backend가 생성합니다.

AI 서버는 아래 값만 반환합니다.

```text
success
score
reasonCode
errorCode
```

---

## 4. AI 서버의 역할

AI 서버는 백엔드가 내부적으로 호출하는 FastAPI 서버입니다.

AI 서버의 역할은 다음과 같습니다.

```text
1. Backend로부터 storyId, sceneId, missionType, poseFrames를 전달받는다.
2. 요청 데이터 구조가 올바른지 확인한다.
3. missionType에 맞는 detector를 선택한다.
4. MediaPipe 좌표를 기반으로 동작을 판정한다.
5. success, score, reasonCode, errorCode를 반환한다.
```

AI 서버는 DB에 직접 저장하지 않습니다.

AI 서버는 사용자에게 보여줄 문장을 만들지 않습니다.

AI 서버는 다음 장면을 결정하지 않습니다.

---

## 5. API 구조

### 5.1 Health Check API

```text
GET /health
```

응답 예시:

```json
{
  "status": "ok",
  "service": "ai-server"
}
```

### 5.2 동작 판정 API

```text
POST /internal/ai/missions/check
```

이 API는 Backend가 AI Server를 호출할 때 사용합니다.

Unity가 직접 호출하지 않습니다.

---

## 6. 요청 JSON 구조

Backend가 AI Server에 보내는 요청은 다음 구조를 따릅니다.

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_001",
  "missionType": "protect_swallow",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.45, "y": 0.48, "visibility": 0.94 },
        "rightElbow": { "x": 0.55, "y": 0.48, "visibility": 0.94 },
        "leftWrist": { "x": 0.49, "y": 0.58, "visibility": 0.91 },
        "rightWrist": { "x": 0.51, "y": 0.58, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    }
  ]
}
```

외부 API JSON 필드는 camelCase를 사용합니다.

Python 내부 변수는 snake_case를 사용해도 됩니다.

Pydantic alias를 사용해 camelCase와 snake_case를 매핑합니다.

---

## 7. 응답 JSON 구조

AI Server는 다음 구조로만 응답합니다.

### 7.1 성공 응답

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### 7.2 동작 실패 응답

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

### 7.3 판정 불가 응답

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "HAND_NOT_VISIBLE"
}
```

AI Server 응답에는 절대 아래 필드를 포함하지 않습니다.

```text
message
nextAction
nextSceneId
warningCode
```

---

## 8. 구현할 폴더 구조

Claude는 아래 구조를 기준으로 AI 서버를 구현합니다.

```text
ai-server/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── mission_router.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── mission_schema.py
│   │   └── pose_schema.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── mission_service.py
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── protect_swallow_detector.py
│   │   ├── receive_seed_detector.py
│   │   └── open_gourd_detector.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── constants.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   ├── pose_utils.py
│   │   └── score_utils.py
│   └── exceptions/
│       ├── __init__.py
│       └── mission_exception.py
├── tests/
│   ├── __init__.py
│   ├── test_protect_swallow.py
│   ├── test_receive_seed.py
│   └── test_open_gourd.py
├── docs/
│   └── ai_api.md
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 9. 파일별 구현 기준

### 9.1 app/main.py

FastAPI 앱의 시작점입니다.

구현 내용:

```text
1. FastAPI 앱 생성
2. mission_router 등록
3. GET /health 구현
4. CORS 설정
```

### 9.2 app/api/mission_router.py

동작 판정 API를 정의합니다.

구현 내용:

```text
1. POST /internal/ai/missions/check 엔드포인트 생성
2. MissionCheckRequest로 요청 검증
3. mission_service.check_mission 호출
4. MissionCheckResponse 반환
```

### 9.3 app/schemas/pose_schema.py

MediaPipe 좌표 구조를 정의합니다.

구현할 schema:

```text
Landmark
PoseFrame
PoseLandmarks
```

Landmark 필드:

```text
x: float
y: float
visibility: float | None
```

PoseFrame 필드:

```text
timestamp: float
landmarks: PoseLandmarks
```

### 9.4 app/schemas/mission_schema.py

동작 판정 요청과 응답 schema를 정의합니다.

구현할 schema:

```text
MissionCheckRequest
MissionCheckResponse
```

MissionCheckRequest 필드:

```text
storyId
sceneId
missionType
captureDurationSec
sampleFps
poseFrames
```

MissionCheckResponse 필드:

```text
success
score
reasonCode
errorCode
```

### 9.5 app/services/mission_service.py

missionType에 따라 detector를 선택하고 실행합니다.

처리 흐름:

```text
1. poseFrames가 비어 있는지 확인
2. storyId / sceneId / missionType 조합 확인
3. missionType에 맞는 detector 선택
4. detector 실행
5. detector 결과 반환
```

missionType 매핑:

```text
protect_swallow → protect_swallow_detector
receive_seed → receive_seed_detector
open_gourd → open_gourd_detector
```

### 9.6 app/detectors/protect_swallow_detector.py

Scene 1의 두 손 모으기 동작을 판정합니다.

미션 정보:

```text
storyId: heungbu_nolbu
sceneId: scene_001
missionType: protect_swallow
```

필요 좌표:

```text
leftShoulder
rightShoulder
leftWrist
rightWrist
```

계산 방식:

```text
handDistance = distance(leftWrist, rightWrist)

bodyCenterX = (leftShoulder.x + rightShoulder.x) / 2
handsCenterX = (leftWrist.x + rightWrist.x) / 2
centerDiff = abs(handsCenterX - bodyCenterX)
```

성공 조건 예시:

```text
leftWrist.visibility >= 0.6
rightWrist.visibility >= 0.6
handDistance < 0.18
centerDiff < 0.2
```

반환 기준:

```text
성공:
success = true
reasonCode = MISSION_SUCCESS

양손 사이가 너무 멀면:
success = false
reasonCode = HANDS_TOO_FAR

양손이 몸 중앙에서 벗어나면:
success = false
reasonCode = HANDS_NOT_CENTERED
```

### 9.7 app/detectors/receive_seed_detector.py

Scene 2의 한 손 들기 동작을 판정합니다.

미션 정보:

```text
storyId: heungbu_nolbu
sceneId: scene_002
missionType: receive_seed
```

필요 좌표:

```text
leftShoulder
rightShoulder
leftWrist
rightWrist
```

MediaPipe 좌표에서는 `y`값이 작을수록 화면 위쪽입니다.

계산 방식:

```text
leftHandRaised = leftWrist.y < leftShoulder.y - 0.05
rightHandRaised = rightWrist.y < rightShoulder.y - 0.05
```

성공 조건 예시:

```text
leftHandRaised == true 또는 rightHandRaised == true
leftWrist.visibility >= 0.6 또는 rightWrist.visibility >= 0.6
```

반환 기준:

```text
성공:
success = true
reasonCode = MISSION_SUCCESS

손이 충분히 올라가지 않으면:
success = false
reasonCode = HAND_NOT_RAISED
```

### 9.8 app/detectors/open_gourd_detector.py

Scene 3의 양팔 크게 벌리기 또는 휘두르기 동작을 판정합니다.

미션 정보:

```text
storyId: heungbu_nolbu
sceneId: scene_003
missionType: open_gourd
```

필요 좌표:

```text
leftShoulder
rightShoulder
leftWrist
rightWrist
```

기본 자세 판정:

```text
shoulderWidth = distance(leftShoulder, rightShoulder)
wristWidth = distance(leftWrist, rightWrist)
```

성공 조건 예시:

```text
leftWrist.visibility >= 0.6
rightWrist.visibility >= 0.6
wristWidth > shoulderWidth * 1.6
leftWrist.x < leftShoulder.x
rightWrist.x > rightShoulder.x
```

선택적 움직임 판정:

```text
leftMovement = totalMovement(leftWrist over poseFrames)
rightMovement = totalMovement(rightWrist over poseFrames)
totalArmMovement = leftMovement + rightMovement
```

움직임 성공 조건 예시:

```text
totalArmMovement > 0.4
```

반환 기준:

```text
성공:
success = true
reasonCode = MISSION_SUCCESS

양팔이 충분히 벌어지지 않으면:
success = false
reasonCode = ARMS_NOT_WIDE

팔 움직임이 너무 작으면:
success = false
reasonCode = MOVEMENT_TOO_SMALL
```

---

## 10. 상수 기준

AI 서버에서는 사용자 메시지를 상수로 관리하지 않습니다.

상수로 관리할 값은 다음과 같습니다.

```text
storyId
sceneId
missionType
reasonCode
errorCode
threshold
```

예시:

```python
STORY_HEUNGBU_NOLBU = "heungbu_nolbu"

SCENE_001 = "scene_001"
SCENE_002 = "scene_002"
SCENE_003 = "scene_003"

MISSION_PROTECT_SWALLOW = "protect_swallow"
MISSION_RECEIVE_SEED = "receive_seed"
MISSION_OPEN_GOURD = "open_gourd"

REASON_MISSION_SUCCESS = "MISSION_SUCCESS"
REASON_LOW_SCORE = "LOW_SCORE"
REASON_HANDS_TOO_FAR = "HANDS_TOO_FAR"
REASON_HANDS_NOT_CENTERED = "HANDS_NOT_CENTERED"
REASON_HAND_NOT_RAISED = "HAND_NOT_RAISED"
REASON_ARMS_NOT_WIDE = "ARMS_NOT_WIDE"
REASON_MOVEMENT_TOO_SMALL = "MOVEMENT_TOO_SMALL"

ERROR_USER_NOT_DETECTED = "USER_NOT_DETECTED"
ERROR_HAND_NOT_VISIBLE = "HAND_NOT_VISIBLE"
ERROR_INVALID_POSE_DATA = "INVALID_POSE_DATA"
ERROR_MISSION_MISMATCH = "MISSION_MISMATCH"
```

---

## 11. threshold 기준

초기 threshold는 다음 값을 사용합니다.

```text
SUCCESS_THRESHOLD = 0.7
VISIBILITY_THRESHOLD = 0.6

PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD = 0.18
PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD = 0.2

RECEIVE_SEED_HAND_RAISE_MARGIN = 0.05

OPEN_GOURD_WRIST_WIDTH_RATIO = 1.6
OPEN_GOURD_MOVEMENT_THRESHOLD = 0.4
```

이 값들은 Unity 실제 테스트 후 조정할 수 있도록 `config.py` 또는 `constants.py`에서 관리합니다.

---

## 12. 테스트 기준

Claude는 최소한 다음 테스트를 작성합니다.

```text
test_receive_seed.py
- 한 손이 어깨보다 위에 있으면 success true
- 양손이 어깨보다 아래에 있으면 success false
- 손목 visibility가 낮으면 errorCode HAND_NOT_VISIBLE

test_protect_swallow.py
- 두 손이 가까우면 success true
- 두 손이 멀면 reasonCode HANDS_TOO_FAR
- 두 손이 몸 중앙에서 벗어나면 reasonCode HANDS_NOT_CENTERED

test_open_gourd.py
- 양팔이 충분히 벌어지면 success true
- 손목 간 거리가 좁으면 reasonCode ARMS_NOT_WIDE
- 움직임 기준 사용 시 이동량이 작으면 reasonCode MOVEMENT_TOO_SMALL
```

가장 먼저 `receive_seed` 테스트와 detector를 구현합니다.

한 손 들기 판정이 가장 단순하기 때문에 전체 API 연결 테스트에 적합합니다.

---

## 13. 개발 순서

Claude는 아래 순서로 개발합니다.

```text
1. FastAPI 기본 서버 생성
2. /health API 구현
3. MissionCheckRequest / MissionCheckResponse schema 구현
4. PoseFrame / Landmark schema 구현
5. /internal/ai/missions/check API 구현
6. constants.py 작성
7. geometry.py 작성
8. pose_utils.py 작성
9. score_utils.py 작성
10. receive_seed_detector 구현
11. receive_seed 테스트 작성
12. mission_service에서 receive_seed 연결
13. protect_swallow_detector 구현
14. protect_swallow 테스트 작성
15. open_gourd_detector 구현
16. open_gourd 테스트 작성
17. 모든 detector를 mission_service에 연결
18. 더미 JSON으로 API 테스트
```

---

## 14. Claude 구현 시 핵심 주의사항

Claude가 코드를 생성할 때 반드시 지켜야 하는 기준입니다.

```text
1. AI 서버는 message를 반환하지 않는다.
2. AI 서버는 nextAction을 반환하지 않는다.
3. AI 서버는 nextSceneId를 반환하지 않는다.
4. AI 서버는 warningCode를 반환하지 않는다.
5. AI 서버는 DB 저장을 하지 않는다.
6. AI 서버는 success, score, reasonCode, errorCode만 반환한다.
7. API 외부 JSON 필드는 camelCase를 사용한다.
8. Python 내부 변수는 snake_case를 사용해도 된다.
9. Pydantic alias를 사용해 camelCase ↔ snake_case를 매핑한다.
10. detector는 사용자 메시지가 아니라 reasonCode만 반환한다.
11. 백엔드가 사용자 message, nextAction, nextSceneId, warningCode를 생성한다.
12. Unity와 직접 통신하는 코드는 작성하지 않는다.
13. WebSocket은 사용하지 않는다.
14. MediaPipe 실시간 추적 코드는 작성하지 않는다.
15. 이미 추출된 poseFrames를 입력으로 받아 판정하는 서버만 구현한다.
```

---

## 15. 최종 산출물

Claude가 최종적으로 만들어야 할 산출물은 다음과 같습니다.

```text
1. FastAPI AI 서버 코드
2. /health API
3. /internal/ai/missions/check API
4. Pydantic 요청/응답 schema
5. 3개 detector
   - protect_swallow_detector.py
   - receive_seed_detector.py
   - open_gourd_detector.py
6. 공통 유틸 함수
   - geometry.py
   - pose_utils.py
   - score_utils.py
7. constants.py / config.py
8. detector별 테스트 코드
9. 실행 방법이 포함된 README.md
10. 필요한 requirements.txt
```

최종적으로 AI 서버는 다음 요청을 받아야 합니다.

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_001",
  "missionType": "protect_swallow",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": []
}
```

그리고 다음 형식으로만 응답해야 합니다.

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```
