# FastAPI 서버 구조 가이드 (fastapi_guide.md)

몸으로 넘기는 전래동화 - AI 서버가 **FastAPI 로 어떻게 동작하는지**를 코드 기준으로 설명하는 문서입니다.
FastAPI 를 처음 보는 사람도 이 저장소의 흐름을 따라갈 수 있도록 작성했습니다.

---

## 1. FastAPI 란?

FastAPI 는 Python 으로 HTTP API 를 만드는 웹 프레임워크입니다. 이 프로젝트에서 쓰는 핵심 특징은 3가지입니다.

1. **타입 힌트 기반 자동 검증** — 함수 인자를 Pydantic 모델로 선언하면, 들어온 JSON 을 자동으로 검증하고 파싱해 줍니다. 잘못된 요청은 FastAPI 가 422 로 막아줍니다.
2. **ASGI 비동기 서버** — `uvicorn` 이라는 ASGI 서버 위에서 돌아갑니다. (`uv run uvicorn app.main:app`)
3. **자동 문서화** — 코드에 선언한 schema 를 기반으로 `/docs`(Swagger UI) 를 자동 생성합니다.

이 저장소는 "이미 추출된 poseFrames 를 받아 룰 기반으로 판정"만 하므로, DB·인증·비동기 I/O 없이 **요청 검증 → 계산 → 응답**의 단순한 동기 구조입니다.

---

## 2. 한 번의 요청이 거치는 전체 경로

`POST /internal/ai/missions/check` 요청 하나가 처리되는 순서입니다.

```text
[Backend가 보낸 JSON]
      │
      ▼
1. uvicorn (ASGI 서버)            ── 네트워크에서 HTTP 요청 수신
      │
      ▼
2. app/main.py : FastAPI(app)     ── CORS 미들웨어 통과, 라우터로 분배
      │
      ▼
3. app/api/mission_router.py      ── 경로 매칭: POST /internal/ai/missions/check
      │                              요청 JSON → MissionCheckRequest 로 검증/파싱
      │                              (여기서 검증 실패하면 자동 422 응답)
      ▼
4. app/services/mission_service.py ── 빈 poseFrames 검사 → INVALID_POSE_DATA
      │                              storyId+sceneId+missionType 방어 검증 → MISSION_MISMATCH
      │                              missionType 으로 detector 선택
      ▼
5. app/detectors/*_detector.py    ── 좌표 기반 룰 판정 (utils 사용)
      │                              MissionCheckResponse(success/score/reasonCode/errorCode) 생성
      ▼
6. FastAPI 응답 직렬화             ── MissionCheckResponse → camelCase JSON
      │                              (response_model 기준 4개 필드만)
      ▼
[Backend로 돌아가는 JSON]
```

핵심: **라우터는 "받고 넘기기"만, 판단 흐름은 service, 실제 계산은 detector**. 책임을 계층으로 분리해 둔 구조입니다.

---

## 3. 진입점 — app/main.py

```python
app = FastAPI(title=..., version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)  # (A)
app.include_router(mission_router)                            # (B)

@app.get("/health")                                           # (C)
def health_check() -> dict:
    return {"status": "ok", "service": "ai-server"}
```

- **(A) CORS 미들웨어**: 모든 HTTP 요청이 라우터로 가기 전에 통과하는 "공통 전처리" 지점. 해커톤 MVP라 모든 origin 을 허용. 미들웨어는 요청·응답을 감싸는 바깥 레이어라고 보면 됩니다.
- **(B) `include_router`**: 미션 관련 엔드포인트를 모아둔 `mission_router` 를 앱에 등록. 라우터를 파일로 분리하면 `main.py` 가 비대해지지 않습니다.
- **(C) `@app.get("/health")`**: 데코레이터로 "GET /health 요청이 오면 이 함수를 실행"을 선언. 함수 반환값(dict)을 FastAPI 가 자동으로 JSON 으로 바꿔 응답합니다.

`app.main:app` 이라는 uvicorn 인자의 의미: `app/main.py` 파일 안의 `app` 객체를 실행하라는 뜻입니다.

---

## 4. 라우터 — app/api/mission_router.py

