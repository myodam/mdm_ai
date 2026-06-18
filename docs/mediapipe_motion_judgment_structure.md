# 몸으로 넘기는 전래동화 - MediaPipe 동작 판정 구조

## 1. 전체 구조

이번 서비스는 사용자가 전래동화 속 장면에 맞는 동작을 수행하면, MediaPipe 기반 포즈 좌표를 이용해 동작 성공 여부를 판단하고 다음 장면으로 넘어가는 방식으로 구현합니다.

대상 연령이 4~7세이기 때문에 실시간으로 계속 자세를 유지하게 하는 방식보다는, 미션마다 충분한 수행 시간을 제공하고 그 시간 동안 수집한 포즈 좌표를 기반으로 성공 여부를 판단하는 방식이 적합합니다.

따라서 WebSocket 기반 실시간 스트리밍 방식은 사용하지 않고, 미션 수행이 끝난 뒤 HTTP 요청으로 좌표 데이터를 한 번에 보내고 결과를 받는 구조로 진행합니다.

최종 구조는 다음과 같습니다.

```
Unity
→ MediaPipe로 사용자 포즈 좌표 추출
→ 미션 수행 시간 동안 poseFrames 수집
→ 백엔드에 storyId, sceneId, missionType, poseFrames 전송
→ 백엔드가 요청 검증 및 storyId / sceneId / missionType 매칭 확인
→ 백엔드가 AI 서버(FastAPI)에 좌표 데이터 전달
→ AI 서버가 장면별 조건에 따라 동작 성공 여부 계산
→ AI 서버가 success / score / reasonCode / errorCode 반환
→ 백엔드가 reasonCode / errorCode 기준으로 message 생성
→ 백엔드가 storyId / sceneId / success 기준으로 nextAction / nextSceneId 생성
→ 백엔드가 판정 결과 저장
→ 백엔드가 Unity에 최종 응답 반환
→ Unity는 성공 시 다음 씬으로 이동, 실패 시 재도전 안내
```

즉, Unity는 AI 서버를 직접 호출하지 않습니다.

Unity는 백엔드 API만 호출하고, 백엔드가 내부적으로 AI 서버를 호출합니다.

AI 서버는 FastAPI로 구현할 수 있으며, AI 서버는 동작 판정만 담당합니다.

사용자 메시지 생성, 다음 장면 결정, DB 저장은 백엔드가 담당합니다.

---

## 2. storyId 사용 기준

이번 MVP에서는 「흥부와 놀부」 하나만 구현하므로 `storyId`는 당장 복잡한 분기에는 많이 사용되지 않을 수 있습니다.

하지만 추후 여러 동화가 추가될 경우 `scene_001`, `scene_002` 같은 sceneId는 동화마다 중복될 수 있습니다.

예시는 다음과 같습니다.

```
heungbu_nolbu / scene_001 → 다친 제비 보호하기
little_prince / scene_001 → 어린왕자가 별에 앉아 있는 장면
red_riding_hood / scene_001 → 숲길을 걷는 장면
```

따라서 `sceneId`만으로 장면을 구분하는 것보다, `storyId + sceneId + missionType` 조합으로 검증하는 구조가 더 안전합니다.

이번 MVP에서는 다음 값을 사용합니다.

```
storyId: heungbu_nolbu
```

백엔드는 `storyId`를 다음 목적으로 사용합니다.

```
1. 지원하는 동화인지 확인
2. 해당 storyId 안에서 sceneId가 유효한지 확인
3. storyId + sceneId + missionType 조합이 올바른지 검증
4. 성공 시 storyId + sceneId 기준으로 nextSceneId 결정
5. 결과 저장 시 어떤 동화의 미션 결과인지 구분
```

즉, `storyId`는 현재 MVP에서는 확장성을 위한 필드이지만, 백엔드 검증과 저장 기준에서도 의미가 있으므로 유지합니다.

---

## 3. 이 구조를 선택하는 이유

Unity가 AI 서버를 직접 호출하는 방식도 가능하지만, 이번 프로젝트에서는 백엔드를 거치는 구조가 더 적합합니다.

이유는 다음과 같습니다.

```
1. Unity는 백엔드 API 하나만 바라보면 되므로 연동 구조가 단순해진다.
2. storyId, sceneId, missionType, nextSceneId 관리를 백엔드에서 일관되게 처리할 수 있다.
3. 여러 동화가 추가될 경우 storyId + sceneId 조합으로 장면을 안전하게 구분할 수 있다.
4. AI 서버 주소나 내부 로직이 바뀌어도 Unity 코드를 크게 수정하지 않아도 된다.
5. 사용자에게 보여줄 메시지를 백엔드에서 통합 관리할 수 있다.
6. AI 판정 결과 저장을 백엔드에서 바로 처리할 수 있다.
7. AI 서버 장애, DB 저장 실패, 요청 데이터 오류를 백엔드에서 통합 관리할 수 있다.
8. 추후 AI 서버가 FastAPI로 분리되어도 백엔드가 중간 게이트웨이 역할을 할 수 있다.
```

최종 역할은 다음과 같이 나눕니다.

