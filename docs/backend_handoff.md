# 백엔드 전달용 — AI 서버 변경 핸드오프

AI 서버(동작 판정) 쪽 기준이 바뀌어서 **백엔드가 반영해야 할 것**을 정리한 문서입니다.
엔드포인트/응답 구조 자체는 그대로지만, **missionType 추가 / 신규 reasonCode / 일부 코드 변경**이 있습니다.

---

## 0. 한눈에 (must-do 체크리스트)

- [ ] `scene_000 → skip_book` 매핑 추가 (신규 미션)
- [ ] 신규 **reasonCode 4개** 메시지 매핑 추가
  - `BOOK_NOT_TURNED`, `HANDS_NOT_TOGETHER`, `HAND_POSITION_TOO_HIGH`, `SAWING_MOTION_TOO_SMALL`
- [ ] `MOVEMENT_TOO_SMALL` 메시지 매핑 추가(이제 skip_book/open_gourd 둘 다 사용)
- [ ] `ARMS_NOT_WIDE` 더 이상 AI가 반환 안 함 (매핑 제거 또는 방치)
- [ ] AI는 더 이상 `MISSION_MISMATCH`를 반환하지 않음. AI는 지원 안 하는 missionType에 `UNKNOWN_MISSION_TYPE` 반환 → 메시지 매핑 추가
- [ ] 미션별 성공/실패 사용자 메시지 문구를 **바뀐 동작 기준**으로 업데이트 (두 손 받기 / 박 썰기 / 책 넘기기)
- [ ] (선택) 요청에 `X-Request-ID` 헤더 전달 → 로그 대조 가능
- [ ] AI 서버 주소: `https://mwm.bellrajin.com` (엔드포인트 `/internal/ai/missions/check`)

---

## 1. 요청 / 응답 계약 (변경 없음, 확인용)

**AI 호출:** `POST /internal/ai/missions/check`

요청 (AI가 실제로 쓰는 필드는 `missionType` + `poseFrames` 뿐):
```json
{ "missionType": "skip_book", "captureDurationSec": 5, "sampleFps": 5, "poseFrames": [ ... ] }
```
- AI 서버는 **storyId / sceneId 를 받지 않습니다.** (보내도 무시 — `scene+mission` 매핑/검증은 백엔드 책임)

응답 (항상 이 4개 필드만):
```json
{ "success": true, "score": 0.88, "reasonCode": "MISSION_SUCCESS", "errorCode": null }
```
- AI는 `message / nextAction / nextSceneId / warningCode` 를 **생성하지 않음** → 백엔드가 생성.

---

## 2. 미션 매핑 (백엔드가 관리)

| sceneId | missionType | 동작(현재 기준) |
|---|---|---|
| scene_000 | `skip_book` | 한 손으로 책장 넘기듯 **좌우로 쓸기** (방향/손 무관) |
| scene_001 | `protect_swallow` | 두 손 모으기 |
| scene_002 | `receive_seed` | **두 손 모아 어깨 위로** (※ 한 손 아님) |
| scene_003 | `open_gourd` | **박 썰기** — 양손이 어깨 아래에서 같은 방향으로 좌우 이동 (※ 양팔 벌리기 아님) |

> `skip_book` 이 신규입니다. `scene_000 → skip_book` 매핑을 추가하세요.
>
> **skip_book 역할 분리:** 책장이 곡선(포물선/반원)으로 넘어가는 연출은 **Unity** 담당이고,
> **AI** 는 "손을 옆으로 충분히 쓸어 넘겼는지"만 넉넉하게 판정합니다(실제 곡선 모양은 검사 안 함).
> 그래서 손 동작만 인정되면 성공 처리되고, 시각적 책 넘김은 Unity가 보여주면 됩니다.

---

## 3. reasonCode 전체 (AI가 반환) → 권장 사용자 메시지

`reasonCode` = 동작은 인식했으나 성공/부족. (정상 게임플레이, 예외 아님)

