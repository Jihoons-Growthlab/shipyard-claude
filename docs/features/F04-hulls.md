# F04 호선 목록 · 호선 상세 · 주요일정 · 블록

- **OBS**: `SCREENS['hull-list']`·`['hull-detail']`, actions 848~936행; `cascadeDeleteHull` 473~485행.
- **DESIGN endpoints**: `GET/POST /api/hulls`, `GET/PATCH/DELETE /api/hulls/{hull_no}`, `PUT /api/hulls/{hull_no}/milestones`, `GET/POST /api/hulls/{hull_no}/blocks`, `DELETE /api/blocks/{block_id}`, `GET /api/hulls/{hull_no}/summary`.
- 권한: M11 View/Write (원본 팝업은 M11 권한 상속).

## 목록(HULL-01)

- 필터: 상태(HULLSTAT), 선종(SHIPTYPE), 키워드(호선번호/호선명/선주 부분일치, 대소문자 무시); 조회/초기화.
- 컬럼: 호선번호, 호선명, 선종, 상태, 선주, 선급, 도크, 계약일, 인도예정, 진척률, 지연 건수, 상세.
- 진척률은 BR-01 가중 평균, 공정이 없으면 '계획 없음', 지연 개수 표시.
- 단일 행 선택, 행 더블클릭 또는 상세 버튼 → 호선 상세 모달. 쓰기 권한 시 '호선 등록'.

## 기본정보(HULL-02 / HULL-03)

| 필드 | 입력/제약 OBS |
|---|---|
| HullNo | 신규 필수·유일, 수정시 readonly |
| HullNm | 텍스트 |
| ShipType | SHIPTYPE 선택 |
| HullStatus | HULLSTAT 선택, 신규 PLAN |
| OwnerNm, ClassSociety | 텍스트 |
| LengthM, BreadthM, DepthM | number 0.01 step; 빈값 null |
| DeadWeight | number; 빈값 null |
| DockNo, Remark | 텍스트 |
| ContractDt, DeliveryDt | date; 둘 다 있을 경우 DeliveryDt >= ContractDt |
| UseYN | checkbox; 신규 true |

- 신규 저장 시 사용자가 입력한 호선을 `TB_MST_Hull`에 추가하고, 5개 마일스톤을 자동 생성. DELIVER PlanDt는 DeliveryDt, 나머지 null.
- 수정 시 기본정보와 ModifyUserId/ModifyDt 기록.
- 호선 삭제: 명시적 확인 후 마일스톤·블록·공정·실적·선후행·도면·결재·PDF·연계까지 전체 삭제(BR-08). DB 트랜잭션 필수.

## 주요일정(HULL-04)

- 기본정보/주요일정/블록 구성/연계 현황 총 4개 서브탭(신규에서는 기본정보만).
- 5개 행: 강재절단(CUT), 기공(KEEL), 진수(LAUNCH), 시운전(TRIAL), 인도(DELIVER).
- 필드: 계획일, 실적일, 차이(실적일-계획일, 일), 일정 저장. 값이 없으면 null.
- **원본은 일정 순서·미래 날짜 검증 없음**; 추가 규칙은 OPEN.

## 블록(HULL-05 / HULL-06)

- 컬럼: 블록코드/명/유형/중량/진척/공정수/도면수/삭제.
- 추가: BlockCd 필수, 같은 호선 내 유일; BlockNm, BlockType(FLAT/CURVE/ENGINE), WeightTon(number/nullable), ParentBlockId=null, UseYN=true.
- 삭제: 확인 후 해당 블록 공정 제거 및 의존·실적·도면연계 삭제. 도면 자체는 유지하되 해당 BlockId=null.

## 연계 현황(HULL-07)

- 공정: 전체 가중 진척률, 상태별 도넛, 간트 보기 버튼.
- 도면: ISSUED/APPROVED/REVIEW/DRAFT 상태별 도넛, 해당 호선 도면 목록 이동.
- 빈 상태 메시지, URL 필터/호선 이동 맥락 보존.

## AC / 테스트

- HULL-T01 상태/선종/검색어 조합 필터, 초기화, 더블클릭 상세.
- HULL-T02 신규 중복 호선번호 거절, 누락 번호 거절, 날짜 역순 거절.
- HULL-T03 신규 시 5개 마일스톤 포함, DELIVER 계획일 인도 예정과 일치.
- HULL-T04 상세 수정 후 목록 반영, 서브탭 유지.
- HULL-T05 같은 호선 블록코드 중복 거절; 다른 호선은 동일 코드 허용.
- HULL-T06 블록 삭제 후 연결 도면 유지·BlockId만 null, 해당 블록 공정 삭제.
- HULL-T07 호선 삭제 후 관련 모든 데이터/파일 메타데이터에서 고아 참조 없음.
- HULL-T08 View 계정은 직접 POST/PATCH/DELETE 시 403.
