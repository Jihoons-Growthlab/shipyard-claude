---
paths:
  - "database/**"
---
# Database-only rules
- Do not invent an unseen `shipyard_schema.sql`. Use `docs/architecture/02-data-model.md` as a provisional source.
- Enable SQLite foreign keys. Preserve BR-08: deleting a block clears drawings.BlockId rather than deleting drawings.
- Migrations must be repeatable in a clean test environment; preserve constraints and uniqueness.
