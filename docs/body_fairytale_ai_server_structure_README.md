# 몸으로 넘기는 전래동화 - AI 서버 폴더 구조 README

## 1. 문서 목적

본 문서는 **몸으로 넘기는 전래동화 - 흥부와 놀부 MVP**에서 AI 서버를 구현하기 위한 추천 폴더 구조와 각 파일의 역할을 정리한 README 문서입니다.

Claude 또는 코드 생성 도구가 이 문서를 읽고 다음 내용을 바로 이해할 수 있도록 작성합니다.

```text
- AI 서버의 역할
- FastAPI API 구조
- Pydantic schema 기준
- detector 분리 기준
- reasonCode / errorCode 반환 기준
- Claude 구현 시 주의사항
```

AI 서버는 Unity에서 직접 호출하지 않습니다.

전체 호출 흐름은 다음과 같습니다.

```text
Unity
→ Backend
→ AI Server(FastAPI)
→ Backend
→ Unity
```

---

## 2. AI 서버 역할

AI 서버는 백엔드가 내부적으로 호출하는 FastAPI 서버입니다.

AI 서버의 핵심 역할은 다음과 같습니다.

```text
1. 백엔드로부터 poseFrames를 전달받는다.
2. storyId, sceneId, missionType을 확인한다.
3. missionType에 맞는 동작 판정 로직을 실행한다.
4. MediaPipe 좌표를 기반으로 거리, 위치, 움직임 변화량을 계산한다.
5. success, score, reasonCode, errorCode를 백엔드에 반환한다.
```

AI 서버는 사용자에게 보여줄 메시지를 직접 생성하지 않습니다.

사용자 안내 문구인 `message`, 다음 진행 상태인 `nextAction`, 다음 장면 ID인 `nextSceneId`는 백엔드에서 결정합니다.

AI 서버는 DB에 직접 저장하지 않습니다.

DB 저장, 사용자 진행 상태 관리, 메시지 생성, `nextSceneId` 결정은 백엔드에서 담당합니다.

AI 서버가 반환하는 값은 다음 4개를 기준으로 합니다.

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

---

## 3. 추천 폴더 구조

```text
ai-server/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── mission_router.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── mission_schema.py
│   │   └── pose_schema.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── mission_service.py
│   │
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── protect_swallow_detector.py
│   │   ├── receive_seed_detector.py
│   │   └── open_gourd_detector.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── constants.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   ├── pose_utils.py
│   │   └── score_utils.py
│   │
│   └── exceptions/
│       ├── __init__.py
│       └── mission_exception.py
│
├── tests/
│   ├── __init__.py
│   ├── test_protect_swallow.py
│   ├── test_receive_seed.py
│   └── test_open_gourd.py
│
├── docs/
│   └── ai_api.md
│
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

기존 폴더 구조를 그대로 사용해도 됩니다.

다만 `message`를 AI 서버에서 관리하지 않기 때문에, `constants.py`에는 사용자 메시지 대신 `reasonCode`, `errorCode`, `missionType`, `sceneId`, threshold 값 위주로 관리합니다.

---

## 4. 폴더별 역할

## 4.1 app/main.py

FastAPI 앱의 시작점입니다.

여기서 FastAPI 객체를 만들고, `mission_router`를 등록합니다.

```text
역할:
- FastAPI 앱 생성
- 라우터 등록
- 헬스체크 API 등록
- CORS 설정
```

예상 API는 다음과 같습니다.

```text
GET /health
POST /internal/ai/missions/check
```

---

## 4.2 app/api/mission_router.py

백엔드가 호출하는 API 엔드포인트를 정의합니다.

AI 서버는 외부 사용자가 직접 호출하는 API가 아니라, 백엔드 내부 호출용 API로 사용합니다.

```text
역할:
- POST /internal/ai/missions/check 요청 수신
- 요청 데이터를 Pydantic schema로 검증
- mission_service 호출
- 판정 결과 반환
```

API 예시:

```text
POST /internal/ai/missions/check
```

요청 예시:

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

응답 예시:

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

AI 서버 응답에는 `message`, `nextAction`, `nextSceneId`를 포함하지 않습니다.

---

## 4.3 app/schemas/

요청과 응답 데이터 구조를 정의합니다.

API JSON은 백엔드와 Unity 연동을 고려하여 camelCase를 사용하고, Python 내부에서는 snake_case를 사용할 수 있습니다.

```text
mission_schema.py
→ MissionCheckRequest
→ MissionCheckResponse

