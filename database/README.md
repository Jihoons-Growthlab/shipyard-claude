# Database

소스에서 확인한 테이블/필드: `docs/architecture/02-data-model.md`.
실제 SQL 정의 `shipyard_schema.sql`은 **첨부되지 않음**. 목업 객체에서 추출한 필드와 제안 PK/FK를 토대로 구현 시 migration 작성.

## 마이그레이션 순서 제안

1. `0001_system`: users, groups, codes, menus, access logs.
2. `0002_hulls`: Hull, Milestone, Block.
3. `0003_plans`: Proc, Plan, PlanDep, Progress.
4. `0004_drawings`: Drawing, Revision, Approval, PlanLink, PDF metadata.
5. `0005_seed_demo`: 단일 테스트/데모용 시드와 고정 기준일, 운영 프로덕션 데이터와 분리.

실제 도구(Alembic/SQL scripts)는 과제 조건 확인 후 결정. `migrations/`에는 정해진 도구의 실행 가능 파일만 둔다. FK CASCADE 및 도면의 블록 연결 해제는 `BR-08`과 일치시킨다.
