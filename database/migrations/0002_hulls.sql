-- 0002_hulls: hull, milestone, block
CREATE TABLE TB_MST_Hull (
  HullNo       TEXT PRIMARY KEY,
  HullNm       TEXT NOT NULL,
  ShipType     TEXT,
  HullStatus   TEXT,
  OwnerNm      TEXT,
  ClassSociety TEXT,
  LengthM      REAL,
  BreadthM     REAL,
  DepthM       REAL,
  DeadWeight   REAL,
  DockNo       TEXT,
  ContractDt   TEXT,
  DeliveryDt   TEXT,
  Remark       TEXT,
  UseYN        INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1)),
  CreateUserId TEXT,
  CreateDt     TEXT,
  ModifyUserId TEXT,
  ModifyDt     TEXT
);
CREATE TABLE TB_MST_HullMilestone (
  HullNo      TEXT NOT NULL REFERENCES TB_MST_Hull(HullNo) ON DELETE CASCADE ON UPDATE CASCADE,
  MilestoneCd TEXT NOT NULL,
  PlanDt      TEXT,
  ActualDt    TEXT,
  Remark      TEXT,
  PRIMARY KEY (HullNo, MilestoneCd)
);
CREATE TABLE TB_MST_Block (
  BlockId       INTEGER PRIMARY KEY AUTOINCREMENT,
  HullNo        TEXT NOT NULL REFERENCES TB_MST_Hull(HullNo) ON DELETE CASCADE ON UPDATE CASCADE,
  BlockCd       TEXT NOT NULL,
  BlockNm       TEXT,
  BlockType     TEXT,
  ParentBlockId INTEGER REFERENCES TB_MST_Block(BlockId) ON DELETE SET NULL,
  WeightTon     REAL,
  UseYN         INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1)),
  UNIQUE (HullNo, BlockCd)
);
