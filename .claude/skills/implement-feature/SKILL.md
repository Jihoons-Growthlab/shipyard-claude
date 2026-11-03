---
name: implement-feature
description: Implement exactly one numbered F01-F09 shipyard feature from docs/features, with focused tests and a short handoff. Run when explicitly invoked for a feature ID.
disable-model-invocation: true
argument-hint: "F01-F09"
---
# Implement one feature / 기능 하나만 구현

1. Get `$ARGUMENTS` feature ID and open `docs/features/00-index.md` + ONLY its `docs/features/Fxx-*.md` spec.
2. Inspect related code by filename/function, not all source. Read needed architecture rules by exact section; reference HTML narrowly only when ambiguous.
3. If a decision in `docs/handoffs/decisions.md` blocks safe implementation, report the blocker and implement independent scope only.
4. Implement minimal backend/frontend/data changes; enforce permissions on the server.
5. Add/run focused tests matching that feature's AC IDs.
6. Update `docs/handoffs/status.md`; if real MCP is used, record actual tool evidence; do not fabricate usage.
7. Return <=10 lines: implementation, modified paths, test summary, blockers, next step. No redundant full-code dump.

한국어: 기능 ID 하나를 기준으로 해당 명세만 읽고 구현·검증한 뒤 인수인계는 10줄 이내로 기록한다.
