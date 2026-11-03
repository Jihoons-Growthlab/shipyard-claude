"""F09 USR-T01~T08 (API). Admin = M91 Admin; D14 self-delete refused; D15 group required on approval."""
import pytest

from .conftest import login


@pytest.fixture
def adm(client):
    return login(client, "admin", "admin1234")


NEW = {"emp_no": "kim.new", "last_name": "김", "first_name": "신규", "birth_date": "1999-01-01", "phone": "010-9999-0009",
       "email": "kim.new@swp.co.kr", "password": "newpass12", "status": "approved", "group": "VIEW", "totp_enabled": False}


def _form(client, h, emp):
    u = client.get(f"/api/users/{emp}", headers=h).json()
    return {"last_name": u["last_name"], "first_name": u["first_name"], "birth_date": u["birth_date"], "phone": u["phone"],
            "email": u["email"], "status": u["status"], "group": (u["groups"] or [{}])[0].get("code"),
            "totp_enabled": u["totp_enabled"], "password": ""}


def test_t01_filters_and_counts(client, adm):
    allu = client.get("/api/users", headers=adm).json()
    assert allu["total"] == 6 and allu["pending"] == 1
    assert [u["emp_no"] for u in client.get("/api/users", params={"status": "pending"}, headers=adm).json()["users"]] == ["jung.new"]
    assert {u["emp_no"] for u in client.get("/api/users", params={"q": "3333"}, headers=adm).json()["users"]} == {"lee.dwg"}
    assert {u["emp_no"] for u in client.get("/api/users", params={"q": "도면"}, headers=adm).json()["users"]} == {"lee.dwg"}
    u = client.get("/api/users/lee.dwg", headers=adm).json()
    assert u["groups"] == [{"code": "DWG", "name": "도면관리자"}] and u["totp_enabled"] is True
    assert client.get("/api/users/nobody", headers=adm).status_code == 404
    assert [g["code"] for g in client.get("/api/auth-groups", headers=adm).json()] == ["ADMIN", "DWG", "PROC", "VIEW"]


@pytest.mark.parametrize("patch,field,code", [
    ({"emp_no": "admin"}, "emp_no", 409), ({"email": "ADMIN@swp.co.kr"}, "email", 409), ({"phone": "01011110001"}, "phone", 409),
    ({"phone": "02-123-4567"}, "phone", 400), ({"email": "bad@"}, "email", 400), ({"password": "short"}, "password", 400),
    ({"emp_no": "ab"}, "emp_no", 400), ({"last_name": " "}, "name", 400), ({"status": "boss"}, "status", 400),
    ({"group": "NOPE"}, "group", 400), ({"birth_date": ""}, "birth_date", 400),
])
def test_t02_create_validation(client, adm, patch, field, code):
    r = client.post("/api/users", json={**NEW, **patch}, headers=adm)
    assert r.status_code == code and r.json()["details"]["field"] == field, r.text


def test_t02_create_and_login(client, adm, db):
    r = client.post("/api/users", json={**NEW, "phone": "01099990009"}, headers=adm)
    assert r.status_code == 201
    u = r.json()
    assert (u["display_name"], u["phone"], u["status"], u["created_at"]) == ("김신규", "010-9999-0009", "approved", "2026-10-19")
    assert "password_hash" not in u and "totp_secret" not in u
    assert db.execute("SELECT id, auth_provider FROM users WHERE emp_no='kim.new'").fetchone()[:] == ("u-kim.new", "local")
    login(client, "kim.new", "newpass12")
    # OTP cannot be switched on without enrollment (D05) — demo secret is not handed out
    assert client.post("/api/users", json={**NEW, "emp_no": "kim.otp", "email": "o@x.kr", "phone": "010-9999-0010",
                                           "totp_enabled": True}, headers=adm).status_code == 409


def test_t03_blank_password_keeps_hash_and_edit_dup_rules(client, adm, db):
    before = db.execute("SELECT password_hash FROM users WHERE emp_no='park.pm'").fetchone()[0]
    f = _form(client, adm, "park.pm")
    r = client.patch("/api/users/park.pm", json={**f, "first_name": "공정2"}, headers=adm)
    assert r.status_code == 200 and r.json()["display_name"] == "박공정2"
    assert db.execute("SELECT password_hash FROM users WHERE emp_no='park.pm'").fetchone()[0] == before
    login(client, "park.pm", "pm1234")
    assert client.patch("/api/users/park.pm", json={**f, "email": "admin@swp.co.kr"}, headers=adm).status_code == 409
    assert client.patch("/api/users/park.pm", json={**f, "emp_no": "renamed"}, headers=adm).status_code == 400
    assert client.patch("/api/users/park.pm", json={**f, "password": "changed99"}, headers=adm).status_code == 200
    login(client, "park.pm", "changed99")


