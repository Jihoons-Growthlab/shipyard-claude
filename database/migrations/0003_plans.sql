-- 0003_plans: process master, plan, dependency, progress (BR-08: block/plan delete cascades)
CREATE TABLE TB_PRC_Proc (
  ProcCd    TEXT PRIMARY KEY,
  ProcNm    TEXT NOT NULL,
  ProcGroup TEXT,
  StdDays   INTEGER,
  Seq       INTEGER NOT NULL DEFAULT 0,
  UseYN     INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1))
);
CREATE TABLE TB_PRC_Plan (
  PlanId        INTEGER PRIMARY KEY AUTOINCREMENT,
  HullNo        TEXT NOT NULL REFERENCES TB_MST_Hull(HullNo) ON DELETE CASCADE ON UPDATE CASCADE,
  BlockId       INTEGER REFERENCES TB_MST_Block(BlockId) ON DELETE CASCADE,
  ProcCd        TEXT NOT NULL REFERENCES TB_PRC_Proc(ProcCd),
  PlanStartDt   TEXT NOT NULL,
  PlanEndDt     TEXT NOT NULL,
  ActualStartDt TEXT,
  ActualEndDt   TEXT,
  ProgressRate  REAL NOT NULL DEFAULT 0 CHECK (ProgressRate BETWEEN 0 AND 100),
  PlanStatus    TEXT NOT NULL DEFAULT 'PLAN',
  ManagerEmpNo  TEXT REFERENCES users(emp_no) ON DELETE SET NULL ON UPDATE CASCADE,
  Remark        TEXT,
  CreateUserId  TEXT,
  CreateDt      TEXT,
  CHECK (PlanStartDt <= PlanEndDt)
);
CREATE TABLE TB_PRC_PlanDep (
  PlanId     INTEGER NOT NULL REFERENCES TB_PRC_Plan(PlanId) ON DELETE CASCADE,
  PredPlanId INTEGER NOT NULL REFERENCES TB_PRC_Plan(PlanId) ON DELETE CASCADE,
  LagDays    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (PlanId, PredPlanId),
  CHECK (PlanId <> PredPlanId)
);
CREATE TABLE TB_PRC_Progress (
  ProgressId   INTEGER PRIMARY KEY AUTOINCREMENT,
  PlanId       INTEGER NOT NULL REFERENCES TB_PRC_Plan(PlanId) ON DELETE CASCADE,
  WorkDt       TEXT NOT NULL,
  ProgressRate REAL NOT NULL CHECK (ProgressRate BETWEEN 0 AND 100),
  ManHour      REAL,
  WorkerCnt    INTEGER,
  WorkerEmpNo  TEXT REFERENCES users(emp_no) ON DELETE SET NULL ON UPDATE CASCADE,
  Remark       TEXT,
  CreateDt     TEXT,
  UNIQUE (PlanId, WorkDt)
);
