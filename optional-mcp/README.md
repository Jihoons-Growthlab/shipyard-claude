# 선택 MCP 설정 예시

이 폴더의 파일은 Claude Code가 읽지 않는다. 프로젝트 루트의 `.mcp.json`만 로드되므로, 여기 있는 것만으로는 아무것도 활성화되지 않는다.

| 파일 | 서버 | 사전 준비 | 인증·환경 변수 |
| --- | --- | --- | --- |
| `context7.mcp.json` | Context7 | 없음 | 없음 (키 없이 호출됨을 2026-11-04 확인) |
| `context7-with-api-key.mcp.json` | Context7 | context7.com/dashboard에서 키 발급 | `CONTEXT7_API_KEY` |
| `serena.mcp.json` | Serena | `uv tool install -p 3.13 serena-agent` 후 `serena init` | 없음 |
| `exa.mcp.json` | Exa | 없음 | 없음(익명, 요청 제한 있음). 대신 `/mcp`에서 OAuth 로그인 가능 |

## 사용 방법

1. 한 번에 **하나만** 적용한다. `mcpServers` 항목을 루트 `.mcp.json`으로 옮긴다.
2. 키가 필요하면 파일이 아니라 셸 환경 변수로 설정한다. 키를 JSON에 적거나 커밋하지 않는다.
3. 새 세션을 열고 프로젝트 서버 승인 프롬프트를 확인한 뒤, `/mcp`에서 연결을 확인한다.
4. `mcp-recommendations.md`의 실험 절차로 비교하고, 이점이 측정되지 않으면 제거한다.

## 주의

- 설정되지 않은 `${VAR}`는 경고와 함께 글자 그대로 남는다. 키 없이 쓸 때는 키 없는 파일을 쓴다.
- Tavily의 URL 쿼리 방식(`?tavilyApiKey=`)은 키가 설정 파일에 남기 쉬워 사용하지 않는다.
- 모든 예시의 연결 상태는 **미검증**이다. 단, Context7의 같은 URL은 기존 루트 설정으로 호출을 시험했다.
