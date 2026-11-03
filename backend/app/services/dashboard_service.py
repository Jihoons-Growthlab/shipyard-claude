"""F03 dashboard: one server-side aggregate (no UI N+1). Reuses BR-01 weighted_progress, BR-02 gate_blockers,
BR-07 drawing_service.impacts — no duplicated business rules."""
from ..config import settings
from .drawing_service import impacts
from .metrics import weighted_progress
from .plan_service import STATUSES, _SELECT, _out, gate_blockers

ACTIVE_HULL = ("DESIGN", "BUILD", "LAUNCH", "TRIAL")
PEND_DWG = ("REVIEW", "APPROVED")
STACK_DWG = ("ISSUED", "APPROVED", "REVIEW", "DRAFT")
LIST_MAX = 6


def _lst(items: list[dict]) -> dict:
    return {"count": len(items), "items": items[:LIST_MAX]}


def _plan_item(p: dict) -> dict:
    return {"plan_id": p["plan_id"], "hull_no": p["hull_no"], "label": p["label"], "plan_status": p["plan_status"],
            "progress_rate": p["progress_rate"], "plan_start_dt": p["plan_start_dt"], "plan_end_dt": p["plan_end_dt"],
            "blockers": [b["drawing_no"] for b in p["blockers"]],
            "link": {"screen": "plan-gantt", "param": p["hull_no"]}}


def summary(conn) -> dict:
    hulls = conn.execute("SELECT HullNo, HullNm, HullStatus, DeliveryDt FROM TB_MST_Hull WHERE UseYN=1 ORDER BY HullNo").fetchall()
    rows = conn.execute(_SELECT + " ORDER BY p.PlanId").fetchall()
    blk = gate_blockers(conn)
    plans = [_out(r, [], blk.get(r["PlanId"], [])) for r in rows]

    delay = [p for p in plans if p["plan_status"] == "DELAY"]
    waiting = sorted((p for p in plans if p["drawing_wait"]), key=lambda p: p["plan_start_dt"])
    pend = conn.execute(f"SELECT COUNT(*) FROM TB_DWG_Drawing WHERE DwgStatus IN ({','.join('?' * len(PEND_DWG))})",
                        PEND_DWG).fetchone()[0]

    by_hull: dict[str, list] = {}
    for r in rows:
        by_hull.setdefault(r["HullNo"], []).append(r)
    hull_progress = [{"hull_no": h["HullNo"], "hull_nm": h["HullNm"], "progress": weighted_progress(by_hull.get(h["HullNo"], [])),
                      "link": {"screen": "plan-gantt", "param": h["HullNo"]}} for h in hulls]

    disc = []
    for c in conn.execute("SELECT Code, CodeName FROM TB_SYS_Code WHERE CodeGroup='DWGDISC' AND UseYN=1 ORDER BY Seq"):
        st = dict(conn.execute("SELECT DwgStatus, COUNT(*) FROM TB_DWG_Drawing WHERE Discipline=? GROUP BY DwgStatus",
                               (c["Code"],)).fetchall())
        total = sum(st.values())
        if total:
            disc.append({"discipline": c["Code"], "name": c["CodeName"], "total": total,
                         "counts": {s: st.get(s, 0) for s in STACK_DWG}})

    mon: dict[str, list] = {}
    for h in hulls:
        if h["DeliveryDt"]:
            mon.setdefault(h["DeliveryDt"][:7], []).append(h["HullNo"])

    status_of = {p["plan_id"]: p for p in plans}
    imp = []
    for x in impacts(conn):
        p = status_of.get(x["plan_id"], {})
        r = conn.execute("SELECT ChangeDesc FROM TB_DWG_Revision WHERE DrawingId=? AND RevNo=?",
                         (x["drawing_id"], x["rev_no"])).fetchone()
        imp.append({**x, "hull_no": p.get("hull_no"), "change_desc": r["ChangeDesc"] if r else None,
                    "link": {"screen": "drawing", "param": x["drawing_id"]}})

    return {
        "today": settings.business_date,
        "kpi": {
            "active_hulls": {"value": sum(1 for h in hulls if h["HullStatus"] in ACTIVE_HULL), "link": {"screen": "hull-list"}},
            "delay_plans": {"value": len(delay), "link": {"screen": "plan-gantt"}},
            "waiting_plans": {"value": len(waiting), "link": {"screen": "plan-gantt"}},
            "pending_drawings": {"value": pend, "link": {"screen": "dwg-approval"}},
        },
        "hull_progress": hull_progress,
        "plan_status": [{"status": s, "count": sum(1 for p in plans if p["plan_status"] == s)} for s in STATUSES],
        "drawing_disciplines": disc,
        "deliveries": [{"month": m, "count": len(v), "hull_nos": v} for m, v in sorted(mon.items())],
        "delay_list": _lst([_plan_item(p) for p in delay]),
        "waiting_list": _lst([_plan_item(p) for p in waiting]),
        "impact_list": _lst(imp),
    }
