# HTML 액션 인벤토리 — 원본 누락 점검용 (OBS)

- 직접 선언된 `ACT.*` 핸들러: **59개**. Source: `reference/shipyard_mockup.html`.
- 이 문서는 검수용 색인이다. 구현 시에는 전체 액션을 컨텍스트에 추가하지 말고 해당 Fxx 명세만 사용한다.
- `document.addEventListener`, `btnLogout`, `btnReset`, `onchange` 등 직접 등록 이벤트는 아래 ACT 개수에 포함되지 않음.

| ACT 핸들러 | 원본 행 | 기능 명세 |
|---|---:|---|
| `goLogin` | 581 | `F01-auth` |
| `goSignup` | 582 | `F01-auth` |
| `login` | 583 | `F01-auth` |
| `verifyOtp` | 590 | `F01-auth` |
| `signup` | 594 | `F01-auth` |
| `menu` | 679 | `F02-shell-weather` |
| `tab` | 722 | `F02-shell-weather` |
| `closeTab` | 723 | `F02-shell-weather` |
| `closeOthers` | 724 | `F02-shell-weather` |
| `modalClose` | 758 | `F02-shell-weather` |
| `search` | 782 | `F02-shell-weather` |
| `resetSearch` | 783 | `F02-shell-weather` |
| `kpi` | 844 | `F03-dashboard` |
| `goPlan` | 845 | `F03-dashboard` |
| `openDwg` | 846 | `F03-dashboard` |
| `pickRow` | 860 | `F04-hulls` |
| `openHull` | 861 | `F04-hulls` |
| `newHull` | 862 | `F04-hulls` |
| `hullTab` | 896 | `F04-hulls` |
| `hullSave` | 897 | `F04-hulls` |
| `hullDel` | 909 | `F04-hulls` |
| `msSave` | 914 | `F04-hulls` |
| `blkAdd` | 923 | `F04-hulls` |
| `blkDel` | 930 | `F04-hulls` |
| `goDwgList` | 936 | `F04-hulls` |
| `ganttHull` | 997 | `F05-planning` |
| `ganttBlock` | 998 | `F05-planning` |
| `ganttZoom` | 999 | `F05-planning` |
| `ganttSel` | 1000 | `F05-planning` |
| `planNew` | 1001 | `F05-planning` |
| `planClose` | 1028 | `F05-planning` |
| `planSave` | 1029 | `F05-planning` |
| `planDel` | 1044 | `F05-planning` |
| `linkAdd` | 1045 | `F05-planning` |
| `linkDel` | 1050 | `F05-planning` |
| `progHull` | 1118 | `F06-progress` |
| `progDone` | 1119 | `F06-progress` |
| `progPick` | 1120 | `F06-progress` |
| `progSave` | 1121 | `F06-progress` |
| `progDel` | 1130 | `F06-progress` |
| `newDwg` | 1148 | `F07-drawings` |
| `dwgViewRev` | 1198 | `F07-drawings` |
| `dwgViewRevBtn` | 1199 | `F07-drawings` |
| `dwgUpload` | 1202 | `F07-drawings` |
| `dwgFileDel` | 1212 | `F07-drawings` |
| `dwgPdfOpen` | 1218 | `F07-drawings` |
| `dwgHullChg` | 1219 | `F07-drawings` |
| `dwgSave` | 1220 | `F07-drawings` |
| `dwgDel` | 1236 | `F07-drawings` |
| `revNew` | 1237 | `F07-drawings` |
| `revRequest` | 1248 | `F07-drawings` |
| `revIssue` | 1255 | `F07-drawings` |
| `dwgLinkAdd` | 1256 | `F07-drawings` |
| `apvDo` | 1276 | `F08-approvals` |
| `usrPick` | 1305 | `F09-user-management` |
| `usrNew` | 1306 | `F09-user-management` |
| `usrSave` | 1307 | `F09-user-management` |
| `usrDel` | 1315 | `F09-user-management` |
| `usrApprove` | 1320 | `F09-user-management` |

## ACT 외 주요 이벤트

- 인증 입력 Enter: 약 604행; 로그인/OTP/가입 primary 버튼.
- 로그아웃 및 전체 데이터 초기화 헤더 버튼: 785~788행.
- 공통 클릭/change/dblclick 위임 이벤트: 761~781행.
- 검색 폼 Enter 처리: 약 778행.
- 날씨 지역 선택 select: `renderHeader` 653~662행.
- 모달 Escape: 약 759행.
- 화면 `SCREENS` 객체 9개(메뉴 7개 + 상세 팝업 2개).

## 유의

- `ACT.*` 이름과 `data-act` 문자열이 목업에서 모든 경로로 테스트되었다는 의미는 아님. 기능별 E2E를 실행해야 함.
- `openTab`의 메뉴 권한 검증은 화면 접근을 완전히 방어하지 못함; 서버 API에서 별도 구현해야 함.
