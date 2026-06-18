# 몸으로 넘기는 전래동화 API 명세서

## 1. API 개요

본 문서는 **몸으로 넘기는 전래동화 - 흥부와 놀부 MVP** 개발을 위한 API 명세서입니다.

이번 프로젝트의 전체 통신 구조는 다음과 같습니다.

```
Unity
→ Backend
→ AI Server(FastAPI)
→ Backend
→ Unity
```

Unity는 AI 서버를 직접 호출하지 않고, 백엔드 API만 호출합니다.

백엔드는 Unity 요청을 검증한 뒤 AI 서버에 동작 판정을 요청합니다. AI 서버는 좌표 기반 판정 결과만 반환하고, 백엔드는 AI 판정 결과를 기반으로 사용자 메시지, 다음 진행 상태, 다음 장면 정보를 생성합니다.

이번 MVP에서는 로그인 기능을 구현하지 않기 때문에 `userId`는 사용하지 않습니다.

다만 `storyId`는 사용합니다. 현재 MVP에서는 「흥부와 놀부」 하나만 구현하지만, 추후 여러 동화가 추가될 경우 같은 `sceneId`가 동화마다 중복될 수 있기 때문입니다.

따라서 백엔드는 `storyId + sceneId + missionType` 조합을 기준으로 요청이 올바른지 검증합니다.

---

## 2. storyId 사용 기준

## 2.1 storyId를 사용하는 이유

현재 MVP에서는 다음 동화 하나만 사용합니다.

```
storyId: heungbu_nolbu
```

하지만 추후 여러 동화가 추가될 경우 `scene_001`, `scene_002` 같은 장면 ID는 동화마다 중복될 수 있습니다.

예시는 다음과 같습니다.

```
heungbu_nolbu / scene_001 → 다친 제비 보호하기
little_prince / scene_001 → 어린왕자가 별에 앉아 있는 장면
red_riding_hood / scene_001 → 숲길을 걷는 장면
```

따라서 `sceneId`만으로 장면을 구분하기보다, `storyId + sceneId` 조합으로 장면을 구분하는 것이 더 안전합니다.

---

## 2.2 Backend에서 storyId를 사용하는 위치

백엔드는 `storyId`를 다음 목적으로 사용합니다.

```
1. 지원하는 동화인지 확인
2. 해당 storyId 안에서 sceneId가 유효한지 확인
3. storyId + sceneId + missionType 조합이 올바른지 확인
4. 성공 시 storyId + sceneId 기준으로 nextSceneId 결정
5. 판정 결과 저장 시 어떤 동화의 결과인지 구분
```

즉, `storyId`는 현재 MVP에서는 확장성을 위한 필드이지만, 백엔드 검증과 저장 기준에서도 의미가 있으므로 유지합니다.

---

## 3. 역할 분리

## 3.1 Unity 역할

```
1. 동화 장면 출력
2. 현재 storyId, sceneId, missionType 관리
3. 미션 안내 UI 출력
4. MediaPipe로 사용자 포즈 좌표 추출
5. 3~5초 동안 poseFrames 수집
6. storyId, sceneId, missionType, poseFrames를 Backend로 전송
7. Backend 응답에 따라 성공/실패 UI 출력
8. 성공 시 nextSceneId 기준으로 다음 장면 전환
9. 실패 시 현재 장면에서 재도전 안내
```

Unity는 AI 서버를 직접 호출하지 않습니다.

Unity는 사용자가 현재 어떤 동화를 진행 중인지 알 수 있도록 `storyId`를 함께 전달합니다.

현재 MVP에서는 `storyId`를 `heungbu_nolbu`로 고정해서 사용할 수 있습니다.

---

## 3.2 Backend 역할

```
1. Unity 요청 수신
2. 요청 데이터 형식 검증
3. storyId가 지원하는 동화인지 확인
4. storyId 안에서 sceneId가 유효한지 확인
5. storyId + sceneId + missionType 조합이 올바른지 확인
6. AI Server에 동작 판정 요청
7. AI Server 응답 수신
8. reasonCode / errorCode 기준으로 message 생성
9. success와 storyId / sceneId 기준으로 nextAction / nextSceneId 생성
10. 판정 결과 저장
11. Unity에 최종 응답 반환
```

사용자에게 보여줄 `message`는 Backend가 관리합니다.

`nextAction`과 `nextSceneId`도 Backend가 결정합니다.

