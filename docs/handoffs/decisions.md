# 미확정 사항 및 제안 결정 로그

이 문서의 `OPEN`은 구현 지시가 아니다. 과제 문제지와 충돌하면 문제지 우선. 선택을 확정할 때 `Decision`을 바꾸고 날짜/근거를 남긴다.

| ID | 쟁점 | 원본 상황 | 권장 설계안 (미확정) | Decision |
|---|---|---|---|---|
| D01 | 필수 평가 범위 | 문제지 미첨부 | problem_sheet와 대조한 뒤 scope 고정 | RESOLVED-BY-SHEET: 필수/선택 범위 = problem_sheet §3 |
| D02 | 완료보고서 양식 | 샘플 미첨부 | 제공 샘플 확인 후 보고서 형식 확정 | RESOLVED-BY-SHEET: reference/completion_report_sample.html 양식 |
| D03 | 스키마 DDL | `shipyard_schema.sql` 주석 언급, 파일 없음 | 목업 필드로 최소 DDL 제안 후 대조 | OPEN[필수] 권장: 순수 SQL 스크립트(0001~0005) — 테이블 수 적고 Alembic 설정 비용 절감 |
| D04 | 로그인 인증 | 데모 JS 해시와 sessionStorage | 보안 해시 + API 세션 or JWT, 과제 명시 조건 확인 | RESOLVED-BY-SHEET: JWT (problem_sheet §3). 세부(D04-b)는 OPEN |
| D05 | OTP | 고정 123456 | 실제 TOTP를 요구할 경우 Authenticator 연동 | OPEN[선택] Phase S에서 결정 |
| D06 | 날짜 기준 | TODAY=2026-10-19 고정 | 데모 시드 고정 + 서비스 런타임 날짜 분리 | RESOLVED-BY-SHEET: 기준일 2026-10-19 고정, 목업 시드·데모계정 사용 |
| D07 | 날씨 MCP | 서버/도구 URL 없음 | 실제 제공 도구 확인 후 서버 어댑터 구성 | OPEN[선택] Phase S에서 결정 |
| D08 | 데이터 초기화 | 누구나 헤더 버튼으로 전체 초기화 | 개발/데모 환경 ADMIN 전용 + 확인 | OPEN[필수] 권장: ADMIN 전용 재시드 API(개발용) — 원본은 누구나 초기화 가능해 보안상 부적절 |
| D09 | 공정 실적 게이트 | status는 필수 미배포도면 확인, 입력 API는 별도 gate 확인 없음 | 신규 착수시 gate 강제(수용 테스트 조정) | OPEN[필수] 권장: 첫 실적(착수) 입력에도 게이트 강제 — 서버 규칙 ① 우회 방지 |
| D10 | 리비전 최신/과거 ISSUED | `hasIssued`는 과거 ISSUED도 인정 | 원본 재현 vs 현재 유효 발행 Rev 기준 선택 | OPEN[필수] 권장: 과거 ISSUED Rev도 인정 — 원본 hasIssued 동작 재현 |
| D11 | 결재/배포 권한 | 결재함 M33 Write일 경우 배포 표시 | 결재는 본인 지정+순서 확인, 배포는 별도 role 선택 | CONFIRMED(2026-11-04 사용자): 도면 편집·리비전·결재요청·배포=M31 Write, 승인/반려=M33 Write+지정된 현재 결재자, 배포는 결재 완료 필수 |
| D12 | PDF 저장 | 브라우저 IndexedDB | 서버 파일시스템 + DB 메타데이터 권장 | OPEN[선택] Phase S에서 결정 |
| D13 | PDF 없는 도면 샘플 | 브라우저에서 자동 샘플 PDF | '샘플/미첨부' 명확히 표시, 선택적 샘플 생성 | OPEN[선택] Phase S에서 결정 |
| D14 | 사용자 삭제 참조 | 로그인 본인 삭제만 막음 | 담당자 참조 유지 위해 탈퇴/중지 또는 SET NULL 정책 | OPEN[필수] 권장: 본인 삭제 금지 + 담당자 참조 SET NULL — 원본 규칙 유지·FK 무결성 |
| D15 | 가입 후 권한 | 승인 전 그룹 없음 | 관리자가 승인 시 그룹 선택/지정 | OPEN[필수] 권장: 관리자 승인 시 그룹 지정 필수 — 승인 후 메뉴 접근 즉시 가능 |
| D16 | 미사용 `TB_SYS_UserBackupCode` | 시드 빈 배열 | 사용처 확인 전 제외 | OPEN[범위외] 권장: 제외 |
| D17 | 고정 로그/IP | `127.0.0.1`/`MOCK-PC` | 서버가 실제 접속 정보 기록하되 프록시 신뢰 설정 주의 | OPEN[범위외] 권장: 요청 IP 기록 |
| D18 | MCP·Skill 사용 실적 | 평가 조건은 사용자 설명 | 해당 도구를 실제 호출하고 호출 증거 기록 | OPEN[필수] 권장: tool-evidence.md에 실호출만 기록 + extract_usage 교차확인 |

| D04-b | JWT 세부 정책 | 해당 없음 | 권장: access token 8h, refresh 없음, 로그아웃=클라이언트 폐기 — 과제는 JWT만 요구 | OPEN[필수] |

> 2026-11-03 Phase 0: 위 RESOLVED-BY-SHEET 외 OPEN[필수] 항목은 권장안만 제시, 사용자 확정 대기.

## 선택 기록 형식

`D09 | 2026-11-XX | DECIDED: ... | reason: ... | affected: F05,F06,tests`.

