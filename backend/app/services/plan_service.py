"""F05 process planning: BR-02 drawing gate, BR-03 status recompute, BR-04 dependencies. Server is the source of truth."""
import sqlite3
from datetime import date

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from .metrics import weighted_progress

STATUSES = ("PLAN", "READY", "WORK", "DONE", "DELAY")


def _bad(msg, field=None, status=400, code="VALIDATION_ERROR", details=None):
    d = {"field": field} if field else {}
    d.update(details or {})
    raise ApiError(status, code, msg, d)


# ---------------- BR-02 gate ----------------
def gate_blockers(conn, plan_ids: list[int] | None = None) -> dict[int, list[dict]]:
    """Required links whose drawing is not OBSOLETE and has no ISSUED revision (D10: past ISSUED Rev counts)."""
    sql = """SELECT l.PlanId, d.DrawingId, d.DrawingNo, d.DwgStatus FROM TB_DWG_PlanLink l
             JOIN TB_DWG_Drawing d ON d.DrawingId = l.DrawingId
             WHERE l.RequiredYN = 1 AND d.DwgStatus <> 'OBSOLETE'
               AND NOT EXISTS (SELECT 1 FROM TB_DWG_Revision r WHERE r.DrawingId = d.DrawingId AND r.RevStatus = 'ISSUED')"""
    args: list = []
    if plan_ids is not None:
        if not plan_ids:
            return {}
        sql += f" AND l.PlanId IN ({','.join('?' * len(plan_ids))})"
        args = list(plan_ids)
    out: dict[int, list[dict]] = {}
    for r in conn.execute(sql + " ORDER BY d.DrawingNo", args):
        out.setdefault(r["PlanId"], []).append({"drawing_id": r["DrawingId"], "drawing_no": r["DrawingNo"], "dwg_status": r["DwgStatus"]})
    return out


# ---------------- BR-03 status ----------------
def _base_status(p, today: str) -> str | None:
    if p["ProgressRate"] >= 100:
        return "DONE"
    if p["ProgressRate"] > 0 or p["ActualStartDt"]:
        return "DELAY" if p["PlanEndDt"] < today else "WORK"
    if p["PlanEndDt"] < today:
        return "DELAY"
    return None  # PLAN/READY decided by predecessors + gate


def refresh_statuses(conn, hull_no: str | None = None) -> None:
    """Deterministic single pass: DONE depends only on ProgressRate, so predecessor DONE-ness is known after the
    base pass (replaces the mockup's double loop). Must run inside the caller's transaction."""
    today = settings.business_date
    where, args = ("WHERE HullNo=?", (hull_no,)) if hull_no else ("", ())
    plans = conn.execute(f"SELECT PlanId, HullNo, ProcCd, ProgressRate, ActualStartDt, PlanEndDt, PlanStatus FROM TB_PRC_Plan {where}", args).fetchall()
    if not plans:
        return
    ids = [p["PlanId"] for p in plans]
    base = {p["PlanId"]: _base_status(p, today) for p in plans}
    preds: dict[int, list[int]] = {}
    for d in conn.execute(f"SELECT PlanId, PredPlanId FROM TB_PRC_PlanDep WHERE PlanId IN ({','.join('?' * len(ids))})", ids):
        preds.setdefault(d["PlanId"], []).append(d["PredPlanId"])
    blockers = gate_blockers(conn, ids)
    pred_done = {}
    if any(preds.values()):
        all_preds = {q for v in preds.values() for q in v}
        for r in conn.execute(f"SELECT PlanId, ProgressRate FROM TB_PRC_Plan WHERE PlanId IN ({','.join('?' * len(all_preds))})", list(all_preds)):
            pred_done[r["PlanId"]] = r["ProgressRate"] >= 100
    new = {}
    for p in plans:
        pid = p["PlanId"]
        st = base[pid]
        if st is None:
            ok = all(pred_done.get(q, False) for q in preds.get(pid, [])) and not blockers.get(pid)
            st = "READY" if ok else "PLAN"
        new[pid] = st
    changed = [(new[p["PlanId"]], p["PlanId"]) for p in plans if p["PlanStatus"] != new[p["PlanId"]]]
    conn.executemany("UPDATE TB_PRC_Plan SET PlanStatus=? WHERE PlanId=?", changed)
    # hull auto transition (BR-03): DESIGN->BUILD on any WORK, BUILD->LAUNCH when LAUNCH process DONE
    by_hull: dict[str, list] = {}
    for p in plans:
        by_hull.setdefault(p["HullNo"], []).append(p)
    for hn, ps in by_hull.items():
        h = conn.execute("SELECT HullStatus FROM TB_MST_Hull WHERE HullNo=?", (hn,)).fetchone()
        if not h:
            continue
        hs = h["HullStatus"]
        if hs == "DESIGN" and any(new[p["PlanId"]] == "WORK" for p in ps):
            hs = "BUILD"
        launch = next((p for p in ps if p["ProcCd"] == "LAUNCH"), None)
        if hs == "BUILD" and launch and new[launch["PlanId"]] == "DONE":
            hs = "LAUNCH"
        if hs != h["HullStatus"]:
            conn.execute("UPDATE TB_MST_Hull SET HullStatus=? WHERE HullNo=?", (hs, hn))


