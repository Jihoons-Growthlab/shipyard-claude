# Claude Code 최소 실행 프롬프트 — 한국어 / English

## 구현 (Korean)

```text
/implement-feature F04
F04만 구현해. docs/features/F04-hulls.md와 직접 필요한 공통 규칙만 읽고, AC 테스트를 추가·실행해. 무관한 파일·전체 HTML은 읽지 마. 변경 파일/테스트/미결정만 10줄 이내로 보고해.
```

## Implementation (English)

```text
/implement-feature F04
Implement F04 only from docs/features/F04-hulls.md and directly required shared rules. Add/run its AC tests. Avoid unrelated files and the full HTML. Report changed files, tests, and blockers in <=10 lines.
```

## 사실 확인 시 (Korean)

```text
F05의 PLAN-04만 원본과 대조해. reference/shipyard_mockup.html에서 gate(), linkAdd, linkDel 함수의 관련 부분만 읽고 차이점 5줄 이내로 알려줘. 코드는 변경하지 마.
```

## Source verification (English)

```text
Verify PLAN-04 only. Inspect only gate(), linkAdd and linkDel in reference/shipyard_mockup.html. Summarize discrepancies in <=5 lines; make no code changes.
```

## 기능 검증 (Korean)

```text
F07의 DWG-T01~T10 테스트만 실행해. 실패한 테스트의 핵심 원인만 제시하고 해당 범위를 최소 수정해.
```

## Feature verification (English)

```text
Run DWG-T01..T10 for F07 only. Report root causes of failures; apply the smallest scoped fixes.
```

### 사용 방법

F04를 F01~F09 중 실제 기능 번호로 바꿔 순차 실행한다. **한 턴에 9개 기능을 동시에 요청하지 않는다**. 첫 단계 I00은 backend/frontend 기초 환경을 별도로 최소화한다.