pose_schema.py
→ Landmark
→ PoseFrame
→ PoseLandmarks
```

예시 역할:

```text
MissionCheckRequest:
- storyId
- sceneId
- missionType
- captureDurationSec
- sampleFps
- poseFrames

MissionCheckResponse:
- success
- score
- reasonCode
- errorCode
```

Python 내부 변수명 예시:

```text
story_id
scene_id
mission_type
capture_duration_sec
sample_fps
pose_frames
reason_code
error_code
```

Pydantic alias를 사용해서 camelCase JSON을 snake_case 변수로 매핑합니다.

---

## 4.4 app/services/mission_service.py

동작 판정의 흐름을 관리하는 서비스 계층입니다.

라우터에서 바로 detector를 호출하지 않고, service를 한 번 거치게 하면 구조가 깔끔해집니다.

```text
역할:
- storyId / sceneId / missionType 확인
- missionType에 맞는 detector 선택
- poseFrames 유효성 검사
- detector 실행
- detector 결과를 공통 응답 형태로 변환
```

예상 흐름:

```text
missionType == protect_swallow
→ protect_swallow_detector 실행

missionType == receive_seed
→ receive_seed_detector 실행

missionType == open_gourd
→ open_gourd_detector 실행
```

service는 detector 결과를 받아 다음 형태로 반환합니다.

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

---

## 4.5 app/detectors/

장면별 실제 판정 로직을 넣는 폴더입니다.

이번 MVP에서는 흥부와 놀부 3개 장면만 구현하면 됩니다.

```text
protect_swallow_detector.py
→ Scene 1. 다친 제비 보호하기
→ 두 손 모으기 판정

receive_seed_detector.py
→ Scene 2. 박씨 받기
→ 한 손 들기 판정

open_gourd_detector.py
→ Scene 3. 박 타기
→ 양팔 크게 벌리기 / 움직임 판정
```

각 detector는 공통적으로 다음 값을 반환합니다.

```text
success
score
reasonCode
errorCode
```

예시:

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

detector는 사용자 메시지를 반환하지 않습니다.

---

## 4.6 app/utils/geometry.py

좌표 계산에 필요한 공통 함수를 모아둡니다.

```text
역할:
- 두 점 사이 거리 계산
- x, y 차이 계산
- 각도 계산
- 프레임 간 이동량 계산
```

필요한 함수 예시:

```text
calculate_distance(point_a, point_b)
calculate_angle(point_a, point_b, point_c)
calculate_total_movement(frames, landmark_name)
```

이번 MVP에서 가장 많이 쓰는 함수는 distance 계산입니다.

```text
handDistance = distance(leftWrist, rightWrist)
shoulderWidth = distance(leftShoulder, rightShoulder)
wristWidth = distance(leftWrist, rightWrist)
```

---

## 4.7 app/utils/pose_utils.py

`poseFrames`에서 필요한 랜드마크를 꺼내거나, visibility를 확인하는 유틸 함수입니다.

```text
역할:
- 특정 프레임에서 leftWrist 가져오기
- 필수 landmark 존재 여부 확인
- visibility 기준 확인
- poseFrames가 비어 있는지 확인
- bestFrame 찾기
```

필요한 함수 예시:

```text
get_landmark(frame, "leftWrist")
has_required_landmarks(frame, required_names)
is_visible(landmark, threshold=0.6)
find_best_frame(pose_frames, scoring_function)
```

---

## 4.8 app/utils/score_utils.py

점수 계산을 공통화하는 폴더입니다.

```text
역할:
- 0~1 사이 score 보정
- score 기준 success 변환
- bestScore 찾기
```

예시 기준:

```text
score >= 0.7
→ success true

