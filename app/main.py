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
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.mission_router import router as mission_router

# FastAPI() 객체 = 우리 웹 애플리케이션 본체.
# title/description/version 은 자동 생성되는 API 문서(/docs, /openapi.json)에 표시된다.
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
    allow_origins=["*"],   # 허용할 출처 목록. ["*"] = 전부 허용
    allow_credentials=True,
    allow_methods=["*"],   # 허용할 HTTP 메서드(GET/POST...)
    allow_headers=["*"],   # 허용할 요청 헤더
)

# [라우터 등록] 동작 판정 엔드포인트들은 app/api/mission_router.py 에 모아두고,
# include_router 로 앱에 붙인다. main.py 가 비대해지지 않도록 경로 정의를 분리한 것.
app.include_router(mission_router)


@app.get("/health")
def health_check() -> dict:
    """헬스체크 엔드포인트 (GET /health).

    @app.get("/health") 데코레이터 = "GET /health 요청이 오면 이 함수를 실행하라".
    함수가 반환한 dict 를 FastAPI 가 자동으로 JSON 응답으로 변환한다.
    백엔드/배포 환경에서 "서버가 살아있는지" 확인하는 용도.
    """
    return {"status": "ok", "service": "ai-server"}
