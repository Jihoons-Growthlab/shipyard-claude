# 미확정 사항 및 제안 결정 로그

이 문서의 `OPEN`은 구현 지시가 아니다. 과제 문제지와 충돌하면 문제지 우선. 선택을 확정할 때 `Decision`을 바꾸고 날짜/근거를 남긴다.

| ID | 쟁점 | 원본 상황 | 권장 설계안 (미확정) | Decision |
|---|---|---|---|---|
| D01 | 필수 평가 범위 | 문제지 미첨부 | problem_sheet와 대조한 뒤 scope 고정 | OPEN |
| D02 | 완료보고서 양식 | 샘플 미첨부 | 제공 샘플 확인 후 보고서 형식 확정 | OPEN |
| D03 | 스키마 DDL | `shipyard_schema.sql` 주석 언급, 파일 없음 | 목업 필드로 최소 DDL 제안 후 대조 | OPEN |
| D04 | 로그인 인증 | 데모 JS 해시와 sessionStorage | 보안 해시 + API 세션 or JWT, 과제 명시 조건 확인 | OPEN |
| D05 | OTP | 고정 123456 | 실제 TOTP를 요구할 경우 Authenticator 연동 | OPEN |
| D06 | 날짜 기준 | TODAY=2026-10-19 고정 | 데모 시드 고정 + 서비스 런타임 날짜 분리 | OPEN |
| D07 | 날씨 MCP | 서버/도구 URL 없음 | 실제 제공 도구 확인 후 서버 어댑터 구성 | OPEN |
| D08 | 데이터 초기화 | 누구나 헤더 버튼으로 전체 초기화 | 개발/데모 환경 ADMIN 전용 + 확인 | OPEN |
| D09 | 공정 실적 게이트 | status는 필수 미배포도면 확인, 입력 API는 별도 gate 확인 없음 | 신규 착수시 gate 강제(수용 테스트 조정) | OPEN |
| D10 | 리비전 최신/과거 ISSUED | `hasIssued`는 과거 ISSUED도 인정 | 원본 재현 vs 현재 유효 발행 Rev 기준 선택 | OPEN |
| D11 | 결재/배포 권한 | 결재함 M33 Write일 경우 배포 표시 | 결재는 본인 지정+순서 확인, 배포는 별도 role 선택 | OPEN |
| D12 | PDF 저장 | 브라우저 IndexedDB | 서버 파일시스템 + DB 메타데이터 권장 | OPEN |
| D13 | PDF 없는 도면 샘플 | 브라우저에서 자동 샘플 PDF | '샘플/미첨부' 명확히 표시, 선택적 샘플 생성 | OPEN |
| D14 | 사용자 삭제 참조 | 로그인 본인 삭제만 막음 | 담당자 참조 유지 위해 탈퇴/중지 또는 SET NULL 정책 | OPEN |
| D15 | 가입 후 권한 | 승인 전 그룹 없음 | 관리자가 승인 시 그룹 선택/지정 | OPEN |
| D16 | 미사용 `TB_SYS_UserBackupCode` | 시드 빈 배열 | 사용처 확인 전 제외 | OPEN |
| D17 | 고정 로그/IP | `127.0.0.1`/`MOCK-PC` | 서버가 실제 접속 정보 기록하되 프록시 신뢰 설정 주의 | OPEN |
| D18 | MCP·Skill 사용 실적 | 평가 조건은 사용자 설명 | 해당 도구를 실제 호출하고 호출 증거 기록 | OPEN |

## 선택 기록 형식

`D09 | 2026-11-XX | DECIDED: ... | reason: ... | affected: F05,F06,tests`.