# ---------------- reads ----------------
def _hull(conn, hull_no):
    if not conn.execute("SELECT 1 FROM TB_MST_Hull WHERE HullNo=?", (hull_no,)).fetchone():
        raise ApiError(404, "HULL_NOT_FOUND", "호선을 찾을 수 없습니다.")


def _plan_row(conn, plan_id):
    p = conn.execute("SELECT * FROM TB_PRC_Plan WHERE PlanId=?", (plan_id,)).fetchone()
    if not p:
        raise ApiError(404, "PLAN_NOT_FOUND", "공정을 찾을 수 없습니다.")
    return p


_SELECT = """SELECT p.*, b.BlockCd, b.BlockNm, pr.ProcNm, pr.Seq AS ProcSeq, u.display_name AS ManagerNm
             FROM TB_PRC_Plan p LEFT JOIN TB_MST_Block b ON b.BlockId = p.BlockId
             JOIN TB_PRC_Proc pr ON pr.ProcCd = p.ProcCd LEFT JOIN users u ON u.emp_no = p.ManagerEmpNo"""


def _sort_key(r):
    cd = r["BlockCd"]
    try:
        bo = float(cd) if cd is not None else 9999
    except ValueError:
        bo = 9998  # non-numeric codes after numeric ones, before hull-wide plans
    return (bo, r["ProcSeq"], r["PlanId"])


def _out(r, preds, blockers) -> dict:
    label = (f"[{r['BlockCd']}] " if r["BlockCd"] is not None else "[호선] ") + r["ProcNm"]
    return {"plan_id": r["PlanId"], "hull_no": r["HullNo"], "block_id": r["BlockId"], "block_cd": r["BlockCd"],
            "block_nm": r["BlockNm"], "proc_cd": r["ProcCd"], "proc_nm": r["ProcNm"], "label": label,
            "plan_start_dt": r["PlanStartDt"], "plan_end_dt": r["PlanEndDt"], "actual_start_dt": r["ActualStartDt"],
            "actual_end_dt": r["ActualEndDt"], "progress_rate": r["ProgressRate"], "plan_status": r["PlanStatus"],
            "manager_emp_no": r["ManagerEmpNo"], "manager_nm": r["ManagerNm"], "remark": r["Remark"],
            "create_user_id": r["CreateUserId"], "create_dt": r["CreateDt"],
            "pred_plan_ids": preds, "gate_ok": not blockers, "blockers": blockers,
            "drawing_wait": r["PlanStatus"] == "PLAN" and bool(blockers)}


