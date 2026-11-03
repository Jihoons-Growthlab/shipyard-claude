# HTTP 계약 인덱스 (DESIGN / 기능별 선택 읽기)

각 feature 문서의 `DESIGN endpoints`가 제안 경로의 기본 계약이다. **API가 목업에 존재한다는 뜻이 아니다.** 기존 사내 과제 지시서가 API 구조를 요구한다면 이를 우선한다.

| 리소스 | 생성/수정/조회 대표 경로 | 문서 |
|---|---|---|
| auth | `/api/auth/login`, `/otp/verify`, `/register`, `/logout`, `/me` | F01 |
| shell | `/api/me/menu`, `/api/weather` | F02 |
| dashboard | `/api/dashboard/summary` | F03 |
| hull | `/api/hulls`, `/api/hulls/{hull_no}/milestones`, `/blocks` | F04 |
| planning | `/api/hulls/{hull_no}/plans`, `/api/plans/{id}/predecessors`, `/drawings` | F05 |
| progress | `/api/plans/{id}/progress/{work_date}` | F06 |
| drawings | `/api/drawings`, `/revisions`, `/pdf`, `/plans` | F07 |
| approval | `/api/approvals/inbox`, `/api/approvals/{id}/decision` | F08 |
| users | `/api/users`, `/api/users/{emp_no}/approve` | F09 |

## 공통 정상/오류 응답

- `GET`: 리소스/배열 JSON. `POST`: 생성 리소스 및 201. `PATCH/PUT`: 변경된 리소스. `DELETE`: 204 권장.
- 오류 형식 제안: `{"code":"PLAN_DEPENDENCY_CYCLE","message":"선행 공정이 순환 구조를 만듭니다.","details":{}}`.
- 401 = 인증없음, 403 = 권한없음, 404 = 없음, 409 = 중복/변경상태충돌, 422 = 데이터 검증 불가.
- idempotent: 일별 실적 UPSERT는 `(plan_id,work_date)` 유일 제약을 DB에서도 적용. 도면·공정 링크도 복합 유일 키.
- 자원 소속 검증: plan.block.hull / drawing.block.hull / link drawing.hull=plan.hull을 서버에서 검사(DESIGN).
- `GET /api/weather`는 `source: "live"|"sample"`을 추가해 출처 표시 가능(DESIGN).
- PDF는 multipart 업로드와 권한 검증된 octet stream/PDF 다운로드를 사용. 원본 데이터의 `idb:` prefix를 API 응답으로 노출하지 않음.

## Swagger / OpenAPI

OpenAPI 전체 YAML을 중복 작성하지 않았다. Pydantic models로 FastAPI가 OpenAPI를 생성하게 하여 명세 이중관리 토큰을 줄인다. 각 기능 구현 시 feature 문서의 필드/검증/오류를 API 테스트로 검증한다.