```python
router = APIRouter(prefix="/internal/ai", tags=["missions"])

@router.post("/missions/check", response_model=MissionCheckResponse)
def check_mission(request: MissionCheckRequest) -> MissionCheckResponse:
    return mission_service.check_mission(request)
```

- **`APIRouter(prefix=...)`**: 이 라우터의 모든 경로 앞에 `/internal/ai` 가 붙습니다. 그래서 최종 경로는 `/internal/ai` + `/missions/check` = `POST /internal/ai/missions/check`.
- **`request: MissionCheckRequest`** (가장 중요): 인자 타입을 Pydantic 모델로 선언하면 FastAPI 가
  1. HTTP body 의 JSON 을 읽고
  2. `MissionCheckRequest` 규칙대로 검증하고 (필수 필드, 타입, camelCase alias)
  3. 통과하면 파싱된 객체를 `request` 로 넣어줍니다.
  - 검증 실패 시 우리 코드는 실행되지도 않고 FastAPI 가 **자동 422** 를 돌려줍니다. (그래서 service/detector 는 "구조는 이미 올바른 데이터"라고 가정하고 룰 판정만 함)
- **`response_model=MissionCheckResponse`**: 응답을 이 모델 기준으로 직렬화. 모델에 없는 필드(`message`, `nextAction` 등)는 **애초에 나갈 수 없습니다.** "AI는 4개 필드만 반환" 규칙이 코드 구조로 강제됩니다.
- **`tags=["missions"]`**: `/docs` 에서 엔드포인트를 그룹으로 묶어주는 라벨.

---

## 5. 데이터 검증 — app/schemas/

FastAPI 의 검증은 전부 Pydantic 모델이 담당합니다.

### 5.1 요청/응답 (mission_schema.py)

```python
class MissionCheckRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    story_id: str = Field(alias="storyId")
    ...
    pose_frames: list[PoseFrame] = Field(alias="poseFrames")
```

- **alias**: 바깥 JSON 은 `storyId`(camelCase), Python 내부 변수는 `story_id`(snake_case)로 받습니다. Unity/Backend 규약(camelCase)과 Python 관례(snake_case)를 둘 다 만족시키는 장치.
- **`populate_by_name=True`**: 코드에서 객체를 만들 때 `story_id=`(필드명)로도, `storyId`(alias)로도 만들 수 있게 허용.
- **타입(`str`, `list[PoseFrame]`)**: 값이 없거나 타입이 다르면 검증 에러. `capture_duration_sec` 처럼 `| None = None` 인 필드는 선택값.

### 5.2 응답이 camelCase 로 나가는 이유

```python
class MissionCheckResponse(BaseModel):
    success: bool
    score: float
    reason_code: str | None = Field(default=None, alias="reasonCode")
    error_code: str | None = Field(default=None, alias="errorCode")
```

라우터에 `response_model` 을 지정하면 FastAPI 는 기본적으로 **alias 로 직렬화**(`response_model_by_alias=True`)합니다. 그래서 내부에서는 `reason_code` 로 다루지만, 실제 응답 JSON 은 `reasonCode` 로 나갑니다.

### 5.3 좌표 (pose_schema.py)

```python
class Landmark(BaseModel):
    x: float
    y: float
    visibility: float | None = None

class PoseLandmarks(BaseModel):
    model_config = ConfigDict(extra="ignore")   # 7개 외 다른 관절이 와도 무시
    leftShoulder: Landmark | None = None
    ...

class PoseFrame(BaseModel):
    timestamp: float
    landmarks: PoseLandmarks
```

- 중첩 모델: `MissionCheckRequest.pose_frames` → `list[PoseFrame]` → `PoseFrame.landmarks` → `PoseLandmarks` → 각 `Landmark`. JSON 의 중첩 구조를 그대로 타입으로 표현하면, FastAPI 가 깊은 곳까지 한 번에 검증합니다.
- `extra="ignore"`: MediaPipe 는 관절이 33개지만 우리는 7개만 쓰므로, 나머지가 들어와도 에러 없이 무시.

---

## 6. 판단 계층 — app/services/mission_service.py

라우터가 호출하는 곳. "어떤 detector 를 돌릴지" 와 "AI 레벨 예외" 를 담당합니다.