def list_plans(conn, hull_no, block_id: int | None = None) -> dict:
    _hull(conn, hull_no)
    rows = conn.execute(_SELECT + " WHERE p.HullNo=?", (hull_no,)).fetchall()
    ids = [r["PlanId"] for r in rows]
    deps = conn.execute(f"SELECT PlanId, PredPlanId, LagDays FROM TB_PRC_PlanDep WHERE PlanId IN ({','.join('?' * len(ids))})", ids).fetchall() if ids else []
    preds: dict[int, list[int]] = {}
    for d in deps:
        preds.setdefault(d["PlanId"], []).append(d["PredPlanId"])
    blockers = gate_blockers(conn, ids)
    shown = sorted((r for r in rows if block_id is None or r["BlockId"] == block_id), key=_sort_key)
    shown_ids = {r["PlanId"] for r in shown}
    return {
        "hull_no": hull_no,
        "hull_progress": weighted_progress(rows) if rows else None,  # always whole hull (PLAN-01)
        "today": settings.business_date,
        "plans": [_out(r, sorted(preds.get(r["PlanId"], [])), blockers.get(r["PlanId"], [])) for r in shown],
        "deps": [{"plan_id": d["PlanId"], "pred_plan_id": d["PredPlanId"], "lag_days": d["LagDays"]}
                 for d in deps if d["PlanId"] in shown_ids and d["PredPlanId"] in shown_ids],
    }


def get_plan(conn, plan_id) -> dict:
    r = conn.execute(_SELECT + " WHERE p.PlanId=?", (plan_id,)).fetchone()
    if not r:
        raise ApiError(404, "PLAN_NOT_FOUND", "공정을 찾을 수 없습니다.")
    preds = sorted(x[0] for x in conn.execute("SELECT PredPlanId FROM TB_PRC_PlanDep WHERE PlanId=?", (plan_id,)))
    return _out(r, preds, gate_blockers(conn, [plan_id]).get(plan_id, []))


def plan_hulls(conn) -> list[dict]:
    rows = conn.execute("""SELECT h.HullNo, h.HullNm, COUNT(p.PlanId) AS n FROM TB_MST_Hull h
                           LEFT JOIN TB_PRC_Plan p ON p.HullNo = h.HullNo GROUP BY h.HullNo ORDER BY h.HullNo""").fetchall()
    return [{"hull_no": r["HullNo"], "hull_nm": r["HullNm"], "plan_count": r["n"]} for r in rows]


# ---------------- writes ----------------
def _reaches(conn, start: int, target: int) -> bool:
    """True if `target` is reachable from `start` following predecessor edges (mockup `reaches`)."""
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        if cur == target:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(r[0] for r in conn.execute("SELECT PredPlanId FROM TB_PRC_PlanDep WHERE PlanId=?", (cur,)))
    return False


def _validate(conn, hull_no, d: dict, plan_id: int | None) -> dict:
    s, e = d.get("plan_start_dt"), d.get("plan_end_dt")
    if not s or not e:
        _bad("계획 시작/종료일을 입력하세요.", "plan_start_dt" if not s else "plan_end_dt")
    try:
        s, e = date.fromisoformat(s).isoformat(), date.fromisoformat(e).isoformat()
    except ValueError:
        _bad("날짜 형식(YYYY-MM-DD)이 올바르지 않습니다.", "plan_start_dt")
    if e < s:
        _bad("계획 종료일이 시작일보다 빠릅니다.", "plan_end_dt")
    bid = d.get("block_id")
    if bid is not None and not conn.execute("SELECT 1 FROM TB_MST_Block WHERE BlockId=? AND HullNo=?", (bid, hull_no)).fetchone():
        _bad("해당 호선의 블록이 아닙니다.", "block_id")
    proc = d.get("proc_cd")
    if not proc or not conn.execute("SELECT 1 FROM TB_PRC_Proc WHERE ProcCd=? AND UseYN=1", (proc,)).fetchone():
        _bad("허용되지 않는 공정 코드입니다.", "proc_cd")
    mgr = d.get("manager_emp_no") or None
    if mgr and not conn.execute("SELECT 1 FROM users WHERE emp_no=? AND status='approved'", (mgr,)).fetchone():
        _bad("승인된 회원만 담당자로 지정할 수 있습니다.", "manager_emp_no")
    remark = (d.get("remark") or "").strip() or None
    return {"BlockId": bid, "ProcCd": proc, "PlanStartDt": s, "PlanEndDt": e, "ManagerEmpNo": mgr, "Remark": remark}