```
Unity:
화면, 카메라, MediaPipe 좌표 추출, storyId / sceneId / missionType 전달,
미션 UI, 장면 전환 담당

Backend:
API 진입점, 요청 검증, storyId / sceneId / missionType 매칭 확인,
AI 서버 호출, reasonCode / errorCode 기반 메시지 생성,
storyId / sceneId / success 기준 nextAction / nextSceneId 생성,
결과 저장 담당

AI Server:
MediaPipe 좌표 기반 동작 판정 담당

DB:
storyId 기준 미션 결과 저장 담당
```

---

## 4. 동작 수집 방식

기존처럼 1~2초만 좌표를 수집하면, 4~7세 아이들이 안내를 듣고 동작을 수행하기에 시간이 부족할 수 있습니다.

따라서 MVP에서는 미션마다 약 3~5초의 동작 수행 시간을 제공합니다.

```
미션 안내
→ “동작을 해볼까요?”
→ Unity가 3~5초 동안 MediaPipe 좌표 수집
→ poseFrames 배열로 묶어서 백엔드에 한 번에 전송
→ 백엔드가 storyId / sceneId / missionType 검증
→ 백엔드가 AI 서버에 poseFrames 전달
→ AI 서버가 전체 프레임을 기준으로 성공 여부와 reasonCode 판단
→ 백엔드가 사용자 메시지와 다음 진행 정보를 생성
```

중요한 점은 3~5초 동안 서버와 계속 통신하는 것이 아닙니다.

Unity가 클라이언트 내부에서 좌표를 모은 뒤, 수집이 끝나면 HTTP 요청으로 한 번에 전송합니다.

---

## 5. 미션별 권장 수집 시간

모든 미션을 동일하게 5초로 처리해도 되고, 장면별로 다르게 설정해도 됩니다.

해커톤 구현 안정성을 고려하면 **전체 미션 5초 통일**이 가장 단순합니다.

다만 장면별로 나누면 다음과 같습니다.

```
Scene 1. 다친 제비 보호하기
→ 두 손을 모으는 자세형 미션
→ 권장 수집 시간: 3초

Scene 2. 박씨 받기
→ 한 손을 드는 자세형 미션
→ 권장 수집 시간: 3초

Scene 3. 박 타기
→ 양팔을 크게 벌리거나 휘두르는 동작형 미션
→ 권장 수집 시간: 5초
```

MVP에서는 다음 방식으로 통일할 수 있습니다.

```
모든 미션 수행 시간: 5초
프레임 샘플링: 초당 5프레임
전송 프레임 수: 약 25개 poseFrame
timestamp 예시: 0.0, 0.2, 0.4, 0.6, ... 4.8
```

30fps 전체를 모두 보내면 데이터가 불필요하게 커질 수 있으므로, 초당 5프레임 정도만 샘플링해서 보내는 것을 추천합니다.

---

# 6. 역할 분리

## 6.1 Unity 역할

Unity는 사용자의 카메라 화면에서 MediaPipe를 통해 포즈 랜드마크 좌표를 추출합니다.

Unity가 담당할 내용은 다음과 같습니다.

```
1. 현재 storyId, sceneId, missionType 관리
2. 미션 시작 시 사용자에게 동작 안내
3. MediaPipe로 포즈 좌표 추출
4. 미션 수행 시간 3~5초 동안 poseFrames 수집
5. 초당 5프레임 정도로 좌표 샘플링
6. storyId, sceneId, missionType, poseFrames를 백엔드 API로 전송
7. 백엔드 응답을 받아 성공/실패 UI 표시
8. 성공이면 nextSceneId 기준으로 다음 씬 이동
9. 실패이면 message를 표시하고 다시 시도 버튼 제공
```

Unity는 동작 성공 여부를 직접 판단하지 않습니다.

Unity는 사용자 동작에서 나온 좌표값을 백엔드에 전달하고, 백엔드가 반환한 결과에 따라 화면을 전환합니다.

`storyId`는 현재 동화가 무엇인지 백엔드가 알 수 있도록 전달합니다.

현재 MVP에서는 `heungbu_nolbu` 하나만 사용하지만, 이후 여러 동화가 추가될 경우 Unity는 선택된 동화의 `storyId`를 함께 전달해야 합니다.

---

## 6.2 백엔드 역할

백엔드는 Unity와 AI 서버 사이의 중간 허브 역할을 합니다.

백엔드가 담당할 내용은 다음과 같습니다.

```
1. Unity로부터 storyId, sceneId, missionType, poseFrames 수신
2. 요청 데이터 형식 검증
3. storyId가 지원하는 동화인지 확인
4. 현재 storyId 안에서 sceneId가 유효한지 확인
5. storyId + sceneId + missionType 조합이 올바른지 확인
6. AI 서버에 동작 판정 요청
7. AI 서버로부터 success, score, reasonCode, errorCode 수신
8. reasonCode / errorCode를 기준으로 사용자 message 생성
9. success와 storyId / sceneId를 기준으로 nextAction / nextSceneId 생성
10. success, score, reasonCode, message, errorCode, warningCode 저장
11. Unity에 최종 응답 반환
```

