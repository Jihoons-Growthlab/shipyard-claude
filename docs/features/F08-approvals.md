# F08 도면 결재함 · 순차 승인 · 배포

- **OBS**: `SCREENS['dwg-approval']` 1261~1275, `ACT.apvDo` 1276~1285, `revRequest/issueRev` F07.
- 공통: BR-06, F07 도면 상태.
- **DESIGN endpoints**: `GET /api/approvals/inbox`, `POST /api/approvals/{approval_id}/decision`, `GET /api/approvals/history`, F07의 issue endpoint.
- 권한: 결재함 메뉴 M33 View/Write; 본인 승인할 수 있는 건인지 서버에서 반드시 추가 확인.

## APV-01 내 결재 대기

- `Result=WAIT`, ApproverEmpNo=현재 사용자, 이전 StepNo 모두 APPROVE, 대상 RevStatus=REVIEW 조건 모두 충족.
- 컬럼: 도면번호, 도면명, Rev, 단계, 변경 사유, 의견 입력, 승인/반려.
- 1단계 검토자 승인 뒤 2단계 승인자가 처리할 수 있음. 결재함 UI에서는 승인/반려 버튼 `data-w`.

## APV-02 결재 처리

- 승인: 의견은 선택, 비었을 경우 Comment='승인'; Result=APPROVE, ActDt 기록.
- 반려: 의견 **필수**; Result=REJECT, ActDt 기록; 해당 Rev와 도면 상태 DRAFT로 되돌리고 **WAIT 결재들만 제거**. 반려 레코드는 이력으로 보존.
- 같은 Rev의 결재 결과가 모두 APPROVE이면 RevStatus와 Drawing.DwgStatus 둘 다 APPROVED.
- 다른 사용자 건/순서가 안 된 step/이미 처리된 건/최신이 아닌 Rev의 승인은 직접 API 호출에도 거절(DESIGN).

## APV-03 배포 대기

- `latestRev(d).RevStatus=APPROVED` 도면 목록: 도면번호/도면명/Rev/배포 시 착수 가능해질 수 있는 공정/배포 버튼.
- 연계 PLAN 공정만 '착수 가능해질 수 있는 공정' 칸에 표시. 배포 시 F07 issue 로직 호출.
- 배포 후 필수 도면 게이트 갱신; 실제 READY 여부는 선행공정 완료 및 다른 blocker까지 확인(BR-03).

## APV-04 최근 결재 이력

- Result!=WAIT 전부를 ActDt 내림차순으로 정렬한 최근 10건: 일시/도면번호/Rev/단계/결재자/결과/의견.
- 원본은 로그인한 사용자 자신 이력으로만 제한하지 않음.

## AC / 테스트

- APV-T01 2단계 승인자는 1단계 미승인 시 inbox에 나타나지 않음.
- APV-T02 지정되지 않은 사용자의 approval_id 승인/반려 API 거절.
- APV-T03 반려 시 의견 필수, Rev는 DRAFT로 복귀, 남은 WAIT 제거, 반려 결과는 이력에 남음.
- APV-T04 두 승인 모두 완료시 APPROVED, 배포 가능.
- APV-T05 배포 후 이전 ISSUED OBSOLETE/신규 ISSUED/Plan 상태 갱신.
- APV-T06 최근 10건은 날짜 내림차순, 빈 목록은 메시지.

## OPEN

- 배포 권한 M33 Write가 있으면 승인자 이외의 사용자가 배포해도 되는지, 검토자 본인 도면 처리 제한, 결재 이력 전체 노출 범위.
