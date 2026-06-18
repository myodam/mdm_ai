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
| `scene_000_skip_book.json` | 오른손 책 넘기기 | `success: true`, `reasonCode: "MISSION_SUCCESS"` |
| `scene_001_protect_swallow.json` | 두 손 모으기 | `success: true`, `reasonCode: "MISSION_SUCCESS"` |
| `scene_002_receive_seed.json` | 한 손 들기 | `success: true`, `reasonCode: "MISSION_SUCCESS"` |
| `scene_003_open_gourd.json` | 양팔 벌리기 | `success: true`, `reasonCode: "MISSION_SUCCESS"` |

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
