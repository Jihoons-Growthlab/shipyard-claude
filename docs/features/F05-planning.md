# F05 공정 계획 · 간트 · 선후행 · 도면 게이트

- **OBS**: `gantt`, `SCREENS['plan-gantt']`, `planPanel`, `reaches`, `ACT.planSave/Del`, `ACT.linkAdd/Del` (939~1050행).
- 공통 업무 규칙: BR-01~04, BR-08; 선행공정/도면 게이트/상태는 **서버 서비스**.
- **DESIGN endpoints**: `GET /api/hulls/{hull_no}/plans`, `POST /api/hulls/{hull_no}/plans`, `GET/PATCH/DELETE /api/plans/{plan_id}`, `PUT /api/plans/{plan_id}/predecessors`, `GET/POST /api/plans/{plan_id}/drawings`, `DELETE /api/plans/{plan_id}/drawings/{drawing_id}`.
- 권한: M21 View/Write. F07 도면 객체와 링크 계약 공유.

## PLAN-01 간트 화면

- 호선 선택: 기본은 공정 존재 첫 호선, 호선 변경 시 블록/선택/스크롤 초기화.
- 블록 선택: 전체 또는 해당 블록의 공정만 표시.
- 확대/축소: 일당 픽셀 기준 2.5/4/6, 시작 디폴트 4.
- 공정 정렬: 블록코드 숫자순 → 표준공정 Seq 순; 블록 없는 호선 전체 공정은 뒤에.
- 타임라인: 표시 계획기간과 고정 TODAY의 최소·최대, 월 헤더, 오늘 빨간 세로선; 최초 스크롤은 오늘이 좌측 약 40% 위치.
- 간트 행: 블록코드/공정명, 상태별 컬러바(PLAN/READY/WORK/DONE/DELAY), 진척률 내부 바, 도면 게이트 미통과 시 📐 표시.
- 선행→후행 화살표 연결선, 가로/세로 스크롤, 상단 월 헤더와 왼쪽 블록 열 sticky.
- 막대/행 클릭 시 하단 선택 공정 패널 열림, 패널 닫기 가능; 탭 재렌더 시 스크롤 유지.
- 상단에 해당 호선 **전체** 진척률 표시(블록으로 필터링해도 전체 진척).

## PLAN-02 공정 추가/수정

| 입력 | 원본 제약 |
|---|---|
| BlockId | 해당 호선 블록 또는 null(호선 전체) |
| ProcCd | CUT/SUBASM/ASM/PAINT/ERECT/LAUNCH/TRIAL |
| PlanStartDt, PlanEndDt | 필수; 종료 >= 시작 |
| ManagerEmpNo | approved 회원 또는 null |
| preds | 동일 호선 다른 공정의 다중 선택(자기 자신/순환 불가) |
| Remark | 텍스트/nullable |

- 신규 초기값: 선택 호선, 선택 블록, CUT, TODAY~TODAY+13, 진척0, PLAN, 실제일 null.
- 추가 시 `PlanId` 생성, 생성자/생성일 저장. 수정할 때 기존 진척·실적은 그대로 보존.
- 선행 연결 교체: 기존 해당 계획의 Dep 삭제 → 선택한 선행을 LagDays=0으로 저장.
- 선행 종료일 > 현재 시작일이면 확인 대화상자로 계속/취소 선택 가능.
- 저장 완료 후 모든 관련 상태 재산정. 상세 패널은 저장한 공정을 계속 선택.

## PLAN-03 삭제

- 삭제 시 확인 모달, 계획과 해당 실적·전후행 의존성·도면 링크 삭제. 연쇄 규칙 BR-08.

## PLAN-04 연계 도면

- 선택 공정의 모든 연계 도면 목록: 도면번호/현재 상태/필수 여부/해제.
- 같은 호선의 미연계 도면을 선택해 필수(기본 checked)/참고로 추가; NeedDt=PlanStartDt.
- 연계 해제 시 레코드 삭제.
- 필수 미배포 도면: 경고 박스에 도면번호·상태 표시; READY 상태 불가(BR-02).
- UI의 경고와 실제 실적 입력 허용 규칙은 별도: `gate`는 상태 READY를 결정하지만 원본 `ACT.progSave`에서 착수 이전 gate를 직접 검사하지 않는 점에 유의(OPEN).

## AC / 테스트

- PLAN-T01 호선/블록/배율 필터·선택·스크롤 복구 및 오늘선 위치.
- PLAN-T02 신규 및 수정 시 기간 검증, 담당자 선택, 메모 저장.
- PLAN-T03 자기 참조와 순환(A→B→C→A) 거절.
- PLAN-T04 선행종료 > 후행시작 시 확인 취소는 무변경, 확인은 저장.
- PLAN-T05 선행공정 DONE 및 필수 도면 ISSUED 전부 만족하면 READY.
- PLAN-T06 필수 도면 DRAFT만 존재하면 PLAN/대기; 배포 후 상태 갱신.
- PLAN-T07 공정 삭제 후 실적/양방향 의존/도면 링크 고아 참조 없음.
- PLAN-T08 도면 연결/해제에 따라 게이트와 간트 경고 재계산.
- PLAN-T09 승인된 VIEW만 가능한 계정은 쓰기 API 403.

## OPEN

- 원본은 계획 `LagDays` 저장을 0으로 고정; 기간 자동 밀기, 드래그 수정, 중요경로 계산은 원본에 없음.
- `refreshStatuses()` 두 번 순회 대신 서버에서는 DAG 정렬 기반 일관성 확보.
- 실제 작업 실적 등록 시 gate 강제 여부는 과제 원문/요구 정책에 따라 확정.
