# 몸으로 넘기는 전래동화 에러코드 정의서

## 1. 문서 목적

본 문서는 **몸으로 넘기는 전래동화 - 흥부와 놀부 MVP**에서 사용하는 `errorCode`, `reasonCode`, `warningCode`의 기준을 정의합니다.

이번 프로젝트에서는 AI 서버와 백엔드의 역할을 분리합니다.

```text
AI Server:
동작 판정 결과 반환
success / score / reasonCode / errorCode 반환

Backend:
storyId / sceneId / missionType 검증
reasonCode / errorCode 기준으로 사용자 message 생성
success와 storyId / sceneId 기준으로 nextAction / nextSceneId 생성
결과 저장
Unity에 최종 응답 반환
```

따라서 AI 서버는 사용자 메시지를 직접 반환하지 않습니다.

사용자에게 보여줄 `message`는 백엔드에서 관리합니다.

---

## 2. storyId 사용 기준

이번 MVP에서는 「흥부와 놀부」 하나만 구현하므로 `storyId`는 다음 값으로 고정합니다.

```text
storyId: heungbu_nolbu
```

현재는 하나의 동화만 사용하지만, 추후 여러 동화가 추가될 경우 `scene_001`, `scene_002` 같은 장면 ID는 동화마다 중복될 수 있습니다.

예시는 다음과 같습니다.

```text
heungbu_nolbu / scene_001 → 다친 제비 보호하기
little_prince / scene_001 → 어린왕자가 별에 앉아 있는 장면
red_riding_hood / scene_001 → 숲길을 걷는 장면
```

따라서 백엔드는 `sceneId`와 `missionType`만 확인하지 않고, 다음 조합을 기준으로 요청을 검증합니다.

```text
storyId + sceneId + missionType
```

---

## 3. 코드 분류 기준

## 3.1 reasonCode

`reasonCode`는 사용자가 동작을 수행했지만, 성공 기준에 부족하거나 성공 조건을 만족했을 때 사용하는 코드입니다.

즉, **동작 판정 결과의 이유**를 나타냅니다.

예시:

```text
두 손이 너무 멀다.
한 손이 충분히 올라가지 않았다.
양팔이 충분히 벌어지지 않았다.
미션에 성공했다.
```

AI 서버가 반환하고, 백엔드는 이를 사용자 메시지로 변환합니다.

---

## 3.2 errorCode

`errorCode`는 동작이 부족한 경우가 아니라, **판정 자체가 어렵거나 시스템 문제가 발생한 경우** 사용합니다.

예시:

```text
사용자가 화면에 감지되지 않는다.
손목 좌표가 보이지 않는다.
poseFrames가 비어 있다.
storyId, sceneId, missionType 조합이 맞지 않는다.
AI 서버 호출에 실패했다.
```

---

## 3.3 warningCode

`warningCode`는 치명적인 실패는 아니지만, 백엔드에서 기록해야 하는 경고 상황에 사용합니다.

예시:

```text
AI 판정은 성공했지만 DB 저장에 실패했다.
```

이 경우 사용자 진행을 막지 않고, 백엔드 로그에 기록하는 방식으로 처리합니다.

---

## 4. reasonCode 정의

## 4.1 전체 reasonCode 목록

| reasonCode | 발생 위치 | 의미 | success |
| --- | --- | --- | --- |
| MISSION_SUCCESS | AI Server | 미션 성공 | true |
| LOW_SCORE | AI Server | 점수가 기준보다 낮음 | false |
| HANDS_TOO_FAR | AI Server | 양손 사이 거리가 너무 멂 | false |
| HANDS_NOT_CENTERED | AI Server | 양손이 몸 중앙에서 벗어남 | false |
| HAND_NOT_RAISED | AI Server | 한 손이 충분히 올라가지 않음 | false |
| ARMS_NOT_WIDE | AI Server | 양팔이 충분히 벌어지지 않음 | false |
| MOVEMENT_TOO_SMALL | AI Server | 팔 움직임 변화량이 부족함 | false |

---

## 5. 장면별 reasonCode 상세 정의

## 5.1 Scene 1 - 다친 제비 보호하기

```text
storyId: heungbu_nolbu
sceneId: scene_001
missionType: protect_swallow
사용자 동작: 두 손 모으기 / 감싸기
```

