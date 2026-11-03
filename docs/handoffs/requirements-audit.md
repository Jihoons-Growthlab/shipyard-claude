# F01–F09 요구사항 감사 (2026-11-04)

근거: `docs/features/F0x-*.md` AC, `docs/handoffs/status.md`, 재실행 결과 — backend `uv run pytest -q` **106 passed**, frontend `npx vitest run` **41 passed** (2026-11-04). 내비게이션 수정 후 frontend **46 passed**, vite build OK (backend 변경 없음). 브라우저 테스트는 이번 감사에서 실행하지 않음.
범위 구분(problem_sheet §3): **필수** = F01 가입·승인·JWT·RBAC, F04 호선 CRUD, F05 계획 CRUD·선후행, F06 실적·상태 자동계산, F07/F08 도면·Rev·2단계 결재·배포, 서버 규칙 ①게이트 ②403 ③중복가입. **선택** = F03 대시보드, 간트, 개정 영향, 호선 상태 자동 전이, OTP, PDF 업로드, 날씨(MCP).

## 요약

| 판정 | AC 수 (68) |
|---|---|
| PASS | 68 |
| FAIL | 0 (SHELL-T04 → 2026-11-04 수정 후 PASS) |
| UNVERIFIED | 0 (DASH-T05 → 2026-11-04 테스트 추가 후 PASS) |

AC 외 명세 항목: 호선 상태 자동 전이(선택) UNVERIFIED, WEATHER-02 실시간 LIVE(선택) FAIL — 아래 Findings 참고.

## 커버리지 매트릭스

B = `backend/tests/`, F = `frontend/src/__tests__/`

