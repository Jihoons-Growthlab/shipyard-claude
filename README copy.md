# SWP 조선소 통합관리 시스템 — 명세 패키지

기준 원본: `reference/shipyard_mockup.html` (2026-10-19 고정 기준일이 포함된 단일 HTML / JavaScript 목업).
목표: **FastAPI + Vue 3 + SQLite** 3-Tier 웹 애플리케이션으로 이전하기 위한 상세 요구사항과 구현 순서 정리. **이 패키지는 작동하는 앱이 아니라 기능별 구현 명세와 Claude Code 실행 구조**이다.

## 먼저 확인할 문서

1. `docs/features/00-index.md`: 기능 ID, 메뉴, 읽기 의존성, 작업 순서.
2. `docs/architecture/00-scope.md`: 원본 사실 / 제안 / 미확정의 구분.
3. `docs/handoffs/decisions.md`: 구현 전 확정할 결정.
4. `docs/handoffs/prompts.md`: 짧은 한글·영문 Claude Code 실행 프롬프트.
5. `docs/handoffs/status.md`: 각 기능 구현 상태.

## 권장 순서

1. 원본 명세 검토 후 미확정 사항 결정 → `docs/handoffs/decisions.md`.
2. 인증·권한, 공통 DB, 셸 구축 → 호선 → 공정 계획 → 실적 → 도면/PDF → 결재 → 대시보드 → 날씨.
3. **한 번에 한 파일**의 `docs/features/*.md` 명세를 Claude Code에 전달한다. 다른 기능 명세와 원본 HTML 전체를 반복 입력하지 않는다.
4. 기능마다 테스트/토큰 사용량/Skill·MCP 사용 증거를 기록한다.

## 디렉터리

- `CLAUDE.md`: 상시 로드되는 짧은 프로젝트 지침.
- `.claude/rules/`: 변경 경로별로만 필요한 개발 규칙.
- `.claude/skills/implement-feature/SKILL.md`: 수동 실행형 기능별 개발 절차.
- `.claude/settings.json`: 최소 설정(추가 MCP나 무분별한 자동승인 없음).
- `docs/features/`: 목업에서 추출한 화면·행위·조건·테스트 시나리오.
- `docs/architecture/`: 스키마, 공통 로직, 3-Tier 구조.
- `contracts/`: 제안 API 규칙과 경계 문서(미확정 API는 구현 전 결정).
- `database/migrations/`: 실제 서버 구축 시 생성할 마이그레이션 위치.
- `docs/handoffs/`: 작업 인수인계, 결정사항, 보고서용 근거.
- `tests/`: 기능별 테스트 위치.
- `reference/`: 원본 HTML 보관. 현재 **목업 1개만 첨부됨**.
- `backend/`, `frontend/`: 이번 단계에서 구현하지 않는 코드 디렉터리.

## 주의

목업 자체는 `localStorage` 기반 단일 페이지 데모이며 진짜 JWT, Google Authenticator TOTP, 날씨 MCP 서버 호출, SQLite 파일, 서버 API, 실제 PDF 서버 저장을 구현하지 않는다. **프론트에서 표시한 쓰기 권한만으로 API 접근을 허용하면 안 된다.**

`reference/problem_sheet.html`, `reference/completion_report_sample.html`, `shipyard_schema.sql`은 제공되지 않았다. 본 패키지는 이를 생성했다고 주장하지 않는다. 과제 원문을 받으면 추가 필수 조건을 이 패키지와 대조해야 한다.

## English quick guide

Treat the HTML as observed behavior, not as secure production logic. Build one feature at a time from `docs/features/` and referenced shared documents. Do not read all feature files or the entire original HTML per task. Backend enforces authorization and invariants. Resolve the documented open decisions before implementing security-sensitive paths.
