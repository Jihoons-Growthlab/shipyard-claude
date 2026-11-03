# 기능별 구현 상태 / 핸드오프

> 명세 패키지 생성 시점. **아래 기능은 아직 구현되지 않았다.** 실제 파일을 생성하고 테스트를 통과할 때만 상태를 바꿀 것.

| 단계 | Feature | 상태 | 테스트 | 산출물/결정 |
|---|---|---|---|---|
| I00 | F01 + F02 셸 + DB 기본 | NOT_STARTED | - | - |
| I01 | F04 호선 | NOT_STARTED | - | - |
| I02 | F05 계획 | NOT_STARTED | - | - |
| I03 | F06 실적 | NOT_STARTED | - | - |
| I04 | F07 도면/PDF | NOT_STARTED | - | - |
| I05 | F08 결재 | NOT_STARTED | - | - |
| I06 | F09 회원관리 | NOT_STARTED | - | - |
| I07 | F03 대시보드 | NOT_STARTED | - | - |
| I08 | F02 날씨 MCP·통합 | NOT_STARTED | - | - |

## 작업 종료 시 5줄만 추가

```text
YYYY-MM-DD / Feature: Fxx / Result: PASS|PARTIAL|BLOCKED
Files: <변경 파일 최대 8개 또는 glob>
Tests: <명령 + 통과/실패 개수>
Decisions: <결정 ID 또는 NONE>
Next: <구체적 다음 작업>
```

별도 장문의 인수인계 문서를 매번 생성하지 않는다. 완료보고서는 최종 시점에 요약해서 작성한다.