score < 0.7
→ success false
```

score 결과에 따라 success를 결정하고, detector에서 적절한 `reasonCode`를 함께 반환합니다.

---

## 4.9 app/core/config.py

환경변수와 서버 설정을 관리합니다.

```text
역할:
- 서버 환경 설정
- score threshold 관리
- visibility threshold 관리
- captureDuration 기본값 관리
```

예시 설정값:

```text
SUCCESS_THRESHOLD = 0.7
VISIBILITY_THRESHOLD = 0.6
DEFAULT_CAPTURE_DURATION_SEC = 5
DEFAULT_SAMPLE_FPS = 5
```

---

## 4.10 app/core/constants.py

`sceneId`, `missionType`, `reasonCode`, `errorCode` 등을 상수로 관리합니다.

AI 서버에서는 사용자 메시지를 관리하지 않습니다.

사용자 메시지는 백엔드에서 관리합니다.

```python
MISSION_PROTECT_SWALLOW = "protect_swallow"
MISSION_RECEIVE_SEED = "receive_seed"
MISSION_OPEN_GOURD = "open_gourd"

SCENE_001 = "scene_001"
SCENE_002 = "scene_002"
SCENE_003 = "scene_003"

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

장면과 미션 매칭도 여기서 관리할 수 있습니다.

```python
MISSION_BY_SCENE = {
    "heungbu_nolbu": {
        "scene_001": "protect_swallow",
        "scene_002": "receive_seed",
        "scene_003": "open_gourd"
    }
}
```

---

## 4.11 app/exceptions/mission_exception.py

AI 판정 중 발생할 수 있는 예외를 정의합니다.

```text
USER_NOT_DETECTED
HAND_NOT_VISIBLE
INVALID_POSE_DATA
MISSION_MISMATCH
```

`AI_SERVER_ERROR`는 주로 백엔드가 AI 서버 호출 실패를 감지했을 때 사용하는 에러 코드입니다.

따라서 AI 서버 내부에서는 직접 `AI_SERVER_ERROR`를 반환하기보다는, 내부 예외를 발생시키고 백엔드가 이를 `AI_SERVER_ERROR`로 변환하는 방식이 더 자연스럽습니다.

예외 처리를 한 곳에서 관리하면 응답 형식을 통일하기 좋습니다.

---

## 4.12 tests/

동작 판정 로직을 테스트하는 폴더입니다.

해커톤이라도 최소한 detector별 테스트 데이터는 만들어두는 것이 좋습니다.

```text
test_protect_swallow.py
→ 두 손이 가까우면 success true, reasonCode MISSION_SUCCESS
→ 두 손이 멀면 success false, reasonCode HANDS_TOO_FAR
→ 두 손이 몸 중앙에서 벗어나면 success false, reasonCode HANDS_NOT_CENTERED

test_receive_seed.py
→ 한 손이 어깨보다 위면 success true, reasonCode MISSION_SUCCESS
→ 양손이 모두 아래면 success false, reasonCode HAND_NOT_RAISED

test_open_gourd.py
→ 양팔이 어깨 너비보다 넓게 벌어지면 success true, reasonCode MISSION_SUCCESS
→ 손목 간 거리가 좁으면 success false, reasonCode ARMS_NOT_WIDE
```

---

## 5. 추천 개발 순서

해커톤에서는 아래 순서로 개발하는 것이 좋습니다.