```python
DETECTOR_REGISTRY = {
    "protect_swallow": protect_swallow_detector.detect,
    "receive_seed":    receive_seed_detector.detect,
    "open_gourd":      open_gourd_detector.detect,
}

def check_mission(request):
    if not request.pose_frames:                       # 1) 빈 입력
        return MissionCheckResponse(..., error_code="INVALID_POSE_DATA")
    if not _is_valid_combination(...):                # 2) 방어적 조합 검증
        return MissionCheckResponse(..., error_code="MISSION_MISMATCH")
    detect = DETECTOR_REGISTRY.get(request.mission_type)
    if detect is None:                                # 3) 미등록 미션
        return MissionCheckResponse(..., error_code="MISSION_MISMATCH")
    return detect(request.pose_frames)                # 4) detector 실행
```

- **레지스트리 패턴**: `if/elif` 대신 dict 로 missionType→함수 매핑. 동화/미션이 늘어나도 dict 에 한 줄 추가하면 됩니다.
- 여기서 처리하는 건 "어느 detector 도 공통으로 막아야 하는 것"(빈 데이터, 조합 불일치)뿐. 좌표 기반 세부 판정은 detector 로 위임.

---

## 7. 계산 계층 — app/detectors/ + app/utils/

- **detector**: 장면별 룰을 구현하고 `MissionCheckResponse` 를 반환. 예) receive_seed 는 "손목 y < 어깨 y - margin" 인 bestFrame 을 찾아 성공/실패와 reasonCode 를 결정.
- **utils**: detector 들이 공통으로 쓰는 순수 계산 함수.
  - `geometry.py`: 거리/각도/이동량
  - `pose_utils.py`: landmark 추출, visibility 확인, bestFrame 탐색
  - `score_utils.py`: 점수 0~1 보정, 0.7 기준 성공 판정
- **detector 는 HTTP/FastAPI 를 전혀 모릅니다.** 입력은 `list[PoseFrame]`, 출력은 응답 모델. 그래서 서버를 안 켜고도 `pytest` 로 함수 단위 테스트가 가능합니다(`tests/test_*_detector` 류).

---

## 8. 서버 실행과 자동 문서

```bash
uv run uvicorn app.main:app --reload --port 8001
```

- `uvicorn`: ASGI 서버 (FastAPI 앱을 실제로 구동)
- `app.main:app`: 구동할 객체 위치
- `--reload`: 코드 저장 시 자동 재시작 (개발용, 운영에선 끔)
- `--port 8001`: 포트 (`.env` 의 `APP_PORT` 와 동일)

켠 뒤:
- `http://127.0.0.1:8001/health` — 헬스체크
- `http://127.0.0.1:8001/docs` — Swagger UI. schema 가 자동 반영되어 브라우저에서 바로 요청 테스트 가능
- `http://127.0.0.1:8001/openapi.json` — 기계가 읽는 API 스펙

---

## 9. 새 미션(detector)을 추가하려면

확장 시 손대는 곳은 정해져 있습니다.

1. `app/core/constants.py` — 새 `MISSION_*`, `REASON_*`, `MISSION_BY_SCENE` 매핑 추가
2. `app/detectors/새미션_detector.py` — `detect(pose_frames) -> MissionCheckResponse` 구현
3. `app/services/mission_service.py` — `DETECTOR_REGISTRY` 에 한 줄 등록
4. `tests/test_새미션.py` — 성공/실패/예외 + bestFrame 테스트 작성

`main.py`, `mission_router.py`, schema 는 보통 건드릴 필요가 없습니다. — 계층 분리의 이점입니다.

---

## 10. 요약

```text
main.py        → 앱 생성 / 미들웨어 / 라우터 등록 / health
mission_router → 경로 매칭 + 요청 자동 검증 + 응답 4필드 강제
schemas        → Pydantic 으로 검증·파싱·camel↔snake·직렬화
mission_service→ 빈 데이터/조합 검증 + detector 분기
detectors+utils→ 좌표 룰 계산 (FastAPI 비의존, 단독 테스트 가능)
uvicorn        → 이 모든 걸 구동하는 ASGI 서버
```

FastAPI 는 "타입으로 선언하면 검증·파싱·직렬화·문서를 알아서 해준다"가 핵심이고,
이 저장소는 그 위에 **라우터→서비스→detector** 3계층으로 동작 판정 로직을 얹은 구조입니다.
