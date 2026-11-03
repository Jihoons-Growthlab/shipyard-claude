# 기능별 구현 상태 / 핸드오프

> 명세 패키지 생성 시점. **아래 기능은 아직 구현되지 않았다.** 실제 파일을 생성하고 테스트를 통과할 때만 상태를 바꿀 것.

## Baseline (Phase 0 시작 시점)

- 2026-11-03T22:45:11+09:00 / branch main / HEAD fd7aa79 / 미추적: .claude/rules/file-reading.md
- 누적 토큰(세션 2·API 16회): 입력 38 · 출력 15,122 · 캐시생성 56,092 · 캐시읽기 847,263 (합 918,515) — docs/handoffs/logs/baseline_usage.json
- Skill/MCP 사용: 없음

| 단계 | Feature | 상태 | 테스트 | 산출물/결정 |
|---|---|---|---|---|
| I00 | F01 + F02 셸 + DB 기본 | DONE (P1) | pytest 20/20, vitest 9/9 | D03·D04-b·D15 권장안 적용 |
| I01 | F04 호선 | DONE (P2) | pytest 33/33, vitest 13/13 | HULL-T01~T08, Playwright CRUD |
| I02 | F05 계획 | DONE (P3) | pytest 44/44, vitest 19/19 | PLAN-T01~T09, D10 권장안, Playwright 계획 흐름 |
| I03 | F06 실적 | DONE (P4) | pytest 55/55, vitest 22/22 | PROG-T01~T06, D09=OBS(입력 게이트 없음) |
| I04 | F07 도면/PDF | DONE (P5) | pytest 66/66, vitest 28/28 | DWG-T01~T10, D12/D13 적용, D11 잠정 |
| I05 | F08 결재 | DONE (P6) | pytest 72/72, vitest 32/32 | APV-T01~T06, D11 CONFIRMED |
| I06 | F09 회원관리 | DONE (P7) | pytest 91/91, vitest 36/36 | USR-T01~T08, D14 적용, D11 유지 |
| I07 | F03 대시보드 | DONE (P8) | pytest 98/98, vitest 38/38 | DASH-T01~T06, GET /api/dashboard/summary |
| I08 | F02 날씨 MCP·통합 | DONE (P9, 날씨만 · 통합테스트 미착수) | pytest 106/106, vitest 41/41 | WEATHER-T01~T03, D07 부분 적용(실 MCP 공급자 없음 → SAMPLE) |

## 작업 종료 시 5줄만 추가

```text
YYYY-MM-DD / Feature: Fxx / Result: PASS|PARTIAL|BLOCKED
Files: <변경 파일 최대 8개 또는 glob>
Tests: <명령 + 통과/실패 개수>
Decisions: <결정 ID 또는 NONE>
Next: <구체적 다음 작업>
```

별도 장문의 인수인계 문서를 매번 생성하지 않는다. 완료보고서는 최종 시점에 요약해서 작성한다.

## 기록

```text
2026-11-03 / Feature: Phase0 / Result: PASS
Files: .mcp.json, docs/handoffs/{status,decisions,tool-evidence}.md, docs/handoffs/logs/*
Tests: N/A (sqlite MCP initialize 스모크 성공, claude mcp list Connected)
Decisions: D01/D02/D04/D06 RESOLVED-BY-SHEET; D03,D04-b,D08,D09,D10,D11,D14,D15,D18 권장안만 제시(OPEN)
Next: 사용자 결정 확정 + /mcp 재연결 → P1 (/implement-feature F01) 별도 요청 시
```

