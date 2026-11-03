"""F06 PROG-T01~T06 (API)."""
import pytest

from .conftest import login
from .test_plans import _id

pytestmark = pytest.mark.full_seed


@pytest.fixture
def pm(client):
    return login(client, "park.pm", "pm1234")


def _plan(db, pid):
    return db.execute("SELECT ProgressRate, ActualStartDt, ActualEndDt, PlanStatus FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()


def _put(client, h, pid, dt, **body):
    return client.put(f"/api/plans/{pid}/progress/{dt}", json=body, headers=h)


def test_t01_targets_default_active_and_include_done(client, pm):
    hs = client.get("/api/progress-hulls", headers=pm).json()
    assert hs["default_hull_no"] == next(h["hull_no"] for h in hs["hulls"] if h["hull_status"] == "BUILD")
    act = client.get("/api/hulls/8001/progress-targets", headers=pm).json()["plans"]
    assert act and {p["plan_status"] for p in act} <= {"READY", "WORK", "DELAY"}
    allp = client.get("/api/hulls/8001/progress-targets", params={"include_done": True}, headers=pm).json()["plans"]
    assert "DONE" in {p["plan_status"] for p in allp} and len(allp) > len(act)
    assert [p["label"] for p in allp][:2] == ["[101] 강재절단", "[101] 소조립"]  # block code asc, proc seq asc


def test_t02_same_day_upsert_and_t03_latest_rate(client, pm, db):
    pid = _id(db, "8004", "101", "CUT") if db.execute("SELECT 1 FROM TB_PRC_Plan WHERE HullNo='8004'").fetchone() else None
    if pid is None:  # 8004 has no plans: create one via F05
        b = db.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo='8004' AND BlockCd='101'").fetchone()[0]
        pid = client.post("/api/hulls/8004/plans", json={"block_id": b, "proc_cd": "CUT", "plan_start_dt": "2026-10-01",
                                                          "plan_end_dt": "2026-11-30"}, headers=pm).json()["plan_id"]
    assert _put(client, pm, pid, "2026-10-10", progress_rate=30, man_hour=8.5, worker_cnt=2, worker_emp_no="han.wk").status_code == 200
    r = _put(client, pm, pid, "2026-10-10", progress_rate=40, remark="수정")
    assert r.status_code == 200
    h = r.json()["history"]
    assert len(h) == 1 and h[0]["progress_rate"] == 40 and h[0]["remark"] == "수정" and h[0]["man_hour"] is None
    _put(client, pm, pid, "2026-10-15", progress_rate=50)
    _put(client, pm, pid, "2026-10-12", progress_rate=45)  # past date inserted out of order
    p = _plan(db, pid)
    assert p["ProgressRate"] == 50 and p["ActualStartDt"] == "2026-10-10" and p["ActualEndDt"] is None  # not 135
    assert p["PlanStatus"] == "WORK"
    hist = client.get(f"/api/plans/{pid}/progress", headers=pm).json()["history"]
    assert [x["work_dt"] for x in hist] == ["2026-10-15", "2026-10-12", "2026-10-10"]  # desc


@pytest.mark.parametrize("dt,body,field", [
    ("2026-10-20", {"progress_rate": 10}, "work_dt"),            # > TODAY
    ("not-a-date", {"progress_rate": 10}, "work_dt"),
    ("2026-10-10", {"progress_rate": -1}, "progress_rate"),
    ("2026-10-10", {"progress_rate": 101}, "progress_rate"),
    ("2026-10-10", {}, "progress_rate"),
    ("2026-10-10", {"progress_rate": 10, "worker_emp_no": "jung.new"}, "worker_emp_no"),  # pending user
])
def test_t04_validation(client, pm, db, dt, body, field):
    pid = _id(db, "8001", "301", "PAINT")
    r = _put(client, pm, pid, dt, **body)
    assert r.status_code == 400 and r.json()["details"]["field"] == field, r.text


def test_t05_done_then_delete_reverts(client, pm, db):
    pid = _id(db, "8001", "301", "PAINT")  # DELAY 60%, successor ERECT PLAN
    erect = _id(db, "8001", "301", "ERECT")
    before = _plan(db, pid)
    r = _put(client, pm, pid, "2026-10-19", progress_rate=100)
    assert r.status_code == 200 and r.json()["plan"]["plan_status"] == "DONE"
    p = _plan(db, pid)
    assert p["ProgressRate"] == 100 and p["ActualEndDt"] == "2026-10-19"
    assert _plan(db, erect)["PlanStatus"] in ("READY", "PLAN", "DELAY") and _plan(db, erect)["PlanStatus"] != "WORK"
    prog_id = next(x["progress_id"] for x in r.json()["history"] if x["work_dt"] == "2026-10-19")
    r = client.delete(f"/api/progress/{prog_id}", headers=pm)
    assert r.status_code == 200
    p = _plan(db, pid)
    # seed overrides Plan.ProgressRate=60 while latest history row is lower; recompute uses history (BR-05, mockup recomputePlan)
    latest = db.execute("SELECT ProgressRate FROM TB_PRC_Progress WHERE PlanId=? ORDER BY WorkDt DESC LIMIT 1", (pid,)).fetchone()[0]
    first = db.execute("SELECT MIN(WorkDt) FROM TB_PRC_Progress WHERE PlanId=?", (pid,)).fetchone()[0]
    assert (p["ProgressRate"], p["ActualStartDt"], p["ActualEndDt"], p["PlanStatus"]) == (latest, first, None, before["PlanStatus"])
    for x in client.get(f"/api/plans/{pid}/progress", headers=pm).json()["history"]:
        client.delete(f"/api/progress/{x['progress_id']}", headers=pm)
    p = _plan(db, pid)
    assert (p["ProgressRate"], p["ActualStartDt"], p["ActualEndDt"]) == (0, None, None)
    assert client.delete("/api/progress/999999", headers=pm).status_code == 404


def test_t06_view_only_writes_403(client, db):
    pid = _id(db, "8001", "301", "PAINT")
    qa = login(client, "choi.qa", "qa1234")  # VIEW group: M22 View
    assert client.get("/api/hulls/8001/progress-targets", headers=qa).status_code == 200
    assert client.get(f"/api/plans/{pid}/progress", headers=qa).status_code == 200
    assert _put(client, qa, pid, "2026-10-19", progress_rate=70).status_code == 403
    prog_id = db.execute("SELECT ProgressId FROM TB_PRC_Progress WHERE PlanId=? LIMIT 1", (pid,)).fetchone()[0]
    assert client.delete(f"/api/progress/{prog_id}", headers=qa).status_code == 403
    lee = login(client, "lee.dwg", "dwg1234")  # DWG: no M22
    assert client.get("/api/hulls/8001/progress-targets", headers=lee).status_code == 403


def test_d09_obs_no_gate_on_progress_input(client, pm, db):
    """D09 (OBS): drawing gate drives READY/PLAN only; first progress on a gated PLAN is accepted as in the mockup."""
    pid = _id(db, "8002", "401", "CUT")
    assert _plan(db, pid)["PlanStatus"] == "PLAN"
    r = _put(client, pm, pid, "2026-10-19", progress_rate=10)
    assert r.status_code == 200 and _plan(db, pid)["PlanStatus"] in ("WORK", "DELAY")