| reasonCode | 발생 조건 | Backend message |
| --- | --- | --- |
| MISSION_SUCCESS | 양손이 몸 중앙 근처에서 충분히 가까움 | 좋아요! 제비를 조심스럽게 보호했어요. |
| HANDS_TOO_FAR | 양손목 사이 거리가 기준보다 멂 | 두 손을 조금 더 가까이 모아주세요. |
| HANDS_NOT_CENTERED | 양손 중심이 몸 중앙에서 벗어남 | 두 손을 몸 가운데로 모아주세요. |
| LOW_SCORE | 점수는 계산됐지만 성공 기준보다 낮음 | 조금 더 정확하게 동작해볼까요? |

### AI Server 응답 예시 - 성공

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### AI Server 응답 예시 - 실패

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

---

## 5.2 Scene 2 - 박씨 받기

```text
storyId: heungbu_nolbu
sceneId: scene_002
missionType: receive_seed
사용자 동작: 한 손 들기
```

| reasonCode | 발생 조건 | Backend message |
| --- | --- | --- |
| MISSION_SUCCESS | 왼손 또는 오른손이 어깨보다 위에 있음 | 잘했어요! 박씨를 받았어요. |
| HAND_NOT_RAISED | 양손 모두 어깨보다 충분히 올라가지 않음 | 한 손을 어깨보다 높게 들어주세요. |
| LOW_SCORE | 점수는 계산됐지만 성공 기준보다 낮음 | 조금 더 크게 손을 들어볼까요? |

### AI Server 응답 예시 - 성공

```json
{
  "success": true,
  "score": 0.91,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### AI Server 응답 예시 - 실패

```json
{
  "success": false,
  "score": 0.35,
  "reasonCode": "HAND_NOT_RAISED",
  "errorCode": null
}
```

---

## 5.3 Scene 3 - 박 타기

```text
storyId: heungbu_nolbu
sceneId: scene_003
missionType: open_gourd
사용자 동작: 양팔 크게 벌리기 / 휘두르기
```

| reasonCode | 발생 조건 | Backend message |
| --- | --- | --- |
| MISSION_SUCCESS | 양팔이 충분히 크게 벌어짐 | 힘차게 박을 탔어요! 박이 열렸어요. |
| ARMS_NOT_WIDE | 양손목 사이 거리가 어깨 너비 기준보다 좁음 | 양팔을 더 크게 벌려주세요. |
| MOVEMENT_TOO_SMALL | 팔 움직임 변화량이 부족함 | 팔을 더 크게 움직여주세요. |
| LOW_SCORE | 점수는 계산됐지만 성공 기준보다 낮음 | 조금 더 크게 동작해볼까요? |

### AI Server 응답 예시 - 성공

```json
{
  "success": true,
  "score": 0.86,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

### AI Server 응답 예시 - 실패

```json
{
  "success": false,
  "score": 0.39,
  "reasonCode": "ARMS_NOT_WIDE",
  "errorCode": null
}
```

---

## 6. errorCode 정의

## 6.1 전체 errorCode 목록

| errorCode | 발생 위치 | 의미 | Backend message |
| --- | --- | --- | --- |
| USER_NOT_DETECTED | AI Server | 사용자가 화면에 감지되지 않음 | 카메라 앞에 서서 다시 시도해주세요. |
| HAND_NOT_VISIBLE | AI Server | 손목 좌표가 보이지 않음 | 손이 화면 안에 보이도록 해주세요. |
| INVALID_POSE_DATA | Backend / AI Server | poseFrames가 없거나 필수 좌표가 누락됨 | 동작 정보를 확인할 수 없어요. 다시 시도해주세요. |
| MISSION_MISMATCH | Backend | storyId, sceneId, missionType 조합이 맞지 않음 | 현재 장면의 미션 정보가 올바르지 않습니다. |
| AI_SERVER_ERROR | Backend | AI 서버 호출 실패 또는 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |
| INTERNAL_SERVER_ERROR | Backend | 백엔드 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |

---

## 7. errorCode 상세 정의

## 7.1 USER_NOT_DETECTED

### 의미

카메라 화면에서 사용자의 몸이 감지되지 않거나, MediaPipe가 주요 포즈 좌표를 거의 추출하지 못한 경우입니다.

### 발생 위치

```text
AI Server
```

### 발생 조건 예시

```text
poseFrames는 존재하지만 주요 관절 좌표가 대부분 없음
shoulder, wrist 등 핵심 좌표 visibility가 너무 낮음
사람이 카메라 화면 밖에 있음
```

### AI Server 응답 예시

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "USER_NOT_DETECTED"
}
```

### Backend → Unity 응답 예시

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

## 7.2 HAND_NOT_VISIBLE

### 의미

동작 판정에 필요한 손목 좌표가 보이지 않거나, visibility가 기준보다 낮은 경우입니다.

### 발생 위치

```text
AI Server
```

### 발생 조건 예시

```text
leftWrist 또는 rightWrist가 없음
손이 카메라 화면 밖으로 나감
손목 visibility가 0.6 미만
```

### AI Server 응답 예시

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "HAND_NOT_VISIBLE"
}
```