| Feature | 구분 | AC | 판정 | 근거 |
|---|---|---|---|---|
| F01 | 필수 | AUTH-T01 | PASS | B test_auth.py::test_t01_* ; P1 Playwright 로그인→셸 |
| | 필수 | AUTH-T02 | PASS | test_auth.py::test_t02_pending_rejected_disabled_* |
| | 선택(OTP) | AUTH-T03 | PASS | test_auth.py::test_t03_* (2차 인증·재사용·5회 제한·토큰 혼용) |
| | 필수 | AUTH-T04 | PASS | test_auth.py::test_t04_registration_validation_and_duplicates |
| | 필수 | AUTH-T05 | PASS | test_auth.py::test_t05_*, test_rbac_shell.py::test_admin_approval_flow_enables_login |
| | 필수 | AUTH-T06 | PASS | test_auth.py::test_t06_logout_and_expiry_return_401, test_t06_session_revoked_* |
| | 필수 | AUTH-T07 | PASS | test_auth.py::test_t07_access_log_matches_account |
| F02 | 필수 | SHELL-T01 | PASS | B test_rbac_shell.py::test_shell_t01_*, F shell.spec.js SHELL-T01 |
| | 필수 | SHELL-T02 | PASS | F shell.spec.js SHELL-T02 |
| | 필수 | SHELL-T03 | PASS | F shell.spec.js SHELL-T03 |
| | 필수 | SHELL-T04 | PASS (수정) | Esc/닫기: F shell.spec.js SHELL-T04. 팝업 이동: F hulls.spec.js 'SHELL-T04 hull popup navigation', drawings.spec.js 'SHELL-T04 drawing popup / list navigation' — 일부러 코드를 깨뜨리면 테스트가 실패하는 것 확인 |
| | 필수 | SHELL-T05 | PASS | F shell.spec.js SHELL-T05 ×2 |
| | 선택 | WEATHER-T01 | PASS | B test_weather.py::test_t01_*, F weather.spec.js WEATHER-T01 |
| | 선택 | WEATHER-T02 | PASS | B test_weather.py::test_t02_*, F weather.spec.js WEATHER-T02 |
| | 선택 | WEATHER-T03 | PASS | F weather.spec.js WEATHER-T03 (가드를 빼면 실패하는 것 확인) |
| F03 | 선택 | DASH-T01 | PASS | B test_dashboard.py::test_t01_* |
| | 선택 | DASH-T02 | PASS | test_dashboard.py::test_t02_* |
| | 선택 | DASH-T03 | PASS | test_dashboard.py::test_t03_* |
| | 선택 | DASH-T04 | PASS | test_dashboard.py::test_t04_* |
| | 선택 | DASH-T05 | PASS (검증 추가) | B test_t05, F dashboard.spec.js + plans.spec.js 'DASH-T05 / SHELL-T04 gantt hull context'(param으로 첫 호선 선택, 이미 열린 탭 재진입 시 호선 복구, 없는 호선이면 기본 호선) |
| | 선택 | DASH-T06 | PASS | B test_t06_lists_capped_at_six, F dashboard.spec.js |
| F04 | 필수 | HULL-T01 | PASS | B test_hulls.py::test_t01_*, F hulls.spec.js HULL-T01 (더블클릭 포함) |
| | 필수 | HULL-T02 | PASS | test_hulls.py::test_t02_create_validation |
| | 필수 | HULL-T03 | PASS | test_hulls.py::test_t03_create_makes_five_milestones_with_delivery |
| | 필수 | HULL-T04 | PASS | B test_t04_*, F hulls.spec.js HULL-T04 (서브탭 유지) |
| | 필수 | HULL-T05 | PASS | test_hulls.py::test_t05_block_code_unique_per_hull |
| | 필수 | HULL-T06 | PASS | test_hulls.py::test_t06_block_delete_keeps_drawing_and_removes_plans |
| | 필수 | HULL-T07 | PASS | test_hulls.py::test_t07_*, test_drawings.py::test_hull_delete_removes_stored_pdfs |
| | 필수 | HULL-T08 | PASS | test_hulls.py::test_t08_* ×2 |
| F05 | 선택(간트) | PLAN-T01 | PASS | F plans.spec.js PLAN-T01 ×4 (오늘선, 배율, 스크롤 복구) |
| | 필수 | PLAN-T02 | PASS | B test_plans.py::test_t02_* (담당자·메모) |
| | 필수 | PLAN-T03 | PASS | test_plans.py::test_t03_self_and_cycle_rejected |
| | 필수 | PLAN-T04 | PASS | B test_t04_*, F plans.spec.js PLAN-T04 |
| | 필수 | PLAN-T05 | PASS | test_plans.py::test_t05_* |
| | 필수 | PLAN-T06 | PASS | test_plans.py::test_t06_* |
| | 필수 | PLAN-T07 | PASS | test_plans.py::test_t07_* |
| | 필수 | PLAN-T08 | PASS | test_plans.py::test_t08_* |
| | 필수 | PLAN-T09 | PASS | test_plans.py::test_t09_view_only_writes_403 |
| F06 | 필수 | PROG-T01 | PASS | B test_progress.py::test_t01_*, F progress.spec.js |
| | 필수 | PROG-T02 | PASS | test_progress.py::test_t02_same_day_upsert_* |
| | 필수 | PROG-T03 | PASS | 같은 테스트(마지막 날짜 누적률) |
| | 필수 | PROG-T04 | PASS | test_progress.py::test_t04_validation (parametrize) |
| | 필수 | PROG-T05 | PASS | test_progress.py::test_t05_done_then_delete_reverts |
| | 필수 | PROG-T06 | PASS | B test_t06_*, F progress.spec.js PROG-T06 |
| F07 | 필수 | DWG-T01 | PASS | B test_drawings.py::test_t01_*, F drawings.spec.js |
| | 필수 | DWG-T02 | PASS | test_drawings.py::test_t02_* |
| | 필수 | DWG-T03 | PASS | B test_t03_*, F drawings.spec.js DWG-T03 |
| | 선택(PDF) | DWG-T04 | PASS | B test_t04_pdf_validation_and_draft_only, F drawings.spec.js |
| | 선택(PDF) | DWG-T05 | PASS | B test_t05_*, F drawings.spec.js DWG-T05 |
| | 필수 | DWG-T06 | PASS | test_drawings.py::test_t06_new_rev_request_approve_issue |
| | 필수 | DWG-T07 | PASS | test_drawings.py::test_t07_issue_reopens_required_gate |
| | 선택(영향) | DWG-T08 | PASS | test_drawings.py::test_t08_link_unlink_and_impact_warning |
| | 필수 | DWG-T09 | PASS | test_drawings.py::test_t09_* |
| | 필수 | DWG-T10 | PASS | B test_t10_*, F drawings.spec.js DWG-T10 |
| F08 | 필수 | APV-T01 | PASS | B test_approvals.py::test_t01_* |
| | 필수 | APV-T02 | PASS | test_approvals.py::test_t02_* |
| | 필수 | APV-T03 | PASS | B test_t03_*, F approvals.spec.js APV-02 (재요청 시 이력 삭제는 Findings #5) |
| | 필수 | APV-T04 | PASS | test_approvals.py::test_t04_t05_full_approval_then_issue |
| | 필수 | APV-T05 | PASS | test_t04_t05_*, test_t05_issue_obsoletes_previous_* |
| | 필수 | APV-T06 | PASS | B test_t06_*, F approvals.spec.js APV-T06 |
| F09 | 필수 | USR-T01 | PASS | B test_users.py::test_t01_*, F users.spec.js USR-T01 |
| | 필수 | USR-T02 | PASS | test_users.py::test_t02_* |
| | 필수 | USR-T03 | PASS | B test_t03_*, F users.spec.js USR-T03 |
| | 필수 | USR-T04 | PASS | test_users.py::test_t04_group_change_applies_immediately |
| | 필수 | USR-T05 | PASS | test_users.py::test_t05_* |
| | 필수 | USR-T06 | PASS | test_users.py::test_t06_* |
| | 필수 | USR-T07 | PASS | test_users.py::test_t07_non_admin_403 |
| | 선택(OTP) | USR-T08 | PASS (조건부) | test_users.py::test_t08_* — secret 비노출, 등록 없이 OTP 켜기는 409. 실제 등록 절차는 D05 미구현 |

## 조치 항목 (심각도순)

| # | 심각도 | Feature | 구분 | 내용 | 근거 | 권장 조치 |
|---|---|---|---|---|---|---|
| 1 | High | 제출물 | 필수 | 실행 방법 README와 완료보고서·PDF·`report_data.json`이 아직 없음. AC는 아니지만 problem_sheet §4 제출 요건 | `README.md`(제목 한 줄), 루트의 `README copy.md`, 보고서 산출물 없음 | 최종 단계에서 README(백엔드·프론트 실행, 시드, 환경변수) 작성 + `extract_usage.py`로 보고서 생성 |
| 2 | ~~Medium~~ RESOLVED | F02/F04/F07 | 필수 | **해결(2026-11-04)**: 호선 상세 요약 탭에 '간트 보기'(plan-gantt)·'목록 보기'(dwg-list, 호선 필터)를 추가하고, 도면 상세 연계 공정 → 도면 호선의 간트로 이동하도록 함. 목업처럼 이동 후 팝업 닫힘. 이미 열린 탭으로 다시 이동하면 shell `navRequest` 신호로 그 탭의 호선 컨텍스트를 복구. 이전 내용: SHELL-T04 FAIL: 팝업에서 다른 화면으로 가는 버튼이 없음. 목업에 있는 호선 상세 요약 탭의 '간트 보기'·'목록 보기'(호선 필터), 도면 상세 연계 공정의 '간트로 이동'이 구현되지 않음 | `frontend/src/screens/hulls/HullDetailModal.vue` 요약 탭, `frontend/src/screens/drawings/DrawingDetailModal.vue` 연계 목록, status.md F07 후속 ② | P8에서 만든 `inject('navigate')`를 재사용해 연결하고, `DrawingList`가 호선 param을 초기 필터로 받도록 수정 + vitest 추가 |
| 3 | Medium | 통합 | 필수 | P4~P8(F06~F09·F03)은 브라우저 E2E를 실행하지 않음. 화면 간 흐름(실적→대시보드, 결재→배포→게이트)은 단위·API 테스트로만 확인됨 | status.md P4~P8 "Playwright 미실행" | 통합 단계에서 핵심 시나리오 E2E 1회: 가입→승인→로그인, 계획→도면 게이트→결재·배포→실적→대시보드 |
| 4 | ~~Medium~~ RESOLVED | F03/F05 | 선택 | **해결(2026-11-04)**: plans.spec.js에 param·재진입 테스트 추가. 남은 부분: `ShellView`의 provide(navigate/navRequest) 연결 자체는 단위 테스트가 없고 브라우저 미확인 → #3 E2E에 포함. 이전 내용: DASH-T05 UNVERIFIED: 대시보드에서 넘어온 호선 번호(`param`)로 `PlanGantt`가 그 호선을 여는 동작에 테스트가 없음 | `frontend/src/screens/plans/PlanGantt.vue:63`, `frontend/src/views/ShellView.vue` provide('navigate') | plans.spec.js에 param 초기 호선 케이스 추가 |
| 5 | Medium | F07/F08 | 필수 | 결재 재요청 시 이전 반려 이력이 삭제되어, "반려 결과는 이력에 남음"(APV-T03)이 재요청 이후에는 깨짐 | `backend/app/services/drawing_service.py:218`, UNIQUE(DrawingId,RevNo,StepNo) | 결정 필요: 목업 그대로 둘지, 반려 이력 보존(스키마 변경)으로 갈지 |
| 6 | Low | F01 | 필수 | 로그인·가입·OTP 화면(`AuthView.vue`)에 프론트 테스트가 없음. OTP 입력 화면은 브라우저에서도 실행된 적 없음(P1 스모크는 OTP 없는 park.pm) | `frontend/src/views/AuthView.vue`, `frontend/src/__tests__/` | auth.spec.js 추가 또는 E2E에서 admin(OTP) 로그인 포함 |
| 7 | Low | F05 | 선택 | 호선 상태 자동 전이는 구현돼 있으나 이를 확인하는 테스트가 없음(UNVERIFIED) | `backend/app/services/plan_service.py:83-93` | 실적 입력→호선 상태 변경 테스트 1건 |
| 8 | Low | F09/F08 | 필수 | 결재 대기(WAIT) 중인 결재자를 삭제하면 결재가 멈춤. 마지막 ADMIN이 자기 권한을 해제하면 관리자가 없어짐 | status.md F09 후속 ①② | 삭제 전 경고 또는 비활성화로 유도, ADMIN 최소 1명 유지 가드 |
| 9 | Low | F03 | 선택 | 대시보드는 처음 열 때만 조회하고 탭을 다시 열어도 새로 고치지 않음 → 다른 탭에서 수정하면 지표가 낡음 | `frontend/src/screens/dashboard/DashboardScreen.vue` onMounted | 탭 활성화 시 다시 조회 |
| 10 | Low | F02 | 선택 | WEATHER-02 실시간 데이터 없음: 날씨 MCP가 구성되지 않아 항상 SAMPLE | decisions.md D07, `backend/app/services/weather_service.py` | 실제 MCP 서버·도구 확보 후 PROVIDERS에 등록 |
| 11 | Low | 결정 | 필수 | 권장안을 적용했지만 사용자 확정이 남은 결정: D03, D04-b, D14, D15, D08(재시드 API 미구현) | `docs/handoffs/decisions.md` | 완료보고서 작성 전에 확정 또는 '권장안 적용'으로 명시 |
