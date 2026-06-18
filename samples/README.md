# AI 서버 통신 테스트 (개발자용 빠른 시작)

서버에 요청을 보내 **값이 잘 돌아오는지** 한 번 확인하는 방법입니다.

## 1. 서버 켜기

```bash
uv run uvicorn app.main:app --reload --port 9000
```

## 2-A. 스웨거(Swagger)로 테스트 — 추천

1. 브라우저에서 **http://127.0.0.1:9000/docs** 접속
2. `POST /internal/ai/missions/check` 클릭 → **Try it out**
3. 아래 `samples/*.json` 중 하나를 **Request body 에 복붙**
4. **Execute** → 응답 확인

## 2-B. curl 로 테스트 (파일 그대로 전송)

```bash
curl -X POST http://127.0.0.1:9000/internal/ai/missions/check \
  -H "Content-Type: application/json" \
  -d @samples/scene_002_receive_seed.json
```

## 3. 고정 요청 샘플 & 기대 응답

| 파일 | 장면 | 기대 응답 |
|---|---|---|
| `scene_000_skip_book.json` | 한 손으로 책장 넘기기(좌우 쓸기, 방향 무관) | `success: true`, `reasonCode: "MISSION_SUCCESS"` |
| `scene_001_protect_swallow.json` | 두 손 모으기 | `success: true`, `reasonCode: "MISSION_SUCCESS"` |
| `scene_002_receive_seed.json` | 두 손 모아 어깨 위로 | `success: true`, `reasonCode: "MISSION_SUCCESS"` |
| `scene_003_open_gourd.json` | 박 썰기(양손 같은 방향 좌우) | `success: true`, `reasonCode: "MISSION_SUCCESS"` |

응답은 항상 **4개 필드만** 옵니다:

```json
{ "success": true, "score": 0.8, "reasonCode": "MISSION_SUCCESS", "errorCode": null }
```

> `score` 숫자는 조금 달라도 정상. `success` 와 `reasonCode` 가 위와 같으면 통신 OK.
> 응답에 `message / nextAction / nextSceneId / warningCode` 는 없습니다(백엔드가 생성).

## 4. 에러 케이스 샘플 & 기대 응답

백엔드가 errorCode 분기/메시지 매핑을 검증할 때 쓰는 고정 샘플입니다.
모든 에러 응답은 `success: false`, `score: 0.0`, `reasonCode: null` 이고 `errorCode` 만 달라집니다.

| 파일 | 상황 | 기대 errorCode |
|---|---|---|
| `error_invalid_pose_data.json` | poseFrames 가 비어 있음 | `INVALID_POSE_DATA` |
| `error_hand_not_visible.json` | 어깨는 보이나 손목 visibility 미달 | `HAND_NOT_VISIBLE` |
| `error_user_not_detected.json` | 주요 관절(어깨)이 거의 감지 안 됨 | `USER_NOT_DETECTED` |
| `error_unknown_mission_type.json` | 지원하지 않는 missionType | `UNKNOWN_MISSION_TYPE` |

예시 응답:
```json
{ "success": false, "score": 0.0, "reasonCode": null, "errorCode": "HAND_NOT_VISIBLE" }
```

```bash
curl -X POST http://127.0.0.1:9000/internal/ai/missions/check \
  -H "Content-Type: application/json" \
  -d @samples/error_hand_not_visible.json
```

> 참고: `INVALID_POSE_DATA` / `UNKNOWN_MISSION_TYPE` 는 보통 백엔드가 AI 호출 전에 1차로 걸러내는 케이스이며,
> AI 서버 단독으로도 동일하게 방어합니다. `MISSION_MISMATCH`(scene-mission 불일치)와 `AI_SERVER_ERROR` 는
> 백엔드 영역이라 AI 서버는 반환하지 않습니다.

## 5. 동작 실패(reasonCode) 샘플 & 기대 응답

동작은 인식했지만 기준에 못 미친 경우입니다. (예외가 아니라 **정상 게임플레이 실패**)
모든 실패 응답은 `success: false`, `errorCode: null` 이고 `reasonCode` 만 달라집니다.
백엔드가 reasonCode → 사용자 메시지 매핑을 검증할 때 사용합니다.

| 파일 | missionType | 기대 reasonCode |
|---|---|---|
| `fail_skip_book_book_not_turned.json` | skip_book | `BOOK_NOT_TURNED` |
| `fail_receive_seed_hand_not_raised.json` | receive_seed | `HAND_NOT_RAISED` |
| `fail_receive_seed_hands_not_together.json` | receive_seed | `HANDS_NOT_TOGETHER` |
| `fail_protect_swallow_hands_too_far.json` | protect_swallow | `HANDS_TOO_FAR` |
| `fail_protect_swallow_hands_not_centered.json` | protect_swallow | `HANDS_NOT_CENTERED` |
| `fail_open_gourd_hand_position_too_high.json` | open_gourd | `HAND_POSITION_TOO_HIGH` |
| `fail_open_gourd_movement_too_small.json` | open_gourd | `MOVEMENT_TOO_SMALL` |
| `fail_open_gourd_sawing_motion_too_small.json` | open_gourd | `SAWING_MOTION_TOO_SMALL` |

예시 응답:
```json
{ "success": false, "score": 0.4, "reasonCode": "HANDS_NOT_TOGETHER", "errorCode": null }
```

> 백엔드 메시지 매핑 참고:
> - `BOOK_NOT_TURNED` → "손으로 책장을 넘기듯이 옆으로 크게 움직여주세요."
> - `MOVEMENT_TOO_SMALL` → "손을 조금 더 크게 움직여주세요."
> - `HAND_NOT_RAISED` → "두 손을 어깨보다 높게 들어주세요."
> - `HANDS_NOT_TOGETHER` → "두 손을 모아서 씨앗을 받아주세요."
> - `HANDS_TOO_FAR` → "두 손을 조금 더 가까이 모아주세요."
> - `HANDS_NOT_CENTERED` → "두 손을 몸 가운데로 모아주세요."
> - `HAND_POSITION_TOO_HIGH` → "손을 조금 더 아래로 내려서 움직여주세요."
> - `SAWING_MOTION_TOO_SMALL` → "톱질하듯이 양손을 번갈아 움직여주세요."
