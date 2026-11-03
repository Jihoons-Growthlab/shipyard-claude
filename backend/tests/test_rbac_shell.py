"""Server-side RBAC (BR-09), admin approval (D15), SHELL-T01 server part, SHELL-08 logging."""
from .conftest import login

EXPECTED = {
    "admin": {"dashboard", "hull-list", "plan-gantt", "progress", "dwg-list", "dwg-approval", "user-mgmt"},
    "park.pm": {"dashboard", "hull-list", "plan-gantt", "progress", "dwg-list"},
    "lee.dwg": {"dashboard", "hull-list", "plan-gantt", "dwg-list", "dwg-approval"},
    "choi.qa": {"dashboard", "hull-list", "plan-gantt", "progress", "dwg-list", "dwg-approval"},
}
PW = {"admin": "admin1234", "park.pm": "pm1234", "lee.dwg": "dwg1234", "choi.qa": "qa1234"}


def test_menu_matches_group_permissions(client):
    for emp, tokens in EXPECTED.items():
        menu = client.get("/api/me/menu", headers=login(client, emp, PW[emp])).json()
        assert {m["token"] for m in menu if m["token"]} == tokens, emp
        ids = {m["menu_id"] for m in menu}
        assert all(m["parent_id"] is None or m["parent_id"] in ids for m in menu)
    view = {m["menu_id"]: m for m in client.get("/api/me/menu", headers=login(client, "choi.qa", "qa1234")).json()}
    assert view["M11"]["auth_gbn"] == "View" and view["M11"]["can_write"] is False
    proc = {m["menu_id"]: m for m in client.get("/api/me/menu", headers=login(client, "park.pm", "pm1234")).json()}
    assert proc["M22"]["can_write"] is True and proc["M31"]["can_write"] is False


def test_highest_gbn_across_groups(client, db):
    db.execute("INSERT INTO TB_SYS_AuthUser VALUES ('DWG','choi.qa')")
    menu = {m["menu_id"]: m for m in client.get("/api/me/menu", headers=login(client, "choi.qa", "qa1234")).json()}
    assert menu["M31"]["auth_gbn"] == "Write" and menu["M22"]["auth_gbn"] == "View"


def test_shell_t01_hidden_menu_direct_request_is_403(client, db):
    h = login(client, "lee.dwg", "dwg1234")  # DWG: no M22, no M91
    for mid in ("M22", "M91"):
        r = client.post("/api/me/menu-access", json={"menu_id": mid}, headers=h)
        assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"
    assert client.post("/api/users/jung.new/approve", json={"groups": ["VIEW"]}, headers=h).status_code == 403
    assert client.post("/api/me/menu-access", json={"menu_id": "M31"}, headers=h).status_code == 204
    rows = db.execute("SELECT MenuId FROM TB_SYS_LogMenuAccess").fetchall()
    assert [r[0] for r in rows] == ["M31"]


def test_missing_auth_is_401(client):
    assert client.get("/api/me/menu").status_code == 401
    assert client.post("/api/me/menu-access", json={"menu_id": "M00"}).status_code == 401
    assert client.post("/api/users/jung.new/approve", json={"groups": ["VIEW"]}).status_code == 401


def test_unauthorized_writes_are_403(client, db):
    for emp in ("choi.qa", "park.pm"):
        h = login(client, emp, PW[emp])
        assert client.post("/api/users/jung.new/approve", json={"groups": ["ADMIN"]}, headers=h).status_code == 403
        assert client.post("/api/users/jung.new/reject", headers=h).status_code == 403
    assert db.execute("SELECT status FROM users WHERE emp_no='jung.new'").fetchone()[0] == "pending"


def test_admin_approval_flow_enables_login(client, db):
    h = login(client, "admin", "admin1234")
    assert client.post("/api/users/jung.new/approve", json={"groups": []}, headers=h).status_code == 400
    assert client.post("/api/users/jung.new/approve", json={"groups": ["NOPE"]}, headers=h).status_code == 400
    assert client.post("/api/users/ghost/approve", json={"groups": ["VIEW"]}, headers=h).status_code == 404
    r = client.post("/api/users/jung.new/approve", json={"groups": ["VIEW"]}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert client.post("/api/users/jung.new/approve", json={"groups": ["VIEW"]}, headers=h).status_code == 409
    menu = client.get("/api/me/menu", headers=login(client, "jung.new", "new12345")).json()
    assert "user-mgmt" not in {m["token"] for m in menu} and "dashboard" in {m["token"] for m in menu}


def test_admin_reject(client):
    h = login(client, "admin", "admin1234")
    assert client.post("/api/users/jung.new/reject", headers=h).json()["status"] == "rejected"
    r = client.post("/api/auth/login", json={"emp_no": "jung.new", "password": "new12345"})
    assert r.json()["code"] == "ACCOUNT_REJECTED"


def test_migrations_are_repeatable_and_fk_on(db):
    from app.db import migrate
    assert migrate(db) == []
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    # BR-08: block delete clears drawing BlockId, cascades plans
    db.execute("INSERT INTO TB_MST_Hull (HullNo, HullNm) VALUES ('9999','T')")
    bid = db.execute("INSERT INTO TB_MST_Block (HullNo, BlockCd) VALUES ('9999','B1')").lastrowid
    db.execute("INSERT OR IGNORE INTO TB_PRC_Proc (ProcCd, ProcNm) VALUES ('CUT','절단')")
    db.execute("INSERT INTO TB_PRC_Plan (HullNo, BlockId, ProcCd, PlanStartDt, PlanEndDt) VALUES ('9999',?,'CUT','2026-10-01','2026-10-05')", (bid,))
    did = db.execute("INSERT INTO TB_DWG_Drawing (DrawingNo, DrawingNm, HullNo, BlockId) VALUES ('D1','d','9999',?)", (bid,)).lastrowid
    db.execute("DELETE FROM TB_MST_Block WHERE BlockId=?", (bid,))
    assert db.execute("SELECT BlockId FROM TB_DWG_Drawing WHERE DrawingId=?", (did,)).fetchone()[0] is None
    assert db.execute("SELECT COUNT(*) FROM TB_PRC_Plan").fetchone()[0] == 0
