"""F01 AUTH-T01~T07."""
import time

from app import config
from app.security import STAGE_FULL, issue_token

from .conftest import current_otp, login

NEW = dict(last_name="홍", first_name="길동", birth_date="1999-01-01", phone="010-7777-0007",
           email="hong@swp.co.kr", emp_no="hong.gd", password="secret123", password_confirm="secret123")


def test_t01_approved_user_logs_in_and_reaches_protected_api(client):
    r = client.post("/api/auth/login", json={"emp_no": "park.pm", "password": "pm1234"})
    assert r.status_code == 200 and r.json()["otp_required"] is False
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    me = client.get("/api/auth/me", headers=h).json()
    assert me["emp_no"] == "park.pm" and me["groups"][0]["code"] == "PROC" and me["today"] == "2026-10-19"
    menu = client.get("/api/me/menu", headers=h).json()
    assert any(m["token"] == "dashboard" for m in menu)


def test_t01_wrong_password_generic_message(client):
    r = client.post("/api/auth/login", json={"emp_no": "park.pm", "password": "nope"})
    assert r.status_code == 401 and r.json()["message"] == "아이디 또는 비밀번호가 올바르지 않습니다."
    r2 = client.post("/api/auth/login", json={"emp_no": "ghost", "password": "nope"})
    assert r2.json() == r.json()


def test_t02_pending_rejected_disabled_are_refused_with_status_message(client, db):
    db.execute("UPDATE users SET status='rejected' WHERE emp_no='han.wk'")
    db.execute("UPDATE users SET status='disabled' WHERE emp_no='choi.qa'")
    cases = [("jung.new", "new12345", "ACCOUNT_PENDING", "승인 대기"),
             ("han.wk", "wk1234", "ACCOUNT_REJECTED", "반려"),
             ("choi.qa", "qa1234", "ACCOUNT_DISABLED", "중지")]
    for emp, pw, code, word in cases:
        r = client.post("/api/auth/login", json={"emp_no": emp, "password": pw})
        assert r.status_code == 403 and r.json()["code"] == code and word in r.json()["message"]
        assert "access_token" not in r.json()


def test_t03_totp_account_needs_second_factor(client):
    r = client.post("/api/auth/login", json={"emp_no": "admin", "password": "admin1234"})
    body = r.json()
    assert body["otp_required"] is True and "access_token" not in body
    otp_h = {"Authorization": f"Bearer {body['otp_token']}"}
    assert client.get("/api/auth/me", headers=otp_h).status_code == 401
    assert client.get("/api/me/menu", headers=otp_h).status_code == 401
    bad = client.post("/api/auth/otp/verify", json={"code": "123456" if current_otp() != "123456" else "000000"}, headers=otp_h)
    assert bad.status_code == 400 and bad.json()["code"] == "OTP_INVALID"
    ok = client.post("/api/auth/otp/verify", json={"code": current_otp()}, headers=otp_h)
    assert ok.status_code == 200
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {ok.json()['access_token']}"}).status_code == 200


def test_t03_otp_code_cannot_be_replayed_and_is_rate_limited(client):
    t1 = client.post("/api/auth/login", json={"emp_no": "admin", "password": "admin1234"}).json()["otp_token"]
    code = current_otp()
    assert client.post("/api/auth/otp/verify", json={"code": code}, headers={"Authorization": f"Bearer {t1}"}).status_code == 200
    t2 = client.post("/api/auth/login", json={"emp_no": "admin", "password": "admin1234"}).json()["otp_token"]
    h2 = {"Authorization": f"Bearer {t2}"}
    assert client.post("/api/auth/otp/verify", json={"code": code}, headers=h2).status_code == 400
    for _ in range(5):
        client.post("/api/auth/otp/verify", json={"code": "000000"}, headers=h2)
    assert client.post("/api/auth/otp/verify", json={"code": current_otp()}, headers=h2).status_code == 429


def test_t03_full_token_cannot_be_used_as_otp_token(client):
    h = login(client, "park.pm", "pm1234")
    assert client.post("/api/auth/otp/verify", json={"code": "000000"}, headers=h).status_code == 401


