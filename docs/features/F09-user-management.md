# F09 회원관리 · 승인 · 그룹 · OTP 설정

- **OBS**: `SCREENS['user-mgmt']`, `ACT.usrSave/Del/Approve` 1286~1320, 검증 `validateUser` 533~544.
- 공통: F01 인증, BR-09 권한.
- **DESIGN endpoints**: `GET/POST /api/users`, `GET/PATCH/DELETE /api/users/{emp_no}`, `POST /api/users/{emp_no}/approve`, `GET /api/auth-groups`.
- 권한: M91 Admin 전용. (원본은 `canWrite(M91)` 방식으로 버튼 보호, API에서는 관리자 확인.)

## USR-01 상하 분할 목록

- 상단 검색: 상태(status), 아이디/이름/이메일/전화번호 키워드, 조회/초기화, 전체 회원 수/승인 대기 수.
- 컬럼: 아이디, 이름, 이메일, 전화, 생년월일, 상태, OTP 사용, 권한그룹, 가입일.
- 목록 행 클릭 시 하단 폼 선택. 신규 버튼은 하단 폼을 새 사용자 기본값(status approved, OTP off)으로 전환.

## USR-02 생성/수정

| 필드 | OBS 규칙 |
|---|---|
| 성·이름 | 필수 |
| 생년월일 | 필수 date |
| 전화 | 필수 / 정규식 / 숫자만 정규화 중복 확인 |
| 이메일 | 필수 / 기본 이메일 정규식 / 중복 불가 |
| 아이디 | 필수, 4~20자 영어/숫자/._-, 신규만 수정 가능 |
| 비밀번호 | 신규 8자 이상, 수정시 비우면 그대로 유지 |
| status | pending/approved/rejected/disabled |
| grp | ADMIN/PROC/DWG/VIEW 또는 없음, **현재 UI는 하나의 그룹만 선택** |
| totp | checkbox, 데모용 시크릿 고정(운영 사용 금지) |
| created_at | readonly |

- 신규: id='u-'+emp_no, status 지정, auth_provider=local, 표시명=성+이름.
- 수정: 사용자의 개인 정보/상태/OTP, 선택 그룹을 저장. 기존 그룹 할당을 삭제하고 지정 그룹 하나로 교체.
- 본인 수정 시 헤더 및 메뉴를 다시 그림.

## USR-03 삭제/가입승인

- 로그인 중인 본인 계정은 삭제 금지.
- 삭제 확인 후 사용자 및 AuthUser 할당 제거.
- 승인 대기(`pending`) 회원 선택 시 '가입 승인' 버튼; 클릭하면 approved 전환.
- 원본은 삭제 시 담당자 참조 Plan/Drawing 등 이력의 참조 재정리 로직이 없음. SQL 제약 및 사용자 비활성화 정책을 정해야 함(OPEN).

## AC / 테스트

- USR-T01 상태+키워드 필터/초기화와 상하 선택 폼.
- USR-T02 중복 아이디/메일/전화 거절, 잘못된 전화/메일, 암호 길이 거절.
- USR-T03 비밀번호 미입력 수정시 기존 해시 불변.
- USR-T04 그룹 변경이 메뉴 권한에 반영되며 서버 직접 API도 즉시 반영.
- USR-T05 pending 회원 승인 후 로그인 가능.
- USR-T06 로그인 중 사용자 삭제 거절.
- USR-T07 ADMIN 외 계정 회원관리 API 403.
- USR-T08 실제 TOTP 설정을 제공한다면 2차 인증 secret은 별도 등록/검증 절차를 거치며 응답에서 비노출.

## OPEN

- 관리자만 OTP를 강제로 설정할 수 있는지, 가입 승인 시 기본 그룹, 사용자 삭제 vs 비활성화, 담당자 FK의 ON DELETE 정책, 복수 그룹 지원.
