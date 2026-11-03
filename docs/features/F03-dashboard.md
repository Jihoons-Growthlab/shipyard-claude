# F03 대시보드 · 지표 · 이동

- **OBS**: `SCREENS.dashboard` 809~843행; `impacts/gate/wAvg` 공통 함수를 사용.
- **DESIGN endpoints**: `GET /api/dashboard/summary` (서버 일괄 집계; UI N+1 요청 방지).

## 구성 요소·정의

| ID | 위젯 | 계산/기능 |
|---|---|---|
| DASH-01 | KPI 진행 호선 | UseYN=true, 상태 DESIGN/BUILD/LAUNCH/TRIAL 호선 수; 클릭 → 호선 목록 |
| DASH-02 | KPI 지연 공정 | PlanStatus=DELAY 공정 수; 클릭 → 공정 계획 |
| DASH-03 | KPI 도면 대기 공정 | PLAN이고 gate blocker 존재하는 공정 수; 클릭 → 공정 계획 |
| DASH-04 | KPI 결재·배포 대기 도면 | DwgStatus REVIEW 또는 APPROVED 도면 수; 클릭 → 결재함 |
| DASH-05 | 호선별 진척률 | 사용중인 호선별 가중 평균 진척률; 행 클릭 → 해당 호선 공정 계획 |
| DASH-06 | 공정 상태 분포 | PLAN, READY, WORK, DONE, DELAY 건수 도넛 |
| DASH-07 | 분야별 도면 상태 | 분야별 도면 수, ISSUED/APPROVED/REVIEW/DRAFT 비율 스택 |
| DASH-08 | 월별 인도 예정 | 호선 DeliveryDt의 YYYY-MM별 집계, 호선번호 표시 |
| DASH-09 | 지연 공정 목록 | 계획 종료일, 진척률; **최대 6건** 표시, 행 클릭 해당 호선 간트 |
| DASH-10 | 도면 대기 공정 목록 | 도면번호 blocker 및 시작일; 최대 6건, 행 클릭 간트 |
| DASH-11 | 도면 개정 영향 목록 | 최근 30일 내 Rev>=1 ISSUED 도면에 연결된 WORK/DONE/DELAY 공정; 최대 6건; 클릭 도면 팝업 |

## 정책

- 원본 화면은 `TODAY`를 헤더에 표시하고 모든 지표를 페이지 렌더 시 즉시 계산.
- API 응답은 요약 카운트, 차트 배열, 목록의 `target_id`와 link metadata를 포함. 차트 라이브러리 새 도입은 필수가 아님.
- 빈 배열일 때 원본의 '없습니다' 문구 표시.
- 경고와 시드 시나리오는 동일 데이터 상태를 재현해야 함.

## AC / 테스트

- DASH-T01 공정 실적 100% 변경 후 지연/완료·진척 집계 갱신.
- DASH-T02 미배포 필수 도면 추가/배포로 도면 대기 지표 증감.
- DASH-T03 최근 30일 배포 도면과 WORK/DONE/DELAY 공정 조합만 영향으로 표시.
- DASH-T04 인도 예정월 5개 호선의 집계가 일관적.
- DASH-T05 각 KPI/행의 이동 목적 화면과 호선/도면 ID 일치.
- DASH-T06 7건 이상 경고 목록에서 최초 6건만 표시.
