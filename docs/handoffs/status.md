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

```text
2026-11-04 / Feature: 전 화면 UI 개선(reference/UiImages 12장 기준) / Result: PASS (아래 미확인 항목 제외)
Files: frontend/src/styles.css, components/{AppHeader,BaseModal,MenuTree,WeatherWidget,ProgressBar(신규)}.vue, views/AuthView.vue, screens/{dashboard,hulls,plans,progress,drawings,approvals,users}/*.vue, __tests__/{plans,drawings}.spec.js
Tests: frontend `npx vitest run` 48 passed(신규 2); vite build OK; Playwright 1917x884 12개 화면 캡처 대조, 1440x900·1024x768 가로 넘침 측정, 조회전용(choi.qa) 쓰기 UI 숨김·모달 Esc·메뉴 접기·로그인 오류 표시 확인; backend 변경 없음
Decisions: 캡처 색은 ICC→sRGB 변환 시 목업 토큰과 일치(팔레트 유지). 캡처의 MOCKUP 문구·데이터 초기화·데모 계정 안내·데모 OTP 문구 미재현. F07 명세 우선으로 리비전 표에 파일명·작성자를 부가 줄로 유지. 샘플 PDF는 DWG-T05에 따라 안내 박스 유지. 공정 패널 도면번호 링크는 목업 openDwg 기준으로 도면 팝업 연결
Next: 미확인 — 승인대기/DRAFT 등 시드로 확인 못 한 상태 조합의 시각 검토, Windows 폰트 렌더링. 1024px 호선 목록은 표 폭 때문에 패널 내부 가로 스크롤(157px) 발생(페이지 자체 넘침 없음)
```
- 근본 원인 수정: 입력 공통 선택자 우선순위가 높아 readonly/disabled 회색이 적용되지 않던 문제(`:where`로 낮춤), body line-height 1.45로 표·메뉴 행이 캡처보다 높던 문제

```text
2026-11-04 / Feature: F10 Unity 샘플 호선 3D 뷰어 / Result: PASS (아래 미확인 항목 제외)
Unity: 6000.5.10f1 (Web Build Support 포함, Built-in RP, WebGL2, 압축 Disabled). 6000.3.23f1은 Web 모듈이 없어 미사용
Files(신규): unity/ShipyardViewer/(Assets/Scripts, Assets/Editor/BuildViewer.cs, Assets/Plugins/WebGL/ViewerBridge.jslib, 씬·재질, Packages, ProjectSettings), frontend/public/unity/ship-viewer/Build/(빌드 산출물 14MB), frontend/src/components/{ShipViewer.vue,unityRuntime.js}, frontend/src/__tests__/shipViewer.spec.js, contracts/unity-viewer.md
Files(수정): frontend/src/screens/hulls/HullDetailModal.vue, frontend/src/__tests__/hulls.spec.js, docs/features/{F10-ship-viewer,00-index}.md. 백엔드·DB 스키마·API 변경 없음
Run: 재빌드 명령은 contracts/unity-viewer.md. 실행은 기존처럼 프론트(vite)·백엔드를 띄운 뒤 호선 상세 > 3D 보기
Tests: frontend `npx vitest run` 56 passed(신규 8); vite build OK; 브라우저 스크린샷 직접 확인 포함
- T01 Esc·닫기로 상세 복귀, 작성 중 내용·서브탭 유지, 두 번째 Esc로 상세 닫힘, 탭 이동 정상, 조회 전용 계정도 열람 가능
- T02 Unity canvas에 선체·갑판·선실 렌더링 및 예시 안내 표시 확인
- T03 회전·줌·이동·정면·측면·상단 동작, 전 조작 후 초기화 시 초기 화면과 픽셀 차이 0.00%, 줌·이동·각도 한계에서 모델 유지
- T04 build.json 없음(HTML 폴백)·wasm 차단 주입 시 안내 표시, 시점 버튼 비활성, 재시도로 복구
- T05 로딩 중 닫고 즉시 재오픈, 8회 반복 열기·닫기: canvas 1→0, window/document 리스너 수 고정, 이후 렌더링 정상
- T07 vite dev와 vite preview(프로덕션 빌드)에서 실행, .wasm=application/wasm 확인, 창 크기 3종 변경 시 canvas 추종·페이지 가로 넘침 없음
Decisions: 상세 모달은 숨기고 뷰어로 교체(중첩 없음). 파일명은 빌드가 생성하는 build.json에서 읽음. config.showBanner는 공식 매뉴얼에 없어 6000.5 로더 코드로 확인
Next: 미확인 — Unity Editor GUI에서의 씬 확인(배치 빌드만 수행), 압축 빌드·실제 배포 서버 헤더, 트랙패드 조작, Safari/Firefox, 실 GPU 체감 성능. 빌드 산출물을 git에 포함할지는 사용자 결정 필요
```
- 알려진 경고(비차단): 뷰어 종료 시 콘솔에 WebGL 경고 5건(bindFramebuffer invalid target 등). loseContext를 꺼도 동일하게 발생하는 Unity 종료 과정의 경고로 이후 재오픈 렌더링에 영향 없음. vite preview에서 [UnityCache] Content-Length 경고 1건. 콘솔 404는 기존 favicon
- 기존 동작(F10 무관, 미수정): 호선 상세에서 조회 응답 전에 입력하면 늦게 온 응답이 값을 덮어씀(뷰어 없이도 재현)
- 구현 중 발견한 사항: Unity 런타임은 canvas id가 필수('#'+id 조회). 선체 정점 병합 시 x=0에서 좌우 현을 분리해야 법선이 0이 되지 않음. 기본 그림자 거리(150)가 궤도 거리보다 짧아 런타임에서 400으로 설정

