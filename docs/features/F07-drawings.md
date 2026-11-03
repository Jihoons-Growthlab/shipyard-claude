# F07 도면 목록 · 상세 · 리비전 · PDF · 공정연계

- **OBS**: `SCREENS['dwg-list']` 1135~1148, `issueRev`, `SCREENS['dwg-detail']` 1150~1198, 파일 저장·액션 1056~1092/1200~1260.
- 공통: BR-02/06/07/08, F05 계획 연결. 결재는 F08.
- **DESIGN endpoints**: `GET/POST /api/drawings`, `GET/PATCH/DELETE /api/drawings/{id}`, `POST /api/drawings/{id}/revisions`, `GET /api/drawings/{id}/revisions`, `POST/GET/DELETE /api/drawings/{id}/revisions/{rev}/pdf`, `POST /api/drawings/{id}/revisions/{rev}/request-approval`, `POST /api/drawings/{id}/revisions/{rev}/issue`, `GET/POST /api/drawings/{id}/plans`, `DELETE /api/drawings/{id}/plans/{plan_id}`.
- 권한: M31 View/Write; 상세 모달은 M31 상속. F08 배포 권한은 추가 정책 결정.

## DWG-01 목록

- 필터: 호선(전체 포함), 분야(DWGDISC), 상태(DWGSTAT), 도면번호/도면명 부분검색, 조회/초기화.
- 컬럼: 도면번호, 도면명, 호선, 블록, 분야, Rev, 상태, 설계자, 연계 공정 수, 상세.
- **Rev 컬럼은 CurrentRevNo(현재 배포 리비전)**. 마지막 생성 RevNo가 다르면 `(최신 RevN)` 병기.
- 행 더블클릭/상세 → 도면 모달; 쓰기 권한이면 신규 도면 등록.

## DWG-02 신규/수정

| 필드 | OBS 규칙 |
|---|---|
| DrawingNo | 신규 필수·전체 유일, 수정 readonly |
| DrawingNm | 필수 |
| Discipline | HULL/MACH/ELEC/PIPE/OUTFIT |
| HullNo | 신규 선택, 수정 시 변경 불가(disabled) |
| BlockId | 선택 호선 블록 또는 null, 호선 변경 시 블록 옵션 초기화 |
| DesignerEmpNo | approved 사용자 또는 null |
| pdf | 신규 선택 업로드, PDF 파일만, <=30MB |

- 신규 생성 시 `TB_DWG_Drawing` 상태 DRAFT, CurrentRevNo=0, `TB_DWG_Revision` Rev0 DRAFT·ChangeDesc='최초 작성'; 파일이 있으면 Rev0에 첨부.
- 수정은 도면명/블록/분야/설계자만 변경, ModifyUserId/ModifyDt 기록.
- 삭제 시 확인 후 도면/전체 리비전/결재/공정 링크/업로드 파일 제거. 원본의 `dropFiles()`는 비동기 삭제를 기다리지 않음: 서버는 실패 복구 정책 필요.

## DWG-03 PDF 뷰어

- 기존 도면 상세: 왼쪽 큰 PDF 뷰어, 오른쪽 정보/리비전/결재/공정 연계.
- 선택 리비전 변경/리비전 이력 '보기' → 해당 PDF 렌더. 새 창으로 열기 지원.
- 첨부 파일 없으면 프로그램이 생성한 **샘플 PDF**, '샘플 PDF (미업로드)' 표기. 실파일 첨부시 '업로드 파일' 배지.
- PDF 업로드·교체·삭제는 `RevStatus=DRAFT`일 때만 허용.
- 검사: 파일명 `.pdf` 확장자 또는 MIME `application/pdf`; 크기 30MiB 이하. 원본은 확장자/MIME만 검사하므로 실제 서버는 magic header 검사 등 보강(DESIGN).
- 브라우저 `IndexedDB`의 `FileId='idb:DrawingId-RevNo'`는 데모 전용; 서버 저장 API와 권한 확인으로 교체.
- PDF 접근은 같은 도면 조회 권한, 임의 경로 접근 금지.

## DWG-04 리비전

- 최신 Rev가 ISSUED/OBSOLETE인 경우에만 '신규 RevN 작성' 폼 표시; 개정 사유 필수, PDF 선택 가능.
- 새 Rev는 N+1 DRAFT; **기존 ISSUED Rev는 신규 Rev 작성 때도 유지**. `Drawing.DwgStatus`는 DRAFT가 됨.
- 최신 DRAFT: 검토자/승인자 선택 → 결재 요청. 같은 사람은 두 단계 겸임 불가; 요청 시 최신 Rev REVIEW로 전환.
- 최신 REVIEW: 결재 진행중 안내. 최신 APPROVED: 배포 버튼 표시.
- 배포: 기존 ISSUED 리비전을 OBSOLETE로 변경, 승인된 Rev를 ISSUED, IssueDt=TODAY, CurrentRevNo 갱신.
- 변경 사유·파일명·작성자·배포일·상태를 리비전 이력 표에 표시.
- **주의**: 기존 발행 리비전과 최신 작성중 리비전이 공존할 때의 도면 게이트/CurrentRevNo 표시 규칙을 그대로 유지하거나 보완할지는 OPEN.

## DWG-05 결재 및 공정 연계 요약

- 결재 이력: Rev/1단계 검토·2단계 승인/결재자/승인·반려·대기. 상세 동작은 F08.
- 공정 연계: 같은 호선의 아직 연결되지 않은 공정만 선택해 추가(필수 기본 true, NeedDt=PlanStartDt); 리스트에서 해제.
- 연결 공정의 상태/필수 여부 표시, 간트로 이동.
- 최근 30일 배포 Rev>=1이 WORK/DONE/DELAY 공정에 영향을 주면 경고(BR-07).

## AC / 테스트

- DWG-T01 검색 필터 조합과 CurrentRevNo/최신 Rev 구분 표기.
- DWG-T02 신규 필수/중복 검사, Rev0 DRAFT 자동 생성.
- DWG-T03 다른 호선 블록이 선택되지 않음, 수정 중 HullNo 변경 불가.
- DWG-T04 30MiB 초과/비PDF 거부, DRAFT에만 파일 업로드/삭제 성공.
- DWG-T05 업로드 파일 없는 뷰어는 '샘플'을 명시하며 실제 파일로 오인하지 않음.
- DWG-T06 RevN 새 작성 → 결재 → 승인 → 배포, 이전 ISSUED는 OBSOLETE.
- DWG-T07 배포 후 CurrentRevNo 갱신, 필수 연결 공정 gate 재산정.
- DWG-T08 연계 추가/해제와 영향 경고 정상 동작.
- DWG-T09 도면 삭제 후 리비전·결재·연결·파일 메타데이터 고아 참조 없음.
- DWG-T10 VIEW 사용자의 PDF 업로드/배포/삭제 직접 호출 403.

## OPEN

- 현재 배포 Rev 없는 신규 도면의 CurrentRevNo=0 표기 의미, 파일 storage 정책, 동시 배포 시 경쟁조건, 임시 샘플 PDF를 서버 생성할지 UI에서만 표시할지.
