---
paths:
  - "tests/**"
---
# Test-only rules
- Verify the currently assigned feature's AC IDs plus direct endpoint authorization checks.
- Use isolated temporary SQLite DB and deterministic clock/seed where required.
- Prefer small targeted commands and concise output; broaden tests only for integration phase.
