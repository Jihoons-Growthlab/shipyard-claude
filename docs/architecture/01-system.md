# 3-Tier 구조 및 공통 실행 명세 (DESIGN)

## 구성

```text
Vue 3 SPA (frontend)
  └── HTTPS/JSON multipart → FastAPI routes + auth/RBAC + services (backend)
                                  ├── SQLite (database/migrations)
                                  ├── PDF storage (local path + metadata)
                                  └── weather adapter → configured MCP-backed provider
```

- Presentation: Vue 3 Composition API, Vue Router, 화면/모달/탭별 상태 보존, 서버 상태 호출. HTTP 호출 로직은 단일 API client 모듈 사용.
- API: FastAPI Pydantic schemas, 인증/인가 dependencies, 서비스 계층과 DB 접근 계층 분리. 모든 쓰기는 서버 검증·DB 트랜잭션 처리.
- DB: SQLite, 외래키 `PRAGMA foreign_keys=ON`, datetime UTC 저장 + 사용자 로컬 표시, 마이그레이션 버전 관리. `busy_timeout`, 테스트용 별도 DB 사용.
- File: PDF 콘텐츠와 메타데이터를 DB와 일관되게 취급. 업로드 파일은 직접 URL로 공개하지 않고 권한 확인 API로 조회.
- Weather: 날씨는 DB 영속화 대상 아님. 서버의 MCP 어댑터 호출 실패 시 명시적 샘플 데이터 표시(요구시), LIVE와 SAMPLE을 반드시 구분.

## 화면 이동

- 로그인 성공 → 권한 허용 화면의 최초 탭 또는 대시보드.
- 트리 메뉴 펼침/접힘, 탭 중복 방지(`screen + ':' + param`), 최대 12개, 활성 탭 전환, 다른 탭 닫기.
- 팝업: 호선/도면 상세. 신규는 각각 `new` 키; Esc/닫기 지원.
- 목록 필터/선택/간트 스크롤은 탭별로 보존. 세션 재시작 시 권한 검증 후 탭 복구.
- 클라이언트에서 버튼 비활성화는 편의 기능뿐이며, 서버는 별도로 권한 확인.

## 공통 데이터 계약

- 요청/응답: JSON, UTF-8, `snake_case` API 필드 사용 시 DB의 PascalCase 매핑을 어댑터에서 일원화. 같은 자원을 화면별로 다른 필드명으로 표현하지 않는다.
- 오류: 400(유효성), 401(미로그인), 403(권한없음), 404(없음), 409(중복/상태 충돌), 422(형식 오류), 500(예상치 못한 오류).
- 날짜: `YYYY-MM-DD`, 일시: ISO 8601, null/빈 문자열의 API 의미 정리.
- 조회: 목업에 페이지네이션은 없으므로 과제 요건 없으면 추가하지 않는다.
- 트랜잭션: 호선/블록/공정/도면 삭제와 연계 삭제는 일관적으로 처리.
- 계산: `docs/architecture/03-business-rules.md`의 서버 함수만 신뢰; UI에서는 계산 결과만 표시.

## 권한 게이트 (원본 + 권장 보완)

- 원본 `myGbn`: `View=1`, `Write=2`, `Admin=3`; 동일 사용자 여러 그룹 중 최고 등급 적용.
- 상세 팝업은 각각 목록 권한(M11/M31)을 상속.
- 클라이언트 메뉴 숨김/쓰기 버튼 비활성화 구현에 더해 API에서 리소스 권한 확인.
- 미승인/반려/중지 사용자 로그인 거절 및 기존 세션 무효화 정책은 서버에서 검증.

## API 개발 순서

`health`(서버 준비 확인) → `auth/me` + RBAC → master/code/seed → hull/block/milestone → plan/dependency → progress → drawing/revision/file/link → approval → dashboard aggregates → weather adapter.

## 환경설정 (키 이름은 제안이며 OPEN)

`DATABASE_URL`, `APP_SECRET`, `TOKEN_TTL`, `UPLOAD_DIR`, `WEATHER_PROVIDER`, `WEATHER_MCP_ENDPOINT`. 비밀값/실토큰은 커밋하지 않는다. `.env.example`은 실제 구현 시 추가.