백엔드는 AI 판정 결과를 그대로 Unity에 전달하는 것이 아니라, 현재 스토리 진행 상태와 메시지 매핑, DB 저장 결과까지 반영해서 최종 응답을 만들어 반환합니다.

`storyId`는 백엔드에서 다음과 같이 사용됩니다.

```
storyId = heungbu_nolbu
sceneId = scene_001
missionType = protect_swallow
→ 올바른 요청

storyId = heungbu_nolbu
sceneId = scene_001
missionType = receive_seed
→ 잘못된 요청
→ errorCode = MISSION_MISMATCH
```

추후 다른 동화가 추가되면 같은 `scene_001`이라도 `storyId`에 따라 다른 미션으로 매핑할 수 있습니다.

---

## 6.3 AI 서버 역할

AI 서버는 백엔드로부터 전달받은 MediaPipe 좌표를 기반으로 장면별 동작을 판정합니다.

AI 서버는 FastAPI로 구현할 수 있습니다.

AI 서버가 담당할 내용은 다음과 같습니다.

```
1. 백엔드에서 전달받은 poseFrames 검증
2. storyId, sceneId, missionType을 참고하여 판정 대상 확인
3. missionType에 따라 판정 함수 선택
4. 필요한 관절 좌표 추출
5. 거리, 각도, 위치 관계, 움직임 변화량 계산
6. success true/false 판단
7. score 계산
8. reasonCode 결정
9. errorCode 결정
10. 백엔드에 판정 결과 반환
```

AI 서버는 DB에 직접 저장하지 않습니다.

AI 서버는 사용자 메시지를 생성하지 않습니다.

AI 서버는 nextAction 또는 nextSceneId를 결정하지 않습니다.

AI 서버는 동작 판정 결과만 계산하고, 저장과 최종 응답 생성은 백엔드에서 처리합니다.

AI 서버는 `storyId`를 직접 분기 로직의 핵심으로 사용하지 않아도 됩니다.

다만 백엔드가 전달한 요청이 어떤 동화의 장면인지 식별할 수 있도록 요청값에 포함할 수 있습니다. MVP에서는 `missionType` 중심으로 detector를 선택해도 충분합니다.

---

# 7. 최종 데이터 흐름

## 7.1 성공 흐름

```
1. Unity에서 heungbu_nolbu / scene_001 미션 시작
2. 사용자가 두 손 모으기 동작 수행
3. Unity가 3~5초 동안 MediaPipe 좌표를 수집
4. Unity가 storyId, sceneId, missionType, poseFrames를 백엔드에 전송
5. 백엔드가 요청 데이터 검증
6. 백엔드가 storyId + sceneId + missionType 매칭 확인
7. 백엔드가 AI 서버에 판정 요청
8. AI 서버가 protect_swallow 판정 로직 실행
9. AI 서버가 success true, score, reasonCode, errorCode 반환
10. 백엔드가 reasonCode 기준으로 성공 메시지 생성
11. 백엔드가 storyId + sceneId 기준으로 nextSceneId와 nextAction 생성
12. 백엔드가 결과를 DB에 저장
13. 백엔드가 Unity에 최종 응답 반환
14. Unity가 다음 장면으로 이동
```

## 7.2 실패 흐름

```
1. Unity에서 현재 장면의 미션 시작
2. 사용자가 동작 수행
3. Unity가 3~5초 동안 poseFrames 수집
4. Unity가 storyId, sceneId, missionType, poseFrames를 백엔드에 전송
5. 백엔드가 storyId + sceneId + missionType 매칭 확인
6. 백엔드가 AI 서버에 판정 요청
7. AI 서버가 success false, score, reasonCode, errorCode 반환
8. 백엔드가 reasonCode 기준으로 실패 힌트 메시지 생성
9. 백엔드가 실패 결과를 DB에 저장
10. 백엔드가 nextAction: RETRY 응답을 Unity에 반환
11. Unity가 실패 메시지와 다시 시도 버튼 표시
```

---

# 8. Unity가 백엔드에 보내야 하는 데이터

Unity는 MediaPipe에서 추출한 좌표값을 백엔드 API로 전달합니다.

기본적으로 다음 정보가 필요합니다.

```
storyId
sceneId
missionType
captureDurationSec
sampleFps
poseFrames
```

이번 MVP에서는 회원가입/로그인을 구현하지 않기 때문에 `userId`는 사용하지 않습니다.

또한 실패 횟수 기반 분기 처리는 MVP 범위에서 제외하므로 `attemptCount`도 사용하지 않습니다.

`storyId`는 현재 사용자가 진행 중인 동화를 구분하기 위한 값입니다.

현재 MVP에서는 다음 값으로 고정합니다.

```
storyId = heungbu_nolbu
```

poseFrames에는 미션 수행 시간 동안 수집한 포즈 좌표 배열이 들어갑니다.

정지 자세에 가까운 미션은 짧은 시간만으로도 가능하지만, 아이들의 움직임이 흔들릴 수 있으므로 3~5초 정도의 수행 시간을 제공하고 약 15~25개 프레임을 전달하는 것이 안정적입니다.

---

