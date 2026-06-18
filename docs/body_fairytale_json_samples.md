# 몸으로 넘기는 전래동화 JSON 요청/응답 샘플

> Claude가 프로젝트 구조를 이해할 수 있도록 정리한 JSON 샘플 문서입니다.  
> 본 문서는 Unity, Backend, AI Server 간 요청/응답 구조와 장면별 샘플 데이터를 설명합니다.

---

## 1. 전체 데이터 흐름

```
Unity
→ Backend
→ AI Server(FastAPI)
→ Backend
→ Unity
```

Unity는 AI 서버를 직접 호출하지 않고, 백엔드 API만 호출합니다.

백엔드는 Unity에서 받은 `storyId`, `sceneId`, `missionType`, `poseFrames`를 검증한 뒤 AI 서버에 전달합니다.

AI 서버는 MediaPipe 좌표를 기반으로 동작 성공 여부만 판정하고, `success`, `score`, `reasonCode`, `errorCode`를 백엔드에 반환합니다.

사용자에게 보여줄 `message`, 다음 진행 상태인 `nextAction`, 다음 장면인 `nextSceneId`는 백엔드가 결정합니다.

---

## 2. storyId 사용 기준

이번 MVP에서는 「흥부와 놀부」 하나만 구현하기 때문에 `storyId`는 다음 값으로 고정합니다.

```
storyId: heungbu_nolbu
```

현재는 하나의 동화만 사용하지만, 추후 여러 동화가 추가될 경우 `scene_001`, `scene_002` 같은 장면 ID는 동화마다 중복될 수 있습니다.

예시는 다음과 같습니다.

```
heungbu_nolbu / scene_001 → 다친 제비 보호하기
little_prince / scene_001 → 어린왕자가 별에 앉아 있는 장면
red_riding_hood / scene_001 → 숲길을 걷는 장면
```

따라서 백엔드는 `storyId + sceneId + missionType` 조합을 기준으로 요청이 올바른지 검증합니다.

```
storyId + sceneId + missionType
→ 현재 요청이 어떤 동화의 어떤 장면, 어떤 미션인지 확인하는 기준
```

---

## 3. 메시지 처리 기준

이번 구조에서는 사용자에게 보여줄 문구를 AI 서버가 직접 만들지 않습니다.

AI 서버는 동작 판정 결과만 반환합니다.

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

백엔드는 `storyId`, `sceneId`, `missionType`, `success`, `reasonCode`, `errorCode`를 기준으로 사용자 메시지를 생성합니다.

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

이렇게 하면 문구 수정은 백엔드에서만 관리할 수 있고, AI 서버는 좌표 판정 로직에만 집중할 수 있습니다.

---

## 4. 좌표 수집 기준

이번 MVP에서는 미션 수행 시간을 3~5초로 설정합니다.

구현을 단순하게 하기 위해 기본값은 다음과 같이 잡습니다.

```
captureDurationSec: 5
sampleFps: 5
poseFrames.length: 약 25개
timestamp 예시: 0.0, 0.2, 0.4, 0.6, ... 4.8
```

즉, Unity는 5초 동안 MediaPipe 좌표를 수집하고, 초당 5개 프레임만 샘플링하여 백엔드로 전송합니다.

30fps 전체 프레임을 모두 보내는 것이 아니라, 일정 간격으로 추출한 `poseFrame`만 보냅니다.

문서의 JSON 예시는 가독성을 위해 일부 프레임만 작성할 수 있지만, 실제 요청에서는 약 15~25개 정도의 `poseFrame`이 전달되는 것을 기준으로 합니다.

---

# 5. 공통 요청 구조

## 5.1 Unity → Backend 공통 요청

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

## 5.2 필드 설명

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| storyId | string | 동화 ID. MVP에서는 heungbu_nolbu |
| sceneId | string | 현재 장면 ID |
| missionType | string | 현재 미션 타입 |
| captureDurationSec | number | Unity가 좌표를 수집한 시간 |
| sampleFps | number | 초당 샘플링한 프레임 수 |
| poseFrames | array | MediaPipe 포즈 좌표 프레임 목록 |

로그인 기능을 구현하지 않기 때문에 `userId`는 사용하지 않습니다.

---

# 6. poseFrames 기본 구조

## 6.1 poseFrame 1개 구조

```json
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
```

## 6.2 landmark 좌표 기준

```
x: 화면 가로 위치, 0~1
y: 화면 세로 위치, 0~1
visibility: 해당 관절이 잘 보이는 정도, 0~1
```

MediaPipe 기준으로 `y`값이 작을수록 화면 위쪽입니다.

