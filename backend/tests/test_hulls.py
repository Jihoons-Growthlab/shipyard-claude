"""F04 HULL-T01~T08 (API level). UI double-click/subtab parts: frontend/src/__tests__/hulls.spec.js + Playwright smoke."""
import pytest

from .conftest import login


@pytest.fixture
def pm(client):  # PROC: M11 Write
    return login(client, "park.pm", "pm1234")


@pytest.fixture
def viewer(client):  # VIEW: M11 View
    return login(client, "choi.qa", "qa1234")


NEW = {"hull_no": "9001", "hull_nm": "Test Ship", "ship_type": "LNG", "owner_nm": "Acme",
       "contract_dt": "2026-01-01", "delivery_dt": "2027-12-31", "length_m": 100.25}


def _plan(db, hull, block, rate, start, end, status="WORK"):
    return db.execute("INSERT INTO TB_PRC_Plan (HullNo,BlockId,ProcCd,PlanStartDt,PlanEndDt,ProgressRate,PlanStatus) "
                      "VALUES (?,?,'CUT',?,?,?,?)", (hull, block, start, end, rate, status)).lastrowid


def test_seed_loaded(client, pm):
    hulls = client.get("/api/hulls", headers=pm).json()
    assert [h["hull_no"] for h in hulls] == ["8001", "8002", "8003", "8004", "8005"]
    assert [len(client.get(f"/api/hulls/{h}/blocks", headers=pm).json()) for h in ("8001", "8002", "8003", "8004", "8005")] == [5, 4, 3, 2, 3]
    ms = {m["milestone_cd"]: m for m in client.get("/api/hulls/8001/milestones", headers=pm).json()}
    assert ms["CUT"]["actual_dt"] == "2026-06-17" and ms["KEEL"]["diff_days"] == 4 and ms["LAUNCH"]["actual_dt"] is None


def test_t01_filters_combination_and_reset(client, pm):
    q = lambda **p: [h["hull_no"] for h in client.get("/api/hulls", params=p, headers=pm).json()]
    assert q(ship_type="LNG") == ["8001", "8005"]
    assert q(ship_type="LNG", status="TRIAL") == ["8005"]
    assert q(q="nordic") == ["8001", "8005"]            # owner, case-insensitive
    assert q(q="TITAN") == ["8002"]                      # name
    assert q(q="800", status="BUILD") == ["8001", "8002"]
    assert q(status="", ship_type="", q="") == ["8001", "8002", "8003", "8004", "8005"]  # reset
    assert q(q="%") == []                                # no LIKE wildcard injection


def test_t01_progress_is_br01_weighted_and_delay_count(client, pm, db):
    h = {x["hull_no"]: x for x in client.get("/api/hulls", headers=pm).json()}
    assert h["8004"]["progress"] is None and h["8004"]["plan_count"] == 0  # '계획 없음'
    _plan(db, "8004", None, 100, "2026-01-01", "2026-01-10", "DONE")   # 10 days
    _plan(db, "8004", None, 40, "2026-01-01", "2026-01-30", "DELAY")   # 30 days
    h = client.get("/api/hulls/8004", headers=pm).json()
    assert h["progress"] == 55 and h["delay_count"] == 1                 # (1000+1200)/40


def test_t02_create_validation(client, pm):
    r = client.post("/api/hulls", json={**NEW, "hull_no": ""}, headers=pm)
    assert r.status_code == 400 and r.json()["details"]["field"] == "hull_no"
    r = client.post("/api/hulls", json={**NEW, "hull_no": "8001"}, headers=pm)
    assert r.status_code == 409 and r.json()["code"] == "DUPLICATE"
    r = client.post("/api/hulls", json={**NEW, "delivery_dt": "2025-12-31"}, headers=pm)
    assert r.status_code == 400 and r.json()["details"]["field"] == "delivery_dt"
    assert client.post("/api/hulls", json={**NEW, "ship_type": "XXX"}, headers=pm).status_code == 400
    assert client.post("/api/hulls", json={**NEW, "contract_dt": "2026-13-01"}, headers=pm).status_code == 400
    assert client.post("/api/hulls", json={**NEW, "length_m": "abc"}, headers=pm).status_code == 422


def test_t03_create_makes_five_milestones_with_delivery(client, pm, db):
    r = client.post("/api/hulls", json=NEW, headers=pm)
    assert r.status_code == 201
    body = r.json()
    assert body["hull_status"] == "PLAN" and body["use_yn"] is True and body["create_user_id"] == "park.pm"
    ms = client.get("/api/hulls/9001/milestones", headers=pm).json()
    assert [m["milestone_cd"] for m in ms] == ["CUT", "KEEL", "LAUNCH", "TRIAL", "DELIVER"]
    assert ms[-1]["plan_dt"] == "2027-12-31" and all(m["plan_dt"] is None for m in ms[:-1])