def test_t04_registration_validation_and_duplicates(client):
    bad_cases = [
        ({"last_name": ""}, "name"), ({"birth_date": ""}, "birth_date"), ({"email": "x@y"}, "email"),
        ({"phone": "02-123-4567"}, "phone"), ({"emp_no": "ab"}, "emp_no"),
        ({"password": "short", "password_confirm": "short"}, "password"), ({"password_confirm": "different1"}, "password_confirm"),
    ]
    for patch, field in bad_cases:
        r = client.post("/api/auth/register", json={**NEW, **patch})
        assert r.status_code == 400 and r.json()["details"]["field"] == field, (patch, r.text)
    dups = [({"emp_no": "park.pm"}, "emp_no"), ({"email": "PARK.PM@swp.co.kr"}, "email"), ({"phone": "01022220002"}, "phone")]
    for patch, field in dups:
        r = client.post("/api/auth/register", json={**NEW, **patch})
        assert r.status_code == 409 and r.json()["code"] == "DUPLICATE" and r.json()["details"]["field"] == field
    assert client.post("/api/auth/register", json={"emp_no": "x"}).status_code == 422


def test_t05_registered_user_is_pending_and_cannot_login_until_approved(client, db):
    r = client.post("/api/auth/register", json=NEW)
    assert r.status_code == 201 and r.json()["status"] == "pending"
    row = db.execute("SELECT status, phone, password_hash, totp_enabled FROM users WHERE emp_no='hong.gd'").fetchone()
    assert row["status"] == "pending" and row["phone"] == "010-7777-0007"
    assert row["password_hash"].startswith("$argon2id$") and row["totp_enabled"] == 0
    assert db.execute("SELECT COUNT(*) FROM TB_SYS_AuthUser WHERE EmpNo='hong.gd'").fetchone()[0] == 0
    assert client.post("/api/auth/register", json=NEW).status_code == 409
    r = client.post("/api/auth/login", json={"emp_no": "hong.gd", "password": "secret123"})
    assert r.status_code == 403 and r.json()["code"] == "ACCOUNT_PENDING"


def test_t06_logout_and_expiry_return_401(client, monkeypatch):
    h = login(client, "park.pm", "pm1234")
    assert client.post("/api/auth/logout", headers=h).status_code == 204
    assert client.get("/api/auth/me", headers=h).status_code == 401
    assert client.get("/api/me/menu", headers=h).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    # expired token
    h2 = login(client, "park.pm", "pm1234")
    from app.security import decode_token
    lid = decode_token(h2["Authorization"][7:])["lid"]
    expired = issue_token("park.pm", STAGE_FULL, ttl=10, log_id=lid, now=time.time() - 3600)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["code"] == "UNAUTHORIZED"


def test_t06_session_revoked_when_user_disabled(client, db):
    h = login(client, "park.pm", "pm1234")
    db.execute("UPDATE users SET status='disabled' WHERE emp_no='park.pm'")
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_t07_access_log_matches_account(client, db):
    h = login(client, "park.pm", "pm1234")
    login(client, "admin", "admin1234")
    rows = db.execute("SELECT LogId, UserId, LoginDt, LogoutDt FROM TB_SYS_LogAccess ORDER BY LogId").fetchall()
    assert [r["UserId"] for r in rows] == ["park.pm", "admin"]
    assert all(r["LoginDt"] and r["LogoutDt"] is None for r in rows)
    client.post("/api/auth/logout", headers=h)
    rows = db.execute("SELECT UserId, LogoutDt FROM TB_SYS_LogAccess ORDER BY LogId").fetchall()
    assert rows[0]["UserId"] == "park.pm" and rows[0]["LogoutDt"] is not None
    assert rows[1]["UserId"] == "admin" and rows[1]["LogoutDt"] is None


def test_secret_never_exposed(client):
    h = login(client, "admin", "admin1234")
    assert "totp_secret" not in client.get("/api/auth/me", headers=h).text
    assert config.settings.app_secret not in client.get("/api/auth/me", headers=h).text