def test_t04_group_change_applies_immediately(client, adm):
    qa = login(client, "choi.qa", "qa1234")  # VIEW: no M91, M31 View
    assert client.post("/api/drawings", json={}, headers=qa).status_code == 403
    assert client.patch("/api/users/choi.qa", json={**_form(client, adm, "choi.qa"), "group": "DWG"}, headers=adm).status_code == 200
    assert client.post("/api/drawings", json={}, headers=qa).status_code == 400  # now M31 Write → reaches validation
    assert any(m["token"] == "dwg-approval" and m["can_write"] for m in client.get("/api/me/menu", headers=qa).json())
    f = _form(client, adm, "choi.qa")
    assert client.patch("/api/users/choi.qa", json={**f, "group": None}, headers=adm).json()["groups"] == []
    assert client.get("/api/drawings", headers=qa).status_code == 403
    # disabling takes effect on the existing session
    client.patch("/api/users/choi.qa", json={**f, "group": "VIEW", "status": "disabled"}, headers=adm)
    assert client.get("/api/me/menu", headers=qa).status_code == 401


def test_t05_pending_approval_then_login(client, adm):
    r = client.post("/api/auth/login", json={"emp_no": "jung.new", "password": "new12345"})
    assert r.status_code == 403
    assert client.post("/api/users/jung.new/approve", json={"groups": []}, headers=adm).status_code == 400  # D15
    assert client.post("/api/users/jung.new/approve", json={"groups": ["VIEW"]}, headers=adm).status_code == 200
    login(client, "jung.new", "new12345")
    assert client.post("/api/users/jung.new/approve", json={"groups": ["VIEW"]}, headers=adm).status_code == 409


def test_t06_self_delete_refused_and_delete_cleans_up(client, adm, db):
    assert client.delete("/api/users/admin", headers=adm).status_code == 409
    assert client.delete("/api/users/han.wk", headers=adm).status_code == 204
    assert db.execute("SELECT COUNT(*) FROM TB_SYS_AuthUser WHERE EmpNo='han.wk'").fetchone()[0] == 0
    assert client.delete("/api/users/han.wk", headers=adm).status_code == 404


def test_t07_non_admin_403(client):
    for emp, pw in (("lee.dwg", "dwg1234"), ("park.pm", "pm1234"), ("choi.qa", "qa1234")):
        h = login(client, emp, pw)
        for method, url, kw in [("get", "/api/users", {}), ("get", "/api/users/admin", {}), ("post", "/api/users", {"json": NEW}),
                                ("patch", "/api/users/admin", {"json": NEW}), ("delete", "/api/users/han.wk", {}),
                                ("post", "/api/users/jung.new/approve", {"json": {"groups": ["VIEW"]}}),
                                ("get", "/api/auth-groups", {})]:
            assert getattr(client, method)(url, headers=h, **kw).status_code == 403, (emp, url)
        assert client.get("/api/users/options", headers=h).status_code == 200  # F05/F07 assignee select unaffected


def test_t08_totp_secret_never_exposed_and_enrollment_required(client, adm, db):
    lst = client.get("/api/users", headers=adm).text
    assert "totp_secret" not in lst and "JBSWY3DPEHPK3PXP" not in lst and "password_hash" not in lst
    f = _form(client, adm, "park.pm")  # no secret enrolled
    r = client.patch("/api/users/park.pm", json={**f, "totp_enabled": True}, headers=adm)
    assert r.status_code == 409 and r.json()["code"] == "OTP_NOT_ENROLLED"
    f = _form(client, adm, "lee.dwg")  # enrolled: off then back on keeps the secret
    assert client.patch("/api/users/lee.dwg", json={**f, "totp_enabled": False}, headers=adm).json()["totp_enabled"] is False
    assert client.post("/api/auth/login", json={"emp_no": "lee.dwg", "password": "dwg1234"}).json()["otp_required"] is False
    assert client.patch("/api/users/lee.dwg", json={**f, "totp_enabled": True}, headers=adm).json()["totp_enabled"] is True
    assert db.execute("SELECT totp_secret IS NOT NULL FROM users WHERE emp_no='lee.dwg'").fetchone()[0] == 1
