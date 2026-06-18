# AI 서버 API 명세 (ai_api.md)

몸으로 넘기는 전래동화 - 흥부와 놀부 MVP / AI Server(FastAPI)

전체 흐름: `Unity → Backend → AI Server(FastAPI) → Backend → Unity`
AI 서버는 백엔드 내부 호출 전용이며, Unity 가 직접 호출하지 않습니다.

---

## 0. Backend 연동 요약 (필독)

```text
AI Server endpoint:
POST /internal/ai/missions/check

Request:
missionType
captureDurationSec
sampleFps
poseFrames

Response:
success
score
reasonCode
errorCode

AI 서버는 storyId / sceneId 를 받지 않음 (scene-mission 매핑/검증은 백엔드 책임).
AI 서버는 아래 필드를 절대 반환하지 않음:
message
nextAction
nextSceneId
warningCode
```

AI 서버는 **missionType + poseFrames 만으로** 동작을 판정합니다.
응답의 message / nextAction / nextSceneId / warningCode 는 모두 **백엔드가 생성**합니다.
AI 서버 기본 포트는 `9000` (`.env` 의 `APP_PORT`).

---

## 1. GET /health

헬스체크.

응답 (200):
```json
{ "status": "ok", "service": "ai-server" }
```

---

## 2. POST /internal/ai/missions/check

백엔드가 동작 판정을 요청하는 엔드포인트.

- Content-Type: `application/json`
- 외부 JSON 필드: camelCase

### 2.1 요청 schema (MissionCheckRequest)

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| missionType | string | 필수 | 미션 타입 (detector 선택 기준) |
| captureDurationSec | number | 선택 | 좌표 수집 시간 |
| sampleFps | number | 선택 | 초당 샘플링 프레임 수 |
| poseFrames | array | 필수 | PoseFrame 목록 |

> AI 서버는 `storyId` / `sceneId` 를 받지 않습니다. (scene-mission 매핑/검증은 백엔드 책임)

PoseFrame:

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| timestamp | number | 필수 | 미션 시작 후 경과 시간 |
| landmarks | object | 필수 | PoseLandmarks |

PoseLandmarks: `leftShoulder, rightShoulder, leftElbow, rightElbow, leftWrist, rightWrist, nose` (모두 선택, 그 외 키는 무시).
Landmark:

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| x | number | 필수 | 가로 위치 0~1 |
| y | number | 필수 | 세로 위치 0~1 (작을수록 화면 위쪽) |
| visibility | number | 선택 | 관절 가시도 0~1 (없으면 보이는 것으로 간주) |

### 2.2 응답 schema (MissionCheckResponse)

응답은 **다음 4개 필드만** 포함합니다.
`message / nextAction / nextSceneId / warningCode` 는 절대 포함하지 않습니다(백엔드 담당).

| 필드 | 타입 | 설명 |
|---|---|---|
| success | bool | 동작 성공 여부 |
| score | number | 0~1 동작 점수 |
| reasonCode | string \| null | 동작 판정 이유 (성공/동작 부족) |
| errorCode | string \| null | 판정 불가/시스템 예외 |

성공:
```json
{ "success": true, "score": 0.88, "reasonCode": "MISSION_SUCCESS", "errorCode": null }
```
동작 실패:
```json
{ "success": false, "score": 0.42, "reasonCode": "HANDS_TOO_FAR", "errorCode": null }
```
판정 불가:
```json
{ "success": false, "score": 0.0, "reasonCode": null, "errorCode": "HAND_NOT_VISIBLE" }
```

---

## 3. reasonCode 목록

| reasonCode | missionType | 의미 |
|---|---|---|
| MISSION_SUCCESS | 공통 | 미션 성공 (score ≥ 0.7) |
| LOW_SCORE | 공통 | 점수 미달 (예약) |
| BOOK_NOT_TURNED | skip_book | 오른손 좌우 스윕이 부족함 |
| MOVEMENT_TOO_SMALL | skip_book / open_gourd | 손 전체 이동량이 부족함 |
| HANDS_TOO_FAR | protect_swallow | 양손 사이 거리가 멂 |
| HANDS_NOT_CENTERED | protect_swallow | 양손이 몸 중앙에서 벗어남 |
| HAND_NOT_RAISED | receive_seed | 손이 충분히 올라가지 않음 |
| ARMS_NOT_WIDE | open_gourd | 양팔이 충분히 벌어지지 않음 |

