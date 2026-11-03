# F06 공정 실적 입력 · 이력 · 누적 진척률

- **OBS**: `recomputePlan`, `SCREENS.progress`, `ACT.progSave/Del` (1094~1133행).
- 공통: BR-03/05, F05 Plan 참조.
- **DESIGN endpoints**: `GET /api/hulls/{hull_no}/progress-targets?include_done=false`, `GET /api/plans/{plan_id}/progress`, `PUT /api/plans/{plan_id}/progress/{work_date}`, `DELETE /api/progress/{progress_id}`.
- 권한: M22 View/Write.

## PROG-01 조회

- 호선 선택: 공정이 있는 호선 중 BUILD 상태 우선, 없으면 첫 호선.
- 기본 표시: READY/WORK/DELAY 공정만; '완료 공정 포함' 체크 시 DONE 등 모두 표시.
- 정렬: 블록코드 숫자 오름차순 + 표준공정 Seq 오름차순.
- 목록 컬럼: 공정, 계획 기간, 실제 착수일, 진척률 바, 상태, 담당자.
- 공정 선택 시 하단 입력과 이력 테이블 표시. 이력은 작업일 내림차순.

## PROG-02 입력

| 입력 | OBS 내용 |
|---|---|
| WorkDt | 기본 TODAY, 필수, 미래 일자 금지 |
| ProgressRate | 누적 진척률 0~100, 정수 step 1, 필수 |
| ManHour | 투입 공수, 숫자 step 0.5, 빈 값 null |
| WorkerCnt | 투입 인원, number, 빈 값 null |
| WorkerEmpNo | 승인된 사용자, 기본 로그인 사용자 |
| Remark | 비고, 빈 값 null |

- 동일 `PlanId + WorkDt` 레코드가 있으면 수정, 없으면 추가.
- 모든 저장 후 같은 공정의 일별 이력 오름차순 계산: 가장 최근 누적률이 Plan.ProgressRate; 첫 작업일이 ActualStartDt; 최신 누적률이 100이면 마지막 작업일이 ActualEndDt.
- 상태는 공통 BR-03으로 다시 계산. 100%이면 완료 토스트.

## PROG-03 실적 삭제

- 이력 행 삭제는 확인창 후 해당 ProgressId 제거.
- 잔여 이력으로 공정 누적률/실제 착수/완료일 재계산; 0건이면 0/null/null.

## AC / 테스트

- PROG-T01 기본 목록 READY/WORK/DELAY, 완료 포함 토글 시 DONE 등장.
- PROG-T02 동일 공정·동일 작업일 두 번 저장 시 1건 유지, 값은 갱신.
- PROG-T03 마지막 날짜의 누적률을 사용하며 일별 진척률 합산하지 않음.
- PROG-T04 WorkDt>TODAY, ProgressRate <0/>100, 빈 날짜/진척률 거절.
- PROG-T05 100% 저장시 DONE 및 ActualEndDt 설정; 이력 삭제 후 정상 되돌림.
- PROG-T06 View 권한 사용자의 쓰기·삭제 403.

## OPEN

- 누적 진척률 역행(60%→50%) 허용/금지, 과거 일자 추가 시 계산 정책, 공수/인원 음수 제한, 도면 게이트를 실제 실적 등록 시 강제할지.
