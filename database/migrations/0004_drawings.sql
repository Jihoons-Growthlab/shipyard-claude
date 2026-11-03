-- 0004_drawings: drawing, revision, approval, plan link (BR-08: block delete -> BlockId NULL)
CREATE TABLE TB_DWG_Drawing (
  DrawingId     INTEGER PRIMARY KEY AUTOINCREMENT,
  DrawingNo     TEXT NOT NULL UNIQUE,
  DrawingNm     TEXT NOT NULL,
  HullNo        TEXT NOT NULL REFERENCES TB_MST_Hull(HullNo) ON DELETE CASCADE ON UPDATE CASCADE,
  BlockId       INTEGER REFERENCES TB_MST_Block(BlockId) ON DELETE SET NULL,
  Discipline    TEXT,
  DwgStatus     TEXT NOT NULL DEFAULT 'DRAFT',
  CurrentRevNo  INTEGER NOT NULL DEFAULT 0,
  DesignerEmpNo TEXT REFERENCES users(emp_no) ON DELETE SET NULL ON UPDATE CASCADE,
  UseYN         INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1)),
  CreateUserId  TEXT,
  CreateDt      TEXT,
  ModifyUserId  TEXT,
  ModifyDt      TEXT
);
CREATE TABLE TB_DWG_Revision (
  DrawingId   INTEGER NOT NULL REFERENCES TB_DWG_Drawing(DrawingId) ON DELETE CASCADE,
  RevNo       INTEGER NOT NULL,
  RevStatus   TEXT NOT NULL DEFAULT 'DRAFT',
  ChangeDesc  TEXT,
  FileId      TEXT,
  FileNm      TEXT,
  AuthorEmpNo TEXT REFERENCES users(emp_no) ON DELETE SET NULL ON UPDATE CASCADE,
  IssueDt     TEXT,
  CreateDt    TEXT,
  PRIMARY KEY (DrawingId, RevNo)
);
CREATE TABLE TB_DWG_Approval (
  ApprovalId    INTEGER PRIMARY KEY AUTOINCREMENT,
  DrawingId     INTEGER NOT NULL,
  RevNo         INTEGER NOT NULL,
  StepNo        INTEGER NOT NULL,
  ApproverEmpNo TEXT REFERENCES users(emp_no) ON DELETE SET NULL ON UPDATE CASCADE,
  Result        TEXT NOT NULL DEFAULT 'WAIT' CHECK (Result IN ('WAIT','APPROVE','REJECT')),
  Comment       TEXT,
  ActDt         TEXT,
  UNIQUE (DrawingId, RevNo, StepNo),
  FOREIGN KEY (DrawingId, RevNo) REFERENCES TB_DWG_Revision(DrawingId, RevNo) ON DELETE CASCADE
);
CREATE TABLE TB_DWG_PlanLink (
  DrawingId  INTEGER NOT NULL REFERENCES TB_DWG_Drawing(DrawingId) ON DELETE CASCADE,
  PlanId     INTEGER NOT NULL REFERENCES TB_PRC_Plan(PlanId) ON DELETE CASCADE,
  RequiredYN INTEGER NOT NULL DEFAULT 1 CHECK (RequiredYN IN (0,1)),
  NeedDt     TEXT,
  PRIMARY KEY (DrawingId, PlanId)
);