```text
2026-11-04 / Feature: F10 진입 방식 변경(버튼 → 호선 상세 서브탭) / Result: PASS
Files: frontend/src/screens/hulls/HullDetailModal.vue, frontend/src/components/ShipViewer.vue(BaseModal 제거), frontend/src/__tests__/hulls.spec.js, docs/features/F10-ship-viewer.md, contracts/unity-viewer.md. Unity 재빌드 불필요
Tests: frontend `npx vitest run` 56 passed; vite build OK; 브라우저(조회 전용 계정, 1600x900) — 3D 탭 렌더링·시점 버튼, 탭 이탈 시 canvas 0, 기본정보 복귀 시 작성 내용 유지·재조회 없음, 3회 반복, 로딩 중 탭 이동 후 재진입 시 canvas 1, Esc로 상세 닫힘·canvas 0
Decisions: 상단 MDI 탭이 아닌 호선 상세 서브탭으로 해석. 3D 탭에서만 모달 xl. 모달이 하나이므로 Esc는 호선 상세를 닫음(이전: 뷰어만 닫음). 제목은 정보 카드에 표시
Next: 이전 F10 항목의 미확인 사항 동일
```

```text
2026-11-04 / Feature: 로그인 화면 디자인 개선(사용자 지시) / Result: PASS
Files: frontend/src/components/AuthScene.vue(신규, 조선소 새벽 풍경 SVG·외부 이미지 없음), frontend/src/views/AuthView.vue, frontend/src/styles.css
Tests: frontend `npx vitest run` 56 passed; vite build OK; Playwright 1440x900·1917x884·1100x700·1024x768·390x844 가로 넘침 0, 로그인·오류·회원가입·OTP 화면 및 실제 로그인·로그아웃 확인
Decisions: login.png의 중앙 카드 대신 좌측 소개+우측 카드(≤1000px은 카드만). 사용자 지시가 시각 기준보다 우선. 소개 문구는 실제 기능만, 수치·데모 계정 미표시. 크레인·경광등 애니메이션은 prefers-reduced-motion에서 정지
Next: NONE (인증 로직 변경 없음)
```

```text
2026-11-04 / Feature: MCP 평가·패키징 / Result: PASS (문서·설정 예시만)
Files: mcp-recommendations.md, mcp-usage-policy.md, template/.mcp.json, optional-mcp/(README + 예시 4개), docs/handoffs/tool-evidence.md. 루트 .mcp.json·전역 설정 변경 없음, 서버 설치 없음
Tests: JSON 구조 검증 5개 OK, 자격 증명 패턴 검색 0건. 트랜스크립트 집계 641회 중 Playwright 184, Context7 0, SQLite 0. 기존 Context7·SQLite 연결은 읽기 호출로 확인. template·optional 설정 연결은 미검증
Decisions: KEEP Playwright / OPTIONAL Context7·Serena·Exa / OMIT Tavily·Memory·SQLite / ADD 없음. 토큰 절감률은 대조군이 없어 미기재
Next: 루트 .mcp.json 정리 여부는 사용자 결정. 추가 시 서버 하나씩 실험
```
