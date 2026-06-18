"""FastAPI 진입점 (app/main.py).

이 파일은 "FastAPI 앱 객체를 만들고 설정하는 곳"입니다.
서버를 켤 때 쓰는 `uv run uvicorn app.main:app` 의 `app.main:app` 은
"app/main.py 안의 app 변수를 구동하라"는 뜻이며, 아래 `app = FastAPI(...)` 가 그 대상입니다.

[ 이 서버의 책임 범위 ]
- 한다  : 백엔드가 전달한 poseFrames 를 받아 동작 판정 → success/score/reasonCode/errorCode 반환
- 안 한다: message / nextAction / nextSceneId / warningCode 생성, DB 저장, Unity 직접 통신
          (위 항목은 모두 백엔드 담당)

[ 요청이 처리되는 큰 흐름 ]
  uvicorn → main.py(app) → mission_router → mission_service → detector → 응답 직렬화

[ 로깅 ]
  - 통신 로그(미들웨어): method/path/status/duration + request_id
  - 판정 요약(service) / 계산 중간값(detector, DEBUG)
  - LOG_LEVEL(.env) 로 레벨 제어, 기본 INFO
  - access 로그 중복을 피하려면 `--no-access-log` 로 실행
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.mission_router import router as mission_router
from app.core.logging_config import get_request_id, set_request_id, setup_logging

# 앱 구동 시 로깅을 가장 먼저 설정한다.
setup_logging()
logger = logging.getLogger("ai.api")

app = FastAPI(
    title="몸으로 넘기는 전래동화 - AI Server",
    description="MediaPipe poseFrames 기반 동작 판정 전용 FastAPI 서버",
    version="0.1.0",
)

# [미들웨어] 모든 요청이 라우터로 가기 전, 모든 응답이 나가기 직전에 거치는 공통 레이어.
# CORS = 브라우저가 다른 출처(origin)에서 이 API 를 호출할 수 있게 허용하는 설정.
# 해커톤 MVP 라 백엔드 내부 호출 전용이므로 모든 출처를 허용한다(운영 시엔 제한 권장).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """요청마다 request_id 를 세팅하고 통신 로그(상태/소요시간)를 남긴다.

    - X-Request-ID 헤더가 있으면 재사용, 없으면 자동 생성
    - 응답에도 X-Request-ID 를 되돌려줘 백엔드가 로그를 대조할 수 있게 함
    - /health 는 INFO 통신 로그에서 제외(폴링 노이즈 방지)
    """
    request_id = set_request_id(request.headers.get("X-Request-ID"))
    is_health = request.url.path == "/health"
    start = time.perf_counter()

    if not is_health:
        logger.debug("→ %s %s", request.method, request.url.path)

    response = await call_next(request)

    if not is_health:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "← %s %s %s (%.0fms)",
            response.status_code,
            request.method,
            request.url.path,
            duration_ms,
        )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def on_validation_error(request: Request, exc: RequestValidationError):
    """요청 형식 오류(422). 어떤 필드가 왜 틀렸는지 ERROR 로 남기고 기본 응답을 반환."""
    logger.error("422 validation on %s: %s", request.url.path, exc.errors())
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def on_unhandled_error(request: Request, exc: Exception):
    """예상치 못한 내부 오류(500). 스택트레이스를 남기고 깔끔한 본문을 반환."""
    logger.exception("500 unhandled on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"},
        headers={"X-Request-ID": get_request_id()},
    )


app.include_router(mission_router)


@app.get("/health")
def health_check() -> dict:
    """헬스체크 엔드포인트 (GET /health).

    @app.get("/health") 데코레이터 = "GET /health 요청이 오면 이 함수를 실행하라".
    함수가 반환한 dict 를 FastAPI 가 자동으로 JSON 응답으로 변환한다.
    백엔드/배포 환경에서 "서버가 살아있는지" 확인하는 용도.
    """
    return {"status": "ok", "service": "ai-server"}
