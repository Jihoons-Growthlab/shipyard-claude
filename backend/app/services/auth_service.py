"""F01 auth business rules: login, TOTP second factor, registration, logout, session check."""
import re
import sqlite3
import threading

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from ..security import (STAGE_FULL, STAGE_OTP, hash_password, issue_token, utcnow_iso, verify_password,
                        verify_totp)
from . import rbac_service

STATUS_MSG = {
    "pending": ("ACCOUNT_PENDING", "관리자 승인 대기 중인 계정입니다."),
    "rejected": ("ACCOUNT_REJECTED", "가입이 반려된 계정입니다."),
    "disabled": ("ACCOUNT_DISABLED", "사용이 중지된 계정입니다."),
}
INVALID_LOGIN = "아이디 또는 비밀번호가 올바르지 않습니다."
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^01\d-?\d{3,4}-?\d{4}$")
ID_RE = re.compile(r"^[A-Za-z0-9._-]{4,20}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_OTP_FAILS = 5

# In-process guards (single-worker demo): OTP failures per pending token, and used TOTP steps per user.
_lock = threading.Lock()
_otp_fails: dict[str, int] = {}
_otp_used: dict[str, int] = {}


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def fmt_phone(p: str) -> str:
    d = _digits(p)
    if len(d) == 11:
        return f"{d[:3]}-{d[3:7]}-{d[7:]}"
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    return p


def public_user(conn: sqlite3.Connection, u: sqlite3.Row) -> dict:
    return {"emp_no": u["emp_no"], "display_name": u["display_name"], "email": u["email"], "status": u["status"],
            "totp_enabled": bool(u["totp_enabled"]), "groups": rbac_service.groups_of(conn, u["emp_no"]),
            "today": settings.business_date}


def _get_user(conn, emp_no: str):
    return conn.execute("SELECT * FROM users WHERE emp_no=?", (emp_no,)).fetchone()


def _start_session(conn, u, ip: str | None) -> dict:
    with transaction(conn):
        cur = conn.execute("INSERT INTO TB_SYS_LogAccess (UserId, LoginDt, IpAddress) VALUES (?,?,?)",
                           (u["emp_no"], utcnow_iso(), ip))
    token = issue_token(u["emp_no"], STAGE_FULL, settings.token_ttl, log_id=cur.lastrowid)
    return {"otp_required": False, "access_token": token, "token_type": "bearer",
            "expires_in": settings.token_ttl, "user": public_user(conn, u)}


def login(conn, emp_no: str, password: str, ip: str | None) -> dict:
    u = _get_user(conn, (emp_no or "").strip())
    if not u or not verify_password(password or "", u["password_hash"]):
        raise ApiError(401, "INVALID_CREDENTIALS", INVALID_LOGIN)
    if u["status"] != "approved":
        code, msg = STATUS_MSG[u["status"]]
        raise ApiError(403, code, msg)
    if u["totp_enabled"]:
        return {"otp_required": True, "otp_token": issue_token(u["emp_no"], STAGE_OTP, settings.otp_token_ttl),
                "expires_in": settings.otp_token_ttl}
    return _start_session(conn, u, ip)


def verify_otp(conn, claims: dict, code: str, ip: str | None) -> dict:
    jti, emp = claims.get("jti", ""), claims["sub"]
    with _lock:
        if _otp_fails.get(jti, 0) >= MAX_OTP_FAILS:
            raise ApiError(429, "OTP_LOCKED", "인증 시도 횟수를 초과했습니다. 다시 로그인하세요.")
    u = _get_user(conn, emp)
    if not u or u["status"] != "approved" or not u["totp_enabled"] or not u["totp_secret"]:
        raise ApiError(401, "UNAUTHORIZED", "다시 로그인하세요.")
    step = verify_totp(u["totp_secret"], (code or "").strip())
    with _lock:
        if step is None or _otp_used.get(emp, -1) >= step:
            _otp_fails[jti] = _otp_fails.get(jti, 0) + 1
            raise ApiError(400, "OTP_INVALID", "인증 코드가 올바르지 않습니다.")
        _otp_used[emp] = step
        _otp_fails.pop(jti, None)
    return _start_session(conn, u, ip)


def validate_registration(conn, d: dict) -> None:
    def bad(field, msg):
        raise ApiError(400, "VALIDATION_ERROR", msg, {"field": field})
    if not d.get("last_name", "").strip() or not d.get("first_name", "").strip():
        bad("name", "성과 이름을 입력하세요.")
    if not DATE_RE.match(d.get("birth_date") or ""):
        bad("birth_date", "생년월일을 입력하세요.")
    if not EMAIL_RE.match(d.get("email") or ""):
        bad("email", "이메일 형식이 올바르지 않습니다.")
    if not PHONE_RE.match(d.get("phone") or ""):
        bad("phone", "전화번호 형식(010-0000-0000)이 올바르지 않습니다.")
    if not ID_RE.match(d.get("emp_no") or ""):
        bad("emp_no", "아이디는 영문/숫자/._- 조합 4~20자입니다.")
    if len(d.get("password") or "") < 8:
        bad("password", "비밀번호는 8자 이상 입력하세요.")
    if d.get("password") != d.get("password_confirm"):
        bad("password_confirm", "비밀번호 확인이 일치하지 않습니다.")
    dup = [
        ("emp_no", "SELECT 1 FROM users WHERE emp_no=?", d["emp_no"], "이미 사용 중인 아이디입니다."),
        ("email", "SELECT 1 FROM users WHERE lower(email)=lower(?)", d["email"], "이미 등록된 이메일입니다."),
        ("phone", "SELECT 1 FROM users WHERE replace(phone,'-','')=?", _digits(d["phone"]), "이미 등록된 전화번호입니다."),
    ]
    for field, sql, val, msg in dup:
        if conn.execute(sql, (val,)).fetchone():
            raise ApiError(409, "DUPLICATE", msg, {"field": field})


def register(conn, d: dict) -> dict:
    d = {k: (v.strip() if isinstance(v, str) and k not in ("password", "password_confirm") else v) for k, v in d.items()}
    validate_registration(conn, d)
    try:
        with transaction(conn):
            conn.execute(
                "INSERT INTO users (id,email,password_hash,display_name,emp_no,status,auth_provider,last_name,first_name,"
                "birth_date,phone,totp_enabled,totp_secret,created_at) VALUES (?,?,?,?,?, 'pending','local',?,?,?,?,0,NULL,?)",
                ("u-" + d["emp_no"], d["email"], hash_password(d["password"]), d["last_name"] + d["first_name"],
                 d["emp_no"], d["last_name"], d["first_name"], d["birth_date"], fmt_phone(d["phone"]),
                 settings.business_date))
    except sqlite3.IntegrityError:  # concurrent duplicate
        raise ApiError(409, "DUPLICATE", "이미 등록된 사용자 정보입니다.")
    return {"emp_no": d["emp_no"], "status": "pending", "message": "가입 신청 완료. 관리자 승인 후 로그인할 수 있습니다."}


def logout(conn, log_id: int) -> None:
    with transaction(conn):
        conn.execute("UPDATE TB_SYS_LogAccess SET LogoutDt=? WHERE LogId=? AND LogoutDt IS NULL", (utcnow_iso(), log_id))


def resolve_session(conn, claims: dict):
    """AUTH-05/T06: full-stage token, open access log, user still approved."""
    if claims.get("stage") != STAGE_FULL or "lid" not in claims:
        return None
    log = conn.execute("SELECT UserId, LogoutDt FROM TB_SYS_LogAccess WHERE LogId=?", (claims["lid"],)).fetchone()
    if not log or log["LogoutDt"] is not None or log["UserId"] != claims["sub"]:
        return None
    u = _get_user(conn, claims["sub"])
    if not u or u["status"] != "approved":
        return None
    return u
