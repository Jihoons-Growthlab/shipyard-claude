"""F06 process progress (BR-05 cumulative rate, BR-03 status via F05 refresh_statuses).
D09: follows the mockup progSave — no drawing-gate check on progress input (gate only drives READY/PLAN status)."""
from datetime import date

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from .plan_service import _SELECT, _bad, _plan_row, _sort_key, gate_blockers, get_plan, refresh_statuses

ACTIVE = ("READY", "WORK", "DELAY")


def progress_hulls(conn) -> dict:
    """PROG-01: hulls that have plans; default = first BUILD hull, else first."""
    rows = conn.execute("""SELECT h.HullNo, h.HullNm, h.HullStatus FROM TB_MST_Hull h
                           WHERE EXISTS (SELECT 1 FROM TB_PRC_Plan p WHERE p.HullNo=h.HullNo) ORDER BY h.HullNo""").fetchall()
    hulls = [{"hull_no": r["HullNo"], "hull_nm": r["HullNm"], "hull_status": r["HullStatus"]} for r in rows]
    default = next((h for h in hulls if h["hull_status"] == "BUILD"), hulls[0] if hulls else None)
    return {"hulls": hulls, "default_hull_no": default["hull_no"] if default else None}


def targets(conn, hull_no: str, include_done: bool) -> dict:
    if not conn.execute("SELECT 1 FROM TB_MST_Hull WHERE HullNo=?", (hull_no,)).fetchone():
        raise ApiError(404, "HULL_NOT_FOUND", "호선을 찾을 수 없습니다.")
    rows = [r for r in conn.execute(_SELECT + " WHERE p.HullNo=?", (hull_no,)) if include_done or r["PlanStatus"] in ACTIVE]
    rows.sort(key=_sort_key)
    blockers = gate_blockers(conn, [r["PlanId"] for r in rows])
    return {"hull_no": hull_no, "today": settings.business_date, "plans": [
        {"plan_id": r["PlanId"], "label": (f"[{r['BlockCd']}] " if r["BlockCd"] is not None else "[호선] ") + r["ProcNm"],
         "plan_start_dt": r["PlanStartDt"], "plan_end_dt": r["PlanEndDt"], "actual_start_dt": r["ActualStartDt"],
         "actual_end_dt": r["ActualEndDt"], "progress_rate": r["ProgressRate"], "plan_status": r["PlanStatus"],
         "manager_emp_no": r["ManagerEmpNo"], "manager_nm": r["ManagerNm"],
         "drawing_wait": r["PlanStatus"] == "PLAN" and bool(blockers.get(r["PlanId"]))} for r in rows]}


def history(conn, plan_id: int) -> dict:
    plan = get_plan(conn, plan_id)
    rows = conn.execute("""SELECT g.*, u.display_name AS WorkerNm FROM TB_PRC_Progress g
                           LEFT JOIN users u ON u.emp_no=g.WorkerEmpNo WHERE g.PlanId=? ORDER BY g.WorkDt DESC""", (plan_id,))
    return {"plan": plan, "history": [
        {"progress_id": r["ProgressId"], "plan_id": r["PlanId"], "work_dt": r["WorkDt"], "progress_rate": r["ProgressRate"],
         "man_hour": r["ManHour"], "worker_cnt": r["WorkerCnt"], "worker_emp_no": r["WorkerEmpNo"],
         "worker_nm": r["WorkerNm"], "remark": r["Remark"], "create_dt": r["CreateDt"]} for r in rows]}


def recompute_plan(conn, plan_id: int) -> None:
    """BR-05: latest work date's cumulative rate (no summing); first date = actual start; 100% => actual end."""
    rows = conn.execute("SELECT WorkDt, ProgressRate FROM TB_PRC_Progress WHERE PlanId=? ORDER BY WorkDt", (plan_id,)).fetchall()
    if not rows:
        vals = (0, None, None)
    else:
        last = rows[-1]
        vals = (last["ProgressRate"], rows[0]["WorkDt"], last["WorkDt"] if last["ProgressRate"] >= 100 else None)
    conn.execute("UPDATE TB_PRC_Plan SET ProgressRate=?, ActualStartDt=?, ActualEndDt=? WHERE PlanId=?", (*vals, plan_id))


def save(conn, plan_id: int, work_dt: str, d: dict) -> dict:
    try:
        work_dt = date.fromisoformat(work_dt).isoformat()
    except ValueError:
        _bad("작업일을 입력하세요.", "work_dt")
    if work_dt > settings.business_date:
        _bad("미래 일자의 실적은 입력할 수 없습니다.", "work_dt")
    rate = d.get("progress_rate")
    if rate is None or not 0 <= rate <= 100:
        _bad("진척률은 0~100 사이로 입력하세요.", "progress_rate")
    worker = d.get("worker_emp_no") or None
    if worker and not conn.execute("SELECT 1 FROM users WHERE emp_no=? AND status='approved'", (worker,)).fetchone():
        _bad("승인된 회원만 작업자로 지정할 수 있습니다.", "worker_emp_no")
    remark = (d.get("remark") or "").strip() or None
    with transaction(conn):
        p = _plan_row(conn, plan_id)
        vals = (rate, d.get("man_hour"), d.get("worker_cnt"), worker, remark)
        cur = conn.execute("SELECT ProgressId FROM TB_PRC_Progress WHERE PlanId=? AND WorkDt=?", (plan_id, work_dt)).fetchone()
        if cur:  # PROG-02: same plan + work date => update
            conn.execute("UPDATE TB_PRC_Progress SET ProgressRate=?,ManHour=?,WorkerCnt=?,WorkerEmpNo=?,Remark=? WHERE ProgressId=?",
                         (*vals, cur["ProgressId"]))
        else:
            conn.execute("INSERT INTO TB_PRC_Progress (PlanId,WorkDt,ProgressRate,ManHour,WorkerCnt,WorkerEmpNo,Remark,CreateDt) "
                         "VALUES (?,?,?,?,?,?,?,?)", (plan_id, work_dt, *vals, settings.business_date))
        recompute_plan(conn, plan_id)
        refresh_statuses(conn, p["HullNo"])
    return history(conn, plan_id)


def delete(conn, progress_id: int) -> dict:
    with transaction(conn):
        r = conn.execute("""SELECT g.PlanId, p.HullNo FROM TB_PRC_Progress g JOIN TB_PRC_Plan p ON p.PlanId=g.PlanId
                            WHERE g.ProgressId=?""", (progress_id,)).fetchone()
        if not r:
            raise ApiError(404, "PROGRESS_NOT_FOUND", "실적을 찾을 수 없습니다.")
        conn.execute("DELETE FROM TB_PRC_Progress WHERE ProgressId=?", (progress_id,))
        recompute_plan(conn, r["PlanId"])
        refresh_statuses(conn, r["HullNo"])
    return history(conn, r["PlanId"])
