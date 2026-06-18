# 몸으로 넘기는 전래동화 - storyId / sceneId / missionType 매핑표

## 1. 문서 목적

본 문서는 **몸으로 넘기는 전래동화 - 흥부와 놀부 MVP**에서 사용하는 `storyId`, `sceneId`, `missionType`의 매핑 기준을 정의합니다.

Unity, Backend, AI Server가 동일한 동화, 장면, 미션 정보를 기준으로 통신하기 위해 이 매핑표를 사용합니다.

이번 MVP에서는 「흥부와 놀부」 하나의 동화만 구현하지만, 추후 여러 동화가 추가될 경우 `scene_001`, `scene_002` 같은 장면 ID는 동화마다 중복될 수 있습니다.

따라서 백엔드는 `sceneId`만으로 장면을 판단하지 않고, 다음 조합을 기준으로 요청을 검증합니다.

```text
storyId + sceneId + missionType
```

현재 MVP에서 사용하는 `storyId`는 다음과 같습니다.

```text
storyId: heungbu_nolbu
```

---

## 2. 핵심 요약

```text
MVP storyId: heungbu_nolbu

heungbu_nolbu / scene_001 → protect_swallow
heungbu_nolbu / scene_002 → receive_seed
heungbu_nolbu / scene_003 → open_gourd
```

Backend는 `storyId + sceneId + missionType` 조합을 검증합니다.

AI Server는 `missionType`을 기준으로 detector를 선택합니다.

Unity는 Backend가 반환한 `nextAction`, `nextSceneId`, `message`를 기준으로 화면을 처리합니다.

---

## 3. 전체 매핑표

| 순서 | storyId | sceneId | missionType | 장면 이름 | 사용자 동작 | 판정 방식 | nextSceneId | 성공 시 nextAction |
|---:|---|---|---|---|---|---|---|---|
| 1 | heungbu_nolbu | scene_001 | protect_swallow | 다친 제비 보호하기 | 두 손 모으기 / 감싸기 | 양손목 거리, 몸 중앙 위치 확인 | scene_002 | NEXT_SCENE |
| 2 | heungbu_nolbu | scene_002 | receive_seed | 박씨 받기 | 한 손 들기 | 한쪽 손목이 어깨보다 위에 있는지 확인 | scene_003 | NEXT_SCENE |
| 3 | heungbu_nolbu | scene_003 | open_gourd | 박 타기 | 양팔 크게 벌리기 / 휘두르기 | 양손목 거리, 어깨 너비 대비 손목 너비, 선택적 손목 이동량 확인 | null | ENDING |

---

# 4. Scene 1 매핑 정보

## 4.1 기본 정보

```text
storyId: heungbu_nolbu
sceneId: scene_001
missionType: protect_swallow
장면 이름: 다친 제비 보호하기
사용자 동작: 두 손 모으기 / 감싸기
nextSceneId: scene_002
성공 시 nextAction: NEXT_SCENE
실패 시 nextAction: RETRY
```

## 4.2 장면 설명

흥부가 길을 걷다가 다친 제비를 발견하는 장면입니다.

사용자는 두 손을 모으거나 감싸는 동작을 하여 다친 제비를 조심스럽게 보호하는 행동을 수행합니다.

## 4.3 주요 사용 좌표

```text
leftShoulder
rightShoulder
leftElbow
rightElbow
leftWrist
rightWrist
```

## 4.4 판정 기준

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

## 4.5 reasonCode 매핑

| 상황 | success | reasonCode | Backend message |
|---|---:|---|---|
| 두 손을 몸 중앙 근처에 잘 모음 | true | MISSION_SUCCESS | 좋아요! 제비를 조심스럽게 보호했어요. |
| 양손 사이가 너무 멂 | false | HANDS_TOO_FAR | 두 손을 조금 더 가까이 모아주세요. |
| 양손이 몸 중앙에서 벗어남 | false | HANDS_NOT_CENTERED | 두 손을 몸 가운데로 모아주세요. |

---

# 5. Scene 2 매핑 정보

## 5.1 기본 정보

```text
storyId: heungbu_nolbu
sceneId: scene_002
missionType: receive_seed
장면 이름: 박씨 받기
사용자 동작: 한 손 들기
nextSceneId: scene_003
성공 시 nextAction: NEXT_SCENE
실패 시 nextAction: RETRY
```

## 5.2 장면 설명

흥부의 도움을 받은 제비가 고마움의 표시로 박씨를 물어다 주는 장면입니다.

사용자는 한 손을 들어 제비가 가져온 박씨를 받는 동작을 수행합니다.

## 5.3 주요 사용 좌표

```text
leftShoulder
rightShoulder
leftElbow
rightElbow
leftWrist
rightWrist
nose
```

## 5.4 판정 기준

MediaPipe 좌표에서는 `y`값이 작을수록 화면 위쪽입니다.

따라서 손을 들었다는 것은 손목의 y좌표가 어깨의 y좌표보다 작다는 의미입니다.

```text
leftHandRaised = leftWrist.y < leftShoulder.y - 0.05
rightHandRaised = rightWrist.y < rightShoulder.y - 0.05
```

