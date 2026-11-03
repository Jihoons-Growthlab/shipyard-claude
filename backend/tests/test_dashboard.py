"""F03 DASH-T01~T06: /api/dashboard/summary aggregates (server-side, reuses BR-01/02/07)."""
import pytest

from .conftest import login
from .test_drawings import _did

pytestmark = pytest.mark.full_seed
URL = "/api/dashboard/summary"


@pytest.fixture
def pm(client):
    return login(client, "park.pm", "pm1234")


def _sum(client, h):
    r = client.get(URL, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _st(s, k):
    return next(x["count"] for x in s["plan_status"] if x["status"] == k)


def test_requires_login(client):
    assert client.get(URL).status_code == 401


def test_t01_progress_100_updates_delay_done_and_progress(client, pm, db):
    s0 = _sum(client, pm)
    pid = s0["delay_list"]["items"][0]["plan_id"]
    hull = s0["delay_list"]["items"][0]["hull_no"]
    hp0 = next(h["progress"] for h in s0["hull_progress"] if h["hull_no"] == hull)
    r = client.put(f"/api/plans/{pid}/progress/2026-10-19", json={"progress_rate": 100}, headers=pm)
    assert r.status_code == 200, r.text
    s1 = _sum(client, pm)
    assert s1["kpi"]["delay_plans"]["value"] == s0["kpi"]["delay_plans"]["value"] - 1
    assert _st(s1, "DONE") == _st(s0, "DONE") + 1 and _st(s1, "DELAY") == _st(s0, "DELAY") - 1
    assert next(h["progress"] for h in s1["hull_progress"] if h["hull_no"] == hull) > hp0


def test_t02_required_unissued_drawing_toggles_waiting(client, pm, db):
    lee = login(client, "lee.dwg", "dwg1234")
    s0 = _sum(client, pm)
    pid = db.execute("SELECT PlanId FROM TB_PRC_Plan p WHERE PlanStatus='PLAN' AND NOT EXISTS "
                     "(SELECT 1 FROM TB_DWG_PlanLink l WHERE l.PlanId=p.PlanId AND l.RequiredYN=1) ORDER BY PlanId").fetchone()[0]
    hull = db.execute("SELECT HullNo FROM TB_PRC_Plan WHERE PlanId=?", (pid,)).fetchone()[0]
    r = client.post("/api/drawings", json={"drawing_no": f"{hull}-HULL-T02", "drawing_nm": "T02", "hull_no": hull,
                                           "discipline": "HULL"}, headers=lee)
    assert r.status_code in (200, 201), r.text
    did = r.json()["drawing_id"]
    assert client.post(f"/api/plans/{pid}/drawings", json={"drawing_id": did, "required": True}, headers=pm).status_code in (200, 201)
    s1 = _sum(client, pm)
    assert s1["kpi"]["waiting_plans"]["value"] == s0["kpi"]["waiting_plans"]["value"] + 1
    db.execute("UPDATE TB_DWG_Revision SET RevStatus='ISSUED', IssueDt='2026-10-19' WHERE DrawingId=?", (did,))
    db.execute("UPDATE TB_DWG_Drawing SET DwgStatus='ISSUED' WHERE DrawingId=?", (did,))
    db.commit()
    assert _sum(client, pm)["kpi"]["waiting_plans"]["value"] == s1["kpi"]["waiting_plans"]["value"] - 1


def test_t03_impacts_only_recent_issued_and_started_plans(client, pm, db):
    imp = _sum(client, pm)["impact_list"]
    assert imp["count"] >= 1
    for x in imp["items"]:
        assert x["plan_status"] in ("WORK", "DONE", "DELAY") and x["rev_no"] >= 1
        assert "2026-09-19" <= x["issue_dt"] <= "2026-10-19"
    did = _did(db, imp["items"][0]["drawing_no"])
    db.execute("UPDATE TB_DWG_Revision SET IssueDt='2026-09-01' WHERE DrawingId=? AND RevStatus='ISSUED' AND RevNo>=1", (did,))
    db.commit()
    assert did not in {x["drawing_id"] for x in _sum(client, pm)["impact_list"]["items"]}


def test_t04_delivery_months_consistent(client, pm, db):
    s = _sum(client, pm)
    rows = db.execute("SELECT HullNo, DeliveryDt FROM TB_MST_Hull WHERE UseYN=1 AND DeliveryDt IS NOT NULL").fetchall()
    assert sum(m["count"] for m in s["deliveries"]) == len(rows) == 5
    for m in s["deliveries"]:
        assert m["count"] == len(m["hull_nos"])
        assert set(m["hull_nos"]) == {r[0] for r in rows if r[1][:7] == m["month"]}
    assert [m["month"] for m in s["deliveries"]] == sorted(m["month"] for m in s["deliveries"])


def test_t05_navigation_targets(client, pm, db):
    s = _sum(client, pm)
    k = s["kpi"]
    assert [k[x]["link"]["screen"] for x in ("active_hulls", "delay_plans", "waiting_plans", "pending_drawings")] == \
        ["hull-list", "plan-gantt", "plan-gantt", "dwg-approval"]
    for h in s["hull_progress"]:
        assert h["link"] == {"screen": "plan-gantt", "param": h["hull_no"]}
    for lst in ("delay_list", "waiting_list"):
        for p in s[lst]["items"]:
            hull = db.execute("SELECT HullNo FROM TB_PRC_Plan WHERE PlanId=?", (p["plan_id"],)).fetchone()[0]
            assert p["link"] == {"screen": "plan-gantt", "param": hull}
    for x in s["impact_list"]["items"]:
        assert x["link"] == {"screen": "drawing", "param": _did(db, x["drawing_no"])}


def test_t06_lists_capped_at_six(client, pm, db):
    ids = [r[0] for r in db.execute("SELECT PlanId FROM TB_PRC_Plan ORDER BY PlanId LIMIT 7")]
    db.execute(f"UPDATE TB_PRC_Plan SET PlanStatus='DELAY' WHERE PlanId IN ({','.join('?' * 7)})", ids)
    db.commit()
    s = _sum(client, pm)
    assert s["kpi"]["delay_plans"]["value"] >= 7 and s["delay_list"]["count"] == s["kpi"]["delay_plans"]["value"]
    assert len(s["delay_list"]["items"]) == 6
    assert s["kpi"]["waiting_plans"]["value"] == 8 and len(s["waiting_list"]["items"]) == 6