---

## 3.3 AI Server 역할

```
1. Backend로부터 poseFrames 수신
2. storyId, sceneId, missionType을 참고하여 판정 대상 확인
3. missionType에 맞는 동작 판정 로직 실행
4. MediaPipe 좌표 기반 거리, 위치, 움직임 계산
5. success / score / reasonCode / errorCode 반환
```

AI Server는 사용자 메시지인 `message`를 반환하지 않습니다.

AI Server는 다음 장면 정보인 `nextSceneId`도 결정하지 않습니다.

AI Server는 다음 진행 상태인 `nextAction`도 결정하지 않습니다.

AI Server는 DB에 직접 저장하지 않습니다.

AI Server는 `missionType`을 기준으로 detector를 선택합니다. `storyId`는 현재 MVP에서는 분기 핵심 값은 아니지만, 어떤 동화의 장면 판정인지 식별하기 위해 전달할 수 있습니다.

---

## 4. 공통 규칙

## 4.1 통신 방식

```
HTTP REST API
Content-Type: application/json
```

WebSocket은 사용하지 않습니다.

Unity는 미션 수행 시간 동안 MediaPipe 좌표를 수집한 뒤, 수집된 `poseFrames`를 HTTP 요청으로 한 번에 Backend에 전송합니다.

---

## 4.2 네이밍 규칙

API JSON 필드는 Unity와 Backend 연동을 고려하여 **camelCase**로 통일합니다.

```
storyId
sceneId
missionType
poseFrames
captureDurationSec
sampleFps
reasonCode
errorCode
warningCode
```

Python AI 서버 내부에서는 snake_case를 사용할 수 있지만, 외부 API 요청/응답은 camelCase를 사용합니다.

예시:

```
API JSON: captureDurationSec
Python 내부 변수: capture_duration_sec
```

---

## 4.3 미션 수행 시간

Unity는 미션 시작 후 3~5초 동안 MediaPipe 좌표를 수집합니다.

MVP에서는 구현 단순화를 위해 모든 미션을 5초로 통일할 수 있습니다.

```
captureDurationSec: 5
sampleFps: 5
전송 poseFrame 수: 약 25개
timestamp 예시: 0.0, 0.2, 0.4, ... 4.8
```

30fps 전체 데이터를 모두 전송하지 않고, 초당 5프레임 정도만 샘플링해서 전송합니다.

문서 예시에서는 가독성을 위해 일부 poseFrame만 작성할 수 있습니다.

---

## 4.4 Backend → Unity 공통 응답 필드

Backend가 Unity에 반환하는 최종 응답은 다음 필드를 기준으로 합니다.

```
success: 동작 성공 여부
sceneCleared: 현재 씬 클리어 여부
currentSceneId: 현재 씬 ID
nextSceneId: 다음 씬 ID
nextAction: 다음 동작
score: 동작 점수
reasonCode: 동작 판정 이유 코드
message: 사용자 안내 메시지
errorCode: 실패 또는 예외 코드
warningCode: 경고 코드
```

---

## 4.5 AI Server → Backend 공통 응답 필드

AI Server가 Backend에 반환하는 응답은 다음 필드를 기준으로 합니다.

```
success: 동작 성공 여부
score: 동작 점수
reasonCode: 동작 판정 이유 코드
errorCode: 예외 코드
```

AI Server 응답에는 `message`, `nextAction`, `nextSceneId`를 포함하지 않습니다.

---

# 5. Story / Scene / Mission 매핑

MVP에서는 「흥부와 놀부」 1개 동화와 3개 장면만 구현합니다.

## 5.1 MVP storyId

```
storyId: heungbu_nolbu
동화 이름: 흥부와 놀부
```

---

## 5.2 전체 매핑표

| storyId | sceneId | missionType | 장면 | 사용자 동작 | nextSceneId |
| --- | --- | --- | --- | --- | --- |
| heungbu_nolbu | scene_001 | protect_swallow | 다친 제비 보호하기 | 두 손 모으기 | scene_002 |
| heungbu_nolbu | scene_002 | receive_seed | 박씨 받기 | 한 손 들기 | scene_003 |
| heungbu_nolbu | scene_003 | open_gourd | 박 타기 | 양팔 크게 벌리기 | null |

마지막 장면인 `scene_003` 성공 시 Backend는 `nextAction`을 `ENDING`으로 반환합니다.