### Backend → Unity 응답 예시

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

## 7.3 INVALID_POSE_DATA

### 의미

Unity에서 전달한 poseFrames 자체가 비어 있거나, 필수 데이터 구조가 잘못된 경우입니다.

### 발생 위치

```text
Backend / AI Server
```

### 발생 조건 예시

```text
poseFrames가 null
poseFrames가 빈 배열
landmarks가 없음
timestamp가 없음
필수 landmark가 누락됨
좌표 x, y 값이 없음
```

### 처리 기준

백엔드에서 1차 검증 가능한 경우, AI 서버를 호출하지 않고 바로 실패 응답을 반환합니다.

### Backend → Unity 응답 예시

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

## 7.4 MISSION_MISMATCH

### 의미

`storyId`, `sceneId`, `missionType` 조합이 매핑표와 일치하지 않는 경우입니다.

예를 들어 MVP 기준으로 `heungbu_nolbu / scene_001`은 `protect_swallow`이어야 하는데, `receive_seed`가 들어온 경우입니다.

### 발생 위치

```text
Backend
```

### 발생 조건 예시

```text
storyId = heungbu_nolbu
sceneId = scene_001
missionType = receive_seed
→ 잘못된 요청

storyId = heungbu_nolbu
sceneId = scene_002
missionType = open_gourd
→ 잘못된 요청

storyId = unknown_story
sceneId = scene_001
missionType = protect_swallow
→ 지원하지 않는 storyId
→ 잘못된 요청
```

### 처리 기준

이 경우 백엔드에서 AI 서버를 호출하지 않고 바로 실패 응답을 반환합니다.

해커톤 MVP에서는 에러코드를 너무 늘리지 않기 위해, 지원하지 않는 `storyId`도 `MISSION_MISMATCH`로 처리합니다.

### Backend → Unity 응답 예시

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

## 7.5 AI_SERVER_ERROR

### 의미

백엔드가 AI 서버 호출에 실패했거나, AI 서버 내부에서 처리 불가능한 예외가 발생한 경우입니다.

### 발생 위치

```text
Backend
```

### 발생 조건 예시

```text
AI 서버가 꺼져 있음
AI 서버 응답 지연
AI 서버에서 500 에러 발생
AI 서버 응답 형식이 잘못됨
```

### 처리 기준

AI 서버 장애가 발생해도 Unity가 멈추지 않도록 백엔드에서 안정적인 실패 응답을 반환합니다.

### Backend → Unity 응답 예시

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

## 7.6 INTERNAL_SERVER_ERROR

### 의미

백엔드 내부에서 예상하지 못한 오류가 발생한 경우입니다.

### 발생 위치

```text
Backend
```

### 발생 조건 예시

```text
백엔드 로직 예외
응답 생성 실패
매핑 테이블 조회 실패
알 수 없는 서버 오류
```

