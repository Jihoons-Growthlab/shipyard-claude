# 실제 Claude Code Skill · MCP 사용 증거

> 실제 실행한 항목만 기록. Phase 0(2026-11-03)까지 Skill 사용 없음.

| Date/Time | Type | Name/Tool | Input scope | Result | Evidence path |
|---|---|---|---|---|---|
| 2026-11-03T22:45+09:00 | MCP | sqlite (db-mcp-server 1.2.1) | 세션 시작 연결 | FAILED: CONNECTION_CLOSED (원인: mcp 2.x 비호환, import 오류) | docs/handoffs/logs/phase0-sqlite-mcp.txt |
| 2026-11-03T22:5x+09:00 | MCP | sqlite (`--with mcp<2`) | initialize 스모크 + `claude mcp list` | SUCCESS: Connected (세션 내 tool 호출은 /mcp 재연결 후) | docs/handoffs/logs/phase0-sqlite-mcp.txt |
| 2026-11-03T23:02+09:00 | MCP | playwright (browser_navigate/fill_form/click/snapshot/close) | localhost:5173 park.pm 로그인→셸 메뉴→로그아웃 | SUCCESS (최초 실행에서 /api/auth/me 500 발견→수정 후 통과) | docs/handoffs/logs/p1-playwright/, logs/p1_end_usage.json |
| 2026-11-03 | Skill | implement-feature | P1 | NOT INVOKED: `disable-model-invocation: true`라 모델 호출 불가 — 절차만 수동 준수 | - |
| 2026-11-03 | MCP | context7 / sqlite | P1 | NOT USED (불필요; DB 확인은 sqlite3 CLI) | - |
| 2026-11-03T23:30+09:00 | Skill | implement-feature (사용자 `/implement-feature F04`) | F04 | SUCCESS: Skill 도구로 로드, 절차 준수 | logs/p2_end_usage.json (Skill: implement-feature 1) |
| 2026-11-03T23:33+09:00 | MCP | playwright (navigate/fill_form/click/handle_dialog/snapshot/close) | park.pm: 호선 등록(날짜역순 400→정상 201)·5개 마일스톤 확인·수정·블록 추가·중복 409·블록 삭제·호선 삭제 | SUCCESS, DB 잔여/FK 위반 0 | docs/handoffs/logs/p2-playwright/ |
| 2026-11-03 | MCP | context7 / sqlite | P2 | NOT USED (불필요) | - |
| 2026-11-03T23:52+09:00 | Skill | implement-feature (사용자 `/implement-feature F05`) | F05 | SUCCESS | logs/p3_end_usage.json (Skill: implement-feature 누적 2) |
| 2026-11-03T23:53+09:00 | MCP | playwright (navigate/fill_form/click/select_option/handle_dialog/snapshot/close, 28회 중 1회 셀렉터 오류) | park.pm: 8001 간트 표시 → 8004 공정 추가(READY) → DRAFT 필수도면 연계(PLAN·📐) → 선행 지연 확인 취소(무변경)/확인(저장) → 연계 해제(READY) → 공정 삭제 | SUCCESS, FK 위반 0 | docs/handoffs/logs/p3-playwright/ |
| 2026-11-03 | MCP | context7 / sqlite | P3 | NOT USED (DB 확인은 sqlite3 CLI) | - |

| 2026-11-04 | Skill / MCP | implement-feature / (없음) | P8 F03 | Skill 도구 미호출(붙여넣은 텍스트로 요청, 절차만 수동 준수), MCP NOT USED | - |
| 2026-11-04T00:39+09:00 | MCP | playwright (navigate/click/snapshot/select_option/network_requests/evaluate) | park.pm 로그인 → 헤더 날씨 울산 SAMPLE(샘플 배지, LIVE 없음) → 거제 선택(GET /api/weather?region=거제 200, localStorage swp_region=거제) → 로그아웃 시 위젯 제거 | SUCCESS (콘솔 오류는 기존 favicon 404뿐) | docs/handoffs/logs/p9-playwright/ |
| 2026-11-04 | MCP | 날씨 MCP | P9 F02 | NOT AVAILABLE: .mcp.json에 날씨 MCP 서버 없음 → 가상 서버 미설정(명세 금지), SAMPLE 폴백 | - |
| 2026-11-04 | MCP | context7 / sqlite | P9 | NOT USED (불필요) | - |
예: `2026-11-XXT..+09:00 | MCP | 실제서버명/실제도구명 | region=거제 | success | docs/handoffs/logs/...`.

과제 기준에 따라 도구의 실제 입출력 로그, 프롬프트, 시점, 토큰 사용량을 완성보고서에 기록한다. 로그인 키·비밀번호·MCP 비밀 토큰 등은 기록에서 제외.