## 4. errorCode 목록

| errorCode | 발생 | 의미 |
|---|---|---|
| USER_NOT_DETECTED | AI | 주요 관절(어깨 등)이 거의 감지되지 않음 |
| HAND_NOT_VISIBLE | AI | 손목 좌표가 없거나 visibility 미달 |
| INVALID_POSE_DATA | AI | poseFrames 가 비었거나 유효하지 않음 |
| UNKNOWN_MISSION_TYPE | AI | detector registry 에 없는 missionType |
| AI_SERVER_ERROR | Backend | AI 호출 실패 (AI 서버는 직접 반환하지 않음) |

> `MISSION_MISMATCH`(scene-mission 불일치)는 AI 서버가 storyId/sceneId 를 더 이상 받지 않으므로
> 백엔드 전용입니다. AI 서버는 지원하지 않는 missionType 에 대해 `UNKNOWN_MISSION_TYPE` 을 반환합니다.

### errorCode 판정 우선순위 (AI 서버)
1. poseFrames 비었거나 유효하지 않음 → `INVALID_POSE_DATA`
2. missionType 이 detector registry 에 없음 → `UNKNOWN_MISSION_TYPE`
3. 주요 관절(어깨) 거의 미감지 → `USER_NOT_DETECTED`
4. 손목 좌표 없음 / 손목 visibility 미달 → `HAND_NOT_VISIBLE`
5. 동작은 감지됐으나 기준 부족 → `reasonCode`

---

## 5. 장면별 요청 예시

### scene_000 / skip_book (오른손 책 넘기기, 동작형)
오른손목이 여러 프레임에 걸쳐 좌우로 이동해야 하므로 poseFrame 이 2개 이상 필요합니다.
```json
{
  "missionType": "skip_book",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    { "timestamp": 0.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
      "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
      "rightWrist": { "x": 0.70, "y": 0.58, "visibility": 0.92 } } },
    { "timestamp": 1.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
      "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
      "rightWrist": { "x": 0.62, "y": 0.50, "visibility": 0.92 } } },
    { "timestamp": 2.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
      "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
      "rightWrist": { "x": 0.48, "y": 0.46, "visibility": 0.92 } } },
    { "timestamp": 3.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
      "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
      "rightWrist": { "x": 0.38, "y": 0.52, "visibility": 0.92 } } }
  ]
}
```

### scene_001 / protect_swallow (두 손 모으기)
```json
{
  "missionType": "protect_swallow",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    { "timestamp": 0.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
      "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
      "leftWrist": { "x": 0.49, "y": 0.57, "visibility": 0.93 },
      "rightWrist": { "x": 0.51, "y": 0.57, "visibility": 0.93 } } }
  ]
}
```

### scene_002 / receive_seed (한 손 들기)
```json
{
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    { "timestamp": 0.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
      "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
      "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
      "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 } } }
  ]
}
```

### scene_003 / open_gourd (양팔 크게 벌리기)
```json
{
  "missionType": "open_gourd",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    { "timestamp": 0.0, "landmarks": {
      "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
      "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
      "leftWrist": { "x": 0.20, "y": 0.46, "visibility": 0.91 },
      "rightWrist": { "x": 0.80, "y": 0.46, "visibility": 0.91 } } }
  ]
}
```

---

## 6. 판정 임계값 (초기값, `.env`/config 로 조정 가능)

| 항목 | 기본값 |
|---|---|
| SUCCESS_THRESHOLD | 0.7 |
| VISIBILITY_THRESHOLD | 0.6 |
| PROTECT_SWALLOW_HAND_DISTANCE_THRESHOLD | 0.18 |
| PROTECT_SWALLOW_CENTER_DIFF_THRESHOLD | 0.2 |
| RECEIVE_SEED_HAND_RAISE_MARGIN | 0.05 |
| OPEN_GOURD_WRIST_WIDTH_RATIO | 1.6 |
| OPEN_GOURD_MOVEMENT_THRESHOLD | 0.4 |
| SKIP_BOOK_X_RANGE_THRESHOLD | 0.20 |
| SKIP_BOOK_MOVEMENT_THRESHOLD | 0.25 |
| SKIP_BOOK_ARC_THRESHOLD (require_arc 시) | 0.08 |

대상 연령(4~7세)을 고려해 기준은 너그럽게 잡았으며, Unity 실제 좌표로 보정합니다.
