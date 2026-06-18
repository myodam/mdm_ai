# MDM_AI — 몸으로 넘기는 전래동화 (AI 서버)

묘달숲 / 「흥부와 놀부」 MVP의 **AI 서버(FastAPI)** 파트입니다.
MediaPipe 로 추출된 poseFrames 를 입력받아 **장면별 동작 성공 여부만 판정**합니다.

```
Unity → Backend → AI Server(FastAPI) → Backend → Unity
                    ▲ 이 저장소가 담당
```

---

## 1. AI 서버 역할

- 백엔드가 내부적으로 호출하는 동작 판정 전용 서버
- 입력: `missionType / poseFrames` (storyId / sceneId 는 받지 않음 — scene 매핑/검증은 백엔드 책임)
- 출력: **`success / score / reasonCode / errorCode` 4개 필드만**
- `missionType` 에 맞는 detector 를 선택해 좌표 기반 룰 판정 수행

### AI 서버가 하지 않는 일
- 사용자 `message` 생성
- `nextAction` / `nextSceneId` / `warningCode` 생성
- DB 저장 / 진행 상태 관리
- Unity 직접 통신, WebSocket, MediaPipe 실시간 추적, 딥러닝 학습

> 위 항목은 모두 백엔드/Unity 담당입니다. `AI_SERVER_ERROR` 도 AI 서버가 직접 반환하지 않고
> 백엔드가 호출 실패를 감지했을 때 사용합니다.

---

## 2. 실행 방법

```bash
# 의존성 설치 (uv)
uv sync

# 개발 서버 실행
uv run uvicorn app.main:app --reload --port 9000

# 헬스체크
curl http://127.0.0.1:9000/health
# → {"status":"ok","service":"ai-server"}
```

환경변수는 `.env` 에서 관리합니다(임계값 등). 값이 없으면 코드 기본값을 사용합니다.

---

## 3. API 목록

| Method | Path | 설명 |
|---|---|---|
| GET | `/health` | 헬스체크 |
| POST | `/internal/ai/missions/check` | 동작 판정 (백엔드 내부 호출용) |

상세 스펙은 [docs/ai_api.md](docs/ai_api.md), FastAPI 서버가 어떻게 동작하는지는 [docs/fastapi_guide.md](docs/fastapi_guide.md) 참고.

---

## 4. 요청 / 응답 예시

요청 (Backend → AI):
```json
{
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
        "rightWrist": { "x": 0.64, "y": 0.24, "visibility": 0.92 }
      }
    }
  ]
}
```

응답 (AI → Backend):
```json
{
  "success": true,
  "score": 0.8,
  "reasonCode": "MISSION_SUCCESS",
  "errorCode": null
}
```

- 외부 JSON 은 camelCase, Python 내부는 snake_case (Pydantic alias 매핑)
- 응답에는 절대 `message / nextAction / nextSceneId / warningCode` 가 포함되지 않습니다.

---

## 5. detector 목록

> AI 서버는 `missionType` 으로만 detector 를 선택합니다. 아래 장면(참고) 칸은 백엔드 기준 매핑이며 AI 요청에는 포함되지 않습니다.

| missionType | 장면(참고) | 동작 | 판정 방식 | 실패 reasonCode |
|---|---|---|---|---|
| `skip_book` | scene_000 | 왼손으로 책장 오른쪽으로 넘기기 | 왼손목 왼→오른쪽 순이동·방향성·곡선 (동작형) | BOOK_NOT_TURNED, MOVEMENT_TOO_SMALL |
| `protect_swallow` | scene_001 | 두 손 모으기 | 양손목 거리 + 몸 중앙 위치 (bestFrame) | HANDS_TOO_FAR, HANDS_NOT_CENTERED |
| `receive_seed` | scene_002 | 두 손 모아 어깨 위로 | 양손 어깨 위 + 손 사이 거리 (bestFrame) | HAND_NOT_RAISED, HANDS_NOT_TOGETHER |
| `open_gourd` | scene_003 | 박 썰기(양손 같은 방향 좌우 이동) | 어깨 아래 + 양손 이동/중심이동/같은방향 (동작형) | HAND_POSITION_TOO_HIGH, MOVEMENT_TOO_SMALL, SAWING_MOTION_TOO_SMALL |

공통 성공 기준: `score >= 0.7` → `reasonCode = MISSION_SUCCESS`.

---

## 6. 폴더 구조

```
MDM_AI/
├── app/
│   ├── main.py                 # FastAPI 진입점, /health, CORS, 라우터 등록
│   ├── api/mission_router.py   # POST /internal/ai/missions/check
│   ├── schemas/                # pose_schema, mission_schema (camel↔snake alias)
│   ├── services/mission_service.py  # missionType → detector 분기 (없으면 UNKNOWN_MISSION_TYPE)
│   ├── detectors/              # skip_book / protect_swallow / receive_seed / open_gourd
│   ├── utils/                  # geometry, pose_utils, score_utils
│   ├── core/                   # config(threshold), constants(미션/reason/error 코드)
│   └── exceptions/             # mission_exception
├── tests/                      # detector별 + schema/utils + 통합 테스트
└── docs/                       # 기획 문서, ai_api.md, test_report.md
```

---

## 7. 테스트 실행 방법

**코드 단위 테스트 (서버 없이)**
```bash
uv run pytest            # 전체
uv run pytest -v         # 상세
uv run pytest tests/test_receive_seed.py -v   # 개별 detector
```

**서버 통신 테스트 (스웨거 / 고정 JSON)**
```bash
# 서버 켜기
uv run uvicorn app.main:app --reload --port 9000
# 브라우저에서 http://127.0.0.1:9000/docs 접속 후 samples/*.json 복붙
# 또는 curl 로 파일 전송:
curl -X POST http://127.0.0.1:9000/internal/ai/missions/check \
  -H "Content-Type: application/json" -d @samples/scene_002_receive_seed.json
```

- 통신 테스트 빠른 시작 + 고정 샘플: [samples/README.md](samples/README.md)
- 자동 테스트 결과 리포트: [docs/test_report.md](docs/test_report.md)