예를 들어 손을 들었는지 확인할 때는 다음처럼 판단합니다.

```
손목 y좌표 < 어깨 y좌표
→ 손이 어깨보다 위에 있음
```

---

# 7. Story / Scene / Mission 매핑

## 7.1 MVP 매핑표

| storyId | sceneId | missionType | 장면 | 사용자 동작 | nextSceneId |
| --- | --- | --- | --- | --- | --- |
| heungbu_nolbu | scene_001 | protect_swallow | 다친 제비 보호하기 | 두 손 모으기 / 감싸기 | scene_002 |
| heungbu_nolbu | scene_002 | receive_seed | 박씨 받기 | 한 손 들기 | scene_003 |
| heungbu_nolbu | scene_003 | open_gourd | 박 타기 | 양팔 크게 벌리기 / 휘두르기 | null |

## 7.2 백엔드 검증 기준

백엔드는 AI 서버를 호출하기 전에 다음 조합이 올바른지 확인합니다.

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

해커톤 MVP에서는 에러코드를 너무 늘리지 않기 위해 지원하지 않는 `storyId`도 `MISSION_MISMATCH`로 처리할 수 있습니다.

---

# 8. ReasonCode 정의

`reasonCode`는 AI 서버가 백엔드에 전달하는 동작 판정 이유입니다.

사용자 메시지를 직접 담지 않고, 백엔드가 메시지를 매핑할 수 있도록 코드값만 전달합니다.

## 8.1 공통 reasonCode

| reasonCode | 의미 |
| --- | --- |
| MISSION_SUCCESS | 미션 성공 |
| LOW_SCORE | 동작 점수가 기준보다 낮음 |

## 8.2 Scene 1 - protect_swallow

| reasonCode | 의미 | 백엔드 메시지 예시 |
| --- | --- | --- |
| MISSION_SUCCESS | 두 손 모으기 성공 | 좋아요! 제비를 조심스럽게 보호했어요. |
| HANDS_TOO_FAR | 양손 사이 거리가 멀다 | 두 손을 조금 더 가까이 모아주세요. |
| HANDS_NOT_CENTERED | 양손이 몸 중앙에서 벗어남 | 두 손을 몸 가운데로 모아주세요. |

## 8.3 Scene 2 - receive_seed

| reasonCode | 의미 | 백엔드 메시지 예시 |
| --- | --- | --- |
| MISSION_SUCCESS | 한 손 들기 성공 | 잘했어요! 박씨를 받았어요. |
| HAND_NOT_RAISED | 손이 충분히 올라가지 않음 | 한 손을 어깨보다 높게 들어주세요. |

## 8.4 Scene 3 - open_gourd

| reasonCode | 의미 | 백엔드 메시지 예시 |
| --- | --- | --- |
| MISSION_SUCCESS | 양팔 벌리기 성공 | 힘차게 박을 탔어요! 박이 열렸어요. |
| ARMS_NOT_WIDE | 양팔이 충분히 벌어지지 않음 | 양팔을 더 크게 벌려주세요. |
| MOVEMENT_TOO_SMALL | 팔 움직임이 작음 | 팔을 더 크게 움직여주세요. |

---

# 9. ErrorCode 정의

`errorCode`는 판정 자체가 어렵거나 시스템 문제가 있을 때 사용합니다.

| errorCode | 발생 위치 | 의미 | 백엔드 메시지 예시 |
| --- | --- | --- | --- |
| USER_NOT_DETECTED | AI | 사용자가 화면에 감지되지 않음 | 카메라 앞에 서서 다시 시도해주세요. |
| HAND_NOT_VISIBLE | AI | 손목 좌표가 감지되지 않음 | 손이 화면 안에 보이도록 해주세요. |
| INVALID_POSE_DATA | Backend / AI | poseFrames가 없거나 필수 좌표가 누락됨 | 동작 정보를 확인할 수 없어요. 다시 시도해주세요. |
| MISSION_MISMATCH | Backend | storyId, sceneId, missionType 조합이 맞지 않음 | 현재 장면의 미션 정보가 올바르지 않습니다. |
| AI_SERVER_ERROR | Backend | AI 서버 호출 실패 또는 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |
| INTERNAL_SERVER_ERROR | Backend | 백엔드 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |

---

# 10. Scene 1 요청/응답 샘플

## 10.1 Scene 1 정보

```
storyId: heungbu_nolbu
sceneId: scene_001
missionType: protect_swallow
장면: 흥부가 다친 제비를 만난다
동작: 두 손 모으기 / 감싸기
판정 기준: 양손목 사이 거리, 몸 중앙 위치
```

