# 데이터 모델 — 목업 기반 데이터 사전

> **OBS**: 아래 필드 이름은 원본 `seed()`에 실제 등장한 객체 속성이다. `shipyard_schema.sql`은 첨부되지 않았으므로 실제 SQL 타입, PK/UK/FK/ON DELETE는 **DESIGN 제안**이며 과제 SQL 원본과 대조 필요.

## 시스템·권한

| 테이블 | 목업 필드 | 제안 키/관계 |
|---|---|---|
| `users` | id, email, password_hash, display_name, emp_no, status, auth_provider, last_name, first_name, birth_date, phone, totp_enabled, totp_secret, created_at | PK id, UNIQUE(emp_no/email/phone), `status` enum |
| `TB_SYS_CodeGroup` | CodeGroup, CodeGroupName, Seq, UseYN | PK CodeGroup |
| `TB_SYS_Code` | CodeGroup, Code, CodeName, Seq, UseYN | PK(CodeGroup,Code), FK CodeGroup |
| `TB_SYS_AuthGroup` | AuthCd, AuthNm | PK AuthCd |
| `TB_SYS_AuthUser` | AuthCd, EmpNo | PK(AuthCd,EmpNo), FK AuthCd/users.emp_no |
| `TB_SYS_MenuInfo` | MenuId, SystemId, ParentId, Title, TokenUrl, Seq, UseYN | PK MenuId, ParentId self-FK |
| `TB_SYS_AuthMenu` | MenuId, AuthCd, AuthGbn | PK(MenuId,AuthCd), FK menu/auth group |
| `TB_SYS_LogAccess` | LogId, UserId, LoginDt, LogoutDt, IpAddress, ComputerNm, WindowAccount | PK LogId, FK UserId(users.emp_no) |
| `TB_SYS_LogMenuAccess` | AccIndex, MenuId, LogId, InDt | PK AccIndex, FKs MenuId/LogId |
| `TB_SYS_UserBackupCode` | 시드 빈 배열, 필드 정의 없음 | **OPEN**: 사용처·구조 확인 전 구현 유보 |

## 호선·블록

| 테이블 | 목업 필드 | 제안 키/관계 |
|---|---|---|
| `TB_MST_Hull` | HullNo, HullNm, ShipType, HullStatus, OwnerNm, ClassSociety, LengthM, BreadthM, DepthM, DeadWeight, DockNo, ContractDt, DeliveryDt, Remark, UseYN, CreateUserId, CreateDt, ModifyUserId, ModifyDt | PK HullNo, 상태/선종 공통코드, Modify 필드 수정 시 등장 |
| `TB_MST_HullMilestone` | HullNo, MilestoneCd, PlanDt, ActualDt, Remark | PK(HullNo,MilestoneCd), FK HullNo |
| `TB_MST_Block` | BlockId, HullNo, BlockCd, BlockNm, BlockType, ParentBlockId, WeightTon, UseYN | PK BlockId, UNIQUE(HullNo, BlockCd), FK HullNo, ParentBlockId(현재 시드 null) |

## 공정

| 테이블 | 목업 필드 | 제안 키/관계 |
|---|---|---|
| `TB_PRC_Proc` | ProcCd, ProcNm, ProcGroup, StdDays, Seq, UseYN | PK ProcCd |
| `TB_PRC_Plan` | PlanId, HullNo, BlockId, ProcCd, PlanStartDt, PlanEndDt, ActualStartDt, ActualEndDt, ProgressRate, PlanStatus, ManagerEmpNo, Remark, CreateUserId, CreateDt | PK PlanId, FKs Hull/Block/Proc/Manager |
| `TB_PRC_PlanDep` | PlanId, PredPlanId, LagDays | PK(PlanId,PredPlanId), 양쪽 PlanId FK |
| `TB_PRC_Progress` | ProgressId, PlanId, WorkDt, ProgressRate, ManHour, WorkerCnt, WorkerEmpNo, Remark, CreateDt | PK ProgressId, UNIQUE(PlanId,WorkDt) 권장, FK PlanId |