def test_t04_update_reflected_in_list(client, pm):
    r = client.patch("/api/hulls/8003", json={"hull_nm": "Renamed", "hull_status": "BUILD", "dock_no": "4도크"}, headers=pm)
    assert r.status_code == 200 and r.json()["modify_user_id"] == "park.pm" and r.json()["modify_dt"] == "2026-10-19"
    row = next(h for h in client.get("/api/hulls", headers=pm).json() if h["hull_no"] == "8003")
    assert row["hull_nm"] == "Renamed" and row["hull_status"] == "BUILD" and row["owner_nm"] == "Asia Container Line"
    # date order checked against stored values; hull_no immutable; 404
    assert client.patch("/api/hulls/8003", json={"delivery_dt": "2026-01-01"}, headers=pm).status_code == 400
    assert client.patch("/api/hulls/8003", json={"hull_no": "X"}, headers=pm).status_code == 400
    assert client.patch("/api/hulls/nope", json={"hull_nm": "a"}, headers=pm).status_code == 404


def test_t04_milestones_save(client, pm):
    items = [{"milestone_cd": "CUT", "plan_dt": "2027-01-10", "actual_dt": "2027-01-12"},
             {"milestone_cd": "KEEL", "plan_dt": None, "actual_dt": None}]
    ms = {m["milestone_cd"]: m for m in client.put("/api/hulls/8003/milestones", json={"items": items}, headers=pm).json()}
    assert ms["CUT"]["diff_days"] == 2 and ms["KEEL"]["plan_dt"] is None and ms["DELIVER"]["plan_dt"] == "2028-03-31"
    bad = client.put("/api/hulls/8003/milestones", json={"items": [{"milestone_cd": "XX"}]}, headers=pm)
    assert bad.status_code == 400


def test_t05_block_code_unique_per_hull(client, pm):
    r = client.post("/api/hulls/8004/blocks", json={"block_cd": "301", "block_nm": "선미", "block_type": "CURVE", "weight_ton": 10}, headers=pm)
    assert r.status_code == 201 and r.json()["block_cd"] == "301"
    dup = client.post("/api/hulls/8004/blocks", json={"block_cd": "301"}, headers=pm)
    assert dup.status_code == 409 and dup.json()["code"] == "DUPLICATE"
    assert client.post("/api/hulls/8004/blocks", json={"block_cd": " "}, headers=pm).status_code == 400
    assert client.post("/api/hulls/8004/blocks", json={"block_cd": "X1", "block_type": "BAD"}, headers=pm).status_code == 400
    # 8001 already has 101; 8004 may also have 101? it does (seed) -> different hull same code allowed
    assert client.post("/api/hulls/8005/blocks", json={"block_cd": "401"}, headers=pm).status_code == 201


def test_t06_block_delete_keeps_drawing_and_removes_plans(client, pm, db):
    bid = db.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo='8001' AND BlockCd='101'").fetchone()[0]
    p1 = _plan(db, "8001", bid, 50, "2026-10-01", "2026-10-10")
    keep = _plan(db, "8001", None, 0, "2026-10-01", "2026-10-10")
    db.execute("INSERT INTO TB_PRC_Progress (PlanId, WorkDt, ProgressRate) VALUES (?, '2026-10-02', 10)", (p1,))
    db.execute("INSERT INTO TB_PRC_PlanDep (PlanId, PredPlanId) VALUES (?,?)", (keep, p1))
    did = db.execute("INSERT INTO TB_DWG_Drawing (DrawingNo, DrawingNm, HullNo, BlockId) VALUES ('8001-T-1','t','8001',?)", (bid,)).lastrowid
    db.execute("INSERT INTO TB_DWG_PlanLink (DrawingId, PlanId) VALUES (?,?)", (did, p1))
    blk = next(b for b in client.get("/api/hulls/8001/blocks", headers=pm).json() if b["block_id"] == bid)
    assert blk["plan_count"] == 1 and blk["drawing_count"] == 1 and blk["progress"] == 50
    assert client.delete(f"/api/blocks/{bid}", headers=pm).status_code == 204
    assert db.execute("SELECT BlockId FROM TB_DWG_Drawing WHERE DrawingId=?", (did,)).fetchone()[0] is None
    assert db.execute("SELECT COUNT(*) FROM TB_PRC_Plan WHERE PlanId=?", (p1,)).fetchone()[0] == 0
    assert db.execute("SELECT PlanId FROM TB_PRC_Plan").fetchall()[0][0] == keep
    for t in ("TB_PRC_Progress", "TB_PRC_PlanDep", "TB_DWG_PlanLink"):
        assert db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0, t
    assert client.delete(f"/api/blocks/{bid}", headers=pm).status_code == 404