def _check_preds(conn, hull_no, plan_id: int | None, preds: list[int], start_dt: str, confirm_late: bool) -> list[int]:
    preds = sorted(set(preds or []))
    if plan_id is not None and plan_id in preds:
        _bad("자기 자신을 선행 공정으로 지정할 수 없습니다.", "pred_plan_ids", code="PLAN_DEPENDENCY_SELF")
    if preds:
        rows = conn.execute(f"SELECT PlanId, HullNo, PlanEndDt FROM TB_PRC_Plan WHERE PlanId IN ({','.join('?' * len(preds))})", preds).fetchall()
        if len(rows) != len(preds) or any(r["HullNo"] != hull_no for r in rows):
            _bad("선행 공정은 같은 호선의 공정이어야 합니다.", "pred_plan_ids")
        if plan_id is not None and any(_reaches(conn, q, plan_id) for q in preds):
            _bad("선행 공정이 순환 구조를 만듭니다.", "pred_plan_ids", code="PLAN_DEPENDENCY_CYCLE")
        late = [r["PlanId"] for r in rows if r["PlanEndDt"] > start_dt]
        if late and not confirm_late:  # BR-04: warn, save only after explicit user confirmation
            _bad("선행 공정 종료일이 이 공정의 시작일보다 늦습니다. 그대로 저장할까요?", "pred_plan_ids", 409,
                 "PRED_LATE_CONFIRM_REQUIRED", {"late_pred_plan_ids": late})
    return preds


def _replace_preds(conn, plan_id, preds):
    conn.execute("DELETE FROM TB_PRC_PlanDep WHERE PlanId=?", (plan_id,))
    conn.executemany("INSERT INTO TB_PRC_PlanDep (PlanId, PredPlanId, LagDays) VALUES (?,?,0)", [(plan_id, q) for q in preds])


def create_plan(conn, hull_no, data: dict, user: str) -> dict:
    with transaction(conn):
        _hull(conn, hull_no)
        v = _validate(conn, hull_no, data, None)
        preds = _check_preds(conn, hull_no, None, data.get("pred_plan_ids") or [], v["PlanStartDt"], data.get("confirm_late_preds", False))
        pid = conn.execute(
            "INSERT INTO TB_PRC_Plan (HullNo,BlockId,ProcCd,PlanStartDt,PlanEndDt,ProgressRate,PlanStatus,ManagerEmpNo,Remark,CreateUserId,CreateDt) "
            "VALUES (?,?,?,?,?,0,'PLAN',?,?,?,?)",
            (hull_no, v["BlockId"], v["ProcCd"], v["PlanStartDt"], v["PlanEndDt"], v["ManagerEmpNo"], v["Remark"], user, settings.business_date)).lastrowid
        _replace_preds(conn, pid, preds)
        refresh_statuses(conn, hull_no)
    return get_plan(conn, pid)


def update_plan(conn, plan_id, data: dict) -> dict:
    with transaction(conn):
        cur = _plan_row(conn, plan_id)
        merged = {"block_id": cur["BlockId"], "proc_cd": cur["ProcCd"], "plan_start_dt": cur["PlanStartDt"],
                  "plan_end_dt": cur["PlanEndDt"], "manager_emp_no": cur["ManagerEmpNo"], "remark": cur["Remark"]}
        merged.update({k: v for k, v in data.items() if k in merged})
        v = _validate(conn, cur["HullNo"], merged, plan_id)
        # progress/actuals are preserved (owned by F06)
        conn.execute("UPDATE TB_PRC_Plan SET BlockId=?,ProcCd=?,PlanStartDt=?,PlanEndDt=?,ManagerEmpNo=?,Remark=? WHERE PlanId=?",
                     (v["BlockId"], v["ProcCd"], v["PlanStartDt"], v["PlanEndDt"], v["ManagerEmpNo"], v["Remark"], plan_id))
        if "pred_plan_ids" in data and data["pred_plan_ids"] is not None:
            preds = _check_preds(conn, cur["HullNo"], plan_id, data["pred_plan_ids"], v["PlanStartDt"], data.get("confirm_late_preds", False))
            _replace_preds(conn, plan_id, preds)
        refresh_statuses(conn, cur["HullNo"])
    return get_plan(conn, plan_id)


def set_predecessors(conn, plan_id, preds: list[int], confirm_late: bool) -> dict:
    with transaction(conn):
        cur = _plan_row(conn, plan_id)
        preds = _check_preds(conn, cur["HullNo"], plan_id, preds, cur["PlanStartDt"], confirm_late)
        _replace_preds(conn, plan_id, preds)
        refresh_statuses(conn, cur["HullNo"])
    return get_plan(conn, plan_id)