---

## 5.3 Backend 검증 기준

Backend는 AI Server를 호출하기 전에 다음 조합이 올바른지 확인합니다.

```
storyId + sceneId + missionType
```

예시:

```
storyId = heungbu_nolbu
sceneId = scene_001
missionType = protect_swallow
→ 정상 요청

storyId = heungbu_nolbu
sceneId = scene_001
missionType = receive_seed
→ 잘못된 요청
→ errorCode = MISSION_MISMATCH

storyId = unknown_story
sceneId = scene_001
missionType = protect_swallow
→ 지원하지 않는 동화
→ errorCode = MISSION_MISMATCH
```

해커톤 MVP에서는 에러코드를 너무 늘리지 않기 위해, 지원하지 않는 `storyId`도 `MISSION_MISMATCH`로 처리할 수 있습니다.

---

# 6. Unity → Backend API

## 6.1 동작 판정 요청 API

Unity가 미션 수행 후 MediaPipe 좌표 데이터를 Backend로 전송하는 API입니다.

```
POST /api/missions/check
```

---

## 6.2 요청 설명

Unity는 현재 동화 정보, 장면 정보, 미션 정보, 그리고 MediaPipe로 수집한 `poseFrames`를 Backend에 전달합니다.

Backend는 `storyId + sceneId + missionType` 조합이 올바른지 검증한 뒤 AI Server에 동작 판정을 요청합니다.

---

## 6.3 Request Body

아래 예시는 5초 동안 수집한 poseFrames 중 일부만 작성한 축약 예시입니다.

실제 요청에서는 `captureDurationSec: 5`, `sampleFps: 5` 기준으로 약 25개의 poseFrame이 전달됩니다.

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
        "leftShoulder": {
          "x": 0.42,
          "y": 0.35,
          "visibility": 0.98
        },
        "rightShoulder": {
          "x": 0.58,
          "y": 0.35,
          "visibility": 0.97
        },
        "leftElbow": {
          "x": 0.45,
          "y": 0.48,
          "visibility": 0.94
        },
        "rightElbow": {
          "x": 0.55,
          "y": 0.48,
          "visibility": 0.94
        },
        "leftWrist": {
          "x": 0.49,
          "y": 0.58,
          "visibility": 0.91
        },
        "rightWrist": {
          "x": 0.51,
          "y": 0.58,
          "visibility": 0.91
        },
        "nose": {
          "x": 0.50,
          "y": 0.20,
          "visibility": 0.95
        }
      }
    }
  ]
}
```

---

## 6.4 Request Field

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| storyId | string | 필수 | 동화 ID. MVP에서는 heungbu_nolbu |
| sceneId | string | 필수 | 현재 장면 ID |
| missionType | string | 필수 | 현재 미션 타입 |
| captureDurationSec | number | 필수 | Unity가 좌표를 수집한 시간 |
| sampleFps | number | 필수 | 초당 샘플링한 프레임 수 |
| poseFrames | array | 필수 | MediaPipe 포즈 프레임 목록 |

---

## 6.5 poseFrame 구조

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| timestamp | number | 필수 | 미션 시작 후 경과 시간 |
| landmarks | object | 필수 | MediaPipe landmark 목록 |

---

## 6.6 landmark 구조

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| x | number | 필수 | 화면 가로 위치, 0~1 |
| y | number | 필수 | 화면 세로 위치, 0~1 |
| visibility | number | 권장 | 해당 관절이 보이는 정도, 0~1 |

MediaPipe 좌표 기준으로 `y`값이 작을수록 화면 위쪽입니다.

---

# 7. Backend → Unity Response

## 7.1 성공 응답

동작 판정에 성공하고 다음 장면으로 이동할 수 있는 경우입니다.

```json
{
  "success": true,
  "sceneCleared": true,
  "currentSceneId": "scene_001",
  "nextSceneId": "scene_002",
  "nextAction": "NEXT_SCENE",
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "message": "좋아요! 제비를 조심스럽게 보호했어요.",
  "errorCode": null,
  "warningCode": null
}
```

---

## 7.2 실패 응답

동작 판정에는 실패했지만, 재시도가 가능한 경우입니다.

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "message": "두 손을 조금 더 가까이 모아주세요.",
  "errorCode": null,
  "warningCode": null
}
```

---

## 7.3 엔딩 응답

마지막 장면인 `scene_003`에서 성공한 경우입니다.