---

## 10.2 Unity → Backend 요청 예시

아래 예시는 5초 동안 수집한 `poseFrames` 중 일부만 작성한 축약 예시입니다.

실제 요청에서는 `timestamp`가 0.0부터 4.8까지 약 25개 들어갑니다.

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
        "leftWrist": { "x": 0.40, "y": 0.60, "visibility": 0.91 },
        "rightWrist": { "x": 0.60, "y": 0.60, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 1.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.45, "y": 0.48, "visibility": 0.94 },
        "rightElbow": { "x": 0.55, "y": 0.48, "visibility": 0.94 },
        "leftWrist": { "x": 0.46, "y": 0.58, "visibility": 0.92 },
        "rightWrist": { "x": 0.54, "y": 0.58, "visibility": 0.92 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.45, "y": 0.48, "visibility": 0.94 },
        "rightElbow": { "x": 0.55, "y": 0.48, "visibility": 0.94 },
        "leftWrist": { "x": 0.49, "y": 0.57, "visibility": 0.93 },
        "rightWrist": { "x": 0.51, "y": 0.57, "visibility": 0.93 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 3.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.45, "y": 0.48, "visibility": 0.94 },
        "rightElbow": { "x": 0.55, "y": 0.48, "visibility": 0.94 },
        "leftWrist": { "x": 0.49, "y": 0.57, "visibility": 0.93 },
        "rightWrist": { "x": 0.51, "y": 0.57, "visibility": 0.93 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.45, "y": 0.48, "visibility": 0.94 },
        "rightElbow": { "x": 0.55, "y": 0.48, "visibility": 0.94 },
        "leftWrist": { "x": 0.50, "y": 0.58, "visibility": 0.92 },
        "rightWrist": { "x": 0.52, "y": 0.58, "visibility": 0.92 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    }
  ]
}
```

---

## 10.3 Backend → AI Server 요청 예시

백엔드는 AI 판정에 필요한 데이터만 AI 서버로 전달합니다.

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
        "leftWrist": { "x": 0.40, "y": 0.60, "visibility": 0.91 },
        "rightWrist": { "x": 0.60, "y": 0.60, "visibility": 0.91 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftWrist": { "x": 0.49, "y": 0.57, "visibility": 0.93 },
        "rightWrist": { "x": 0.51, "y": 0.57, "visibility": 0.93 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftWrist": { "x": 0.50, "y": 0.58, "visibility": 0.92 },
        "rightWrist": { "x": 0.52, "y": 0.58, "visibility": 0.92 }
      }
    }
  ]
}
```

---

## 10.4 AI Server → Backend 성공 응답 예시

AI 서버는 사용자 메시지를 반환하지 않습니다.

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

---

## 10.5 AI Server → Backend 실패 응답 예시

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

---

## 10.6 Backend → Unity 성공 응답 예시

백엔드는 `storyId`, `sceneId`, `missionType`, `reasonCode`를 보고 사용자 메시지와 다음 장면 정보를 생성합니다.

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

## 10.7 Backend → Unity 실패 응답 예시

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

# 11. Scene 2 요청/응답 샘플

## 11.1 Scene 2 정보

```
storyId: heungbu_nolbu
sceneId: scene_002
missionType: receive_seed
장면: 제비가 박씨를 물어다 준다
동작: 한 손 들기
판정 기준: 한쪽 손목이 어깨보다 위에 있는지 확인
```

---

## 11.2 Unity → Backend 요청 예시

