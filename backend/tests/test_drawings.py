"""F07 DWG-T01~T10 (API). Approve/reject are F08: approvals are completed directly in the DB here."""
from pathlib import Path

import pytest

from app import config
from .conftest import login
from .test_plans import _id

pytestmark = pytest.mark.full_seed
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def dw(client):
    return login(client, "lee.dwg", "dwg1234")  # DWG: M31 Write


def _did(db, no):
    return db.execute("SELECT DrawingId FROM TB_DWG_Drawing WHERE DrawingNo=?", (no,)).fetchone()[0]


def _upload(client, h, did, rev, data=PDF, name="a.pdf", ctype="application/pdf"):
    return client.post(f"/api/drawings/{did}/revisions/{rev}/pdf", params={"filename": name}, content=data,
                       headers={**h, "Content-Type": ctype})


def _approve_all(db, did, rev):  # stands in for F08
    db.execute("UPDATE TB_DWG_Approval SET Result='APPROVE' WHERE DrawingId=? AND RevNo=?", (did, rev))
    db.execute("UPDATE TB_DWG_Revision SET RevStatus='APPROVED' WHERE DrawingId=? AND RevNo=?", (did, rev))
    db.execute("UPDATE TB_DWG_Drawing SET DwgStatus='APPROVED' WHERE DrawingId=?", (did,))
    db.commit()


def _files():
    d = Path(config.settings.file_dir)
    return sorted(p.name for p in d.glob("*")) if d.exists() else []


def test_t01_filters_and_current_vs_latest_rev(client, dw, db):
    all_ = client.get("/api/drawings", headers=dw).json()
    assert len(all_) == 47
    r = client.get("/api/drawings", params={"hull_no": "8001", "discipline": "HULL", "q": "hull-201"}, headers=dw).json()
    assert [x["drawing_no"] for x in r] == ["8001-HULL-201"] and r[0]["current_rev_no"] == 2 == r[0]["latest_rev_no"]
    st = client.get("/api/drawings", params={"status": "APPROVED"}, headers=dw).json()
    assert st and all(x["dwg_status"] == "APPROVED" for x in st)
    # new DRAFT rev on an issued drawing: current stays 2, latest becomes 3
    did = _did(db, "8001-HULL-201")
    client.post(f"/api/drawings/{did}/revisions", json={"change_desc": "개정"}, headers=dw)
    x = client.get("/api/drawings", params={"q": "8001-HULL-201"}, headers=dw).json()[0]
    assert (x["current_rev_no"], x["latest_rev_no"], x["dwg_status"]) == (2, 3, "DRAFT")


def test_t02_create_validation_and_rev0(client, dw, db):
    base = {"drawing_no": "8004-HULL-NEW", "drawing_nm": "신규", "hull_no": "8004", "discipline": "HULL", "designer_emp_no": "lee.dwg"}
    for patch, field in [({"drawing_no": ""}, "drawing_no"), ({"drawing_nm": " "}, "drawing_nm"), ({"discipline": "XX"}, "discipline"),
                         ({"designer_emp_no": "jung.new"}, "designer_emp_no"), ({"hull_no": "9999"}, "hull_no")]:
        r = client.post("/api/drawings", json={**base, **patch}, headers=dw)
        assert r.status_code == 400 and r.json()["details"]["field"] == field, (patch, r.text)
    r = client.post("/api/drawings", json=base, headers=dw)
    assert r.status_code == 201
    d = r.json()
    assert (d["dwg_status"], d["current_rev_no"]) == ("DRAFT", 0)
    assert [(v["rev_no"], v["rev_status"], v["change_desc"], v["author_emp_no"]) for v in d["revisions"]] == [(0, "DRAFT", "최초 작성", "lee.dwg")]
    dup = client.post("/api/drawings", json=base, headers=dw)
    assert dup.status_code == 409 and dup.json()["code"] == "DUPLICATE"


def test_t03_block_must_match_hull_and_hull_immutable(client, dw, db):
    other = db.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo='8001' LIMIT 1").fetchone()[0]
    r = client.post("/api/drawings", json={"drawing_no": "X-1", "drawing_nm": "x", "hull_no": "8004", "discipline": "HULL",
                                           "block_id": other}, headers=dw)
    assert r.status_code == 400 and r.json()["details"]["field"] == "block_id"
    did = _did(db, "8001-HULL-201")
    assert client.patch(f"/api/drawings/{did}", json={"hull_no": "8002"}, headers=dw).json()["details"]["field"] == "hull_no"
    assert client.patch(f"/api/drawings/{did}", json={"drawing_no": "Z"}, headers=dw).json()["details"]["field"] == "drawing_no"
    r = client.patch(f"/api/drawings/{did}", json={"drawing_nm": "수정명", "block_id": None}, headers=dw)
    assert r.status_code == 200 and r.json()["drawing_nm"] == "수정명" and r.json()["block_id"] is None
    assert r.json()["modify_user_id"] == "lee.dwg" and r.json()["hull_no"] == "8001"