```json
{
  "success": true,
  "sceneCleared": true,
  "currentSceneId": "scene_003",
  "nextSceneId": null,
  "nextAction": "ENDING",
  "score": 0.86,
  "reasonCode": "MISSION_SUCCESS",
  "message": "힘차게 박을 탔어요! 박이 열렸어요.",
  "errorCode": null,
  "warningCode": null
}
```

---

# 8. Backend → AI Server API

## 8.1 AI 동작 판정 내부 API

Backend가 AI Server에 동작 판정을 요청하는 내부 API입니다.

```
POST /internal/ai/missions/check
```

AI Server는 FastAPI로 구현합니다.

AI Server는 동작 판정만 담당하고, 사용자 메시지, DB 저장, `nextSceneId`, `nextAction` 결정은 하지 않습니다.

---

## 8.2 Backend → AI Request Body

Backend는 AI 판정에 필요한 정보만 AI Server로 전달합니다.

`storyId`는 현재 MVP에서는 AI Server의 핵심 분기 기준은 아니지만, 어떤 동화의 장면 판정인지 식별하기 위해 전달할 수 있습니다.

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
        "leftShoulder": {
          "x": 0.42,
          "y": 0.35,
          "visibility": 0.98
        },
        "rightShoulder": {
          "x": 0.58,
          "y": 0.35,
          "visibility": 0.97
        },
        "leftWrist": {
          "x": 0.49,
          "y": 0.58,
          "visibility": 0.91
        },
        "rightWrist": {
          "x": 0.51,
          "y": 0.58,
          "visibility": 0.91
        }
      }
    }
  ]
}
```

---

## 8.3 Backend → AI Request Field

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| storyId | string | 필수 | 동화 ID. MVP에서는 heungbu_nolbu |
| sceneId | string | 필수 | 현재 장면 ID |
| missionType | string | 필수 | 현재 미션 타입 |
| captureDurationSec | number | 필수 | 좌표 수집 시간 |
| sampleFps | number | 필수 | 초당 샘플링 프레임 수 |
| poseFrames | array | 필수 | MediaPipe 포즈 프레임 목록 |

---

## 8.4 AI → Backend 성공 응답

AI Server는 메시지를 반환하지 않습니다.

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

---

## 8.5 AI → Backend 실패 응답

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

---

## 8.6 AI → Backend 예외 응답

AI Server에서 `poseFrames`를 판정할 수 없는 경우입니다.

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "INVALID_POSE_DATA"
}
```

---

# 9. NextAction 정의

`nextAction`은 Backend가 결정하여 Unity에 반환합니다.

| nextAction | 설명 | Unity 처리 |
| --- | --- | --- |
| NEXT_SCENE | 다음 장면으로 이동 | nextSceneId로 장면 전환 |
| RETRY | 현재 미션 재시도 | 현재 sceneId 유지, 힌트 출력 |
| ENDING | 엔딩 화면으로 이동 | 엔딩 연출 출력 |

---

# 10. ReasonCode 정의

`reasonCode`는 AI Server가 Backend에 전달하는 동작 판정 이유입니다.

사용자 메시지를 직접 담지 않고, Backend가 메시지를 매핑할 수 있도록 코드값만 전달합니다.

## 10.1 공통 reasonCode

| reasonCode | 의미 |
| --- | --- |
| MISSION_SUCCESS | 미션 성공 |
| LOW_SCORE | 동작 점수가 기준보다 낮음 |

---

## 10.2 Scene 1 - protect_swallow

| reasonCode | 의미 | Backend 메시지 예시 |
| --- | --- | --- |
| MISSION_SUCCESS | 두 손 모으기 성공 | 좋아요! 제비를 조심스럽게 보호했어요. |
| HANDS_TOO_FAR | 양손 사이 거리가 멀다 | 두 손을 조금 더 가까이 모아주세요. |
| HANDS_NOT_CENTERED | 양손이 몸 중앙에서 벗어남 | 두 손을 몸 가운데로 모아주세요. |

---

## 10.3 Scene 2 - receive_seed

| reasonCode | 의미 | Backend 메시지 예시 |
| --- | --- | --- |
| MISSION_SUCCESS | 한 손 들기 성공 | 잘했어요! 박씨를 받았어요. |
| HAND_NOT_RAISED | 손이 충분히 올라가지 않음 | 한 손을 어깨보다 높게 들어주세요. |

