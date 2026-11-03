# Migrations (D03 권장안: 순수 SQL 스크립트)

`backend/app/db.py`가 `NNNN_*.sql`을 번호순으로 적용하고 `schema_migrations`에 기록한다(반복 실행 안전).
시드(시스템 코드·그룹·메뉴·데모 계정)는 비밀번호 해시가 필요하므로 `backend/app/seed.py`에서 수행한다.

- 0001_system / 0002_hulls / 0003_plans / 0004_drawings
- 초기화: `cd backend && uv run python -m app.cli init-db --seed`
