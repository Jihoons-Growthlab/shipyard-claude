# 교차 기능 업무 규칙 — 구현 핵심

이 문서의 로직은 목업의 `gate`, `impacts`, `refreshStatuses`, `recomputePlan`, `wAvg`를 기준으로 분석했다. 각 기능이 중복 구현하지 않도록 서버 서비스 한 곳에 둔다.

## BR-01 진척률 가중 평균 (OBS; 435~438행)

- 대상 공정의 계획기간 = `PlanEndDt - PlanStartDt + 1` (양 끝 포함).
- 호선/블록 진척률 = `round(sum(ProgressRate × 각 계획기간) / sum(계획기간))`.
- 대상 공정이 없으면 `0`.

## BR-02 공정 도면 게이트 (OBS; 440~444행)

- `TB_DWG_PlanLink`에서 `RequiredYN=true`인 연계만 검사.
- 해당 도면의 `DwgStatus != OBSOLETE`이고 `TB_DWG_Revision`에 `ISSUED` 리비전이 한 건도 없다면 착수를 막는 blocker.
- 모든 blocker가 없을 때 게이트 통과. `APPROVED`만으로는 통과하지 않음.
- **주의**: 과거 ISSUED Rev가 남아 있으면 최신 개정이 DRAFT/REVIEW라도 현재 로직은 통과한다. 원본 재현 vs 최신 유효 Rev 기준을 OPEN으로 남김.

## BR-03 공정 상태 재산정 (OBS; 457~470행)

우선순위:

1. `ProgressRate >= 100` → DONE.
2. `ProgressRate > 0` 또는 `ActualStartDt` 있음 → 종료일이 TODAY보다 이전이면 DELAY, 아니면 WORK.
3. 미착수이면서 종료일이 TODAY 이전 → DELAY.
4. 그 외: 모든 선행공정 DONE **그리고** 필수 도면 게이트 통과 → READY; 아니면 PLAN.
5. 원본 구현은 선행 공정 상태 갱신을 위해 2회 순회한다. 서버 구현에서는 의존 DAG의 위상 정렬 또는 안정적 반복 계산을 선택해 결과 불변 보장(DESIGN).

- 호선 상태: DESIGN 상태에서 WORK 공정 있으면 BUILD, BUILD 상태에서 LAUNCH 공정 DONE이면 LAUNCH. 다른 자동 전이는 원본에 없음.

## BR-04 선행공정 의존성 (OBS; 1027~1044행)

- 동일 호선 내 다른 공정들을 다중 선택해 선행으로 연결.
- 자기 자신을 선행으로 지정하면 거절.
- 도달성 검사로 순환 구조 검출하면 거절.
- 선행 종료일이 현재 계획 시작일보다 늦을 때 *경고하고 사용자가 동의하면 저장* (원본).
- 의존성 저장은 해당 PlanId의 기존 선행 연결을 통째로 교체, `LagDays=0`.
- 삭제 시 해당 계획의 전후행 관계·실적·도면 연결 함께 삭제.

## BR-05 실적 누적률 (OBS; 1094~1099, 1121~1133행)

- 동일 공정·작업일은 insert가 아니라 update.
- 작업일 내림차순 목록, 계산 시는 오름차순.
- 계산 진척률 = **가장 최근 작업일**의 `ProgressRate` (누적). 별도 합산 금지.
- 실제착수일 = 가장 이른 기록의 작업일.
- 실제종료일 = 최근 진척률이 100 이상이면 그 최근 작업일; 아니면 null.
- 이력 0건이면 진척 0, 실제 시작·종료 null.
- 작업일 > TODAY 불허, 진척률 0~100. 0 이하 공수/인원 제한, 누적률 단조 증가 등은 원본 검증에 없어 별도 결정.

## BR-06 도면 개정 상태 (OBS; 1151~1155, 1237~1285행)

- 신규 도면은 Rev0 DRAFT.
- 최신 Rev가 ISSUED 또는 OBSOLETE일 때 새 Rev(N+1) DRAFT 작성 가능; 개정 사유 필수.
- DRAFT → REVIEW(검토/승인 2단계 요청; 검토자≠승인자).
- 검토자 step 1 승인 후 step 2 승인 가능; 두 단계 모두 승인하면 APPROVED.
- 반려: 해당 Rev DRAFT로 되돌리고 아직 WAIT인 결재 항목 제거; 반려된 결재 결과는 이력에 남김.
- APPROVED → ISSUED(배포): 기존 ISSUED Rev는 OBSOLETE, 지정 Rev의 IssueDt=TODAY, Drawing.CurrentRevNo 갱신.
- 파일 업로드/교체/삭제는 DRAFT Rev만 가능. PDF 확장자 또는 MIME 검사, 30MB 상한.

## BR-07 최근 도면 개정 영향 (OBS; 447~454행)

- Rev>=1, ISSUED, IssueDt 있는 리비전 중 최근 30일([TODAY-30일, TODAY])의 최신 해당 Rev.
- 해당 도면의 연계 공정 중 `WORK`, `DONE`, `DELAY` 상태인 것만 영향으로 표시.
- 단순 경고/목록 제공이며 자동 중단·이메일 알림은 없음.

## BR-08 삭제 동작 (OBS; 473~497, 909~934, 1236행)

- 호선 삭제: 블록, 마일스톤, 공정, 의존, 실적, 도면, 개정, 결재, 연결, PDF 파일 삭제.
- 블록 삭제: 해당 블록의 공정·연계 삭제, 도면은 **삭제하지 않고 BlockId를 null로 해제**.
- 공정 삭제: 실적·선후행·도면 연계 삭제.
- 도면 삭제: 개정·결재·도면-공정 연계·PDF 파일 삭제.
- 파일 삭제와 DB 트랜잭션 사이 실패 처리 전략은 DESIGN/OPEN.

## BR-09 권한 (OBS; 283~297, 500~508, 725~737행)

- ADMIN: 전체 메뉴 Admin.
- PROC: 대시보드 View, 호선·공정 Write, 도면 목록 View. `M22` 공정 실적 Write.
- DWG: 대시보드·호선·공정계획 View, 도면목록·결재함 Write. **공정실적(M22) 권한 없음**.
- VIEW: 대시보드·호선·공정·도면·결재함 View. 시스템 회원관리 없음.
- 회원관리(M91): 관리자만 접근.
- 주의: 원본 `data-w`는 화면 버튼만 disabled 처리. API에서 같은 권한을 반드시 검증하고 필요한 업무 상태 검증을 추가.
