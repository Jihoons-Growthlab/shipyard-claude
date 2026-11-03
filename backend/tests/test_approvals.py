"""F08 APV-T01~T06 + D11 (approve/reject = M33 Write + assigned current approver; issue = M31 Write + completed approval)."""
import pytest

from .conftest import login
from .test_drawings import _did
from .test_plans import _id

pytestmark = pytest.mark.full_seed


@pytest.fixture
def lee(client):
    return login(client, "lee.dwg", "dwg1234")  # DWG: M31/M33 Write, step-1 reviewer in seed


@pytest.fixture
def adm(client):
    return login(client, "admin", "admin1234")  # step-2 approver in seed


def _apv(db, no, step):
    return db.execute("SELECT a.ApprovalId FROM TB_DWG_Approval a JOIN TB_DWG_Drawing d USING(DrawingId) "
                      "WHERE d.DrawingNo=? AND a.StepNo=? ORDER BY a.RevNo DESC LIMIT 1", (no, step)).fetchone()[0]


def _decide(client, h, aid, result, comment=None):
    return client.post(f"/api/approvals/{aid}/decision", json={"result": result, "comment": comment}, headers=h)


def _status(db, did):
    return db.execute("SELECT d.DwgStatus, r.RevStatus FROM TB_DWG_Drawing d JOIN TB_DWG_Revision r ON r.DrawingId=d.DrawingId "
                      "WHERE d.DrawingId=? ORDER BY r.RevNo DESC LIMIT 1", (did,)).fetchone()


def test_t01_step2_hidden_until_step1_approved(client, lee, adm, db):
    nos = lambda h: {w["drawing_no"] for w in client.get("/api/approvals/inbox", headers=h).json()["waiting"]}
    assert "8003-HULL-201" not in nos(adm) and "8003-HULL-201" in nos(lee)
    assert "8002-HULL-401" in nos(adm)  # step 1 already approved in seed
    # direct API call out of order is refused too
    assert _decide(client, adm, _apv(db, "8003-HULL-201", 2), "APPROVE").status_code == 409
    assert _decide(client, lee, _apv(db, "8003-HULL-201", 1), "APPROVE", "").status_code == 200
    assert "8003-HULL-201" in nos(adm)
    row = db.execute("SELECT Result, Comment, ActDt FROM TB_DWG_Approval WHERE ApprovalId=?", (_apv(db, "8003-HULL-201", 1),)).fetchone()
    assert (row[0], row[1]) == ("APPROVE", "승인") and row[2].startswith("2026-10-19 ")


def test_t02_unassigned_or_processed_refused(client, lee, adm, db):
    aid = _apv(db, "8002-HULL-401", 2)  # assigned to admin
    assert _decide(client, lee, aid, "APPROVE").status_code == 403
    assert _decide(client, lee, aid, "REJECT", "x").status_code == 403
    qa = login(client, "choi.qa", "qa1234")  # M33 View only
    assert client.get("/api/approvals/inbox", headers=qa).status_code == 200
    assert _decide(client, qa, aid, "APPROVE").status_code == 403
    pm = login(client, "park.pm", "pm1234")  # no M33
    assert client.get("/api/approvals/inbox", headers=pm).status_code == 403
    assert _decide(client, adm, aid, "MAYBE").status_code == 400
    assert _decide(client, adm, 999999, "APPROVE").status_code == 404
    assert _decide(client, lee, _apv(db, "8002-HULL-401", 1), "APPROVE").status_code == 409  # already approved
    assert _decide(client, adm, _apv(db, "8001-ELEC-401", 2), "APPROVE").status_code == 409  # rev already APPROVED


def test_t03_reject_requires_comment_and_keeps_history(client, lee, db):
    no = "8003-HULL-201"
    did, aid = _did(db, no), _apv(db, no, 1)
    r = _decide(client, lee, aid, "REJECT", "  ")
    assert r.status_code == 400 and r.json()["details"]["field"] == "comment"
    assert _decide(client, lee, aid, "REJECT", "치수 오류").status_code == 200
    assert tuple(_status(db, did)) == ("DRAFT", "DRAFT")
    rows = db.execute("SELECT StepNo, Result, Comment FROM TB_DWG_Approval WHERE DrawingId=? AND RevNo=0", (did,)).fetchall()
    assert [tuple(x) for x in rows] == [(1, "REJECT", "치수 오류")]  # WAIT step 2 removed, reject kept
    h = {x["approval_id"]: x for x in client.get("/api/approvals/history", headers=lee).json()}
    assert (h[aid]["drawing_no"], h[aid]["result"], h[aid]["comment"]) == (no, "REJECT", "치수 오류")
    assert _decide(client, lee, aid, "APPROVE").status_code == 409  # no longer pending


