"""로깅 설정 + request_id 컨텍스트 전파.

- stdout + 파일(logs/ai.log, RotatingFileHandler) 병행 출력
- request_id 를 ContextVar 에 저장하고, logging Filter 가 모든 로그 줄에 자동 주입
  → service / detector 는 request_id 를 인자로 받지 않아도 됨
- LOG_LEVEL 환경변수로 레벨 제어(기본 INFO)
- setup_logging() 은 중복 호출/재import 시 핸들러가 중복 등록되지 않도록 가드
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 현재 요청의 request_id 를 담는 컨텍스트 (요청마다 격리됨)
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

_MAX_REQUEST_ID_LEN = 64
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")  # 개행/제어문자 (로그 인젝션 방지)

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "ai.log"

_configured = False


def set_request_id(raw: str | None) -> str:
    """헤더값(X-Request-ID)을 정제해 ContextVar 에 저장하고 최종 id 를 반환.

    - 값이 있으면 제어문자 제거 + 64자 제한 후 사용
    - 없거나 정제 후 비면 8자리 짧은 id 자동 생성
    """
    cleaned = ""
    if raw:
        cleaned = _CONTROL_CHARS.sub("", raw).strip()[:_MAX_REQUEST_ID_LEN]
    if not cleaned:
        cleaned = uuid.uuid4().hex[:8]
    _request_id_ctx.set(cleaned)
    return cleaned


def get_request_id() -> str:
    return _request_id_ctx.get()


class _RequestIdFilter(logging.Filter):
    """모든 LogRecord 에 현재 request_id 를 주입한다."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_ctx.get()
        return True


def setup_logging() -> None:
    """로깅을 1회 설정한다. (재import/reload 시 중복 핸들러 방지)"""
    global _configured
    if _configured:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    req_filter = _RequestIdFilter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(req_filter)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(req_filter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()  # 중복 등록 방지
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    _configured = True