아래 예시는 사용자가 5초 안에 오른손을 들어 올리는 흐름입니다.

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_002",
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftElbow": { "x": 0.41, "y": 0.50, "visibility": 0.93 },
        "rightElbow": { "x": 0.61, "y": 0.50, "visibility": 0.93 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.60, "y": 0.62, "visibility": 0.90 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 1.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftElbow": { "x": 0.41, "y": 0.50, "visibility": 0.93 },
        "rightElbow": { "x": 0.61, "y": 0.40, "visibility": 0.94 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.62, "y": 0.48, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftElbow": { "x": 0.41, "y": 0.50, "visibility": 0.93 },
        "rightElbow": { "x": 0.62, "y": 0.30, "visibility": 0.94 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 3.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftElbow": { "x": 0.41, "y": 0.50, "visibility": 0.93 },
        "rightElbow": { "x": 0.62, "y": 0.30, "visibility": 0.94 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftElbow": { "x": 0.41, "y": 0.50, "visibility": 0.93 },
        "rightElbow": { "x": 0.62, "y": 0.30, "visibility": 0.94 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    }
  ]
}
```

---

## 11.3 Backend → AI Server 요청 예시

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_002",
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.60, "y": 0.62, "visibility": 0.90 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 }
      }
    }
  ]
}
```

---

## 11.4 AI Server → Backend 성공 응답 예시

```json
{
  "success": true,
  "score": 0.91,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

---

## 11.5 AI Server → Backend 실패 응답 예시

```json
{
  "success": false,
  "score": 0.35,
  "reasonCode": "HAND_NOT_RAISED",
  "errorCode": null
}
```

---

## 11.6 Backend → Unity 성공 응답 예시

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

---

## 11.7 Backend → Unity 실패 응답 예시

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

# 12. Scene 3 요청/응답 샘플

## 12.1 Scene 3 정보

```
storyId: heungbu_nolbu
sceneId: scene_003
missionType: open_gourd
장면: 흥부가 박을 탄다
동작: 양팔 크게 벌리기 또는 휘두르기
판정 기준: 양손목 사이 거리와 어깨 너비 비교, 손목 이동량
```

---

## 12.2 Unity → Backend 요청 예시

아래 예시는 사용자가 5초 안에 양팔을 크게 벌리는 흐름입니다.

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_003",
  "missionType": "open_gourd",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.44, "y": 0.48, "visibility": 0.93 },
        "rightElbow": { "x": 0.56, "y": 0.48, "visibility": 0.93 },
        "leftWrist": { "x": 0.48, "y": 0.58, "visibility": 0.91 },
        "rightWrist": { "x": 0.52, "y": 0.58, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 1.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.38, "y": 0.46, "visibility": 0.93 },
        "rightElbow": { "x": 0.62, "y": 0.46, "visibility": 0.93 },
        "leftWrist": { "x": 0.32, "y": 0.52, "visibility": 0.91 },
        "rightWrist": { "x": 0.68, "y": 0.52, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.32, "y": 0.42, "visibility": 0.93 },
        "rightElbow": { "x": 0.68, "y": 0.42, "visibility": 0.93 },
        "leftWrist": { "x": 0.20, "y": 0.46, "visibility": 0.91 },
        "rightWrist": { "x": 0.80, "y": 0.46, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 3.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.30, "y": 0.43, "visibility": 0.93 },
        "rightElbow": { "x": 0.70, "y": 0.43, "visibility": 0.93 },
        "leftWrist": { "x": 0.18, "y": 0.48, "visibility": 0.91 },
        "rightWrist": { "x": 0.82, "y": 0.48, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.30, "y": 0.43, "visibility": 0.93 },
        "rightElbow": { "x": 0.70, "y": 0.43, "visibility": 0.93 },
        "leftWrist": { "x": 0.18, "y": 0.48, "visibility": 0.91 },
        "rightWrist": { "x": 0.82, "y": 0.48, "visibility": 0.91 },
        "nose": { "x": 0.50, "y": 0.20, "visibility": 0.95 }
      }
    }
  ]
}
```

---

## 12.3 Backend → AI Server 요청 예시

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_003",
  "missionType": "open_gourd",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftWrist": { "x": 0.48, "y": 0.58, "visibility": 0.91 },
        "rightWrist": { "x": 0.52, "y": 0.58, "visibility": 0.91 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftWrist": { "x": 0.20, "y": 0.46, "visibility": 0.91 },
        "rightWrist": { "x": 0.80, "y": 0.46, "visibility": 0.91 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftWrist": { "x": 0.18, "y": 0.48, "visibility": 0.91 },
        "rightWrist": { "x": 0.82, "y": 0.48, "visibility": 0.91 }
      }
    }
  ]
}
```

---

## 12.4 AI Server → Backend 성공 응답 예시

```json
{
  "success": true,
  "score": 0.86,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

---

## 12.5 AI Server → Backend 실패 응답 예시

```json
{
  "success": false,
  "score": 0.39,
  "reasonCode": "ARMS_NOT_WIDE",
  "errorCode": null
}
```

---

## 12.6 Backend → Unity 성공 응답 예시

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

## 12.7 Backend → Unity 실패 응답 예시

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

# 13. 예외 응답 JSON 샘플

## 13.1 사용자가 감지되지 않는 경우

AI 서버 응답:

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "USER_NOT_DETECTED"
}
```

Backend → Unity 응답:

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

## 13.2 손이 화면 밖으로 나간 경우

AI 서버 응답:

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "HAND_NOT_VISIBLE"
}
```

Backend → Unity 응답:

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

## 13.3 poseFrames가 비어 있는 경우