def test_t04_pdf_validation_and_draft_only(client, dw, db, monkeypatch):
    did = client.post("/api/drawings", json={"drawing_no": "8004-P", "drawing_nm": "p", "hull_no": "8004", "discipline": "PIPE"},
                      headers=dw).json()["drawing_id"]
    assert _upload(client, dw, did, 0, b"hello", "a.txt", "text/plain").json()["code"] == "INVALID_FILE_TYPE"
    assert _upload(client, dw, did, 0, b"not a pdf", "a.pdf").json()["code"] == "INVALID_FILE_TYPE"  # magic header
    monkeypatch.setattr(config.settings, "max_pdf_bytes", 64)
    r = _upload(client, dw, did, 0, PDF + b"x" * 64)
    assert r.status_code == 413 and r.json()["code"] == "FILE_TOO_LARGE"
    monkeypatch.setattr(config.settings, "max_pdf_bytes", 30 * 1024 * 1024)
    r = _upload(client, dw, did, 0, name="도면 A.pdf")
    assert r.status_code == 200 and r.json()["revisions"][0]["has_file"] and r.json()["revisions"][0]["file_nm"] == "도면 A.pdf"
    first = _files()
    assert len(first) == 1
    g = client.get(f"/api/drawings/{did}/revisions/0/pdf", headers=dw)
    assert g.status_code == 200 and g.content == PDF and g.headers["content-type"] == "application/pdf"
    _upload(client, dw, did, 0, PDF + b"%v2")  # replace: old file removed
    assert len(_files()) == 1 and _files() != first
    assert client.delete(f"/api/drawings/{did}/revisions/0/pdf", headers=dw).status_code == 200 and _files() == []
    # non-DRAFT revision: upload/delete refused
    issued = _did(db, "8001-HULL-201")
    assert _upload(client, dw, issued, 2).status_code == 409
    assert client.delete(f"/api/drawings/{issued}/revisions/2/pdf", headers=dw).status_code == 409
    assert _files() == []


def test_t05_no_upload_is_not_mistaken_for_file(client, dw, db):
    did = _did(db, "8001-HULL-201")
    d = client.get(f"/api/drawings/{did}", headers=dw).json()
    rev2 = next(r for r in d["revisions"] if r["rev_no"] == 2)
    assert rev2["has_file"] is False and rev2["file_nm"]  # seed FileNm only, no stored binary
    r = client.get(f"/api/drawings/{did}/revisions/2/pdf", headers=dw)
    assert r.status_code == 404 and r.json()["code"] == "NO_FILE"


def test_t06_new_rev_request_approve_issue(client, dw, db):
    did = _did(db, "8001-HULL-201")
    assert client.post(f"/api/drawings/{did}/revisions", json={"change_desc": ""}, headers=dw).status_code == 400
    d = client.post(f"/api/drawings/{did}/revisions", json={"change_desc": "보강"}, headers=dw).json()
    assert d["revisions"][0]["rev_no"] == 3 and d["revisions"][0]["rev_status"] == "DRAFT"
    assert next(r for r in d["revisions"] if r["rev_no"] == 2)["rev_status"] == "ISSUED"  # kept
    assert client.post(f"/api/drawings/{did}/revisions", json={"change_desc": "x"}, headers=dw).status_code == 409  # latest is DRAFT
    url = f"/api/drawings/{did}/revisions/3"
    assert client.post(url + "/issue", headers=dw).status_code == 409  # not approved
    same = client.post(url + "/request-approval", json={"reviewer_emp_no": "lee.dwg", "approver_emp_no": "lee.dwg"}, headers=dw)
    assert same.status_code == 400
    assert client.post(f"/api/drawings/{did}/revisions/2/request-approval",
                       json={"reviewer_emp_no": "lee.dwg", "approver_emp_no": "admin"}, headers=dw).status_code == 409
    d = client.post(url + "/request-approval", json={"reviewer_emp_no": "lee.dwg", "approver_emp_no": "admin"}, headers=dw).json()
    assert d["dwg_status"] == "REVIEW" and d["revisions"][0]["rev_status"] == "REVIEW"
    assert [(a["step_no"], a["approver_emp_no"], a["result"]) for a in d["approvals"] if a["rev_no"] == 3] == [(1, "lee.dwg", "WAIT"), (2, "admin", "WAIT")]
    _approve_all(db, did, 3)
    d = client.post(url + "/issue", headers=dw).json()
    revs = {r["rev_no"]: r for r in d["revisions"]}
    assert revs[3]["rev_status"] == "ISSUED" and revs[3]["issue_dt"] == "2026-10-19" and revs[2]["rev_status"] == "OBSOLETE"
    assert (d["current_rev_no"], d["dwg_status"]) == (3, "ISSUED")