---

## 10.4 Scene 3 - open_gourd

| reasonCode | 의미 | Backend 메시지 예시 |
| --- | --- | --- |
| MISSION_SUCCESS | 양팔 벌리기 성공 | 힘차게 박을 탔어요! 박이 열렸어요. |
| ARMS_NOT_WIDE | 양팔이 충분히 벌어지지 않음 | 양팔을 더 크게 벌려주세요. |
| MOVEMENT_TOO_SMALL | 팔 움직임이 작음 | 팔을 더 크게 움직여주세요. |

---

# 11. ErrorCode 정의

`errorCode`는 판정 자체가 어렵거나 시스템 문제가 있을 때 사용합니다.

| errorCode | 발생 위치 | 의미 | Backend 메시지 예시 |
| --- | --- | --- | --- |
| USER_NOT_DETECTED | AI | 사용자가 화면에 감지되지 않음 | 카메라 앞에 서서 다시 시도해주세요. |
| HAND_NOT_VISIBLE | AI | 손목 좌표가 감지되지 않음 | 손이 화면 안에 보이도록 해주세요. |
| INVALID_POSE_DATA | Backend / AI | poseFrames가 없거나 필수 좌표가 누락됨 | 동작 정보를 확인할 수 없어요. 다시 시도해주세요. |
| MISSION_MISMATCH | Backend | storyId, sceneId, missionType 조합이 맞지 않음 | 현재 장면의 미션 정보가 올바르지 않습니다. |
| AI_SERVER_ERROR | Backend | AI Server 호출 실패 또는 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |
| INTERNAL_SERVER_ERROR | Backend | Backend 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |

---

# 12. WarningCode 정의

| warningCode | 발생 위치 | 설명 | 처리 방식 |
| --- | --- | --- | --- |
| SAVE_FAILED | Backend | AI 판정은 성공했지만 DB 저장 실패 | 성공 판정이면 다음 씬 진행 허용 |

`SAVE_FAILED`는 치명적인 실패가 아니라 경고로 처리합니다.

시연 안정성을 위해 AI 판정이 성공했다면 DB 저장 실패만으로 다음 장면 진행을 막지 않습니다.

---

# 13. 장면별 요청/응답 예시

## 13.1 Scene 1 - 다친 제비 보호하기

### Unity → Backend 요청

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

### AI → Backend 성공 응답

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### Backend → Unity 성공 응답

```json
{
  "success": true,
  "sceneCleared": true,
  "currentSceneId": "scene_001",
  "nextSceneId": "scene_002",
  "nextAction": "NEXT_SCENE",
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "message": "좋아요! 제비를 조심스럽게 보호했어요.",
  "errorCode": null,
  "warningCode": null
}
```

### AI → Backend 실패 응답

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

### Backend → Unity 실패 응답

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "message": "두 손을 조금 더 가까이 모아주세요.",
  "errorCode": null,
  "warningCode": null
}
```

---

## 13.2 Scene 2 - 박씨 받기

### Unity → Backend 요청

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_002",
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": []
}
```

### AI → Backend 성공 응답

```json
{
  "success": true,
  "score": 0.91,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### Backend → Unity 성공 응답

```json
{
  "success": true,
  "sceneCleared": true,
  "currentSceneId": "scene_002",
  "nextSceneId": "scene_003",
  "nextAction": "NEXT_SCENE",
  "score": 0.91,
  "reasonCode": "MISSION_SUCCESS",
  "message": "잘했어요! 박씨를 받았어요.",
  "errorCode": null,
  "warningCode": null
}
```

### AI → Backend 실패 응답

```json
{
  "success": false,
  "score": 0.35,
  "reasonCode": "HAND_NOT_RAISED",
  "errorCode": null
}
```

### Backend → Unity 실패 응답

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_002",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.35,
  "reasonCode": "HAND_NOT_RAISED",
  "message": "한 손을 어깨보다 높게 들어주세요.",
  "errorCode": null,
  "warningCode": null
}
```

---

## 13.3 Scene 3 - 박 타기