def test_t04_t05_full_approval_then_issue(client, lee, adm, db):
    no = "8002-HULL-401"
    did, pid = _did(db, no), _id(db, "8002", "401", "CUT")
    # issue before approval completes is refused
    assert client.post(f"/api/drawings/{did}/revisions/0/issue", headers=lee).status_code == 409
    body = _decide(client, adm, _apv(db, no, 2), "APPROVE", "OK").json()
    assert tuple(_status(db, did)) == ("APPROVED", "APPROVED")
    ready = next(x for x in body["ready"] if x["drawing_no"] == no)
    assert ready["rev_no"] == 0 and any(p.startswith("[401]") for p in ready["effect_plans"])  # linked PLAN-status CUT
    inbox = client.get("/api/approvals/inbox", headers=lee).json()
    assert inbox["can_issue"] is True and no in {x["drawing_no"] for x in inbox["ready"]}
    # D11: issue needs M31 Write; a M33/M31-View user cannot
    qa = login(client, "choi.qa", "qa1234")
    assert client.get("/api/approvals/inbox", headers=qa).json()["can_issue"] is False
    assert client.post(f"/api/drawings/{did}/revisions/0/issue", headers=qa).status_code == 403
    d = client.post(f"/api/drawings/{did}/revisions/0/issue", headers=lee).json()
    assert (d["dwg_status"], d["current_rev_no"]) == ("ISSUED", 0)
    assert db.execute("SELECT PlanStatus FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0] == "READY"
    assert no not in {x["drawing_no"] for x in client.get("/api/approvals/inbox", headers=lee).json()["ready"]}


def test_t05_issue_obsoletes_previous_and_requires_complete_steps(client, lee, adm, db):
    did = _did(db, "8001-HULL-201")  # latest ISSUED Rev2
    client.post(f"/api/drawings/{did}/revisions", json={"change_desc": "보강"}, headers=lee)
    client.post(f"/api/drawings/{did}/revisions/3/request-approval", json={"reviewer_emp_no": "lee.dwg", "approver_emp_no": "admin"}, headers=lee)
    # forged APPROVED rev without completed steps cannot be issued
    db.execute("UPDATE TB_DWG_Revision SET RevStatus='APPROVED' WHERE DrawingId=? AND RevNo=3", (did,)); db.commit()
    r = client.post(f"/api/drawings/{did}/revisions/3/issue", headers=lee)
    assert r.status_code == 409 and r.json()["code"] == "APPROVAL_INCOMPLETE"
    db.execute("UPDATE TB_DWG_Revision SET RevStatus='REVIEW' WHERE DrawingId=? AND RevNo=3", (did,)); db.commit()
    a1 = db.execute("SELECT ApprovalId FROM TB_DWG_Approval WHERE DrawingId=? AND RevNo=3 AND StepNo=1", (did,)).fetchone()[0]
    assert _decide(client, lee, a1, "APPROVE").status_code == 200
    assert _decide(client, adm, a1 + 1, "APPROVE").status_code == 200
    d = client.post(f"/api/drawings/{did}/revisions/3/issue", headers=lee).json()
    revs = {r["rev_no"]: r["rev_status"] for r in d["revisions"]}
    assert (revs[3], revs[2], d["current_rev_no"]) == ("ISSUED", "OBSOLETE", 3)


def test_t06_history_desc_top10_and_empty(client, lee, db):
    h = client.get("/api/approvals/history", headers=lee).json()
    assert 0 < len(h) <= 10
    assert [x["act_dt"] for x in h] == sorted((x["act_dt"] for x in h), reverse=True)
    assert all(x["result"] != "WAIT" for x in h)
    db.execute("DELETE FROM TB_DWG_Approval WHERE Result<>'WAIT'"); db.commit()
    assert client.get("/api/approvals/history", headers=lee).json() == []
