-- 0001_system: users, auth groups, codes, menus, access logs (docs/architecture/02-data-model.md)
CREATE TABLE users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  emp_no        TEXT NOT NULL UNIQUE,
  status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','disabled')),
  auth_provider TEXT NOT NULL DEFAULT 'local',
  last_name     TEXT NOT NULL,
  first_name    TEXT NOT NULL,
  birth_date    TEXT NOT NULL,
  phone         TEXT NOT NULL,
  totp_enabled  INTEGER NOT NULL DEFAULT 0 CHECK (totp_enabled IN (0,1)),
  totp_secret   TEXT,
  created_at    TEXT NOT NULL
);
-- phone uniqueness compares digits only (OBS validateUser)
CREATE UNIQUE INDEX ux_users_phone_digits ON users (replace(phone, '-', ''));

CREATE TABLE TB_SYS_CodeGroup (
  CodeGroup     TEXT PRIMARY KEY,
  CodeGroupName TEXT NOT NULL,
  Seq           INTEGER NOT NULL DEFAULT 0,
  UseYN         INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1))
);
CREATE TABLE TB_SYS_Code (
  CodeGroup TEXT NOT NULL REFERENCES TB_SYS_CodeGroup(CodeGroup) ON DELETE CASCADE,
  Code      TEXT NOT NULL,
  CodeName  TEXT NOT NULL,
  Seq       INTEGER NOT NULL DEFAULT 0,
  UseYN     INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1)),
  PRIMARY KEY (CodeGroup, Code)
);

CREATE TABLE TB_SYS_AuthGroup (
  AuthCd TEXT PRIMARY KEY,
  AuthNm TEXT NOT NULL
);
CREATE TABLE TB_SYS_AuthUser (
  AuthCd TEXT NOT NULL REFERENCES TB_SYS_AuthGroup(AuthCd) ON DELETE CASCADE,
  EmpNo  TEXT NOT NULL REFERENCES users(emp_no) ON DELETE CASCADE ON UPDATE CASCADE,
  PRIMARY KEY (AuthCd, EmpNo)
);

CREATE TABLE TB_SYS_MenuInfo (
  MenuId   TEXT PRIMARY KEY,
  SystemId TEXT NOT NULL DEFAULT 'SHIP',
  ParentId TEXT REFERENCES TB_SYS_MenuInfo(MenuId) ON DELETE CASCADE,
  Title    TEXT NOT NULL,
  TokenUrl TEXT UNIQUE,
  Seq      INTEGER NOT NULL DEFAULT 0,
  UseYN    INTEGER NOT NULL DEFAULT 1 CHECK (UseYN IN (0,1))
);
CREATE TABLE TB_SYS_AuthMenu (
  MenuId  TEXT NOT NULL REFERENCES TB_SYS_MenuInfo(MenuId) ON DELETE CASCADE,
  AuthCd  TEXT NOT NULL REFERENCES TB_SYS_AuthGroup(AuthCd) ON DELETE CASCADE,
  AuthGbn TEXT NOT NULL CHECK (AuthGbn IN ('View','Write','Admin')),
  PRIMARY KEY (MenuId, AuthCd)
);

CREATE TABLE TB_SYS_LogAccess (
  LogId         INTEGER PRIMARY KEY AUTOINCREMENT,
  UserId        TEXT REFERENCES users(emp_no) ON DELETE SET NULL ON UPDATE CASCADE,
  LoginDt       TEXT NOT NULL,
  LogoutDt      TEXT,
  IpAddress     TEXT,
  ComputerNm    TEXT,
  WindowAccount TEXT
);
CREATE INDEX ix_logaccess_user ON TB_SYS_LogAccess (UserId);
CREATE TABLE TB_SYS_LogMenuAccess (
  AccIndex INTEGER PRIMARY KEY AUTOINCREMENT,
  MenuId   TEXT NOT NULL REFERENCES TB_SYS_MenuInfo(MenuId) ON DELETE CASCADE,
  LogId    INTEGER NOT NULL REFERENCES TB_SYS_LogAccess(LogId) ON DELETE CASCADE,
  InDt     TEXT NOT NULL
);
