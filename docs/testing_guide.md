# AI 서버 통신 테스트 가이드 (팀원용)

몸으로 넘기는 전래동화 - AI 서버가 **잘 켜지고, 요청을 보내면 값이 제대로 돌아오는지**
직접 확인하는 방법입니다. 순서대로 따라 하시면 됩니다.

> 전체 흐름: `Unity → Backend → AI Server(FastAPI) → Backend → Unity`
> 여기서 테스트하는 건 **AI Server** 부분입니다. (백엔드가 호출하는 API)

---

## 0. 준비물

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- (선택) `jq` — 응답 JSON 을 예쁘게 보여줌. 없어도 동작함
  - macOS: `brew install jq`

저장소를 받은 뒤 프로젝트 루트(`mdm_ai/`)에서 의존성을 설치합니다.

```bash
uv sync
```

---

## 1. 서버 켜기 (터미널 A)

```bash
uv run uvicorn app.main:app --reload --port 9000
```

아래 로그가 보이면 정상입니다.

```
INFO:     Uvicorn running on http://127.0.0.1:9000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

- 이 터미널은 **켜둔 채로** 둡니다. (끄려면 `Ctrl + C`)
- 포트(9000)는 바꿔도 되지만, 아래 테스트 스크립트 기본값과 맞추려면 **9000 권장**.

---

## 2. 테스트 방법 ① — 자동 스크립트 (가장 빠름)

**새 터미널(터미널 B)** 을 열고 프로젝트 루트에서 실행합니다.

```bash
bash scripts/test_api.sh
# 서버를 다른 포트로 켰다면: bash scripts/test_api.sh 8001
```

- 9개 케이스(성공/실패/예외)를 한 번에 호출하고, **기대값과 실제 응답을 나란히** 출력합니다.
- 맨 위 `GET /health` 에서 연결 실패가 뜨면 → 서버(터미널 A)가 안 켜졌거나 포트가 다른 것입니다.

### 정상 출력 예시 (일부)

```
▶ receive_seed 성공 (오른손 듦)
  기대: success=true, MISSION_SUCCESS
  응답: {
  "success": true,
  "score": 0.805,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

> `score` 숫자값은 조금 달라도 됩니다. **`success` 와 `reasonCode`/`errorCode` 가 "기대" 와 같으면 정상**입니다.

---

## 3. 테스트 방법 ② — Swagger UI (브라우저, 클릭만으로)

서버를 켠 상태에서 브라우저로:

```
http://127.0.0.1:9000/docs
```

1. `POST /internal/ai/missions/check` 항목을 클릭해 펼친다
2. **Try it out** 버튼 클릭
3. Request body 에 JSON 을 붙여넣는다 (아래 4번 예시 사용)
4. **Execute** 클릭 → 아래 Response 에서 결과 확인

코드/curl 없이 가장 쉽게 값 확인이 가능합니다.

---

## 4. 테스트 방법 ③ — curl 직접 호출 (한 케이스만)

```bash
curl -X POST http://127.0.0.1:9000/internal/ai/missions/check \
  -H "Content-Type: application/json" \
  -d '{
    "storyId": "heungbu_nolbu",
    "sceneId": "scene_002",
    "missionType": "receive_seed",
    "captureDurationSec": 5,
    "sampleFps": 5,
    "poseFrames": [
      {"timestamp": 0.0, "landmarks": {
        "leftShoulder": {"x": 0.42, "y": 0.36, "visibility": 0.97},
        "rightShoulder": {"x": 0.58, "y": 0.36, "visibility": 0.97},
        "leftWrist": {"x": 0.40, "y": 0.62, "visibility": 0.90},
        "rightWrist": {"x": 0.64, "y": 0.24, "visibility": 0.92}
      }}
    ]
  }'
```

기대 응답:

```json
{ "success": true, "score": 0.8, "reasonCode": "MISSION_SUCCESS", "errorCode": null }
```

---

## 5. 무엇을 확인하면 되나 (체크리스트)

- [ ] `GET /health` → `{"status":"ok","service":"ai-server"}` 가 온다 (= 서버 통신 OK)
- [ ] 성공 케이스 → `success: true`, `reasonCode: "MISSION_SUCCESS"`
- [ ] 실패 케이스 → `success: false`, 장면별 `reasonCode` (HAND_NOT_RAISED / HANDS_TOO_FAR / ARMS_NOT_WIDE)
- [ ] 예외 케이스 → `errorCode` (INVALID_POSE_DATA / HAND_NOT_VISIBLE / MISSION_MISMATCH)
- [ ] **응답에 `message`, `nextAction`, `nextSceneId`, `warningCode` 가 없다**
      (이 4개는 AI 서버가 만들지 않음 → 백엔드가 생성)

응답은 항상 아래 **4개 필드만** 옵니다.

```text
success, score, reasonCode, errorCode
```

---

## 6. 장면별 테스트 입력 요약

| sceneId | missionType | 성공 조건(요약) | 성공 reasonCode | 실패 reasonCode |
|---|---|---|---|---|
| scene_001 | protect_swallow | 두 손이 가깝고 몸 중앙 | MISSION_SUCCESS | HANDS_TOO_FAR, HANDS_NOT_CENTERED |
| scene_002 | receive_seed | 한 손이 어깨보다 위 | MISSION_SUCCESS | HAND_NOT_RAISED |
| scene_003 | open_gourd | 양팔을 어깨폭보다 넓게 | MISSION_SUCCESS | ARMS_NOT_WIDE, (MOVEMENT_TOO_SMALL) |

좌표 기준: `x,y` 는 0~1, **y 가 작을수록 화면 위쪽** (MediaPipe 기준).

---

## 7. 자주 나오는 문제

| 증상 | 원인 / 해결 |
|---|---|
| `curl: connection refused` / health 실패 | 서버(터미널 A) 가 안 켜짐. `uv run uvicorn ...` 다시 실행 |
| 스크립트가 다 connection 실패 | 서버 포트와 스크립트 포트 불일치 → `bash scripts/test_api.sh <포트>` |
| `422 Unprocessable Entity` | 요청 JSON 형식 오류(필수 필드 누락 등). FastAPI 가 자동으로 막은 것 |
| `uv: command not found` | uv 미설치 → https://docs.astral.sh/uv/ 참고 후 설치 |

---

## 8. 참고 문서

- API 상세 스펙: [docs/ai_api.md](ai_api.md)
- FastAPI 서버 구조 설명: [docs/fastapi_guide.md](fastapi_guide.md)
- 자동 테스트(pytest) 결과: [docs/test_report.md](test_report.md)
  - 코드 단위 테스트는 `uv run pytest` 로 실행 (서버 안 켜도 됨)