### Backend → Unity 응답 예시

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
  "errorCode": "INTERNAL_SERVER_ERROR",
  "warningCode": null
}
```

---

## 8. warningCode 정의

## 8.1 전체 warningCode 목록

| warningCode | 발생 위치 | 의미 | 처리 방식 |
| --- | --- | --- | --- |
| SAVE_FAILED | Backend | AI 판정은 성공했지만 DB 저장 실패 | 성공 판정이면 다음 장면 진행 허용 |

---

## 8.2 SAVE_FAILED

### 의미

AI 서버의 동작 판정은 성공했지만, 백엔드에서 결과를 DB에 저장하는 과정에서 실패한 경우입니다.

### 발생 위치

```text
Backend
```

### 처리 기준

해커톤 시연 안정성을 위해, 동작 판정이 성공했다면 DB 저장 실패만으로 다음 장면 진행을 막지 않습니다.

대신 백엔드 로그에 저장 실패를 남기고, 가능하면 재저장을 시도합니다.

### Backend → Unity 응답 예시

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

## 9. 최종 응답 필드 기준

Backend가 Unity에 반환하는 최종 응답은 다음 구조를 기준으로 합니다.

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

## 필드 설명

| 필드명 | 설명 |
| --- | --- |
| success | 동작 판정 성공 여부 |
| sceneCleared | 현재 장면 클리어 여부 |
| currentSceneId | 현재 장면 ID |
| nextSceneId | 다음 장면 ID, 실패 또는 엔딩이면 null |
| nextAction | NEXT_SCENE, RETRY, ENDING 중 하나 |
| score | AI 동작 판정 점수 |
| reasonCode | 성공 또는 동작 실패 이유 코드 |
| message | 백엔드가 생성한 사용자 안내 메시지 |
| errorCode | 판정 불가 또는 시스템 오류 코드 |
| warningCode | 경고 코드 |

`storyId`는 요청 검증과 저장에는 사용하지만, 현재 Backend → Unity 최종 응답에는 포함하지 않습니다.

필요하다면 디버깅이나 프론트 상태 확인을 위해 `storyId`를 응답에 포함할 수 있지만, MVP에서는 요청값으로 이미 알고 있으므로 필수 응답 필드는 아닙니다.

---

## 10. 처리 우선순위

백엔드는 다음 순서로 코드를 판단합니다.

```text
1. 요청 형식 검증
   → 실패 시 INVALID_POSE_DATA

2. storyId 지원 여부 및 storyId / sceneId / missionType 매칭 검증
   → 실패 시 MISSION_MISMATCH

3. AI 서버 호출
   → 호출 실패 시 AI_SERVER_ERROR

4. AI 서버 응답 확인
   → errorCode가 있으면 errorCode 기준으로 message 생성
   → reasonCode가 있으면 reasonCode 기준으로 message 생성

5. success 여부 확인
   → true이면 storyId / sceneId 기준으로 nextSceneId / nextAction 생성
   → false이면 nextAction = RETRY

6. 결과 저장
   → 저장 실패 시 warningCode = SAVE_FAILED

7. Unity에 최종 응답 반환
```

---

## 11. 코드 사용 기준 요약

## 11.1 reasonCode를 사용하는 경우

```text
동작은 감지되었지만 성공 기준에 부족한 경우
동작 판정에 성공한 경우
AI 서버가 정상적으로 점수를 계산한 경우
```

예시:

```text
MISSION_SUCCESS
HANDS_TOO_FAR
HAND_NOT_RAISED
ARMS_NOT_WIDE
```

---

## 11.2 errorCode를 사용하는 경우

```text
동작 판정 자체가 어려운 경우
입력 데이터가 잘못된 경우
시스템 오류가 발생한 경우
storyId, sceneId, missionType 조합이 맞지 않는 경우
```

예시:

```text
USER_NOT_DETECTED
HAND_NOT_VISIBLE
INVALID_POSE_DATA
MISSION_MISMATCH
AI_SERVER_ERROR
```

---

## 11.3 warningCode를 사용하는 경우

```text
사용자 진행은 가능하지만, 백엔드에서 기록해야 하는 문제가 발생한 경우
```

예시:

```text
SAVE_FAILED
```

---

## 12. 최종 정리

이번 MVP에서는 코드 체계를 다음처럼 분리합니다.

```text
reasonCode:
동작 판정 결과 이유

errorCode:
판정 불가 또는 시스템 오류

warningCode:
진행은 가능하지만 기록이 필요한 경고
```

AI 서버는 다음 값만 반환합니다.

```text
success
score
reasonCode
errorCode
```

백엔드는 AI 서버 응답을 바탕으로 다음 값을 생성합니다.

```text
message
nextAction
nextSceneId
warningCode
```

백엔드는 요청을 처리하기 전에 다음 조합을 검증합니다.

```text
storyId + sceneId + missionType
```

Backend는 `success = true`인 경우 `storyId + sceneId` 기준으로 `nextSceneId`와 `nextAction`을 결정합니다.

Unity는 백엔드의 최종 응답을 기준으로 장면 전환 또는 재시도 UI를 처리합니다.

`storyId`는 현재 MVP에서는 `heungbu_nolbu` 하나로 고정되지만, 추후 여러 동화가 추가될 경우 같은 `sceneId`를 동화별로 구분하기 위한 핵심 값이므로 유지합니다.
