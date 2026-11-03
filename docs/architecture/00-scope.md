# 범위·증거·결정 원칙

## 소스 현황

- **OBS (원본 확인)**: `reference/shipyard_mockup.html`, 1328줄, 단일 HTML/CSS/JS. 고정 `TODAY='2026-10-19'`, 데이터 `localStorage`, 세션 `sessionStorage`, 파일 `IndexedDB`.
- **DESIGN (제안)**: 사용자 요청에 따른 FastAPI + Vue 3 + SQLite 구조, REST API, 서버 검증·권한·트랜잭션·파일 저장 설계. 원본에서 이미 존재하는 구현으로 오인하면 안 된다.
- **OPEN (미확정)**: 과제 지시서(`problem_sheet.html`)와 샘플 보고서, 별도 `shipyard_schema.sql`, 토큰 평가 산식, JWT/TOTP 실제 보안 정책, 날씨 MCP 서버, 기준일 정책.

## 명세 해석 정책

1. 목업의 텍스트/필드/기능/계산식은 OBS로 기록한다.
2. 3-Tier 구현이 필요한 API, DB 키, 에러 코드, 인증 토큰 전략은 DESIGN으로 기록한다.
3. 원본이 모호하거나 보안상 데모 로직을 그대로 복제할 수 없으면 OPEN에 기록하고 구현 전에 선택한다.
4. `docs/features/*.md`의 Acceptance Criteria는 제품 동작을 테스트할 최소 계약이다. 원본 재현과 안전 개선이 충돌하면 `docs/handoffs/decisions.md`에 선택 및 이유를 남긴다.
5. 소스 함수/행 번호는 HTML의 실제 파일 기준. 파일 편집 후에는 줄 번호가 달라질 수 있다.

## 제외 / 과도한 구현 금지

- 이슈관리 메뉴/데이터: 원본의 `purgeIssue`는 이전 이슈관리 데이터를 명시적으로 제거함(409~414행). 신규 이슈 시스템 구현 금지.
- 블록관리 독립 메뉴, 사용자 비밀번호 찾기, 이메일 인증, 실제 CAD/DWG 렌더링, 작업지시, 알림/메시징, 감사 대시보드, 외부 ERP 연동: 목업에 없음.
- 샘플 PDF는 실도면이 아니다. UI 동등성 테스트용 샘플과 실제 업로드 파일을 구분한다.

## 메뉴와 화면

- 화면 메뉴(7): `dashboard` / `hull-list` / `plan-gantt` / `progress` / `dwg-list` / `dwg-approval` / `user-mgmt`.
- 팝업(2): `hull-detail` / `dwg-detail`.
- 그룹 루트 메뉴: 호선관리(M10), 공정관리(M20), 도면관리(M30), 시스템(M90); 기본 화면 M00.
- 소스: `seed()` 285~297행, 화면 객체 809~1320행.

## 구현 범위 외에서 반드시 확인할 사항

- 인증 방식: JWT/세션쿠키, 만료/갱신/로그아웃, 실제 TOTP 등록·복구.
- 날짜: 목업 고정 2026-10-19을 시드·데모용으로 유지할지, 운영 환경에서는 현재 날짜로 전환할지.
- 권한: 원본 `ADMIN/PROC/DWG/VIEW`, 메뉴별 `View/Write/Admin`; 승인·배포 및 회원관리 API의 세부 권한.
- PDF: SQLite BLOB vs 파일시스템 + DB 메타데이터; 권장 사항은 파일시스템 저장 + 메타데이터.
- 초기화: 데모 전용 관리자 동작인지 전체 사용자용 기능인지.