def delete_plan(conn, plan_id) -> None:
    """BR-08: progress, deps (both directions) and drawing links cascade via FK."""
    with transaction(conn):
        cur = _plan_row(conn, plan_id)
        conn.execute("DELETE FROM TB_PRC_Plan WHERE PlanId=?", (plan_id,))
        refresh_statuses(conn, cur["HullNo"])


# ---------------- PLAN-04 drawing links ----------------
def plan_drawings(conn, plan_id) -> dict:
    p = _plan_row(conn, plan_id)
    links = conn.execute("""SELECT l.DrawingId, l.RequiredYN, l.NeedDt, d.DrawingNo, d.DrawingNm, d.DwgStatus,
                              EXISTS (SELECT 1 FROM TB_DWG_Revision r WHERE r.DrawingId=d.DrawingId AND r.RevStatus='ISSUED') AS HasIssued
                            FROM TB_DWG_PlanLink l JOIN TB_DWG_Drawing d ON d.DrawingId=l.DrawingId
                            WHERE l.PlanId=? ORDER BY d.DrawingNo""", (plan_id,)).fetchall()
    free = conn.execute("""SELECT DrawingId, DrawingNo, DrawingNm, DwgStatus FROM TB_DWG_Drawing
                           WHERE HullNo=? AND DrawingId NOT IN (SELECT DrawingId FROM TB_DWG_PlanLink WHERE PlanId=?)
                           ORDER BY DrawingNo""", (p["HullNo"], plan_id)).fetchall()
    return {
        "plan_id": plan_id,
        "blockers": gate_blockers(conn, [plan_id]).get(plan_id, []),
        "links": [{"drawing_id": r["DrawingId"], "drawing_no": r["DrawingNo"], "drawing_nm": r["DrawingNm"],
                   "dwg_status": r["DwgStatus"], "has_issued": bool(r["HasIssued"]), "required": bool(r["RequiredYN"]),
                   "need_dt": r["NeedDt"]} for r in links],
        "available": [{"drawing_id": r["DrawingId"], "drawing_no": r["DrawingNo"], "drawing_nm": r["DrawingNm"],
                       "dwg_status": r["DwgStatus"]} for r in free],
    }


def link_drawing(conn, plan_id, drawing_id: int, required: bool) -> dict:
    try:
        with transaction(conn):
            p = _plan_row(conn, plan_id)
            d = conn.execute("SELECT HullNo FROM TB_DWG_Drawing WHERE DrawingId=?", (drawing_id,)).fetchone()
            if not d:
                raise ApiError(404, "DRAWING_NOT_FOUND", "도면을 찾을 수 없습니다.")
            if d["HullNo"] != p["HullNo"]:
                _bad("같은 호선의 도면만 연계할 수 있습니다.", "drawing_id")
            if conn.execute("SELECT 1 FROM TB_DWG_PlanLink WHERE DrawingId=? AND PlanId=?", (drawing_id, plan_id)).fetchone():
                _bad("이미 연계된 도면입니다.", "drawing_id", 409, "DUPLICATE")
            conn.execute("INSERT INTO TB_DWG_PlanLink (DrawingId, PlanId, RequiredYN, NeedDt) VALUES (?,?,?,?)",
                         (drawing_id, plan_id, int(required), p["PlanStartDt"]))
            refresh_statuses(conn, p["HullNo"])
    except sqlite3.IntegrityError:
        _bad("이미 연계된 도면입니다.", "drawing_id", 409, "DUPLICATE")
    return plan_drawings(conn, plan_id)


def unlink_drawing(conn, plan_id, drawing_id: int) -> None:
    with transaction(conn):
        p = _plan_row(conn, plan_id)
        if not conn.execute("DELETE FROM TB_DWG_PlanLink WHERE DrawingId=? AND PlanId=?", (drawing_id, plan_id)).rowcount:
            raise ApiError(404, "LINK_NOT_FOUND", "연계를 찾을 수 없습니다.")
        refresh_statuses(conn, p["HullNo"])
