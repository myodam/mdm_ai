# AI 서버 테스트 리포트 (test_report.md)

몸으로 넘기는 전래동화 - 흥부와 놀부 MVP / AI Server

---

## 1. 테스트 실행 명령어

```bash
uv run pytest              # 전체
uv run pytest -v           # 상세
uv run pytest tests/test_receive_seed.py -v   # 개별
```

## 2. 테스트 환경

| 항목 | 값 |
|---|---|
| OS | macOS (darwin) |
| Python | 3.12.13 |
| 테스트 러너 | pytest 9.1.0 |
| 주요 패키지 | fastapi 0.137.1, pydantic 2.13.4, httpx 0.28.1, uvicorn 0.49.0 |
| 패키지 매니저 | uv |

## 3. 결과 요약

| 구분 | 값 |
|---|---|
| 전체 테스트 | **53** |
| 통과 | **53** |
| 실패 | **0** |
| 경고 | 1 (StarletteDeprecationWarning — TestClient/httpx, 동작 무관) |

```
======================== 53 passed, 1 warning in 0.21s =========================
```

> 변경 이력: storyId/sceneId 제거(42→41) → skip_book 추가(41→50)
> → 3개 미션 판정 기준 개편(50→52)
> → skip_book 을 "양손 중 더 큰 손 자동 선택 + 방향 비강제"로 재개편(실제 캡처 실패 대응, 52→53).

## 4. 테스트 케이스 목록 / 결과

### tests/test_schema.py (5) — 요청/응답 schema
| 케이스 | 결과 |
|---|---|
| 정상 요청 통과 + camelCase→snake_case 매핑 | PASS |
| 필수 필드(missionType) 누락 → ValidationError | PASS |
| poseFrames 누락 → ValidationError | PASS |
| 응답 camelCase 직렬화 + 금지필드 미포함 | PASS |
| 예외(errorCode) 응답 형태 | PASS |

### tests/test_utils.py (9) — 공통 유틸
| 케이스 | 결과 |
|---|---|
| calculate_distance | PASS |
| calculate_total_movement | PASS |
| is_visible 임계값 / None 처리 | PASS |
| has_required_landmarks | PASS |
| get_landmark | PASS |
| find_best_frame | PASS |
| find_best_frame 빈 입력 | PASS |
| clamp_score | PASS |
| is_success | PASS |

### tests/test_skip_book.py (8) — scene_000 (한 손 자동 선택, 방향 비강제)
| 케이스 | 기대 | 결과 |
|---|---|---|
| 왼손 좌우 스윕 | MISSION_SUCCESS | PASS |
| x 감소 방향(미러링)도 성공 | MISSION_SUCCESS | PASS |
| 왼손 고정·오른손이 움직임 → 오른손 자동선택 | MISSION_SUCCESS | PASS |
| 거의 정지 | MOVEMENT_TOO_SMALL | PASS |
| 좁은 폭 떨기 | BOOK_NOT_TURNED | PASS |
| yRange 0 이어도 가로 스윕이면 성공 | MISSION_SUCCESS | PASS |
| 손목 미제공(visible<2) | HAND_NOT_VISIBLE | PASS |
| 손목 visibility 낮아 전부 필터 | HAND_NOT_VISIBLE | PASS |

### tests/test_receive_seed.py (7) — scene_002 (두 손 모아 어깨 위)
| 케이스 | 기대 | 결과 |
|---|---|---|
| 두 손 모아 어깨 위 | MISSION_SUCCESS | PASS |
| 두 손 어깨 아래 | HAND_NOT_RAISED | PASS |
| 한 손만 올림 | HAND_NOT_RAISED | PASS |
| 올렸지만 멀리 떨어짐 | HANDS_NOT_TOGETHER | PASS |
| 한쪽 손목 미감지 | HAND_NOT_VISIBLE | PASS |
| 어깨 미감지 | USER_NOT_DETECTED | PASS |
| 프레임 간 bestFrame | MISSION_SUCCESS | PASS |

### tests/test_protect_swallow.py (6) — scene_001
| 케이스 | 기대 | 결과 |
|---|---|---|
| 손 가깝고 중앙 | MISSION_SUCCESS | PASS |
| 손 사이 멂 | HANDS_TOO_FAR | PASS |
| 가깝지만 중앙 이탈 | HANDS_NOT_CENTERED | PASS |
| 손목 visibility 낮음 | HAND_NOT_VISIBLE | PASS |
| 어깨 미감지 | USER_NOT_DETECTED | PASS |
| bestFrame(앞 실패→나중 중앙 모음) | MISSION_SUCCESS | PASS |

### tests/test_open_gourd.py (6) — scene_003 (박 썰기: 같은 방향 좌우 이동)
| 케이스 | 기대 | 결과 |
|---|---|---|
| 같은 방향 좌우 톱질 | MISSION_SUCCESS | PASS |
| 손이 어깨보다 높음 | HAND_POSITION_TOO_HIGH | PASS |
| 거의 정지 | MOVEMENT_TOO_SMALL | PASS |
| 서로 반대 방향(중심 고정) | SAWING_MOTION_TOO_SMALL | PASS |
| 한쪽 손목 미감지 | HAND_NOT_VISIBLE | PASS |
| 어깨 미감지 | USER_NOT_DETECTED | PASS |

### tests/test_integration_api.py (12) — API 레벨 통합
| 케이스 | 기대 | 결과 |
|---|---|---|
| skip_book 성공 | MISSION_SUCCESS | PASS |
| skip_book 실패 | MOVEMENT_TOO_SMALL | PASS |
| receive_seed 성공 | MISSION_SUCCESS | PASS |
| receive_seed 실패 | HAND_NOT_RAISED | PASS |
| protect_swallow 성공 | MISSION_SUCCESS | PASS |
| protect_swallow 실패 | HANDS_TOO_FAR | PASS |
| open_gourd 성공 | MISSION_SUCCESS | PASS |
| open_gourd 실패 | MOVEMENT_TOO_SMALL | PASS |
| poseFrames 빈 배열 | INVALID_POSE_DATA | PASS |
| 필수 landmark(손목) 누락 | HAND_NOT_VISIBLE | PASS |
| 알 수 없는 missionType | UNKNOWN_MISSION_TYPE | PASS |
| 응답 4개 필드만(금지필드 미포함) | 전 케이스 단언 | PASS |
| GET /health | status ok | PASS |

## 5. 실패한 경우 원인과 수정 내용

개발 중 1건 일시 실패 → 수정 후 통과:

| 테스트 | 원인 | 수정 |
|---|---|---|
| test_open_gourd::test_movement_ok_when_required_success | 두 프레임 손목 이동 합이 0.30 으로 임계값(0.4) 미달 → 의도와 달리 MOVEMENT_TOO_SMALL | 손목이 좌우로 크게 휘둘리는 3프레임(이동 합 ≈1.2)으로 테스트 데이터 수정 |

최종 전체 재실행 결과 **40 passed**.

## 6. 비고 (추후 조정 포인트)

- 점수(score) 절대값은 기획서 예시(0.88, 0.91 등)와 다를 수 있음 — 성공 여부와 reasonCode 가 기준에 맞도록 설계.
- 임계값은 Unity 실제 poseFrames 로 보정 필요(`app/core/config.py` / `.env`).