## 8.1 Unity → Backend 요청 예시

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
        "leftShoulder": { "x": 0.42, "y": 0.35, "visibility": 0.98 },
        "rightShoulder": { "x": 0.58, "y": 0.35, "visibility": 0.97 },
        "leftElbow": { "x": 0.45, "y": 0.48, "visibility": 0.94 },
        "rightElbow": { "x": 0.55, "y": 0.48, "visibility": 0.94 },
        "leftWrist": { "x": 0.49, "y": 0.58, "visibility": 0.91 },
        "rightWrist": { "x": 0.51, "y": 0.58, "visibility": 0.91 }
      }
    }
  ]
}
```

좌표는 MediaPipe 기준으로 정규화된 x, y 값을 사용합니다.

```
x: 화면 가로 위치, 0~1
y: 화면 세로 위치, 0~1
visibility: 해당 관절이 잘 보이는 정도
```

MediaPipe 좌표 기준으로 `y`값이 작을수록 화면 위쪽입니다.

API JSON 필드는 Unity와 백엔드 연동을 고려하여 camelCase로 통일합니다.

---

# 9. 백엔드가 AI 서버에 보내는 데이터

백엔드는 Unity에서 받은 요청을 검증한 뒤 AI 서버에 판정 요청을 보냅니다.

백엔드가 AI 서버에 보내는 데이터는 Unity 요청과 거의 동일하지만, AI 서버가 판정에 필요한 값만 전달하는 것이 좋습니다.

AI 서버는 동작 판정만 담당하므로, DB 저장에 필요한 정보는 백엔드가 관리합니다.

`storyId`는 AI 서버에서 필수 분기 기준은 아니지만, 어떤 동화의 장면 판정인지 식별하기 위해 전달할 수 있습니다.

---

## 9.1 Backend → AI 요청 예시

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
        "rightWrist": { "x": 0.51, "y": 0.58, "visibility": 0.91 }
      }
    }
  ]
}
```

---

# 10. AI 서버가 백엔드에 반환하는 데이터

AI 서버는 좌표를 분석한 뒤 성공 여부, 점수, 판정 이유 코드를 백엔드에 반환합니다.

AI 서버는 사용자 메시지를 직접 반환하지 않습니다.

AI 서버는 nextAction을 직접 결정하지 않습니다.

AI 서버는 nextSceneId를 직접 결정하지 않습니다.

message, nextAction, nextSceneId는 백엔드가 결정합니다.

---

## 10.1 AI → Backend 성공 응답 예시

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

## 10.2 AI → Backend 실패 응답 예시

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

## 10.3 AI → Backend 예외 응답 예시

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "HAND_NOT_VISIBLE"
}
```

---

# 11. 백엔드가 Unity에 반환하는 데이터

백엔드는 AI 판정 결과를 기반으로 message, nextAction, nextSceneId를 생성한 뒤 Unity에 최종 응답을 반환합니다.

---

## 11.1 성공 응답 예시

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

## 11.2 실패 응답 예시

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

## 11.3 엔딩 응답 예시

마지막 장면 성공 시에는 nextSceneId는 null, nextAction은 ENDING으로 반환합니다.

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

# 12. API 구조 추천

## 12.1 Unity → Backend 동작 판정 요청 API

Unity는 이 API만 호출합니다.

```
POST /api/missions/check
```

요청:

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

응답:

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

## 12.2 Backend → AI 동작 판정 내부 API

백엔드가 AI 서버를 호출할 때 사용합니다.

```
POST /internal/ai/missions/check
```

요청:

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

응답:

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

---

# 13. DB 저장 추천 항목

백엔드는 AI 판정 결과와 최종 응답 정보를 DB에 저장합니다.

좌표 원본은 필수 저장 대상이 아닙니다.

좌표값은 양이 많고, 카메라 기반 데이터와 연결될 수 있으므로 해커톤에서는 저장하지 않는 것을 추천합니다.

---

## 13.1 저장 항목

이번 MVP에서는 회원가입/로그인을 구현하지 않기 때문에 user_id는 저장하지 않습니다.

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

여기서 `story_id`는 어떤 동화의 미션 결과인지 구분하기 위해 저장합니다.

현재 MVP에서는 `heungbu_nolbu`로 저장됩니다.

추후 여러 동화가 추가되면 같은 `scene_id`라도 `story_id`에 따라 다른 장면으로 구분할 수 있습니다.

## 13.2 저장 데이터 예시

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

# 14. storyId / sceneId / missionType 매핑

## 14.1 MVP 매핑

이번 MVP에서는 `heungbu_nolbu` 하나의 동화만 사용합니다.

```
storyId: heungbu_nolbu
```

매핑은 다음과 같습니다.

| storyId | sceneId | missionType | 장면 | nextSceneId |
| --- | --- | --- | --- | --- |
| heungbu_nolbu | scene_001 | protect_swallow | 다친 제비 보호하기 | scene_002 |
| heungbu_nolbu | scene_002 | receive_seed | 박씨 받기 | scene_003 |
| heungbu_nolbu | scene_003 | open_gourd | 박 타기 | null |

## 14.2 백엔드 검증 기준

백엔드는 AI 서버를 호출하기 전에 다음 항목을 확인합니다.

```
1. storyId가 지원하는 동화인지 확인
2. sceneId가 해당 storyId 안에 존재하는지 확인
3. missionType이 해당 storyId + sceneId에 맞는지 확인
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