Backend → Unity 응답:

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

## 13.4 storyId, sceneId, missionType이 맞지 않는 경우

예를 들어 다음 요청은 잘못된 요청입니다.

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_001",
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": []
}
```

`heungbu_nolbu`의 `scene_001`은 `protect_swallow` 미션이어야 하므로, 백엔드는 AI 서버를 호출하지 않고 실패 응답을 반환합니다.

Backend → Unity 응답:

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

## 13.5 지원하지 않는 storyId가 들어온 경우

예를 들어 다음 요청은 잘못된 요청입니다.

```json
{
  "storyId": "unknown_story",
  "sceneId": "scene_001",
  "missionType": "protect_swallow",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": []
}
```

MVP에서는 지원하지 않는 `storyId`도 `MISSION_MISMATCH`로 처리합니다.

Backend → Unity 응답:

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

## 13.6 AI 서버 오류가 발생한 경우

Backend → Unity 응답:

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

## 13.7 DB 저장 실패가 발생했지만 동작 판정은 성공한 경우

Backend → Unity 응답:

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

# 14. Health Check JSON 샘플

## 14.1 Backend Health Check

```
GET /api/health
```

```json
{
  "status": "ok",
  "service": "backend"
}
```

---

## 14.2 AI Server Health Check

```
GET /health
```

```json
{
  "status": "ok",
  "service": "ai-server"
}
```

---

# 15. 최소 테스트용 더미 요청

개발 초기에는 실제 MediaPipe 좌표가 없어도 아래 JSON으로 API 연결 테스트를 할 수 있습니다.

더미 요청에도 `storyId`는 반드시 포함합니다.

현재 MVP에서는 다음 값을 사용합니다.

```
storyId: heungbu_nolbu
```

---

## 15.1 receive_seed 성공 테스트용

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_002",
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.60, "y": 0.62, "visibility": 0.90 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 }
      }
    }
  ]
}
```

AI 서버 예상 결과:

```json
{
  "success": true,
  "score": 0.91,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

Backend → Unity 예상 결과:

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

---

## 15.2 receive_seed 실패 테스트용

```json
{
  "storyId": "heungbu_nolbu",
  "sceneId": "scene_002",
  "missionType": "receive_seed",
  "captureDurationSec": 5,
  "sampleFps": 5,
  "poseFrames": [
    {
      "timestamp": 0.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.60, "y": 0.62, "visibility": 0.90 }
      }
    },
    {
      "timestamp": 2.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.60, "y": 0.62, "visibility": 0.90 }
      }
    },
    {
      "timestamp": 4.0,
      "landmarks": {
        "leftShoulder": { "x": 0.42, "y": 0.36, "visibility": 0.97 },
        "rightShoulder": { "x": 0.58, "y": 0.36, "visibility": 0.97 },
        "leftWrist": { "x": 0.40, "y": 0.62, "visibility": 0.90 },
        "rightWrist": { "x": 0.60, "y": 0.62, "visibility": 0.90 }
      }
    }
  ]
}
```

AI 서버 예상 결과:

```json
{
  "success": false,
  "score": 0.35,
  "reasonCode": "HAND_NOT_RAISED",
  "errorCode": null
}
```

Backend → Unity 예상 결과:

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

# 16. 실제 전송 기준 정리

실제 Unity 요청에서는 다음 기준을 권장합니다.

```
storyId = heungbu_nolbu
captureDurationSec = 5
sampleFps = 5
poseFrames.length = 약 25
timestamp = 0.0, 0.2, 0.4, 0.6, ... 4.8
```

다만 문서나 테스트용 JSON에서는 가독성을 위해 3~5개 프레임만 작성할 수 있습니다.

이 경우 반드시 해당 JSON이 축약 예시임을 명시합니다.

```
문서 예시: 3~5개 poseFrame만 표시
실제 요청: 약 25개 poseFrame 전송
```

---

# 17. 최종 정리

이번 JSON 응답 형식에서는 `storyId`를 유지합니다.

현재 MVP에서는 `storyId = heungbu_nolbu`로 고정합니다.

백엔드는 다음 조합으로 요청을 검증합니다.

```
storyId + sceneId + missionType
```

AI 서버는 `missionType`을 기준으로 동작 detector를 선택하고, 다음 값만 반환합니다.

```
success
score
reasonCode
errorCode
```

백엔드는 AI 서버 응답을 바탕으로 다음 값을 생성합니다.

```
message
nextAction
nextSceneId
warningCode
```

Unity는 백엔드의 최종 응답만 보고 다음 장면 전환 또는 재시도 UI를 처리합니다.