### Unity → Backend 요청

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_003",
  "missionType": "open_gourd",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": []
}
```

### AI → Backend 성공 응답

```json
{
  "success": true,
  "score": 0.86,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### Backend → Unity 성공 응답

```json
{
  "success": true,
  "sceneCleared": true,
  "currentSceneId": "scene_003",
  "nextSceneId": null,
  "nextAction": "ENDING",
  "score": 0.86,
  "reasonCode": "MISSION_SUCCESS",
  "message": "힘차게 박을 탔어요! 박이 열렸어요.",
  "errorCode": null,
  "warningCode": null
}
```

### AI → Backend 실패 응답

```json
{
  "success": false,
  "score": 0.39,
  "reasonCode": "ARMS_NOT_WIDE",
  "errorCode": null
}
```

### Backend → Unity 실패 응답

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_003",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.39,
  "reasonCode": "ARMS_NOT_WIDE",
  "message": "양팔을 더 크게 벌려주세요.",
  "errorCode": null,
  "warningCode": null
}
```

---

# 14. 예외 응답 예시

## 14.1 사용자가 감지되지 않는 경우

### AI → Backend 응답

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "USER_NOT_DETECTED"
}
```

### Backend → Unity 응답

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.0,
  "reasonCode": null,
  "message": "카메라 앞에 서서 다시 시도해주세요.",
  "errorCode": "USER_NOT_DETECTED",
  "warningCode": null
}
```

---

## 14.2 손이 화면 밖으로 나간 경우

### AI → Backend 응답

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "HAND_NOT_VISIBLE"
}
```

### Backend → Unity 응답

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.0,
  "reasonCode": null,
  "message": "손이 화면 안에 보이도록 해주세요.",
  "errorCode": "HAND_NOT_VISIBLE",
  "warningCode": null
}
```

---

## 14.3 poseFrames가 비어 있는 경우

Backend에서 1차 검증 후 AI Server를 호출하지 않고 바로 응답할 수 있습니다.

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.0,
  "reasonCode": null,
  "message": "동작 정보를 확인할 수 없어요. 다시 시도해주세요.",
  "errorCode": "INVALID_POSE_DATA",
  "warningCode": null
}
```

---

## 14.4 storyId, sceneId, missionType이 맞지 않는 경우

Backend에서 1차 검증 후 AI Server를 호출하지 않고 바로 응답합니다.

예를 들어 다음과 같은 경우입니다.

```
storyId = heungbu_nolbu
sceneId = scene_001
missionType = receive_seed
```

위 요청은 `scene_001`의 미션이 `protect_swallow`이어야 하므로 잘못된 요청입니다.

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.0,
  "reasonCode": null,
  "message": "현재 장면의 미션 정보가 올바르지 않습니다.",
  "errorCode": "MISSION_MISMATCH",
  "warningCode": null
}
```

---

## 14.5 AI 서버 오류가 발생한 경우

Backend가 AI Server 호출 실패를 감지한 경우입니다.

```json
{
  "success": false,
  "sceneCleared": false,
  "currentSceneId": "scene_001",
  "nextSceneId": null,
  "nextAction": "RETRY",
  "score": 0.0,
  "reasonCode": null,
  "message": "잠시 문제가 발생했어요. 다시 시도해주세요.",
  "errorCode": "AI_SERVER_ERROR",
  "warningCode": null
}
```

---

## 14.6 DB 저장 실패가 발생했지만 동작 판정은 성공한 경우

```json
{
  "success": true,
  "sceneCleared": true,
  "currentSceneId": "scene_001",
  "nextSceneId": "scene_002",
  "nextAction": "NEXT_SCENE",
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "message": "좋아요! 다음 장면으로 넘어가요.",
  "errorCode": null,
  "warningCode": "SAVE_FAILED"
}
```

---

# 15. 백엔드 저장 데이터

백엔드는 최종 판정 결과를 DB에 저장합니다.

로그인 기능을 구현하지 않기 때문에 사용자 ID는 저장하지 않습니다.

좌표 원본은 저장하지 않는 것을 기본으로 합니다.

MVP에서는 `attemptCount`를 사용하지 않으므로 요청값과 저장 필드에서 제외합니다.

## 15.1 저장 권장 필드

```
id
story_id
scene_id
mission_type
success
score
reason_code
message
error_code
warning_code
created_at
```

`story_id`는 어떤 동화의 미션 결과인지 구분하기 위해 저장합니다.

현재 MVP에서는 `heungbu_nolbu`로 저장됩니다.

추후 여러 동화가 추가될 경우 같은 `scene_id`라도 `story_id`에 따라 다른 장면으로 구분할 수 있습니다.

---

## 15.2 저장 데이터 예시

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_001",
  "missionType": "protect_swallow",
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "message": "좋아요! 제비를 조심스럽게 보호했어요.",
  "errorCode": null,
  "warningCode": null
}
```