단, MVP에서 에러 코드를 단순화하려면 `INVALID_STORY`를 별도로 만들지 않고 `MISSION_MISMATCH` 또는 `INVALID_POSE_DATA` 계열로 처리할 수 있습니다.

추천은 다음과 같습니다.

```
지원하지 않는 storyId → MISSION_MISMATCH
sceneId와 missionType 불일치 → MISSION_MISMATCH
poseFrames 누락 또는 좌표 구조 오류 → INVALID_POSE_DATA
```

해커톤에서는 에러 코드를 너무 늘리지 않는 것이 좋기 때문에 `MISSION_MISMATCH`로 통합해도 충분합니다.

---

# 15. reasonCode / errorCode 정리

## 15.1 reasonCode

reasonCode는 사용자가 동작을 수행했지만, 성공 기준에 부족하거나 성공 조건을 만족했을 때 사용하는 판정 이유 코드입니다.

AI 서버가 반환하고, 백엔드는 reasonCode를 사용자 메시지로 변환합니다.

```
MISSION_SUCCESS
HANDS_TOO_FAR
HANDS_NOT_CENTERED
HAND_NOT_RAISED
ARMS_NOT_WIDE
MOVEMENT_TOO_SMALL
LOW_SCORE
```

## 15.2 errorCode

errorCode는 판정 자체가 어렵거나 시스템 문제가 있을 때 사용합니다.

```
USER_NOT_DETECTED
HAND_NOT_VISIBLE
INVALID_POSE_DATA
MISSION_MISMATCH
AI_SERVER_ERROR
INTERNAL_SERVER_ERROR
```

`MISSION_MISMATCH`는 백엔드에서 storyId, sceneId, missionType 매칭 검증 시 주로 사용합니다.

`AI_SERVER_ERROR`는 백엔드가 AI 서버 호출 실패를 감지했을 때 주로 사용합니다.

---

# 16. 흥부와 놀부 장면별 동작 판정

## 16.1 Scene 1. 흥부가 다친 제비를 만난다

## 미션

흥부가 다친 제비를 조심스럽게 보호하는 장면입니다.

사용자는 두 손을 모으거나 감싸는 동작을 합니다.

## 필요한 주요 좌표

```
leftShoulder
rightShoulder
leftElbow
rightElbow
leftWrist
rightWrist
```

## AI 판정 기준

핵심은 두 손목이 몸 중앙 근처에서 가까워졌는지를 판단하는 것입니다.

이 장면은 자세형 미션이므로, 전체 poseFrames 중 가장 성공 조건에 가까운 프레임을 기준으로 판단합니다.

## 계산 방식

```
handDistance = distance(leftWrist, rightWrist)

bodyCenterX = (leftShoulder.x + rightShoulder.x) / 2
handsCenterX = (leftWrist.x + rightWrist.x) / 2
centerDiff = abs(handsCenterX - bodyCenterX)
```

## 성공 조건 예시

```
양손 visibility >= 0.6
handDistance < 0.18
centerDiff < 0.2
```

실제 Unity 테스트 후 기준값은 조정할 수 있습니다.

```
handDistance 기준 추천 범위: 0.15~0.25
centerDiff 기준 추천 범위: 0.15~0.25
```

## 반환 코드

성공:

```json
{
  "success": true,
  "score": 0.88,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

실패 - 양손이 너무 멀 때:

```json
{
  "success": false,
  "score": 0.42,
  "reasonCode": "HANDS_TOO_FAR",
  "errorCode": null
}
```

실패 - 손이 몸 중앙에서 벗어났을 때:

```json
{
  "success": false,
  "score": 0.45,
  "reasonCode": "HANDS_NOT_CENTERED",
  "errorCode": null
}
```

백엔드는 reasonCode를 기준으로 다음과 같은 메시지를 생성합니다.

```
MISSION_SUCCESS → 좋아요! 제비를 조심스럽게 보호했어요.
HANDS_TOO_FAR → 두 손을 조금 더 가까이 모아주세요.
HANDS_NOT_CENTERED → 두 손을 몸 가운데로 모아주세요.
```

---

## 16.2 Scene 2. 제비가 박씨를 물어다 준다

## 미션

제비가 흥부에게 박씨를 가져다주는 장면입니다.

사용자는 한 손을 들어 박씨를 받는 동작을 합니다.

## 필요한 주요 좌표

```
leftShoulder
rightShoulder
leftElbow
rightElbow
leftWrist
rightWrist
nose
```

## AI 판정 기준

핵심은 한쪽 손목이 어깨보다 위로 올라갔는지 판단하는 것입니다.

이 장면도 자세형 미션이므로, 전체 poseFrames 중 가장 성공 조건에 가까운 프레임을 기준으로 판단합니다.

MediaPipe 좌표에서는 y값이 작을수록 화면 위쪽입니다.

따라서 손을 들었다는 것은 다음과 같이 판단합니다.

```
wrist.y < shoulder.y
```

## 계산 방식

```
leftHandRaised = leftWrist.y < leftShoulder.y - 0.05
rightHandRaised = rightWrist.y < rightShoulder.y - 0.05
```

## 성공 조건 예시

```
leftHandRaised == true 또는 rightHandRaised == true
왼손 또는 오른손 visibility >= 0.6
```

## 반환 코드

성공:

```json
{
  "success": true,
  "score": 0.91,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

실패:

```json
{
  "success": false,
  "score": 0.35,
  "reasonCode": "HAND_NOT_RAISED",
  "errorCode": null
}
```

백엔드는 reasonCode를 기준으로 다음과 같은 메시지를 생성합니다.

```
MISSION_SUCCESS → 잘했어요! 박씨를 받았어요.
HAND_NOT_RAISED → 한 손을 어깨보다 높게 들어주세요.
```

---

## 16.3 Scene 3. 흥부가 박을 탄다

## 미션

흥부가 커다란 박을 열기 위해 박을 타는 장면입니다.

사용자는 양팔을 크게 휘두르는 동작을 합니다.

해커톤에서는 실제로 복잡한 휘두르기 동작을 완벽하게 분석하기보다, 양팔을 크게 벌리거나 팔이 크게 움직였는지 정도로 단순화해서 판단하는 것이 현실적입니다.

## 필요한 주요 좌표

```
leftShoulder
rightShoulder
leftElbow
rightElbow
leftWrist
rightWrist
```

## AI 판정 방식

이 장면은 자세형 판정과 움직임 판정을 함께 사용할 수 있습니다.

해커톤에서는 우선 단순 자세 판정을 기본으로 하고, 시간이 남으면 움직임 판정을 추가하는 것을 추천합니다.

---

## 1안. 단순 자세 판정 방식

양팔을 크게 벌리면 박을 타는 동작으로 인정합니다.

해커톤에서 가장 구현이 쉽고 안정적인 방식입니다.

## 계산 방식

```
shoulderWidth = distance(leftShoulder, rightShoulder)
wristWidth = distance(leftWrist, rightWrist)
```

성공 기준 예시:

```
wristWidth > shoulderWidth * 1.6
```

추가 조건:

```
leftWrist.x < leftShoulder.x
rightWrist.x > rightShoulder.x
```

최종 성공 조건:

```
leftWrist.visibility >= 0.6
rightWrist.visibility >= 0.6
wristWidth > shoulderWidth * 1.6
leftWrist.x < leftShoulder.x
rightWrist.x > rightShoulder.x
```

---

## 2안. 짧은 움직임 판정 방식

박을 타는 동작을 조금 더 자연스럽게 보이게 하려면, 5초 동안 수집된 poseFrames에서 손목의 움직임 변화량을 확인합니다.

Unity가 여러 프레임을 보내면 AI는 손목의 이동 거리를 계산합니다.

## 계산 방식

```
leftMovement = totalMovement(leftWrist over poseFrames)
rightMovement = totalMovement(rightWrist over poseFrames)
totalArmMovement = leftMovement + rightMovement
```

성공 기준 예시:

```
totalArmMovement > 0.4
```

즉, 양팔이 일정 거리 이상 움직였으면 박을 타는 동작으로 인정합니다.

## 해커톤 추천

해커톤에서는 1안을 기본으로 하고, 시간이 남으면 2안을 추가하는 것을 추천합니다.

즉, 우선은 다음처럼 처리합니다.

```
양팔을 크게 벌리면 박을 탄 것으로 인정
```

이 방식이 시연 안정성이 높고, 아이들도 이해하기 쉽습니다.

## 반환 코드

성공:

```json
{
  "success": true,
  "score": 0.86,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

실패 - 양팔이 충분히 벌어지지 않은 경우:

```json
{
  "success": false,
  "score": 0.39,
  "reasonCode": "ARMS_NOT_WIDE",
  "errorCode": null
}
```

실패 - 움직임이 부족한 경우:

```json
{
  "success": false,
  "score": 0.45,
  "reasonCode": "MOVEMENT_TOO_SMALL",
  "errorCode": null
}
```

백엔드는 reasonCode를 기준으로 다음과 같은 메시지를 생성합니다.

```
MISSION_SUCCESS → 힘차게 박을 탔어요! 박이 열렸어요.
ARMS_NOT_WIDE → 양팔을 더 크게 벌려주세요.
MOVEMENT_TOO_SMALL → 팔을 더 크게 움직여주세요.
```

---

# 17. AI 판정 방식 정리

AI 서버는 poseFrames 전체를 보고 점수를 계산합니다.

미션 유형에 따라 판정 방식이 다릅니다.

```
자세형 미션:
전체 poseFrames 중 가장 점수가 높은 bestFrame 기준으로 판정

동작형 미션:
poseFrames 전체에서 손목 이동량, 방향, 변화량을 기준으로 판정
```

흥부와 놀부 MVP 기준은 다음과 같습니다.

```
Scene 1. protect_swallow
→ 자세형 미션
→ bestFrame 기준
→ 성공 reasonCode: MISSION_SUCCESS
→ 실패 reasonCode: HANDS_TOO_FAR, HANDS_NOT_CENTERED

Scene 2. receive_seed
→ 자세형 미션
→ bestFrame 기준
→ 성공 reasonCode: MISSION_SUCCESS
→ 실패 reasonCode: HAND_NOT_RAISED

Scene 3. open_gourd
→ 자세형 + 동작형
→ 기본은 bestFrame, 선택적으로 movement 계산 추가
→ 성공 reasonCode: MISSION_SUCCESS
→ 실패 reasonCode: ARMS_NOT_WIDE, MOVEMENT_TOO_SMALL
```

성공 기준은 다음과 같이 통일할 수 있습니다.

```
score >= 0.7
→ success true
→ reasonCode = MISSION_SUCCESS

score < 0.7
→ success false
→ 장면별 실패 reasonCode 반환
```

---

# 18. 예외 처리

## 18.1 사람이 화면에 감지되지 않는 경우

MediaPipe에서 주요 좌표가 거의 나오지 않거나 visibility가 낮으면 판정하지 않습니다.

## 조건 예시

```
shoulder, wrist 좌표 visibility가 0.5 미만
필수 관절 좌표가 null
poseFrames가 비어 있음
```

## AI 서버 응답 예시

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "USER_NOT_DETECTED"
}
```

## 백엔드 최종 응답 예시

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

## 18.2 손이 화면 밖으로 나간 경우

손목 좌표가 감지되지 않거나 visibility가 낮으면 손 동작을 판단할 수 없습니다.

## AI 서버 응답 예시

```json
{
  "success": false,
  "score": 0.0,
  "reasonCode": null,
  "errorCode": "HAND_NOT_VISIBLE"
}
```

## 백엔드 최종 응답 예시

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

## 18.3 좌표 데이터가 부족한 경우

Unity에서 poseFrames가 비어 있거나, 필수 landmark가 없는 경우입니다.

이 경우 백엔드에서 1차로 요청 형식을 검증하고, 필요하면 AI 서버를 호출하지 않고 바로 실패 응답을 반환할 수 있습니다.

## 백엔드 최종 응답 예시

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

## 18.4 storyId, sceneId, missionType이 맞지 않는 경우

예를 들어 `storyId = heungbu_nolbu`, `sceneId = scene_001`인데 `missionType = receive_seed`처럼 잘못 들어온 경우입니다.

이 경우 백엔드에서 `storyId + sceneId + missionType` 매칭을 확인하고, AI 서버를 호출하지 않는 것이 좋습니다.

## 백엔드 최종 응답 예시

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

## 18.5 AI 서버 오류

AI 서버 내부에서 계산 중 오류가 발생하거나 AI 서버 호출이 실패한 경우입니다.

이 경우 백엔드는 Unity에 안정적인 실패 응답을 반환합니다.

## 백엔드 최종 응답 예시

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

## 18.6 DB 저장 실패

AI 판정은 성공했지만 백엔드 저장에 실패한 경우입니다.

이 경우 Unity 시연에서는 사용자가 멈추지 않도록 처리하는 것이 중요합니다.

추천 방식은 다음과 같습니다.

```
AI 판정 성공
DB 저장 실패
→ Unity에는 성공 결과 반환
→ 백엔드 로그에 저장 실패 기록
→ 가능하면 재저장 시도
```

사용자 경험을 위해 저장 실패 때문에 다음 씬 진행을 막지 않는 것이 좋습니다.

## 백엔드 최종 응답 예시

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

# 19. 장면별 missionType 정리

## Scene 1

```
storyId: heungbu_nolbu
sceneId: scene_001
missionType: protect_swallow
동작: 두 손 모으기 / 감싸기
판정: 양손목 거리, 몸 중앙 위치
권장 수행 시간: 3~5초
성공 reasonCode: MISSION_SUCCESS
실패 reasonCode: HANDS_TOO_FAR, HANDS_NOT_CENTERED
```

## Scene 2

```
storyId: heungbu_nolbu
sceneId: scene_002
missionType: receive_seed
동작: 한 손 들기
판정: 손목이 어깨보다 위에 있는지 확인
권장 수행 시간: 3~5초
성공 reasonCode: MISSION_SUCCESS
실패 reasonCode: HAND_NOT_RAISED
```

## Scene 3

```
storyId: heungbu_nolbu
sceneId: scene_003
missionType: open_gourd
동작: 양팔 크게 벌리기 또는 휘두르기
판정: 양손목 거리, 어깨 너비 대비 손목 너비, 선택적으로 손목 이동량
권장 수행 시간: 5초
성공 reasonCode: MISSION_SUCCESS
실패 reasonCode: ARMS_NOT_WIDE, MOVEMENT_TOO_SMALL
```

---

# 20. 구현 시 주의사항

## 20.1 storyId는 MVP에서도 유지하기

현재 MVP에서는 동화가 하나뿐이므로 `storyId`가 없어도 기능 구현은 가능합니다.

하지만 추후 여러 동화가 추가될 경우 `sceneId`가 중복될 수 있으므로 `storyId`를 유지하는 것이 좋습니다.

```
현재:
heungbu_nolbu / scene_001 / protect_swallow

확장 예시:
little_prince / scene_001 / look_at_star
red_riding_hood / scene_001 / walk_forest
```

따라서 백엔드는 `storyId + sceneId + missionType` 조합으로 요청을 검증하는 구조를 권장합니다.

---

## 20.2 기준값은 처음부터 엄격하게 잡지 않기

대상 연령이 4~7세이기 때문에 동작 판정 기준을 너무 엄격하게 잡으면 실패가 자주 발생할 수 있습니다.

예를 들어 한 손 들기 동작에서 손목이 어깨보다 아주 높아야만 성공으로 처리하면 아이들이 불편할 수 있습니다.

따라서 처음에는 기준을 널널하게 잡는 것이 좋습니다.

```
visibility 기준: 0.6 정도
손 들기 기준: 어깨보다 살짝 위
양손 모으기 기준: 손목 거리 0.18~0.25 사이 테스트
양팔 벌리기 기준: 어깨 너비의 1.5~1.7배
```

---

## 20.3 모든 프레임을 보내지 않기

5초 동안 30fps 전체를 보내면 150프레임이 되어 데이터가 커질 수 있습니다.

따라서 Unity에서 초당 5프레임 정도만 샘플링해서 보내는 것을 추천합니다.

```
5초 수집
초당 5프레임 샘플링
약 25개 poseFrame 전송
```

이 정도면 아이가 천천히 동작해도 충분히 판정할 수 있고, 네트워크 데이터도 과하게 커지지 않습니다.

---

## 20.4 한 프레임만 믿지 않기

아이들이 움직이는 도중 좌표가 흔들릴 수 있습니다.

따라서 AI에서는 poseFrames 중 가장 성공 조건에 가까운 프레임을 기준으로 판단하는 것이 좋습니다.

예를 들어 25개 프레임 중 하나라도 성공 조건을 만족하면 성공으로 처리할 수 있습니다.

```
poseFrames 중 하나라도 조건 만족
→ success true
```

또는 각 프레임 점수를 계산해서 가장 높은 점수를 최종 점수로 사용할 수 있습니다.

```
각 프레임 점수 계산
가장 높은 점수 사용
score >= 0.7이면 성공
```

---

## 20.5 실패 메시지는 백엔드에서 관리하기

실패 메시지는 AI 서버에서 직접 만들지 않고, 백엔드에서 reasonCode 또는 errorCode를 기준으로 관리합니다.

AI 서버는 다음과 같은 코드만 반환합니다.

```
HANDS_TOO_FAR
HAND_NOT_RAISED
ARMS_NOT_WIDE
HAND_NOT_VISIBLE
```

백엔드는 이를 아이가 이해하기 쉬운 문구로 변환합니다.

좋은 예시:

```
두 손을 조금 더 가까이 모아주세요.
한 손을 하늘 위로 들어주세요.
양팔을 더 크게 벌려주세요.
카메라 앞에 서서 다시 해볼까요?
```

나쁜 예시:

```
좌표값이 기준보다 낮습니다.
visibility가 부족합니다.
랜드마크 인식 실패입니다.
```

---

## 20.6 백엔드에는 결과 중심으로 저장하기

좌표 원본을 모두 저장하면 데이터가 복잡해지고 불필요하게 커집니다.

해커톤에서는 다음 정도만 저장하면 충분합니다.

```
스토리 ID
씬 ID
미션 타입
성공 여부
점수
reasonCode
메시지
생성 시간
```

좌표 원본은 DB에 저장하지 않고, 필요하다면 개발 중 디버깅 로그로만 확인합니다.

---

# 21. 최종 정리

이번 흥부와 놀부 예시는 총 3개 미션으로 구성합니다.

```
Scene 1. 다친 제비 보호하기
→ 두 손 모으기 판정

Scene 2. 제비에게 박씨 받기
→ 한 손 들기 판정

Scene 3. 흥부가 박 타기
→ 양팔 크게 벌리기 또는 움직임 판정
```

최종 구조는 다음과 같습니다.

```
Unity
→ Backend
→ AI Server(FastAPI)
→ Backend
→ Unity
```

Unity는 MediaPipe 좌표를 추출해 3~5초 동안 poseFrames를 수집하고, 이를 백엔드에 보냅니다.

Unity는 현재 진행 중인 동화를 구분하기 위해 `storyId`도 함께 전달합니다.

백엔드는 `storyId + sceneId + missionType` 조합을 검증한 뒤 AI 서버에 판정을 요청합니다.

AI 서버는 장면별 조건에 따라 거리, 위치, 각도, 움직임 변화량 등을 계산해 `success`, `score`, `reasonCode`, `errorCode`를 반환합니다.

백엔드는 AI 결과를 바탕으로 사용자 메시지와 다음 장면 정보를 생성하고, 결과를 DB에 저장한 뒤 Unity에 최종 응답을 반환합니다.

해커톤 규모에서는 WebSocket 없이 HTTP 요청/응답 방식으로 충분하며, 실시간 추적보다는 미션 수행 구간의 좌표를 한 번에 전송하는 방식이 더 안정적입니다.

`storyId`는 현재 MVP에서는 `heungbu_nolbu` 하나로 고정되지만, 추후 여러 동화가 추가될 경우 같은 `sceneId`를 동화별로 구분하기 위한 핵심 값이므로 유지하는 것이 좋습니다.