성공 조건 예시:

```text
leftHandRaised == true 또는 rightHandRaised == true
leftWrist.visibility >= 0.6 또는 rightWrist.visibility >= 0.6
```

## 5.5 reasonCode 매핑

| 상황 | success | reasonCode | Backend message |
|---|---:|---|---|
| 한 손을 어깨보다 높게 듦 | true | MISSION_SUCCESS | 잘했어요! 박씨를 받았어요. |
| 손이 충분히 올라가지 않음 | false | HAND_NOT_RAISED | 한 손을 어깨보다 높게 들어주세요. |

---

# 6. Scene 3 매핑 정보

## 6.1 기본 정보

```text
storyId: heungbu_nolbu
sceneId: scene_003
missionType: open_gourd
장면 이름: 박 타기
사용자 동작: 양팔 크게 벌리기 / 휘두르기
nextSceneId: null
성공 시 nextAction: ENDING
실패 시 nextAction: RETRY
```

## 6.2 장면 설명

박씨에서 커다란 박이 자라고, 흥부가 박을 열기 위해 박을 타는 장면입니다.

사용자는 양팔을 크게 벌리거나 휘두르는 동작을 수행합니다.

해커톤 MVP에서는 복잡한 휘두르기 동작을 정교하게 분석하기보다, 양팔을 크게 벌리는 동작을 기본 성공 조건으로 사용합니다.

## 6.3 주요 사용 좌표

```text
leftShoulder
rightShoulder
leftElbow
rightElbow
leftWrist
rightWrist
```

## 6.4 판정 기준

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

## 6.5 reasonCode 매핑

| 상황 | success | reasonCode | Backend message |
|---|---:|---|---|
| 양팔을 충분히 크게 벌림 | true | MISSION_SUCCESS | 힘차게 박을 탔어요! 박이 열렸어요. |
| 양팔이 충분히 벌어지지 않음 | false | ARMS_NOT_WIDE | 양팔을 더 크게 벌려주세요. |
| 팔 움직임이 너무 작음 | false | MOVEMENT_TOO_SMALL | 팔을 더 크게 움직여주세요. |

---

# 7. ErrorCode 매핑표

`errorCode`는 동작이 부족한 경우가 아니라, 판정 자체가 어렵거나 시스템 문제가 있을 때 사용합니다.

| errorCode | 발생 위치 | 의미 | Backend message |
|---|---|---|---|
| USER_NOT_DETECTED | AI Server | 사람이 화면에 감지되지 않음 | 카메라 앞에 서서 다시 시도해주세요. |
| HAND_NOT_VISIBLE | AI Server | 손목 좌표가 보이지 않음 | 손이 화면 안에 보이도록 해주세요. |
| INVALID_POSE_DATA | Backend / AI Server | poseFrames가 없거나 필수 좌표가 누락됨 | 동작 정보를 확인할 수 없어요. 다시 시도해주세요. |
| MISSION_MISMATCH | Backend | storyId, sceneId, missionType 조합이 맞지 않음 | 현재 장면의 미션 정보가 올바르지 않습니다. |
| AI_SERVER_ERROR | Backend | AI 서버 호출 실패 또는 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |
| INTERNAL_SERVER_ERROR | Backend | 백엔드 내부 오류 | 잠시 문제가 발생했어요. 다시 시도해주세요. |

---

# 8. Backend 검증용 매핑

백엔드는 AI Server를 호출하기 전에 `storyId`, `sceneId`, `missionType`이 올바르게 매칭되는지 검증합니다.

MVP 기준 검증 매핑은 다음과 같습니다.

```json
{
  "heungbu_nolbu": {
    "scene_001": "protect_swallow",
    "scene_002": "receive_seed",
    "scene_003": "open_gourd"
  }
}
```

검증 예시:

```text
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
→ 지원하지 않는 storyId
→ errorCode = MISSION_MISMATCH
```

해커톤 MVP에서는 에러코드를 너무 늘리지 않기 위해, 지원하지 않는 `storyId`도 `MISSION_MISMATCH`로 처리합니다.

---

# 9. NextScene 매핑

백엔드는 `success = true`인 경우 현재 `storyId`와 `sceneId`를 기준으로 다음 장면을 결정합니다.

```json
{
  "heungbu_nolbu": {
    "scene_001": "scene_002",
    "scene_002": "scene_003",
    "scene_003": null
  }
}
```

처리 기준:

```text
heungbu_nolbu / scene_001 성공
→ nextSceneId = scene_002
→ nextAction = NEXT_SCENE

heungbu_nolbu / scene_002 성공
→ nextSceneId = scene_003
→ nextAction = NEXT_SCENE

heungbu_nolbu / scene_003 성공
→ nextSceneId = null
→ nextAction = ENDING

실패
→ nextSceneId = null
→ nextAction = RETRY
```

---

# 10. AI Server detector 매핑

AI Server는 `missionType`을 기준으로 실행할 detector를 선택합니다.

```json
{
  "protect_swallow": "protect_swallow_detector",
  "receive_seed": "receive_seed_detector",
  "open_gourd": "open_gourd_detector"
}
```

