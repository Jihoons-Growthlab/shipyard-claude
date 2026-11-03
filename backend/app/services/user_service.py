"""F09 user management (M91 Admin): list/detail/create/update/delete + pending approval (D15: group required).
Validation reuses F01 auth_service rules; RBAC changes take effect on the next request (rbac_service reads per call)."""
import sqlite3

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from ..security import hash_password
from .auth_service import DATE_RE, EMAIL_RE, ID_RE, PHONE_RE, _digits, fmt_phone
from .rbac_service import groups_of

STATUSES = ("pending", "approved", "rejected", "disabled")


def _pending(conn, emp_no: str):
    u = conn.execute("SELECT emp_no, status FROM users WHERE emp_no=?", (emp_no,)).fetchone()
    if not u:
        raise ApiError(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")
    if u["status"] != "pending":
        raise ApiError(409, "INVALID_STATUS", "승인 대기 상태가 아닙니다.", {"status": u["status"]})
    return u


def approve(conn, emp_no: str, groups: list[str]) -> dict:
    groups = sorted(set(groups or []))
    if not groups:
        raise ApiError(400, "VALIDATION_ERROR", "승인 시 권한 그룹을 1개 이상 지정하세요.", {"field": "groups"})
    known = {r[0] for r in conn.execute("SELECT AuthCd FROM TB_SYS_AuthGroup")}
    unknown = [g for g in groups if g not in known]
    if unknown:
        raise ApiError(400, "VALIDATION_ERROR", "존재하지 않는 권한 그룹입니다.", {"groups": unknown})
    with transaction(conn):
        _pending(conn, emp_no)
        conn.execute("UPDATE users SET status='approved' WHERE emp_no=?", (emp_no,))
        conn.executemany("INSERT OR IGNORE INTO TB_SYS_AuthUser (AuthCd, EmpNo) VALUES (?,?)", [(g, emp_no) for g in groups])
    return {"emp_no": emp_no, "status": "approved", "groups": groups}


def reject(conn, emp_no: str) -> dict:
    with transaction(conn):
        _pending(conn, emp_no)
        conn.execute("UPDATE users SET status='rejected' WHERE emp_no=?", (emp_no,))
    return {"emp_no": emp_no, "status": "rejected"}


# ---------------- USR-01 list / detail ----------------
def _out(conn, u) -> dict:  # never exposes password_hash / totp_secret (USR-T08)
    return {"emp_no": u["emp_no"], "last_name": u["last_name"], "first_name": u["first_name"], "display_name": u["display_name"],
            "email": u["email"], "phone": u["phone"], "birth_date": u["birth_date"], "status": u["status"],
            "totp_enabled": bool(u["totp_enabled"]), "groups": groups_of(conn, u["emp_no"]), "created_at": u["created_at"]}


def list_users(conn, status: str | None = None, q: str | None = None) -> dict:
    sql, args = "SELECT * FROM users WHERE 1=1", []
    if status:
        sql += " AND status=?"
        args.append(status)
    if q:
        sql += " AND instr(lower(emp_no || display_name || email || phone), lower(?)) > 0"
        args.append(q.strip())
    rows = [_out(conn, u) for u in conn.execute(sql + " ORDER BY created_at, emp_no", args)]
    pending = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
    return {"users": rows, "total": len(rows), "pending": pending}


def _user(conn, emp_no):
    u = conn.execute("SELECT * FROM users WHERE emp_no=?", (emp_no,)).fetchone()
    if not u:
        raise ApiError(404, "USER_NOT_FOUND", "사용자를 찾을 수 없습니다.")
    return u


def get_user(conn, emp_no: str) -> dict:
    return _out(conn, _user(conn, emp_no))


def auth_groups(conn) -> list[dict]:
    return [{"code": r[0], "name": r[1]} for r in conn.execute("SELECT AuthCd, AuthNm FROM TB_SYS_AuthGroup ORDER BY AuthCd")]


# ---------------- USR-02 create / update ----------------
def _validate(conn, d: dict, editing: str | None) -> dict:
    def bad(field, msg, status=400, code="VALIDATION_ERROR"):
        raise ApiError(status, code, msg, {"field": field})
    d = {k: (v.strip() if isinstance(v, str) and k != "password" else v) for k, v in d.items()}
    if not d.get("last_name") or not d.get("first_name"):
        bad("name", "성과 이름을 입력하세요.")
    if not DATE_RE.match(d.get("birth_date") or ""):
        bad("birth_date", "생년월일을 입력하세요.")
    if not EMAIL_RE.match(d.get("email") or ""):
        bad("email", "이메일 형식이 올바르지 않습니다.")
    if not PHONE_RE.match(d.get("phone") or ""):
        bad("phone", "전화번호 형식(010-0000-0000)이 올바르지 않습니다.")
    if editing is None and not ID_RE.match(d.get("emp_no") or ""):
        bad("emp_no", "아이디는 영문/숫자/._- 조합 4~20자입니다.")
    pw = d.get("password") or ""
    if (editing is None or pw) and len(pw) < 8:
        bad("password", "비밀번호는 8자 이상 입력하세요.")
    if d.get("status") not in STATUSES:
        bad("status", "허용되지 않는 상태입니다.")
    grp = d.get("group") or None
    if grp and not conn.execute("SELECT 1 FROM TB_SYS_AuthGroup WHERE AuthCd=?", (grp,)).fetchone():
        bad("group", "존재하지 않는 권한 그룹입니다.")
    me = editing or d["emp_no"]
    dups = [("emp_no", "SELECT 1 FROM users WHERE emp_no=?", d.get("emp_no"), "이미 사용 중인 아이디입니다.")] if editing is None else []
    dups += [("email", "SELECT 1 FROM users WHERE lower(email)=lower(?) AND emp_no<>?", d["email"], "이미 등록된 이메일입니다."),
             ("phone", "SELECT 1 FROM users WHERE replace(phone,'-','')=? AND emp_no<>?", _digits(d["phone"]), "이미 등록된 전화번호입니다.")]
    for field, sql, val, msg in dups:
        if conn.execute(sql, (val,) if sql.count("?") == 1 else (val, me)).fetchone():
            bad(field, msg, 409, "DUPLICATE")
    return {**d, "group": grp, "phone": fmt_phone(d["phone"])}


def _set_group(conn, emp_no, grp):  # USR-02: single group replaces existing assignments
    conn.execute("DELETE FROM TB_SYS_AuthUser WHERE EmpNo=?", (emp_no,))
    if grp:
        conn.execute("INSERT INTO TB_SYS_AuthUser (AuthCd, EmpNo) VALUES (?,?)", (grp, emp_no))


def create_user(conn, data: dict) -> dict:
    data = {**data, "status": data.get("status") or "approved"}  # USR-01 new-user default
    if data.get("totp_enabled"):  # no server-side enrollment yet (D05); demo secret is not issued to new users
        raise ApiError(409, "OTP_NOT_ENROLLED", "2차 인증은 등록 절차(D05) 이후 사용할 수 있습니다.", {"field": "totp_enabled"})
    try:
        with transaction(conn):
            d = _validate(conn, data, None)
            conn.execute(
                "INSERT INTO users (id,email,password_hash,display_name,emp_no,status,auth_provider,last_name,first_name,"
                "birth_date,phone,totp_enabled,totp_secret,created_at) VALUES (?,?,?,?,?,?,'local',?,?,?,?,0,NULL,?)",
                ("u-" + d["emp_no"], d["email"], hash_password(d["password"]), d["last_name"] + d["first_name"], d["emp_no"],
                 d["status"], d["last_name"], d["first_name"], d["birth_date"], d["phone"], settings.business_date))
            _set_group(conn, d["emp_no"], d["group"])
    except sqlite3.IntegrityError:
        raise ApiError(409, "DUPLICATE", "이미 등록된 사용자 정보입니다.")
    return get_user(conn, d["emp_no"])


def update_user(conn, emp_no: str, data: dict) -> dict:
    if data.get("emp_no") not in (None, emp_no):
        raise ApiError(400, "VALIDATION_ERROR", "아이디는 변경할 수 없습니다.", {"field": "emp_no"})
    try:
        with transaction(conn):
            u = _user(conn, emp_no)
            d = _validate(conn, data, emp_no)
            totp = bool(d.get("totp_enabled"))
            if totp and not u["totp_secret"]:
                raise ApiError(409, "OTP_NOT_ENROLLED", "2차 인증 secret이 등록되지 않은 사용자입니다. (D05)", {"field": "totp_enabled"})
            conn.execute("UPDATE users SET email=?, display_name=?, last_name=?, first_name=?, birth_date=?, phone=?, status=?, "
                         "totp_enabled=? WHERE emp_no=?",  # secret kept on disable so re-enable works without re-enrollment
                         (d["email"], d["last_name"] + d["first_name"], d["last_name"], d["first_name"], d["birth_date"],
                          d["phone"], d["status"], int(totp), emp_no))
            if d.get("password"):
                conn.execute("UPDATE users SET password_hash=? WHERE emp_no=?", (hash_password(d["password"]), emp_no))
            _set_group(conn, emp_no, d["group"])
    except sqlite3.IntegrityError:
        raise ApiError(409, "DUPLICATE", "이미 등록된 사용자 정보입니다.")
    return get_user(conn, emp_no)


# ---------------- USR-03 delete ----------------
def delete_user(conn, emp_no: str, me: str) -> None:
    """D14: self-delete refused; AuthUser cascades, assignee/author/approver/log refs SET NULL (schema FKs)."""
    if emp_no == me:
        raise ApiError(409, "SELF_DELETE", "로그인 중인 본인 계정은 삭제할 수 없습니다.")
    with transaction(conn):
        _user(conn, emp_no)
        conn.execute("DELETE FROM users WHERE emp_no=?", (emp_no,))
