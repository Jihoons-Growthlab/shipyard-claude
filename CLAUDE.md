# SWP Shipyard

Stack: FastAPI, Vue 3, SQLite.
Source: reference/shipyard_mockup.html.

## UI reference workflow
- Before UI creation or visual changes, read `reference/UiImages/README.md`.
- Open the relevant PNG files with an image-capable tool before editing; filenames alone are not visual evidence.
- Use those images as the visual reference while preserving feature specs, API behavior, and authorization.
- Follow the comparison and validation checklist in that README; report any images or browser checks you could not inspect.

## Workflow
- Implement only the requested feature.
- Read its spec in docs/features/ and required dependencies.
- Inspect source files narrowly; avoid full-file dumps.
- Reuse existing services, models, and components.
- No speculative features or unrelated refactors.
- Run focused tests.
- Update docs/handoffs/status.md.
- Keep final summaries under 10 lines.

## Boundaries
- Backend owns validation, authorization, and business rules.
- Follow established contracts and database schema.
- Ask only when an unresolved decision blocks implementation.
- Do not invent MCP usage or test results.
