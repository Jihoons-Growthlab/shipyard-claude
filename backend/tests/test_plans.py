"""F05 PLAN-T02~T09 (API). PLAN-T01 (zoom/filter/today/scroll) is UI: frontend/src/__tests__/plans.spec.js + Playwright."""
import pytest

from .conftest import login

pytestmark = pytest.mark.full_seed


@pytest.fixture
def pm(client):
    return login(client, "park.pm", "pm1234")


def _id(db, hull, block_cd, proc):
    sql = "SELECT p.PlanId FROM TB_PRC_Plan p LEFT JOIN TB_MST_Block b ON b.BlockId=p.BlockId WHERE p.HullNo=? AND p.ProcCd=? AND "
    if block_cd is None:
        return db.execute(sql + "p.BlockId IS NULL", (hull, proc)).fetchone()[0]
    return db.execute(sql + "b.BlockCd=?", (hull, proc, block_cd)).fetchone()[0]


def _block(db, hull, cd):
    return db.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo=? AND BlockCd=?", (hull, cd)).fetchone()[0]


def _status(db, pid):
    return db.execute("SELECT PlanStatus FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0]


def test_seed_scenario_and_list_order(client, pm, db):
    r = client.get("/api/hulls/8001/plans", headers=pm).json()
    labels = [p["label"] for p in r["plans"]]
    assert labels[:5] == ["[101] 강재절단", "[101] 소조립", "[101] 대조립", "[101] 도장", "[101] 탑재"]
    assert labels[-2:] == ["[호선] 진수", "[호선] 시운전"]                  # hull-wide plans last
    paint = next(p for p in r["plans"] if p["label"] == "[301] 도장")
    assert paint["plan_status"] == "DELAY" and paint["progress_rate"] == 60
    assert next(p for p in r["plans"] if p["label"] == "[301] 탑재")["plan_status"] == "PLAN"
    one = client.get("/api/hulls/8001/plans", params={"block_id": _block(db, "8001", "301")}, headers=pm).json()
    assert len(one["plans"]) == 5 and one["hull_progress"] == r["hull_progress"]  # whole-hull progress
    assert all(d["plan_id"] in {p["plan_id"] for p in one["plans"]} for d in one["deps"])
    w = client.get("/api/hulls/8002/plans", headers=pm).json()
    cut401 = next(p for p in w["plans"] if p["label"] == "[401] 강재절단")
    assert cut401["drawing_wait"] and cut401["blockers"][0]["drawing_no"] == "8002-HULL-401"
    hulls = client.get("/api/plan-hulls", headers=pm).json()
    assert next(h for h in hulls if h["hull_no"] == "8004")["plan_count"] == 0


def test_t02_create_update_validation(client, pm, db):
    base = {"block_id": _block(db, "8004", "101"), "proc_cd": "CUT", "plan_start_dt": "2026-11-01",
            "plan_end_dt": "2026-11-14", "manager_emp_no": "han.wk", "remark": "메모"}
    for patch, field in [({"plan_end_dt": "2026-10-01"}, "plan_end_dt"), ({"plan_start_dt": None}, "plan_start_dt"),
                         ({"manager_emp_no": "jung.new"}, "manager_emp_no"), ({"proc_cd": "XX"}, "proc_cd"),
                         ({"block_id": _block(db, "8001", "101")}, "block_id")]:
        r = client.post("/api/hulls/8004/plans", json={**base, **patch}, headers=pm)
        assert r.status_code == 400 and r.json()["details"]["field"] == field, (patch, r.text)
    r = client.post("/api/hulls/8004/plans", json=base, headers=pm)
    assert r.status_code == 201
    p = r.json()
    assert p["manager_nm"] == "한현장" and p["remark"] == "메모" and p["progress_rate"] == 0 and p["create_user_id"] == "park.pm"
    assert p["plan_status"] == "READY"  # no preds, no required links (BR-03)
    # update keeps progress/actuals
    pid = _id(db, "8001", "401", "PAINT")
    before = db.execute("SELECT ProgressRate, ActualStartDt FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()
    u = client.patch(f"/api/plans/{pid}", json={"remark": "수정", "manager_emp_no": None}, headers=pm).json()
    assert u["remark"] == "수정" and u["manager_emp_no"] is None
    assert (u["progress_rate"], u["actual_start_dt"]) == (before[0], before[1])
    assert client.patch(f"/api/plans/{pid}", json={"plan_end_dt": "2020-01-01"}, headers=pm).status_code == 400
    assert client.get("/api/plans/999999", headers=pm).status_code == 404


def test_t02_new_plan_without_preds_or_drawings_is_ready(client, pm):
    r = client.post("/api/hulls/8004/plans", json={"proc_cd": "CUT", "plan_start_dt": "2026-11-01", "plan_end_dt": "2026-11-14"}, headers=pm)
    assert r.json()["plan_status"] == "READY" and r.json()["block_id"] is None


def test_t03_self_and_cycle_rejected(client, pm, db):
    cut, sub, asm = (_id(db, "8003", "101", x) for x in ("CUT", "SUBASM", "ASM"))  # chain CUT->SUBASM->ASM
    r = client.put(f"/api/plans/{cut}/predecessors", json={"pred_plan_ids": [cut]}, headers=pm)
    assert r.status_code == 400 and r.json()["code"] == "PLAN_DEPENDENCY_SELF"
    r = client.put(f"/api/plans/{cut}/predecessors", json={"pred_plan_ids": [asm], "confirm_late_preds": True}, headers=pm)
    assert r.status_code == 400 and r.json()["code"] == "PLAN_DEPENDENCY_CYCLE"
    r = client.patch(f"/api/plans/{cut}", json={"pred_plan_ids": [sub], "confirm_late_preds": True}, headers=pm)
    assert r.json()["code"] == "PLAN_DEPENDENCY_CYCLE"
    other = _id(db, "8001", "101", "CUT")
    assert client.put(f"/api/plans/{asm}/predecessors", json={"pred_plan_ids": [other]}, headers=pm).status_code == 400
    assert db.execute("SELECT COUNT(*) FROM TB_PRC_PlanDep WHERE PlanId=?", (cut,)).fetchone()[0] == 0


def test_t04_late_predecessor_needs_confirmation(client, pm, db):
    cut, asm = _id(db, "8003", "101", "CUT"), _id(db, "8003", "201", "ASM")
    prev = db.execute("SELECT PredPlanId FROM TB_PRC_PlanDep WHERE PlanId=?", (asm,)).fetchall()
    late_pred = _id(db, "8003", "301", "ERECT")  # ends well after 201-ASM starts
    r = client.put(f"/api/plans/{asm}/predecessors", json={"pred_plan_ids": [late_pred]}, headers=pm)
    assert r.status_code == 409 and r.json()["code"] == "PRED_LATE_CONFIRM_REQUIRED"
    assert r.json()["details"]["late_pred_plan_ids"] == [late_pred]
    assert db.execute("SELECT PredPlanId FROM TB_PRC_PlanDep WHERE PlanId=?", (asm,)).fetchall() == prev  # cancel = unchanged
    r = client.put(f"/api/plans/{asm}/predecessors", json={"pred_plan_ids": [late_pred], "confirm_late_preds": True}, headers=pm)
    assert r.status_code == 200 and r.json()["pred_plan_ids"] == [late_pred]
    assert db.execute("SELECT LagDays FROM TB_PRC_PlanDep WHERE PlanId=?", (asm,)).fetchone()[0] == 0
    ok = client.put(f"/api/plans/{_id(db, '8003', '101', 'SUBASM')}/predecessors", json={"pred_plan_ids": [cut]}, headers=pm)
    assert ok.status_code == 200  # on-time predecessor: no confirmation needed


def _make_done(db, pid):
    db.execute("UPDATE TB_PRC_Plan SET ProgressRate=100 WHERE PlanId=?", (pid,))


def test_t05_ready_when_preds_done_and_required_issued(client, pm, db):
    # 8001-501: CUT DONE, SUBASM DONE, ASM WORK -> PAINT PLAN. Make ASM done -> PAINT READY (gate ok: no PAINT links)
    asm, paint = _id(db, "8001", "501", "ASM"), _id(db, "8001", "501", "PAINT")
    assert _status(db, paint) == "PLAN"
    _make_done(db, asm)
    client.patch(f"/api/plans/{paint}", json={"remark": "trigger"}, headers=pm)  # any write recomputes statuses
    assert _status(db, asm) == "DONE" and _status(db, paint) == "READY"


def test_t06_draft_required_drawing_blocks_until_issued(client, pm, db):
    cut = _id(db, "8002", "401", "CUT")  # no preds, required 8002-HULL-401 is REVIEW
    assert _status(db, cut) == "PLAN"
    d = db.execute("SELECT DrawingId FROM TB_DWG_Drawing WHERE DrawingNo='8002-HULL-401'").fetchone()[0]
    db.execute("UPDATE TB_DWG_Revision SET RevStatus='ISSUED', IssueDt='2026-10-18' WHERE DrawingId=?", (d,))
    db.execute("UPDATE TB_DWG_Drawing SET DwgStatus='ISSUED' WHERE DrawingId=?", (d,))
    client.patch(f"/api/plans/{cut}", json={}, headers=pm)
    assert _status(db, cut) == "READY"
    # APPROVED alone does not pass (BR-02)
    cut3 = _id(db, "8003", "101", "CUT")
    assert db.execute("SELECT DwgStatus FROM TB_DWG_Drawing WHERE DrawingNo='8003-HULL-101'").fetchone()[0] == "APPROVED"
    assert _status(db, cut3) == "PLAN"


def test_t07_delete_plan_leaves_no_orphans(client, pm, db):
    pid = _id(db, "8001", "301", "PAINT")  # has progress, pred (ASM), successor (ERECT), drawing links? (none for PAINT)
    d = db.execute("SELECT DrawingId FROM TB_DWG_Drawing WHERE DrawingNo='8001-HULL-101'").fetchone()[0]
    db.execute("INSERT INTO TB_DWG_PlanLink (DrawingId, PlanId, RequiredYN) VALUES (?,?,1)", (d, pid))
    erect = _id(db, "8001", "301", "ERECT")
    assert client.delete(f"/api/plans/{pid}", headers=pm).status_code == 204
    for sql in ("SELECT COUNT(*) FROM TB_PRC_Progress WHERE PlanId=?", "SELECT COUNT(*) FROM TB_PRC_PlanDep WHERE PlanId=?",
                "SELECT COUNT(*) FROM TB_PRC_PlanDep WHERE PredPlanId=?", "SELECT COUNT(*) FROM TB_DWG_PlanLink WHERE PlanId=?"):
        assert db.execute(sql, (pid,)).fetchone()[0] == 0, sql
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert db.execute("SELECT COUNT(*) FROM TB_DWG_Drawing WHERE DrawingId=?", (d,)).fetchone()[0] == 1
    assert _status(db, erect) in ("PLAN", "WORK", "READY", "DELAY")
    assert client.delete(f"/api/plans/{pid}", headers=pm).status_code == 404


def test_t08_link_unlink_recomputes_gate(client, pm, db):
    pid = _id(db, "8003", "101", "SUBASM")
    _make_done(db, _id(db, "8003", "101", "CUT"))
    client.patch(f"/api/plans/{pid}", json={}, headers=pm)
    assert _status(db, pid) == "READY"
    draft = db.execute("SELECT DrawingId FROM TB_DWG_Drawing WHERE DrawingNo='8003-PIPE-101'").fetchone()[0]  # DRAFT
    info = client.get(f"/api/plans/{pid}/drawings", headers=pm).json()
    assert draft in {d["drawing_id"] for d in info["available"]}
    r = client.post(f"/api/plans/{pid}/drawings", json={"drawing_id": draft}, headers=pm)
    assert r.status_code == 201 and r.json()["blockers"][0]["drawing_no"] == "8003-PIPE-101"
    assert r.json()["links"][0]["need_dt"] == db.execute("SELECT PlanStartDt FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0]
    assert _status(db, pid) == "PLAN"
    plan = next(p for p in client.get("/api/hulls/8003/plans", headers=pm).json()["plans"] if p["plan_id"] == pid)
    assert plan["drawing_wait"] is True                                  # gantt 📐 warning
    assert client.post(f"/api/plans/{pid}/drawings", json={"drawing_id": draft}, headers=pm).status_code == 409
    other_hull = db.execute("SELECT DrawingId FROM TB_DWG_Drawing WHERE HullNo='8001' LIMIT 1").fetchone()[0]
    assert client.post(f"/api/plans/{pid}/drawings", json={"drawing_id": other_hull}, headers=pm).status_code == 400
    assert client.delete(f"/api/plans/{pid}/drawings/{draft}", headers=pm).status_code == 204
    assert _status(db, pid) == "READY"
    # reference (not required) link does not block
    client.post(f"/api/plans/{pid}/drawings", json={"drawing_id": draft, "required": False}, headers=pm)
    assert _status(db, pid) == "READY"
    assert client.delete(f"/api/plans/{pid}/drawings/999999", headers=pm).status_code == 404


def test_t09_view_only_writes_403(client, db):
    h = login(client, "choi.qa", "qa1234")  # VIEW: M21 View
    pid = _id(db, "8001", "101", "CUT")
    assert client.get("/api/hulls/8001/plans", headers=h).status_code == 200
    assert client.get(f"/api/plans/{pid}/drawings", headers=h).status_code == 200
    calls = [("post", "/api/hulls/8001/plans", {"json": {"proc_cd": "CUT", "plan_start_dt": "2026-11-01", "plan_end_dt": "2026-11-02"}}),
             ("patch", f"/api/plans/{pid}", {"json": {"remark": "x"}}), ("delete", f"/api/plans/{pid}", {}),
             ("put", f"/api/plans/{pid}/predecessors", {"json": {"pred_plan_ids": []}}),
             ("post", f"/api/plans/{pid}/drawings", {"json": {"drawing_id": 1}}), ("delete", f"/api/plans/{pid}/drawings/1", {})]
    for m, url, kw in calls:
        assert getattr(client, m)(url, headers=h, **kw).status_code == 403, (m, url)
        assert getattr(client, m)(url, **kw).status_code == 401
    lee = login(client, "lee.dwg", "dwg1234")  # DWG: M21 View only
    assert client.patch(f"/api/plans/{pid}", json={"remark": "x"}, headers=lee).status_code == 403
    assert db.execute("SELECT Remark FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0] is None


def test_block_delete_recomputes_successors(client, pm, db):
    # LAUNCH (8003) waits on all ERECTs; removing blocks leaves remaining preds -> status recomputed without error
    bid = _block(db, "8003", "301")
    assert client.delete(f"/api/blocks/{bid}", headers=pm).status_code == 204
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
