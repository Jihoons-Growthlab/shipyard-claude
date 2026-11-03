# F01 인증 · 회원가입 · OTP · 세션

- **OBS**: `showAuth`, `validateUser`, `ACT.login`, `ACT.verifyOtp`, `ACT.signup`, `enterApp`, `logout`, `boot` (533~618, 619~628행).
- **연계**: F02 메뉴 권한, F09 관리자 승인, 03-business-rules BR-09.
- **DESIGN endpoints**: `POST /api/auth/login`, `POST /api/auth/otp/verify`, `POST /api/auth/register`, `POST /api/auth/logout`, `GET /api/auth/me`; 필요시 refresh endpoint(OPEN).

## 기능별 요구

| ID | 동작 | 입력 | 서버 처리/응답 |
|---|---|---|---|
| AUTH-01 | 로그인 화면 | id, password | 존재 계정/비밀번호 확인; pending/rejected/disabled 로그인 거절; approved만 허용 |
| AUTH-02 | 2차 인증 분기 | OTP 6자리 | TOTP enabled면 OTP pending 상태로 전환, 검증 성공 뒤만 정식 세션 발급 |
| AUTH-03 | 회원가입 화면 | 성, 이름, 생일, 전화번호, 이메일, 아이디, 비밀번호, 확인 | 검증 후 pending 생성, 관리자 승인을 기다린다는 메시지 |
| AUTH-04 | 로그인/로그아웃 접근 로그 | 사용자, IP, 시각 | `TB_SYS_LogAccess`: login 시 추가, logout 시 종료 일시 기록 |
| AUTH-05 | 세션 복구 | 저장된 세션 | 사용자 현재 상태 approved 및 유효 세션 재검사; F02 화면 복구 |

## OBS 입력 검증

- 성·이름 필수, 생년월일 필수.
- 이메일 기본 정규식 검사; 전화번호 `^01\d-?\d{3,4}-?\d{4}$`; 아이디 `[A-Za-z0-9._-]{4,20}`.
- 비밀번호 8자 이상; 가입 시 비밀번호 확인 동일.
- 중복 아이디/이메일/전화(전화번호는 숫자만 비교) 불허.
- 기존 회원 수정에서는 비밀번호 빈 값이면 유지(F09).
- 로그인 실패: '아이디 또는 비밀번호가 올바르지 않습니다'. 계정 상태별 안내 메시지 제공.
- OTP 데모는 `123456` 고정값으로만 검증함. **실제 Google Authenticator TOTP 구현이 아님**.

## DESIGN 구현 및 보안 경계

- 단순 해시 `hp()`(djb2 유사)를 금지; Argon2id 또는 충분히 안전한 패스워드 해시 사용.
- JWT 방식 선택 시 access/refresh 수명, 보관 위치, 로테이션/폐기 정책을 먼저 확정. 가능하면 HttpOnly Secure SameSite 쿠키 세션 전략도 검토.
- 실제 TOTP를 요구하면 시크릿 생성/QR 등록/6자리 시차 허용/재사용 방지/비활성화 절차 필요. 원본의 고정 secret과 123456을 운영에 이식 금지.
- 로그인·OTP 시도 횟수 제한, 실패/성공 응답의 민감 정보 노출 제한.
- 가입 사용자는 그룹이 없고 approved 전 로그인할 수 없음; 승인 이후 기본 그룹 결정(OPEN).
- 인증이 필요한 endpoint는 만료/중지/삭제된 사용자 세션을 거절.

## AC / 테스트

- AUTH-T01 올바른 일반 approved 사용자는 로그인 후 대시보드를 열 수 있다.
- AUTH-T02 승인 대기·반려·중지 사용자는 정확한 상태 안내와 함께 거절된다.
- AUTH-T03 TOTP 활성 계정은 1차 인증만으로 보호 API에 접근할 수 없다.
- AUTH-T04 아이디/이메일/전화 중복, 잘못된 형식, 비밀번호 확인 불일치 각각 등록 거절.
- AUTH-T05 회원 가입 후 상태는 pending, 미승인 계정은 로그인 불가.
- AUTH-T06 로그아웃 및 세션 만료 시 보호 API는 401을 반환.
- AUTH-T07 로그인·로그아웃 로그의 사용자는 해당 계정과 매칭된다.

## OPEN

- JWT 명시 요구 여부/쿠키 정책, 실제 TOTP 필수 여부, 가입 승인 후 기본 그룹과 2차 인증 설정 절차. `docs/handoffs/decisions.md` 참고.
