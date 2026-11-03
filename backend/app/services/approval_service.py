"""F08 approval inbox / sequential decisions / issue-ready list / history (BR-06).
D11 CONFIRMED: approve/reject = M33 Write + assigned current approver (checked here); issue = M31 Write + completed approval
(F07 drawing_service.issue)."""
from datetime import datetime

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from .drawing_service import _label
from .plan_service import _SELECT, _bad, refresh_statuses

_PENDING = """a.Result='WAIT' AND r.RevStatus='REVIEW'
  AND r.RevNo=(SELECT MAX(RevNo) FROM TB_DWG_Revision x WHERE x.DrawingId=a.DrawingId)
  AND NOT EXISTS (SELECT 1 FROM TB_DWG_Approval p WHERE p.DrawingId=a.DrawingId AND p.RevNo=a.RevNo
                  AND p.StepNo<a.StepNo AND p.Result<>'APPROVE')"""
_JOIN = """FROM TB_DWG_Approval a JOIN TB_DWG_Drawing d ON d.DrawingId=a.DrawingId
           JOIN TB_DWG_Revision r ON r.DrawingId=a.DrawingId AND r.RevNo=a.RevNo"""


def _now() -> str:  # mockup nowStr: business date + wall-clock time
    return f"{settings.business_date} {datetime.now():%H:%M}"


def inbox(conn, emp_no: str) -> dict:
    mine = conn.execute(f"SELECT a.*, d.DrawingNo, d.DrawingNm, r.ChangeDesc {_JOIN} WHERE a.ApproverEmpNo=? AND {_PENDING} "
                        "ORDER BY a.ApprovalId", (emp_no,)).fetchall()
    return {
        "waiting": [{"approval_id": a["ApprovalId"], "drawing_id": a["DrawingId"], "drawing_no": a["DrawingNo"],
                     "drawing_nm": a["DrawingNm"], "rev_no": a["RevNo"], "step_no": a["StepNo"], "change_desc": a["ChangeDesc"]}
                    for a in mine],
        "ready": ready(conn),
    }


def ready(conn) -> list[dict]:
    """APV-03: latest Rev APPROVED; linked PLAN-status processes may become startable on issue."""
    rows = conn.execute("""SELECT d.DrawingId, d.DrawingNo, d.DrawingNm, r.RevNo FROM TB_DWG_Drawing d
                           JOIN TB_DWG_Revision r ON r.DrawingId=d.DrawingId
                           WHERE r.RevNo=(SELECT MAX(RevNo) FROM TB_DWG_Revision x WHERE x.DrawingId=d.DrawingId)
                             AND r.RevStatus='APPROVED' ORDER BY d.DrawingId""").fetchall()
    out = []
    for d in rows:
        plans = conn.execute(_SELECT + " JOIN TB_DWG_PlanLink l ON l.PlanId=p.PlanId WHERE l.DrawingId=? AND p.PlanStatus='PLAN'",
                             (d["DrawingId"],)).fetchall()
        out.append({"drawing_id": d["DrawingId"], "drawing_no": d["DrawingNo"], "drawing_nm": d["DrawingNm"],
                    "rev_no": d["RevNo"], "effect_plans": [_label(p) for p in plans]})
    return out


def history(conn, limit: int = 10) -> list[dict]:
    """APV-04: all users' processed approvals, ActDt desc (not limited to the caller)."""
    rows = conn.execute(f"""SELECT a.*, d.DrawingNo, u.display_name AS ApproverNm {_JOIN}
                            LEFT JOIN users u ON u.emp_no=a.ApproverEmpNo WHERE a.Result<>'WAIT'
                            ORDER BY COALESCE(a.ActDt,'') DESC, a.ApprovalId DESC LIMIT ?""", (limit,)).fetchall()
    return [{"approval_id": a["ApprovalId"], "act_dt": a["ActDt"], "drawing_id": a["DrawingId"], "drawing_no": a["DrawingNo"],
             "rev_no": a["RevNo"], "step_no": a["StepNo"], "approver_emp_no": a["ApproverEmpNo"], "approver_nm": a["ApproverNm"],
             "result": a["Result"], "comment": a["Comment"]} for a in rows]


def decide(conn, approval_id: int, result: str, comment: str | None, emp_no: str) -> dict:
    """APV-02. Only the assigned approver of the current pending step on the latest REVIEW rev may act (D11)."""
    if result not in ("APPROVE", "REJECT"):
        _bad("결재 결과는 APPROVE 또는 REJECT 이어야 합니다.", "result")
    cm = (comment or "").strip()
    if result == "REJECT" and not cm:
        _bad("반려 시 의견을 입력하세요.", "comment")
    with transaction(conn):  # BEGIN IMMEDIATE: re-check state under the write lock
        a = conn.execute("SELECT * FROM TB_DWG_Approval WHERE ApprovalId=?", (approval_id,)).fetchone()
        if not a:
            raise ApiError(404, "APPROVAL_NOT_FOUND", "결재 건을 찾을 수 없습니다.")
        if a["ApproverEmpNo"] != emp_no:
            raise ApiError(403, "NOT_ASSIGNED_APPROVER", "본인에게 지정된 결재 건이 아닙니다.")
        if a["Result"] != "WAIT":
            raise ApiError(409, "ALREADY_DECIDED", "이미 처리된 결재 건입니다.")
        if not conn.execute(f"SELECT 1 {_JOIN} WHERE a.ApprovalId=? AND {_PENDING}", (approval_id,)).fetchone():
            raise ApiError(409, "NOT_CURRENT_STEP", "결재 순서가 아니거나 최신 검토중 리비전이 아닙니다.")
        did, rev = a["DrawingId"], a["RevNo"]
        conn.execute("UPDATE TB_DWG_Approval SET Result=?, Comment=?, ActDt=? WHERE ApprovalId=?",
                     (result, cm or ("승인" if result == "APPROVE" else ""), _now(), approval_id))
        if result == "REJECT":  # reject row kept as history; only remaining WAIT rows removed
            conn.execute("UPDATE TB_DWG_Revision SET RevStatus='DRAFT' WHERE DrawingId=? AND RevNo=?", (did, rev))
            conn.execute("UPDATE TB_DWG_Drawing SET DwgStatus='DRAFT' WHERE DrawingId=?", (did,))
            conn.execute("DELETE FROM TB_DWG_Approval WHERE DrawingId=? AND RevNo=? AND Result='WAIT'", (did, rev))
        elif not conn.execute("SELECT 1 FROM TB_DWG_Approval WHERE DrawingId=? AND RevNo=? AND Result<>'APPROVE'", (did, rev)).fetchone():
            conn.execute("UPDATE TB_DWG_Revision SET RevStatus='APPROVED' WHERE DrawingId=? AND RevNo=?", (did, rev))
            conn.execute("UPDATE TB_DWG_Drawing SET DwgStatus='APPROVED' WHERE DrawingId=?", (did,))
        hull = conn.execute("SELECT HullNo FROM TB_DWG_Drawing WHERE DrawingId=?", (did,)).fetchone()[0]
        refresh_statuses(conn, hull)
    return {"approval_id": approval_id, "result": result, **inbox(conn, emp_no)}