```text
2026-11-03 / Feature: P1(I00: DB+F01+RBAC+F02 셸) / Result: PASS
Files: database/migrations/000{1-4}_*.sql, backend/app/**, backend/tests/*, frontend/src/**, .gitignore
Tests: backend `uv run pytest -q` 20 passed (AUTH-T01~T07, SHELL-T01 403, 401/409/403, 승인); frontend `npx vitest run` 9 passed (SHELL-T01~T05); vite build OK; Playwright MCP 스모크(로그인→셸→로그아웃) 통과
Decisions: D03/D04-b/D15 권장안 적용(사용자 확정 대기), 시드 TOTP=목업 데모 secret(실 등록은 D05)
Next: P2 I01 F04 호선(도메인 시드 포함) — 별도 요청 시. 미포함: 날씨(F02 P2), 회원관리 UI(F09), D08 재시드 API
```
- P1 토큰(프롬프트 #1, extract_usage): 입력+캐시 3,301,765 · 출력 54,734 / 누적(세션3·API63): 입력 134 · 출력 78,682 · 캐시생성 178,590 · 캐시읽기 5,094,760 — docs/handoffs/logs/p1_end_usage.json
- 스모크에서 발견·수정: sync `yield` 의존성의 스레드 교차로 sqlite close 500 → `check_same_thread=False`(요청당 연결)

```text
2026-11-03 / Feature: F04(P2) / Result: PASS
Files: backend/app/{services/hull_service,metrics,code_service,routers/hulls,schemas,seed,cli}.py, backend/tests/test_hulls.py, frontend/src/screens/hulls/*, frontend/src/{api/client,stores/codes,screens/registry,views/ShellView}.*, frontend/src/__tests__/hulls.spec.js
Tests: backend pytest 33 passed(P1 20 회귀 포함, HULL-T01~T08); frontend vitest 13 passed(SHELL 9 + HULL 4); vite build OK; Playwright MCP CRUD 통과
Decisions: NONE 신규. 시드에 호선 5·블록 17·마일스톤 25·표준공정 7 추가(공정계획 시드는 F05)
Next: P3 I02 F05 공정계획 — 별도 요청 시. 미결: PDF 파일 삭제는 D12/F07에서 delete_hull에 연결
```
- P2 토큰(P1 종료 대비 누적 증분): 입력 58 · 출력 38,170 · 캐시생성 57,477 · 캐시읽기 4,452,693 — docs/handoffs/logs/p2_end_usage.json

```text
2026-11-03 / Feature: F05(P3) / Result: PASS
Files: backend/app/services/plan_service.py, backend/app/routers/{plans,users}.py, backend/app/{seed,schemas,cli,main}.py, hull_service.delete_block(상태 재산정), backend/tests/{test_plans,conftest}.py, frontend/src/screens/plans/*, frontend/src/__tests__/plans.spec.js
Tests: backend pytest 44 passed(P1/P2 회귀 33 포함); frontend vitest 19 passed; vite build OK; Playwright MCP 계획 흐름 통과
Decisions: D10 권장안 적용(과거 ISSUED Rev도 게이트 통과); 선행 지연 확인은 409 PRED_LATE_CONFIRM_REQUIRED → confirm_late_preds 재전송
Next: P4 I03 F06 실적(D09 게이트 강제 여부 확정 필요) — 별도 요청 시
```
- 시드 추가: 공정 79·선후행 79·실적 60·도면 47·Rev 79·결재 72·연계 45(목업 seed 규칙 이식 후 서버 refresh_statuses)
- P3 토큰(P2 종료 대비 누적 증분): 입력 64 · 출력 52,978 · 캐시생성 77,404 · 캐시읽기 7,071,038 — docs/handoffs/logs/p3_end_usage.json

```text
2026-11-04 / Feature: F06(P4) / Result: PASS
Files: backend/app/services/progress_service.py, backend/app/routers/progress.py, backend/app/{schemas,main}.py, backend/tests/test_progress.py, frontend/src/screens/progress/ProgressScreen.vue, frontend/src/{api/client,screens/registry}.js, frontend/src/__tests__/progress.spec.js
Tests: backend `uv run pytest -q` 55 passed(회귀 44 포함, PROG-T01~T06+D09); frontend `npx vitest run` 22 passed; vite build OK; Playwright 미실행
Decisions: D09 APPLIED=원본 동작(실적 입력 시 도면 게이트 미강제, 게이트는 READY/PLAN 판정에만 사용). 추가 API GET /api/progress-hulls(M22 View, BUILD 우선 기본 호선)
Next: P5 I04 F07 도면/Rev/PDF — 별도 요청 시. 참고: 시드 8001-[301]도장은 Plan 60%/착수 09-27이 이력(최신 57%, 첫 10-17)과 불일치(목업 seed 동일) → 실적 저장/삭제 시 이력 기준으로 재계산됨
```

```text
2026-11-04 / Feature: F07(P5) / Result: PASS
Files: backend/app/services/{drawing_service,file_store}.py, backend/app/routers/drawings.py, backend/app/{schemas,main,config}.py, hull_service.delete_hull(파일 정리), backend/tests/{test_drawings,conftest}.py, frontend/src/screens/drawings/*, frontend/src/{api/client,screens/registry}.js, frontend/src/__tests__/drawings.spec.js
Tests: backend `uv run pytest -q` 66 passed(회귀 55 포함, DWG-T01~T10 + 호선삭제 파일정리); frontend `npx vitest run` 28 passed; vite build OK; Playwright 미실행
Decisions: D12 APPLIED(서버 FS+DB 메타), D13 APPLIED(UI 샘플 라벨, 서버 생성 없음), D11 잠정(배포=M31 Write), D09/D10 유지 검증
Next: P6 I05 F08 결재(승인/반려, D11 확정) — 별도 요청 시
```
- 후속 개선(비차단): ① 목업처럼 샘플 PDF를 실제 렌더(현재는 라벨 박스) ② 연계 공정 '간트로 이동' 미구현 ③ 고아 파일 주기 정리(삭제 실패 시 로그만) ④ 업로드 multipart 미사용(raw body+filename 쿼리) — 필요 시 python-multipart 도입 ⑤ 재요청 시 반려 결재 이력 삭제(UNIQUE(DrawingId,RevNo,StepNo) 제약, 목업 동일) — F08에서 이력 보존 방식 검토 ⑥ 시각 polish(warnbox/muted 스타일 등)

```text
2026-11-04 / Feature: F08(P6) / Result: PASS
Files: backend/app/services/approval_service.py, backend/app/routers/approvals.py, backend/app/{schemas,main}.py, drawing_service.issue(결재완료 확인), backend/tests/test_approvals.py, frontend/src/screens/approvals/ApprovalInbox.vue, frontend/src/{api/client,screens/registry}.js, frontend/src/__tests__/approvals.spec.js
Tests: backend `uv run pytest -q` 72 passed(회귀 66 포함, APV-T01~T06 + D11 권한); frontend `npx vitest run` 32 passed; vite build OK; Playwright 미실행
Decisions: D11 CONFIRMED(M31 Write=편집/리비전/결재요청/배포, M33 Write+지정 현재 결재자=승인/반려, 배포는 결재 완료 필수)
Next: P7 I06 F09 회원관리 — 별도 요청 시
```
- API: GET /api/approvals/inbox → {waiting, ready, can_issue(M31 Write UI 힌트)}, POST /api/approvals/{id}/decision {result, comment}, GET /api/approvals/history(전체 사용자 최근 10건). 배포는 F07 issue 재사용
- 남은 사항(비차단): ① 결재 재요청 시 이전 반려 이력은 F07 request_approval이 삭제(UNIQUE(DrawingId,RevNo,StepNo) 스키마 제약, 목업 동일) — 보존하려면 스키마 변경 필요 ② ActDt=업무일자+실제 시각이라 시드 이력(16:00 등)과 정렬이 섞일 수 있음 ③ 시각 polish 보류

```text
2026-11-04 / Feature: F09(P7) / Result: PASS
Files: backend/app/services/user_service.py, backend/app/routers/users.py, backend/app/{schemas,main}.py, backend/tests/test_users.py, frontend/src/screens/users/UserManagement.vue, frontend/src/{api/client,screens/registry}.js, frontend/src/__tests__/users.spec.js
Tests: backend `uv run pytest -q` 91 passed(회귀 72 포함, USR-T01~T08); frontend `npx vitest run` 36 passed; vite build OK; Playwright 미실행
Decisions: D14 APPLIED, F09 권한=M91 Admin, OTP 등록 없는 활성화 거절(D05 대기). D11 변경 없음
Next: P8 I07 F03 대시보드 — 별도 요청 시
```
- 후속 개선(비차단): ① 관리자 본인 상태 변경/ADMIN 그룹 해제 시 즉시 잠김(목업 동일, 차단 안 함) — 최소 1명 ADMIN 유지 가드 검토 ② 삭제된 사용자가 WAIT 결재자이면 ApproverEmpNo=NULL로 결재가 멈춤 → 재요청 필요(삭제 전 경고 또는 비활성화 권장) ③ 관리자에 의한 OTP 실 등록(QR/검증) 미구현(D05) ④ 복수 그룹 미지원(UI 단일 선택, DB는 복수 가능) ⑤ 삭제 대신 '중지(disabled)' 권장 안내 ⑥ 시각 polish(상하 분할 레이아웃·폼 그리드 스타일)

```text
2026-11-04 / Feature: F03(P8) / Result: PASS
Files: backend/app/services/dashboard_service.py, backend/app/routers/dashboard.py, backend/app/main.py, backend/tests/test_dashboard.py, frontend/src/screens/dashboard/DashboardScreen.vue, frontend/src/{api/client,screens/registry}.js, frontend/src/views/ShellView.vue(provide navigate + tab param), frontend/src/screens/plans/PlanGantt.vue(param=초기 호선), frontend/src/__tests__/dashboard.spec.js
Tests: backend `uv run pytest -q` 98 passed(회귀 91 포함, DASH-T01~T06 + 401); frontend `npx vitest run` 38 passed; vite build OK; Playwright 미실행
Decisions: NONE. 집계는 weighted_progress(BR-01)·gate_blockers(BR-02)·drawing_service.impacts(BR-07) 재사용, 권한 M00 View. 목록은 서버가 count+최대 6건 반환
Next: P9 I08 F02 날씨 MCP·통합 — 별도 요청 시
```
- 후속 개선(비차단): ① 시각 polish(목업 CSS 이식) ② 호선 진척 행·지연/대기 행 이동은 plan-gantt 호선별 탭으로 열림(탭 키=화면+param, SHELL-04) ③ 대시보드 자동 새로고침 없음(탭 재진입 시 재조회 미구현)

```text
2026-11-04 / Feature: F02 날씨(P9) / Result: PARTIAL (요구 기능 PASS, 실 날씨 MCP 미연결)
Files: backend/app/services/weather_service.py, backend/app/routers/weather.py, backend/app/{config,main}.py, backend/.env.example, backend/tests/test_weather.py, frontend/src/components/{WeatherWidget,AppHeader}.vue, frontend/src/api/client.js, frontend/src/__tests__/weather.spec.js
Tests: backend `uv run pytest -q` 106 passed(회귀 98 포함, 날씨 8); frontend `npx vitest run` 41 passed(날씨 3, T03는 가드 제거 시 실패 확인); vite build OK; Playwright MCP 헤더 날씨 스모크 통과
Decisions: D07 APPLIED(부분) — 날씨=선택 범위, 날씨 MCP 미구성이라 SAMPLE 폴백(LIVE는 등록 공급자 성공 시만)
Next: 최종 UI 정리 + 통합 테스트(별도 요청 시). 실 날씨 MCP 확보 시 PROVIDERS 등록 + WEATHER_PROVIDER 설정
```
- 후속 개선(비차단): ① 실 날씨 MCP 서버/도구 ID 확인 후 공급자 구현(D07 잔여) ② 클라이언트 네트워크 실패 시 '날씨 조회 실패'만 표시(샘플 값은 서버 단일 소스) ③ 지역 저장은 브라우저별(사용자별 아님) ④ 10분 주기 갱신은 탭 비활성 시에도 동작 ⑤ 시각 polish(헤더 배치·배지 색) ⑥ favicon 404(기존)

```text
2026-11-04 / Feature: 감사 후속(SHELL-T04, DASH-T05) / Result: PASS
Files: frontend/src/views/ShellView.vue(navRequest), frontend/src/screens/hulls/HullDetailModal.vue, frontend/src/screens/drawings/{DrawingDetailModal,DrawingList}.vue, frontend/src/screens/plans/PlanGantt.vue, frontend/src/__tests__/{hulls,drawings,plans}.spec.js, docs/handoffs/requirements-audit.md
Tests: frontend `npx vitest run` 46 passed(신규 5, 일부러 코드를 깨뜨린 5건 모두 탐지); vite build OK; backend 변경 없음; 브라우저 미실행
Decisions: NONE. 목록 이동은 화면+param 탭(SHELL-04)으로 열림 — 목업은 단일 dwg-list 탭에 필터만 적용
Next: 감사 #1(README·완료보고서), #3(E2E), #5(반려 이력 보존 결정)
```

```text
2026-11-04 / Feature: 공통 UI 정리(목업 기준, 1440x900) / Result: PASS (공통 범위만)
Files: frontend/src/styles.css(전면 재정리: 목업 토큰·셸·탭·메뉴·표·폼·모달·배지), frontend/src/components/AppHeader.vue(브랜드 부제+spacer)
Tests: frontend `npx vitest run` 46 passed; vite build OK; Playwright MCP 목업 대비 대시보드·호선·결재함·회원관리·공정계획·호선/도면 모달 확인
Decisions: NONE. 근본 원인 수정 — auth `.card`가 화면 카드에 누수(360px 고정), `.bdg/.b-*/.btn.ok/.grid.g4/.split/.empty/.note` 미정의, `.btn.sm`의 margin-left:auto 전역 적용
Next: 화면별 polish(아래 잔여 항목) — 별도 요청 시
```
- 잔여 시각 이슈(비차단, 화면 개별): ① 도면 상세 모달 우측 리비전 표 가로 넘침(목업은 `.tw.r3` 스크롤 래퍼, 모달 xl 1640px·전체 높이 분할) ② 목록 상태 열이 텍스트(목업은 s-*/d-* 배지) — 호선·도면·실적 ③ 공정계획 간트가 max-height 60vh 고정(목업은 남은 높이 사용 + 하단 상세 패널) ④ 대시보드 scoped 스타일(.bdg/.lst/.empty 중복 정의)·차트 색이 목업과 상이 ⑤ 표 `.tw` 래퍼 미사용으로 긴 표 헤더 sticky가 페인 스크롤 기준 ⑥ 회원관리 2차인증 체크박스 라벨 정렬 미세 차이

```text
2026-11-04 / Feature: 레이아웃 우측 빈 공간 점검 / Result: PASS (추가 변경 없음)
Files: 없음 (원인은 직전 공통 UI 정리에서 이미 수정: auth `.card{width:min(360px)}`가 결재함·회원관리 카드에 누수 → `.auth .card`로 한정)
Tests: Playwright MCP 측정 1440x900·1920x1080 — 대시보드·호선·공정계획·공정실적·도면·결재함·회원관리 모두 섹션/카드/표 우측 끝 = 뷰포트-18px(의도된 패딩), html·.panes scrollWidth=clientWidth(가로 오버플로 없음)
Decisions: NONE
Next: 재현되면 화면·해상도·스크린샷 제공 요청(브라우저 캐시된 이전 CSS 가능성)
```

```text
2026-11-04 / Feature: F07 도면 상세 모달 UI / Result: PASS
Files: frontend/src/screens/drawings/DrawingDetailModal.vue(템플릿 재구성+scoped 레이아웃), frontend/src/components/BaseModal.vue(xl prop), frontend/src/styles.css(.modal.xl, .tw, td.wrap 줄바꿈)
Tests: frontend `npx vitest run` 46 passed; vite build OK; Playwright 1440x900·1024x768 — 모달 중앙(좌우·상하 여백 동일), 가로 스크롤 0, 셀 잘림 0
Decisions: NONE. 목업 .dwgx 구조(좌 PDF 뷰어 전체 높이 + 우 섹션 카드 스크롤), 폭 min(85vw,1600px)·높이 94vh, ≤1100px 세로 스택. 리비전 표 7열→5열(사유+파일, 작성자+배포일 2줄 표기, 데이터 동일)
Next: NONE (기능·API 변경 없음)
```