def test_t07_hull_delete_leaves_no_orphans(client, pm, db):
    bid = db.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo='8002' LIMIT 1").fetchone()[0]
    a = _plan(db, "8002", bid, 10, "2026-10-01", "2026-10-10")
    b = _plan(db, "8002", None, 0, "2026-10-11", "2026-10-20")
    db.execute("INSERT INTO TB_PRC_PlanDep (PlanId, PredPlanId) VALUES (?,?)", (b, a))
    db.execute("INSERT INTO TB_PRC_Progress (PlanId, WorkDt, ProgressRate) VALUES (?, '2026-10-02', 10)", (a,))
    did = db.execute("INSERT INTO TB_DWG_Drawing (DrawingNo, DrawingNm, HullNo, BlockId) VALUES ('8002-T-1','t','8002',?)", (bid,)).lastrowid
    db.execute("INSERT INTO TB_DWG_Revision (DrawingId, RevNo, FileId, FileNm) VALUES (?,0,'f1','a.pdf')", (did,))
    db.execute("INSERT INTO TB_DWG_Approval (DrawingId, RevNo, StepNo, ApproverEmpNo) VALUES (?,0,1,'lee.dwg')", (did,))
    db.execute("INSERT INTO TB_DWG_PlanLink (DrawingId, PlanId) VALUES (?,?)", (did, a))
    other = db.execute("SELECT COUNT(*) FROM TB_MST_Block WHERE HullNo<>'8002'").fetchone()[0]
    assert client.delete("/api/hulls/8002", headers=pm).status_code == 204
    for t in ("TB_MST_HullMilestone", "TB_MST_Block", "TB_PRC_Plan", "TB_DWG_Drawing"):
        assert db.execute(f"SELECT COUNT(*) FROM {t} WHERE HullNo='8002'").fetchone()[0] == 0, t
    for t in ("TB_PRC_Progress", "TB_PRC_PlanDep", "TB_DWG_Revision", "TB_DWG_Approval", "TB_DWG_PlanLink"):
        assert db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0, t
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert db.execute("SELECT COUNT(*) FROM TB_MST_Block").fetchone()[0] == other
    assert client.get("/api/hulls/8002", headers=pm).status_code == 404
    assert client.delete("/api/hulls/8002", headers=pm).status_code == 404


def test_t08_view_account_writes_are_403(client, viewer, db):
    assert client.get("/api/hulls", headers=viewer).status_code == 200
    assert client.get("/api/hulls/8001/summary", headers=viewer).status_code == 200
    bid = db.execute("SELECT BlockId FROM TB_MST_Block LIMIT 1").fetchone()[0]
    calls = [("post", "/api/hulls", {"json": NEW}), ("patch", "/api/hulls/8001", {"json": {"hull_nm": "x"}}),
             ("delete", "/api/hulls/8001", {}), ("put", "/api/hulls/8001/milestones", {"json": {"items": []}}),
             ("post", "/api/hulls/8001/blocks", {"json": {"block_cd": "Z"}}), ("delete", f"/api/blocks/{bid}", {})]
    for m, url, kw in calls:
        r = getattr(client, m)(url, headers=viewer, **kw)
        assert r.status_code == 403, (m, url, r.status_code)
    assert db.execute("SELECT HullNm FROM TB_MST_Hull WHERE HullNo='8001'").fetchone()[0] == "SWP LNG 174K 1호"
    for m, url, kw in calls:
        assert getattr(client, m)(url, **kw).status_code == 401


def test_t08_no_m11_menu_means_403(client, db):
    db.execute("DELETE FROM TB_SYS_AuthMenu WHERE AuthCd='VIEW' AND MenuId='M11'")
    h = login(client, "choi.qa", "qa1234")
    assert client.get("/api/hulls", headers=h).status_code == 403


def test_summary(client, pm, db):
    _plan(db, "8001", None, 100, "2026-01-01", "2026-01-10", "DONE")
    db.execute("INSERT INTO TB_DWG_Drawing (DrawingNo, DrawingNm, HullNo, DwgStatus) VALUES ('S1','s','8001','ISSUED')")
    s = client.get("/api/hulls/8001/summary", headers=pm).json()
    assert s["progress"] == 100 and s["plan_status"]["DONE"] == 1 and s["drawing_status"]["ISSUED"] == 1
    empty = client.get("/api/hulls/8004/summary", headers=pm).json()
    assert empty["progress"] is None and empty["drawing_count"] == 0
