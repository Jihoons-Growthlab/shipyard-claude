# UI 이미지 참고 가이드

이 폴더는 사용자가 제공한 원본 UI 캡처를 보관한다. 모델을 재학습시키는 데이터가 아니라, UI 생성·개선 작업 중 직접 열어 비교할 시각적 기준이다. 경로의 대소문자는 `reference/UiImages/`로 유지한다.

## 작업 순서

1. 작업 대상 기능 명세(`docs/features/`)와 아래 이미지 목록을 확인한다.
2. 이미지 읽기 도구로 해당 PNG를 직접 연다. 공통 레이아웃을 바꾸면 `dashboard.png`도 함께 본다. 이미지를 볼 수 없으면 그 사실을 알리고 시각 검증 완료로 보고하지 않는다.
3. 현재 화면과 비교하여 배치, 간격, 크기, 색, 글자, 표와 폼의 차이를 정리한 뒤 요청된 화면을 수정한다.
4. 공통 스타일과 기존 컴포넌트를 먼저 재사용한다. 구체적인 원본 CSS 수치가 필요하면 `../shipyard_mockup.html`의 관련 부분을 확인한다.
5. 기존 API 연결, 데이터 처리, 메뉴 권한, 모달·탭 이동, 입력 검증을 유지한다. 이미지와 업무 규칙이 다르면 기능 명세와 현재 서버 계약을 따른다. 사용자의 추가 지시는 이 시각적 기준보다 우선한다.
6. 가능하면 브라우저에서 동일한 화면 상태와 비슷한 앱 영역 크기로 비교한다. 가로 넘침, 잘림, 스크롤, 선택 행, 모달 닫기, 읽기 전용 상태를 확인한다. 공통 CSS 변경 시 목록·모달·로그인 화면에도 영향이 없는지 확인한다.
7. 변경에 관련된 테스트와 프론트엔드 빌드를 실행하고, 실제 실행한 검증과 미확인 항목을 구분해 보고한다.

## 화면별 이미지와 코드

코드 경로는 프로젝트 루트 기준이다. 원래 파일명을 함께 남겨 추적할 수 있도록 했다.

| 이미지 | 화면 / 참고 포인트 | 기능 / 주요 코드 | 원래 파일명 |
| --- | --- | --- | --- |
| [dashboard.png](dashboard.png) | 대시보드, 공통 헤더·메뉴·탭, KPI 4개, 차트와 목록 카드 | F02/F03 · `frontend/src/screens/dashboard/DashboardScreen.vue`, `frontend/src/views/ShellView.vue` | image.png |
| [hull-list.png](hull-list.png) | 호선 목록, 필터, 등록 버튼, 표와 진척률 | F04 · `frontend/src/screens/hulls/HullList.vue` | image copy.png |
| [plan-gantt.png](plan-gantt.png) | 공정 간트, 상태 범례, 오늘선, 선택 공정 하단 편집 패널 | F05 · `frontend/src/screens/plans/PlanGantt.vue`, `PlanPanel.vue` | image copy 2.png |
| [progress-entry.png](progress-entry.png) | 공정 실적 목록, 선택 공정 입력 폼, 실적 이력 | F06 · `frontend/src/screens/progress/ProgressScreen.vue` | image copy 3.png |
| [drawing-list.png](drawing-list.png) | 도면 목록, 검색, 상태 배지, Rev 표시 | F07 · `frontend/src/screens/drawings/DrawingList.vue` | image copy 4.png |
| [approval-inbox.png](approval-inbox.png) | 결재 대기·배포 대기·최근 이력의 세 영역 | F08 · `frontend/src/screens/approvals/ApprovalInbox.vue` | image copy 5.png |
| [user-management.png](user-management.png) | 상단 회원 목록과 하단 수정 폼 | F09 · `frontend/src/screens/users/UserManagement.vue` | image copy 6.png |
| [drawing-create-modal.png](drawing-create-modal.png) | 도면 신규 등록 모달, 두 열 폼, PDF 선택 | F07 · `frontend/src/screens/drawings/DrawingDetailModal.vue` | image copy 7.png |
| [hull-create-modal.png](hull-create-modal.png) | 호선 신규 등록 모달, 여러 열 폼 | F04 · `frontend/src/screens/hulls/HullDetailModal.vue` | image copy 8.png |
| [hull-detail-modal.png](hull-detail-modal.png) | 호선 상세 기본정보, 서브탭, 저장·삭제 | F04 · `frontend/src/screens/hulls/HullDetailModal.vue` | image copy 9.png |
| [drawing-detail-modal.png](drawing-detail-modal.png) | 왼쪽 큰 PDF 뷰어, 오른쪽 도면 정보·리비전·결재 이력 | F07 · `frontend/src/screens/drawings/DrawingDetailModal.vue` | image copy 10.png |
| [login.png](login.png) | 남색 배경, 중앙 흰색 로그인 카드, 입력과 주요 버튼 | F01 · `frontend/src/views/AuthView.vue` | image copy 11.png |

공통 구현: `frontend/src/styles.css`, `frontend/src/components/AppHeader.vue`, `MenuTree.vue`, `TabBar.vue`, `BaseModal.vue`.

## 시각적 기준과 주의점

- 남색 헤더, 밝은 회청색 작업 배경, 흰색 카드, 파란 주요 버튼, 얇은 테두리, 조밀한 업무용 표·폼을 기준으로 한다. 정확한 색·치수는 이미지와 원본 CSS를 확인해 결정한다.
- 선택 행은 연한 파랑, 상태는 배지와 색상으로 구분한다. 숫자·날짜·이름·진척률은 캡처 당시 데이터이므로 하드코딩하지 않는다.
- 일부 캡처의 오른쪽에는 다른 앱이나 검은 여백이, 아래쪽에는 macOS Dock이 포함되어 있다. 앱 영역만 참고하고 이런 요소는 재현하지 않는다. 원본 이미지는 자르거나 수정하지 않았다.
- 캡처의 `데이터 초기화`, 데모 계정 안내, 고정 OTP, 초기화 오류 문구는 목업의 상태다. 시각적 일치를 위해 새 기능을 추가하거나 현재 인증·보안 동작을 변경하지 않는다.
- PDF 도구 모음은 브라우저 내장 뷰어에 따라 달라질 수 있다. 주요 기준은 좌우 배치와 정보 영역이며 도구 모음을 별도로 복제하지 않는다.
- 잘린 화면 아래쪽과 미제공 상태는 추측해 확정하지 않는다. 로그인 외 회원가입·OTP, 호선 상세의 다른 서브탭, 좁은 화면은 관련 명세와 기존 동작을 기준으로 구성한다.

## Claude Code 요청 예시

```text
CLAUDE.md와 reference/UiImages/README.md를 읽고,
작업 대상 PNG를 직접 열어 현재 화면과 비교해줘.
우선 대시보드 UI를 참고 이미지에 맞춰 개선해줘.
기존 기능·API·권한 처리는 유지하고 공통 스타일을 재사용해.
수정 후 관련 테스트와 빌드, 가능한 브라우저 시각 비교를 진행하고 결과를 알려줘.
```