---

# 16. 백엔드 검증 규칙

Backend는 AI Server 호출 전에 다음 항목을 검증합니다.

```
1. storyId가 존재하는지 확인
2. storyId가 지원하는 동화인지 확인
3. sceneId가 존재하는지 확인
4. sceneId가 해당 storyId 안에 존재하는지 확인
5. missionType이 존재하는지 확인
6. storyId + sceneId + missionType 조합이 올바른지 확인
7. poseFrames가 비어 있지 않은지 확인
8. poseFrames 안에 landmarks가 존재하는지 확인
9. 필수 landmark가 포함되어 있는지 확인
```

`storyId + sceneId + missionType` 매칭이 맞지 않으면 AI Server를 호출하지 않고 바로 실패 응답을 반환합니다.

이때 `errorCode`는 `MISSION_MISMATCH`를 사용합니다.

---

# 17. AI 서버 판정 규칙 요약

AI Server는 `missionType`에 따라 다른 판정 로직을 실행합니다.

| missionType | 판정 방식 | 주요 좌표 | 실패 reasonCode |
| --- | --- | --- | --- |
| protect_swallow | 두 손목 거리와 몸 중앙 위치 확인 | leftWrist, rightWrist, leftShoulder, rightShoulder | HANDS_TOO_FAR, HANDS_NOT_CENTERED |
| receive_seed | 한쪽 손목이 어깨보다 위에 있는지 확인 | leftWrist, rightWrist, leftShoulder, rightShoulder | HAND_NOT_RAISED |
| open_gourd | 양손목 사이 거리와 어깨 너비 비교 | leftWrist, rightWrist, leftShoulder, rightShoulder | ARMS_NOT_WIDE, MOVEMENT_TOO_SMALL |

기본 성공 기준은 다음과 같습니다.

```
score >= 0.7
→ success true

score < 0.7
→ success false
```

성공 시 AI Server는 `reasonCode: MISSION_SUCCESS`를 반환합니다.

---

# 18. Health Check API

## 18.1 Backend Health Check

```
GET /api/health
```

응답:

```json
{
  "status": "ok",
  "service": "backend"
}
```

---

## 18.2 AI Server Health Check

```
GET /health
```

응답:

```json
{
  "status": "ok",
  "service": "ai-server"
}
```

---

# 19. 개발 우선순위

API 개발은 다음 순서로 진행합니다.

```
1. AI Server /health 구현
2. AI Server /internal/ai/missions/check 구현
3. AI Server가 success / score / reasonCode / errorCode 반환하도록 구현
4. Backend /api/health 구현
5. Backend /api/missions/check 구현
6. Backend에서 storyId + sceneId + missionType 매핑 검증 구현
7. Backend에서 reasonCode / errorCode 기준 message 매핑 구현
8. Backend에서 storyId + sceneId 기준 nextSceneId / nextAction 생성 구현
9. Backend → AI Server 내부 호출 테스트
10. 더미 poseFrames로 receive_seed 판정 테스트
11. Unity → Backend 요청 테스트
12. protect_swallow 판정 연결
13. open_gourd 판정 연결
14. 전체 시연 흐름 테스트
```

가장 먼저 `receive_seed`를 구현하는 것을 추천합니다.

한 손 들기 판정은 손목 y좌표와 어깨 y좌표만 비교하면 되기 때문에, 전체 API 연동 테스트에 가장 적합합니다.

---

# 20. 최종 정리

이번 API 구조에서 `storyId`는 유지합니다.

현재 MVP에서는 `heungbu_nolbu` 하나만 사용하지만, 추후 여러 동화가 추가될 경우 `sceneId`가 중복될 수 있기 때문입니다.

따라서 Backend는 다음 조합을 기준으로 요청을 검증합니다.

```
storyId + sceneId + missionType
```

AI Server는 `missionType`을 기준으로 detector를 선택하고, `success`, `score`, `reasonCode`, `errorCode`를 반환합니다.

Backend는 AI Server의 응답을 바탕으로 `message`, `nextAction`, `nextSceneId`를 생성합니다.

Unity는 Backend의 최종 응답만 보고 다음 장면 전환 또는 재시도 UI를 처리합니다.