## 도면

| 테이블 | 목업 필드 | 제안 키/관계 |
|---|---|---|
| `TB_DWG_Drawing` | DrawingId, DrawingNo, DrawingNm, HullNo, BlockId, Discipline, DwgStatus, CurrentRevNo, DesignerEmpNo, UseYN, CreateUserId, CreateDt, ModifyUserId, ModifyDt | PK DrawingId, UNIQUE DrawingNo, BlockId nullable |
| `TB_DWG_Revision` | DrawingId, RevNo, RevStatus, ChangeDesc, FileId, FileNm, AuthorEmpNo, IssueDt, CreateDt | PK(DrawingId,RevNo), FK DrawingId |
| `TB_DWG_Approval` | ApprovalId, DrawingId, RevNo, StepNo, ApproverEmpNo, Result, Comment, ActDt | PK ApprovalId; UNIQUE(DrawingId,RevNo,StepNo) 권장, FK (DrawingId,RevNo) |
| `TB_DWG_PlanLink` | DrawingId, PlanId, RequiredYN, NeedDt | PK(DrawingId,PlanId), FKs DrawingId/PlanId |

## 시드 데이터 (OBS)

- 시스템 그룹: `ADMIN`, `PROC`, `DWG`, `VIEW`. 7개의 실제 화면 메뉴, 2개의 상세 모달.
- 초기 회원 6명: `admin`, `park.pm`, `lee.dwg`, `han.wk`, `choi.qa`는 approved, `jung.new`는 pending.
- 호선 5척: 8001 LNG / 8002 VLCC / 8003 CONT / 8004 PC / 8005 LNG.
- 블록: 호선별 5/4/3/2/3개. 공정 코드: CUT, SUBASM, ASM, PAINT, ERECT, LAUNCH, TRIAL.
- 도면 분야: HULL, PIPE, ELEC(시드에 사용), 코드 정의는 MACH, OUTFIT도 포함.
- 8001-301 도장 공정을 DELAY/60%로 오버라이드, 후행 탑재 대기; 8001-HULL-201 Rev2에는 하중 조건 변경 개정 이력이 포함.
- 재현성 요구가 있다면 씨드는 별도 테스트 모드에서만 `TODAY=2026-10-19`로 초기화.

## 코드값 (OBS; 253~260행)

- SHIPTYPE: LNG / VLCC / CONT / PC.
- HULLSTAT: PLAN / DESIGN / BUILD / LAUNCH / TRIAL / DELIVER.
- MILESTONE: CUT / KEEL / LAUNCH / TRIAL / DELIVER.
- BLOCKTYPE: FLAT / CURVE / ENGINE.
- PLANSTAT: PLAN / READY / WORK / DONE / DELAY.
- DWGDISC: HULL / MACH / ELEC / PIPE / OUTFIT.
- DWGSTAT: DRAFT / REVIEW / APPROVED / ISSUED / OBSOLETE.
- 회원 status: pending / approved / rejected / disabled. 결재 Result: WAIT / APPROVE / REJECT.

## 설계시 필수 확인

1. 원본의 실제 `shipyard_schema.sql`이 있다면 그 DDL이 우선한다.
2. SQLite의 `BOOLEAN`은 INTEGER 0/1, 날짜는 TEXT ISO8601 또는 표준 datetime 규칙으로 선택.
3. `TB_SYS_UserBackupCode`는 목업 시드 빈 배열만 존재: 실제 기능 명세 없음.
4. 기존 localStorage의 단순 `hp()` 해시와 `totp_secret` 공개 구조를 서버에 이식하지 않는다.
5. PDF 메타데이터 `FileId=idb:`는 브라우저 데모 전용. 서버 저장 키는 별도 설계.
6. 마이그레이션은 실제 구현 시작 후 코드/테스트와 함께 작성; 이 문서만으로 원본 SQL 스키마를 확정하지 않는다.
