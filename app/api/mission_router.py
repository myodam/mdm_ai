"""동작 판정 API 라우터 (app/api/mission_router.py).

이 파일은 "어떤 URL 로 요청이 오면 어떤 함수를 실행할지"를 정의하는 곳(라우팅)입니다.
실제 판정 로직은 여기 두지 않고 mission_service 로 위임한다 → 라우터는 "받고 넘기기"만 담당.

엔드포인트: POST /internal/ai/missions/check  (백엔드 내부 호출 전용, Unity 직접 호출 X)
응답      : success / score / reasonCode / errorCode 4개 필드만
"""

from fastapi import APIRouter

from app.schemas.mission_schema import MissionCheckRequest, MissionCheckResponse
from app.services import mission_service

# APIRouter = 엔드포인트 묶음. prefix 로 공통 경로 접두사를 지정한다.
#   prefix="/internal/ai" + 아래 @router.post("/missions/check")
#   → 최종 경로: POST /internal/ai/missions/check
# tags=["missions"] 는 /docs(Swagger UI)에서 엔드포인트를 묶는 라벨.
router = APIRouter(prefix="/internal/ai", tags=["missions"])


@router.post("/missions/check", response_model=MissionCheckResponse)
def check_mission(request: MissionCheckRequest) -> MissionCheckResponse:
    """백엔드가 호출하는 동작 판정 엔드포인트.

    [ request: MissionCheckRequest 의 동작 — FastAPI 의 핵심 ]
    인자 타입을 Pydantic 모델로 선언하면 FastAPI 가 자동으로:
      1) HTTP body 의 JSON 을 읽고
      2) MissionCheckRequest 규칙대로 검증(필수 필드/타입/camelCase alias)하고
      3) 통과한 데이터를 파싱해 request 객체로 넣어준다.
    → 구조가 잘못된 요청은 이 함수가 실행되기 전에 FastAPI 가 자동으로 422 로 막는다.
      그래서 service/detector 는 "구조는 이미 올바른 데이터"라고 가정하고 룰 판정에만 집중한다.

    [ response_model=MissionCheckResponse 의 의미 ]
    응답을 이 모델 기준으로 직렬화한다. 모델에 없는 필드(message/nextAction/
    nextSceneId/warningCode)는 애초에 응답으로 나갈 수 없다 → "AI 는 4개 필드만 반환"
    규칙이 코드 구조로 강제된다. 또한 alias 덕분에 출력 JSON 은 camelCase 로 나간다.

    실제 판정은 mission_service.check_mission 에 위임한다.
    """
    return mission_service.check_mission(request)