처리 기준:

```text
missionType = protect_swallow
→ protect_swallow_detector 실행

missionType = receive_seed
→ receive_seed_detector 실행

missionType = open_gourd
→ open_gourd_detector 실행
```

AI Server는 현재 MVP에서는 `missionType`을 기준으로 detector를 선택해도 충분합니다.

다만 요청에는 `storyId`도 함께 전달되므로, 추후 여러 동화가 추가될 경우 `storyId + missionType` 기준으로 detector를 세분화할 수 있습니다.

---

# 11. Backend message 매핑

AI Server는 사용자 메시지를 직접 반환하지 않습니다.

AI Server는 `reasonCode` 또는 `errorCode`만 반환하고, Backend가 이를 사용자 메시지로 변환합니다.

Backend는 `storyId`, `sceneId`, `missionType`, `reasonCode`, `errorCode`를 기준으로 메시지를 생성합니다.

---

## 11.1 reasonCode 기반 message 매핑

성공 메시지는 같은 `MISSION_SUCCESS`라도 장면마다 달라질 수 있으므로, `storyId + sceneId` 기준으로 관리합니다.

```json
{
  "MISSION_SUCCESS": {
    "heungbu_nolbu": {
      "scene_001": "좋아요! 제비를 조심스럽게 보호했어요.",
      "scene_002": "잘했어요! 박씨를 받았어요.",
      "scene_003": "힘차게 박을 탔어요! 박이 열렸어요."
    }
  },
  "HANDS_TOO_FAR": "두 손을 조금 더 가까이 모아주세요.",
  "HANDS_NOT_CENTERED": "두 손을 몸 가운데로 모아주세요.",
  "HAND_NOT_RAISED": "한 손을 어깨보다 높게 들어주세요.",
  "ARMS_NOT_WIDE": "양팔을 더 크게 벌려주세요.",
  "MOVEMENT_TOO_SMALL": "팔을 더 크게 움직여주세요.",
  "LOW_SCORE": "조금 더 크게 동작해볼까요?"
}
```

---

## 11.2 errorCode 기반 message 매핑

```json
{
  "USER_NOT_DETECTED": "카메라 앞에 서서 다시 시도해주세요.",
  "HAND_NOT_VISIBLE": "손이 화면 안에 보이도록 해주세요.",
  "INVALID_POSE_DATA": "동작 정보를 확인할 수 없어요. 다시 시도해주세요.",
  "MISSION_MISMATCH": "현재 장면의 미션 정보가 올바르지 않습니다.",
  "AI_SERVER_ERROR": "잠시 문제가 발생했어요. 다시 시도해주세요.",
  "INTERNAL_SERVER_ERROR": "잠시 문제가 발생했어요. 다시 시도해주세요."
}
```

---

# 12. Claude 구현 참고용 요약

## 12.1 Backend가 해야 하는 일

```text
1. Unity 요청 수신
2. storyId + sceneId + missionType 검증
3. poseFrames 유효성 검증
4. AI Server에 판정 요청
5. AI Server의 reasonCode / errorCode 수신
6. message 생성
7. success 기준 nextAction / nextSceneId 생성
8. Unity에 최종 응답 반환
```

## 12.2 AI Server가 해야 하는 일

```text
1. Backend에서 poseFrames 수신
2. missionType 기준 detector 선택
3. 좌표 기반 점수 계산
4. success / score / reasonCode / errorCode 반환
```

## 12.3 Unity가 해야 하는 일

```text
1. 현재 storyId, sceneId, missionType 관리
2. MediaPipe로 poseFrames 수집
3. Backend에 요청 전송
4. Backend 응답의 nextAction 기준으로 UI 처리
5. NEXT_SCENE이면 nextSceneId로 이동
6. RETRY이면 현재 장면 유지
7. ENDING이면 엔딩 화면 이동
```

---

# 13. 최종 정리

MVP에서 사용하는 `storyId`, `sceneId`, `missionType`은 다음 3개 조합으로 고정합니다.

```text
heungbu_nolbu / scene_001 → protect_swallow
heungbu_nolbu / scene_002 → receive_seed
heungbu_nolbu / scene_003 → open_gourd
```

Backend는 `storyId + sceneId + missionType` 매칭이 맞는지 먼저 검증합니다.

AI Server는 `missionType`을 기준으로 detector를 선택합니다.

AI Server는 동작 성공 여부를 판정한 뒤 `success`, `score`, `reasonCode`, `errorCode`를 반환합니다.

Backend는 AI Server의 `reasonCode` 또는 `errorCode`를 기준으로 사용자 메시지를 생성합니다.

Backend는 `success`, `storyId`, `sceneId`를 기준으로 `nextAction`, `nextSceneId`를 결정합니다.

Unity는 Backend의 최종 응답만 보고 장면 전환 또는 재시도 UI를 처리합니다.

`storyId`는 현재 MVP에서는 `heungbu_nolbu` 하나로 고정되지만, 추후 여러 동화가 추가될 경우 같은 `sceneId`를 동화별로 구분하기 위한 핵심 값이므로 유지합니다.