| reasonCode | missionType | success | 권장 message |
|---|---|---|---|
| `MISSION_SUCCESS` | 전체 | true | (장면별 성공 문구) |
| `BOOK_NOT_TURNED` 🆕 | skip_book | false | 손으로 책장을 넘기듯이 옆으로 크게 움직여주세요. |
| `MOVEMENT_TOO_SMALL` ♻️ | skip_book / open_gourd | false | 손을 조금 더 크게 움직여주세요. |
| `HANDS_TOO_FAR` | protect_swallow | false | 두 손을 조금 더 가까이 모아주세요. |
| `HANDS_NOT_CENTERED` | protect_swallow | false | 두 손을 몸 가운데로 모아주세요. |
| `HAND_NOT_RAISED` ✏️ | receive_seed | false | 두 손을 어깨보다 높게 들어주세요. |
| `HANDS_NOT_TOGETHER` 🆕 | receive_seed | false | 두 손을 모아서 씨앗을 받아주세요. |
| `HAND_POSITION_TOO_HIGH` 🆕 | open_gourd | false | 손을 조금 더 아래로 내려서 움직여주세요. |
| `SAWING_MOTION_TOO_SMALL` 🆕 | open_gourd | false | 톱질하듯이 양손을 번갈아 움직여주세요. |

성공(`MISSION_SUCCESS`) 장면별 문구 예:
- skip_book → "좋아요! 책장이 넘어갔어요."
- protect_swallow → "좋아요! 제비를 조심스럽게 보호했어요."
- receive_seed → "잘했어요! 박씨를 받았어요."
- open_gourd → "힘차게 박을 탔어요! 박이 열렸어요."

🆕 신규 / ♻️ 사용처 확대 / ✏️ 문구 수정 필요
**삭제:** `ARMS_NOT_WIDE` — open_gourd가 톱질로 바뀌어 AI가 더 이상 반환하지 않음.
(참고) `LOW_SCORE` 는 예약만 되어 있고 현재 AI가 반환하지 않음.

---

## 4. errorCode 전체 → 권장 메시지

`errorCode` = 판정 불가/시스템 문제.

| errorCode | 누가 반환 | 권장 message |
|---|---|---|
| `USER_NOT_DETECTED` | AI | 카메라 앞에 서서 다시 시도해주세요. |
| `HAND_NOT_VISIBLE` | AI | 손이 화면 안에 보이도록 해주세요. |
| `INVALID_POSE_DATA` | AI(또는 백엔드 1차) | 동작 정보를 확인할 수 없어요. 다시 시도해주세요. |
| `UNKNOWN_MISSION_TYPE` 🆕 | AI | 현재 미션 정보를 확인할 수 없습니다. |
| `MISSION_MISMATCH` | **백엔드 전용** | 현재 장면의 미션 정보가 올바르지 않습니다. |
| `AI_SERVER_ERROR` | **백엔드 전용** | 잠시 문제가 발생했어요. 다시 시도해주세요. |
| `INTERNAL_SERVER_ERROR` | **백엔드 전용** | 잠시 문제가 발생했어요. 다시 시도해주세요. |

변경점:
- **AI는 이제 `MISSION_MISMATCH`를 반환하지 않습니다.** scene-mission 불일치 검증은 백엔드가 호출 전에 처리하세요(`MISSION_MISMATCH`는 백엔드가 직접 생성).
- AI가 모르는 missionType을 받으면 `UNKNOWN_MISSION_TYPE`을 반환합니다 → 백엔드 메시지 매핑 추가.
- `skip_book`은 `USER_NOT_DETECTED`를 반환하지 않고, 손이 안 보이면 `HAND_NOT_VISIBLE`로 처리합니다.

---

## 5. (선택) X-Request-ID — 로그 대조

백엔드가 요청에 `X-Request-ID` 헤더를 넣으면 AI 서버가 **같은 값을 로그에 찍고 응답 헤더로도 돌려줍니다.** 양쪽 로그를 같은 id로 맞춰볼 수 있어 디버깅이 쉬워집니다. 안 보내면 AI가 자동 생성합니다.

```
요청 헤더:  X-Request-ID: <백엔드 트레이스 id>
응답 헤더:  X-Request-ID: <그대로 반환>
```

---

## 6. 호출 예시

```bash
curl -X POST https://mwm.bellrajin.com/internal/ai/missions/check \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: trace-12345" \
  -d '{ "missionType": "receive_seed", "captureDurationSec": 5, "sampleFps": 5, "poseFrames": [ ... ] }'
```

응답:
```json
{ "success": false, "score": 0.40, "reasonCode": "HANDS_NOT_TOGETHER", "errorCode": null }
```
→ 백엔드: `reasonCode=HANDS_NOT_TOGETHER` → message "두 손을 모아서 씨앗을 받아주세요." + `nextAction=RETRY`.

---

## 7. 참고
- 요청/응답 상세 스펙: `docs/ai_api.md`
- 케이스별 테스트 JSON(성공/실패/에러): `samples/` 폴더 (백엔드 메시지 매핑 검증에 그대로 사용 가능)
- AI 서버는 동작 판정만 담당. message/nextAction/nextSceneId/warningCode/DB저장은 백엔드.
