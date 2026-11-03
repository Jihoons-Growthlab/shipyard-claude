---
paths:
  - "backend/**"
---
# Backend-only rules
- FastAPI owns RBAC, validation, transactions, and business rules. Never trust Vue-disabled controls.
- Service functions own gate/status/revision decisions; route handlers stay thin.
- Keep code aligned with ONE assigned feature spec; avoid extra dependencies.
- Error body: `{code,message,details}` unless an earlier decision changed it.
- Use parameterized DB access and safe password hashing. No fixed demo OTP in real auth.
