# 토큰 사용량 최소화 워크플로

## 원칙

1. 기능 목록(`docs/features/00-index.md`)에서 현재 Fxx 하나만 선택한다.
2. 해당 Feature 명세만 읽고, 그 기능의 필요한 공통 계약(`docs/architecture/03-business-rules.md` 등)만 읽는다.
3. 필요 없는 HTML 원본 124KB를 그대로 컨텍스트에 넣지 않는다. 기능 동작에 이견이 있을 때 특정 JS 함수 범위만 확인한다.
4. `CLAUDE.md`는 짧게 유지하고 `.claude/rules/`는 `paths:`로 필요한 파일에서만 읽는다.
5. **Skill은 기능 실행 시 수동 호출**, MCP는 실제 도구 호출이 필요할 때만 사용.
6. 명령 출력은 오류와 요약만 요청한다(`pytest -q`, 파일 내용 cat 대량 출력 금지).
7. 한 기능 구현 후 테스트→짧은 인수인계→다음 기능. '계획만 세워줘'와 '구현해줘'를 분리할 수 있다.
8. 불필요한 반복 설명·전체 레포 재검색·다중 에이전트 병렬 호출·사소한 파일 생성 금지.
9. 캐시를 사용하려고 대형 공통 프롬프트를 매번 복붙하지 않는다. 안정된 짧은 상시 지침과 선택 문서로 구성한다.
10. 실제 사용량은 `extract_usage.py`로 지정 세션 기록을 집계하고 리포트에 남긴다. 이 수치는 과금/토큰 평가 산식과 다를 수 있다.

## 최소 문서 로딩 예

- F04 실행: `CLAUDE.md` + `docs/features/F04-hulls.md` + `docs/architecture/02-data-model.md` 중 호선 부분 + `BR-08`.
- F06 실행: `CLAUDE.md` + `docs/features/F06-progress.md` + `BR-03/05`.
- F08 실행: `CLAUDE.md` + `docs/features/F08-approvals.md` + `BR-06`.

## 요약 지시 템플릿

> Implement F04 only per `docs/features/F04-hulls.md`. Read shared rules only where referenced. Write tests for its AC. Avoid unrelated files. Report changed paths, test results, blockers in <=10 lines.

## 토큰 분석과 비용

`prompt_total = input_tokens + cache_creation_input_tokens + cache_read_input_tokens`.
`total_observed = prompt_total + output_tokens`.

**중요:** 이 합은 대화에서 관찰된 API usage 추정치이며 실제 비용이 아니다. 캐시 읽기 토큰은 할인되더라도 0 토큰이 아니다. 세션의 모든 기록을 추출하는 경우 중복 메시지를 제거해야 한다.

## MCP 사용 증빙

- 반드시 과제에서 정한 실제 MCP 서버/도구를 확인해 호출한다.
- 실제 응답·도구명·호출 시각/결과를 `docs/handoffs/tool-evidence.md`에 기록한다.
- 날씨가 실패해서 목업 샘플을 표시한 것만으로 'MCP 사용'을 증명했다고 보고하지 않는다.