def test_t07_issue_reopens_required_gate(client, dw, db):
    did = _did(db, "8002-HULL-401")  # REVIEW, required by 8002-[401] CUT (PLAN, drawing wait)
    pid = _id(db, "8002", "401", "CUT")
    assert db.execute("SELECT PlanStatus FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0] == "PLAN"
    rev = db.execute("SELECT MAX(RevNo) FROM TB_DWG_Revision WHERE DrawingId=?", (did,)).fetchone()[0]
    _approve_all(db, did, rev)
    d = client.post(f"/api/drawings/{did}/revisions/{rev}/issue", headers=dw).json()
    assert d["current_rev_no"] == rev
    p = client.get(f"/api/plans/{pid}", headers=login(client, "park.pm", "pm1234")).json()
    assert p["gate_ok"] and p["plan_status"] == "READY"
    # D10 preserved: a new DRAFT rev over the ISSUED one keeps the gate open
    client.post(f"/api/drawings/{did}/revisions", json={"change_desc": "개정"}, headers=dw)
    assert db.execute("SELECT PlanStatus FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0] == "READY"


def test_t08_link_unlink_and_impact_warning(client, dw, db):
    did = _did(db, "8001-HULL-201")  # Rev2 issued 2026-10-12 (within 30 days)
    d = client.get(f"/api/drawings/{did}/plans", headers=dw).json()
    assert d["impacts"] and all(i["rev_no"] == 2 and i["plan_status"] in ("WORK", "DONE", "DELAY") for i in d["impacts"])
    free = d["available_plans"][0]["plan_id"]
    r = client.post(f"/api/drawings/{did}/plans", json={"plan_id": free}, headers=dw)
    assert r.status_code == 201 and any(p["plan_id"] == free and p["required"] for p in r.json()["plans"])
    need = db.execute("SELECT NeedDt, (SELECT PlanStartDt FROM TB_PRC_Plan WHERE PlanId=?) FROM TB_DWG_PlanLink WHERE DrawingId=? AND PlanId=?",
                      (free, did, free)).fetchone()
    assert need[0] == need[1]
    assert client.post(f"/api/drawings/{did}/plans", json={"plan_id": free}, headers=dw).status_code == 409
    other = _id(db, "8002", "401", "CUT")
    assert client.post(f"/api/drawings/{did}/plans", json={"plan_id": other}, headers=dw).status_code == 400  # other hull
    r = client.delete(f"/api/drawings/{did}/plans/{free}", headers=dw)
    assert r.status_code == 200 and all(p["plan_id"] != free for p in r.json()["plans"])


def test_t09_delete_drawing_leaves_no_orphans(client, dw, db):
    did = client.post("/api/drawings", json={"drawing_no": "8001-DEL", "drawing_nm": "d", "hull_no": "8001", "discipline": "HULL"},
                      headers=dw).json()["drawing_id"]
    _upload(client, dw, did, 0)
    client.post(f"/api/drawings/{did}/revisions/0/request-approval", json={"reviewer_emp_no": "lee.dwg", "approver_emp_no": "admin"}, headers=dw)
    pid = _id(db, "8001", "101", "CUT")
    client.post(f"/api/drawings/{did}/plans", json={"plan_id": pid}, headers=dw)
    assert len(_files()) == 1
    assert client.delete(f"/api/drawings/{did}", headers=dw).status_code == 204
    for t in ("TB_DWG_Drawing", "TB_DWG_Revision", "TB_DWG_Approval", "TB_DWG_PlanLink"):
        assert db.execute(f"SELECT COUNT(*) FROM {t} WHERE DrawingId=?", (did,)).fetchone()[0] == 0, t
    assert _files() == [] and client.get(f"/api/drawings/{did}", headers=dw).status_code == 404


def test_hull_delete_removes_stored_pdfs(client, dw, db):
    did = _did(db, "8002-HULL-401")
    db.execute("UPDATE TB_DWG_Revision SET RevStatus='DRAFT' WHERE DrawingId=? AND RevNo=0", (did,))
    db.commit()
    assert _upload(client, dw, did, 0).status_code == 200 and len(_files()) == 1
    admin = login(client, "admin", "admin1234")
    assert client.delete("/api/hulls/8002", headers=admin).status_code == 204
    assert _files() == []


def test_t10_view_user_writes_403(client, db):
    qa = login(client, "choi.qa", "qa1234")  # VIEW: M31 View
    did = _did(db, "8003-HULL-101")
    assert client.get(f"/api/drawings/{did}", headers=qa).status_code == 200
    for method, url, kw in [("post", "/api/drawings", {"json": {}}), ("patch", f"/api/drawings/{did}", {"json": {}}),
                            ("delete", f"/api/drawings/{did}", {}), ("post", f"/api/drawings/{did}/revisions/0/issue", {}),
                            ("post", f"/api/drawings/{did}/revisions", {"json": {"change_desc": "x"}}),
                            ("delete", f"/api/drawings/{did}/revisions/0/pdf", {}),
                            ("post", f"/api/drawings/{did}/plans", {"json": {"plan_id": 1}})]:
        assert getattr(client, method)(url, headers=qa, **kw).status_code == 403, url
    assert _upload(client, qa, did, 0).status_code == 403
    assert db.execute("SELECT DwgStatus FROM TB_DWG_Drawing WHERE DrawingId=?", (did,)).fetchone()[0] == "APPROVED"