```text
1. FastAPI 기본 서버 생성
2. /health API 생성
3. /internal/ai/missions/check API 생성
4. MissionCheckRequest / Response schema 작성
5. MissionCheckResponse에 success, score, reasonCode, errorCode 적용
6. receive_seed_detector 먼저 구현
7. receive_seed_detector가 reasonCode를 반환하도록 구현
8. protect_swallow_detector 구현
9. open_gourd_detector 구현
10. mission_service에서 missionType별 detector 연결
11. 백엔드와 API 연동 테스트
12. Unity에서 넘어오는 실제 poseFrames로 기준값 조정
```

가장 먼저 구현할 것은 `receive_seed`입니다.

이유는 한 손 들기 판정이 가장 단순하기 때문입니다.

```text
rightWrist.y < rightShoulder.y - 0.05
또는
leftWrist.y < leftShoulder.y - 0.05
```

이 미션이 성공하면 Unity → Backend → AI → Backend → Unity 전체 흐름을 빠르게 검증할 수 있습니다.

---

## 6. detector별 구현 기준

## 6.1 protect_swallow_detector.py

Scene 1의 두 손 모으기 미션을 판정합니다.

```text
storyId: heungbu_nolbu
sceneId: scene_001
missionType: protect_swallow
```

주요 좌표:

```text
leftShoulder
rightShoulder
leftWrist
rightWrist
```

계산 기준:

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

---

## 6.2 receive_seed_detector.py

Scene 2의 한 손 들기 미션을 판정합니다.

```text
storyId: heungbu_nolbu
sceneId: scene_002
missionType: receive_seed
```

주요 좌표:

```text
leftShoulder
rightShoulder
leftWrist
rightWrist
```

MediaPipe 좌표에서는 `y`값이 작을수록 화면 위쪽입니다.

계산 기준:

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

---

## 6.3 open_gourd_detector.py

Scene 3의 박 타기 미션을 판정합니다.

```text
storyId: heungbu_nolbu
sceneId: scene_003
missionType: open_gourd
```

주요 좌표:

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

## 7. 최종 추천 구조 요약

```text
ai-server/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── mission_router.py
│   ├── schemas/
│   │   ├── mission_schema.py
│   │   └── pose_schema.py
│   ├── services/
│   │   └── mission_service.py
│   ├── detectors/
│   │   ├── protect_swallow_detector.py
│   │   ├── receive_seed_detector.py
│   │   └── open_gourd_detector.py
│   ├── utils/
│   │   ├── geometry.py
│   │   ├── pose_utils.py
│   │   └── score_utils.py
│   ├── core/
│   │   ├── config.py
│   │   └── constants.py
│   └── exceptions/
│       └── mission_exception.py
├── tests/
├── docs/
├── .env
├── requirements.txt
└── README.md
```

이 구조로 가면 AI 파트의 역할이 명확해집니다.

```text
api
→ 요청을 받는 곳

schemas
→ 요청/응답 데이터 구조

services
→ 어떤 판정 로직을 실행할지 결정하는 곳

detectors
→ 실제 장면별 동작 판정 로직

utils
→ 거리, 각도, visibility, bestFrame 계산

core
→ 설정값, sceneId, missionType, reasonCode, errorCode 상수

exceptions
→ 예외 처리
```

---

## 8. Claude 구현 시 핵심 주의사항

Claude가 코드를 생성할 때 반드시 지켜야 하는 기준입니다.

```text
1. AI 서버는 message를 반환하지 않는다.
2. AI 서버는 nextAction을 반환하지 않는다.
3. AI 서버는 nextSceneId를 반환하지 않는다.
4. AI 서버는 DB 저장을 하지 않는다.
5. AI 서버는 success, score, reasonCode, errorCode만 반환한다.
6. API 외부 JSON 필드는 camelCase를 사용한다.
7. Python 내부 변수는 snake_case를 사용해도 된다.
8. Pydantic alias를 사용해 camelCase ↔ snake_case를 매핑한다.
9. detector는 사용자 메시지가 아니라 reasonCode만 반환한다.
10. 백엔드가 사용자 message, nextAction, nextSceneId, warningCode를 생성한다.
```