## P1 적용 기록 (권장안 적용, 사용자 최종 확정 대기)

- D03 | 2026-11-03 | APPLIED: 순수 SQL 0001~0004 + `schema_migrations`, 시드는 `backend/app/seed.py`(Argon2 해시 필요) | affected: database, backend
- D04-b | 2026-11-03 | APPLIED: HS256 access 8h, refresh 없음, sessionStorage 보관. 로그아웃은 `TB_SYS_LogAccess.LogoutDt` 기록으로 서버측 토큰 무효화(AUTH-T06) | affected: F01
- D15 | 2026-11-03 | APPLIED: `POST /api/users/{emp_no}/approve {groups:[..]}` 그룹 1개 이상 필수, M91 Write 필요 | affected: F01,F09
- D05 관련 | 2026-11-03 | APPLIED(최소): 고정 123456 제거, RFC6238 TOTP(±1 step, 재사용 차단, 토큰당 5회 실패 시 429). 시드 TOTP secret은 목업 데모값(API 비노출). 등록/QR은 D05(Phase S) | affected: F01
- D10 | 2026-11-03 | APPLIED: BR-02 게이트는 과거 ISSUED Rev 존재 시 통과(원본 hasIssued 재현), APPROVED 단독은 미통과 | affected: F05,F07
- F05 OPEN 처리 | 2026-11-03 | APPLIED: 상태 재산정은 DAG 2회 순회 대신 단일 패스(DONE은 진척률만으로 결정되므로 결과 동일), LagDays=0 고정, 자동 일정 밀기 없음 | affected: F05
- D09 | 2026-11-04 | APPLIED: 원본 progSave 재현 — 실적 입력 API는 도면 게이트를 검사하지 않음(사용자 지시: 명시 요구와 충돌 없으면 원본 동작). 역행(60→50) 허용, 공수/인원 음수 제한 없음(OBS), 작업자는 승인 회원만 | affected: F06
- D12 | 2026-11-04 | APPLIED: PDF는 서버 파일시스템(SHIPYARD_FILE_DIR, 기본 storage/drawings, gitignore), FileId=서버 생성 32hex, FileNm=원본명. 업로드=raw body(ext/MIME + %PDF- 헤더 + 30MiB 스트리밍 상한, RBAC 선검사). 새 파일은 커밋 전 기록·실패 시 제거, 교체/삭제 파일은 커밋 후 제거(도면·호선 삭제 포함, BR-08) | affected: F07,F04
- D13 | 2026-11-04 | APPLIED: 파일 없는 리비전은 GET pdf 404 NO_FILE, UI는 '샘플 PDF (미업로드)' 라벨 박스 표시(서버 샘플 생성 없음) | affected: F07
- D11(잠정) | 2026-11-04 | APPLIED-INTERIM: 결재 요청·배포 API는 M31 Write. 승인/반려 권한(지정자 본인·순서)은 F08에서 확정 | affected: F07,F08
- F07 OPEN | 2026-11-04 | APPLIED: CurrentRevNo=0은 배포 이력 없음(목록 Rev0 표기 원본 유지), 배포 경쟁은 BEGIN IMMEDIATE + APPROVED 상태 재확인으로 직렬화, 결재 재요청 시 해당 Rev 결재행 교체(목업 revRequest) | affected: F07
- D11 | 2026-11-04 | CONFIRMED: 도면 편집·리비전·결재요청·배포 = M31 Write. 승인/반려 = M33 Write + ApproverEmpNo 본인 + 이전 단계 모두 APPROVE + 최신 Rev가 REVIEW(아니면 403/409). 배포 = M31 Write + RevStatus APPROVED + 해당 Rev 결재행 전부 APPROVE(409 APPROVAL_INCOMPLETE) | reason: 사용자 확정 | affected: F07,F08,tests
- D14 | 2026-11-04 | APPLIED(권장안): 본인 삭제 409 SELF_DELETE, 삭제 시 AuthUser CASCADE·담당자/작성자/결재자/로그 참조 SET NULL(기존 스키마 FK) | affected: F09
- F09 권한 | 2026-11-04 | APPLIED: /api/users(목록·상세·생성·수정·삭제·approve/reject)와 /api/auth-groups는 M91 Admin(명세 'M91 Admin 전용'; 기존 approve의 M91 Write를 Admin으로 상향, 시드상 ADMIN만 M91 보유라 동작 동일). /api/users/options는 기존대로 로그인 사용자 | affected: F01,F09
- F09 OPEN 처리 | 2026-11-04 | APPLIED: 그룹은 단일 선택(기존 할당 교체, '없음' 허용), 승인 시 그룹 필수(D15 유지). OTP: 데모 고정 secret 신규 발급 안 함 — secret 없는 사용자 OTP 켜기 409 OTP_NOT_ENROLLED, 끄기는 secret 유지(재활성 가능), secret/hash 응답 비노출(실 등록은 D05) | affected: F09
- D07 | 2026-11-04 | APPLIED(부분): 날씨는 문제지 §3 '선택' 범위. GET /api/weather?region=울산|거제|목포(로그인 사용자, 메뉴 권한 무관, DB 미저장) 서버 어댑터 + 공급자 레지스트리(WEATHER_PROVIDER, 기본 빈값). 날씨 MCP 서버가 구성돼 있지 않아 실 공급자 미연결 → 항상 SOURCE=SAMPLE+사유, 공급자 실패·형식오류도 SAMPLE(LIVE 허위표기 금지). 지역은 브라우저별 localStorage(swp_region, 목업 동일) | remaining OPEN: 실제 날씨 MCP 서버/도구 ID | affected: F02
