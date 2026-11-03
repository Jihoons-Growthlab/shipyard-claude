"""F07 drawings/revisions/PDF/plan links (BR-02 gate via F05 refresh_statuses, BR-06 revision states, BR-07 impacts,
BR-08 deletes). Approve/reject: approval_service (F08)."""
import sqlite3
from datetime import date, timedelta

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from . import file_store, plan_service
from .code_service import codes
from .plan_service import _SELECT, _bad, refresh_statuses


# ---------------- helpers ----------------
def _drawing(conn, drawing_id):
    d = conn.execute("SELECT * FROM TB_DWG_Drawing WHERE DrawingId=?", (drawing_id,)).fetchone()
    if not d:
        raise ApiError(404, "DRAWING_NOT_FOUND", "도면을 찾을 수 없습니다.")
    return d


def _rev(conn, drawing_id, rev_no):
    r = conn.execute("SELECT * FROM TB_DWG_Revision WHERE DrawingId=? AND RevNo=?", (drawing_id, rev_no)).fetchone()
    if not r:
        raise ApiError(404, "REVISION_NOT_FOUND", "리비전을 찾을 수 없습니다.")
    return r


def _latest(conn, drawing_id):
    return conn.execute("SELECT * FROM TB_DWG_Revision WHERE DrawingId=? ORDER BY RevNo DESC LIMIT 1", (drawing_id,)).fetchone()


def _approved_user(conn, emp, field):
    if emp and not conn.execute("SELECT 1 FROM users WHERE emp_no=? AND status='approved'", (emp,)).fetchone():
        _bad("승인된 회원만 지정할 수 있습니다.", field)


def _label(r):
    return (f"[{r['BlockCd']}] " if r["BlockCd"] is not None else "[호선] ") + r["ProcNm"]


def impacts(conn, drawing_id: int | None = None) -> list[dict]:
    """BR-07: latest Rev>=1 ISSUED within [TODAY-30, TODAY] -> linked plans in WORK/DONE/DELAY."""
    today = settings.business_date
    since = (date.fromisoformat(today) - timedelta(days=30)).isoformat()
    sql = """SELECT r.DrawingId, MAX(r.RevNo) AS RevNo FROM TB_DWG_Revision r
             WHERE r.RevStatus='ISSUED' AND r.RevNo>=1 AND r.IssueDt BETWEEN ? AND ?"""
    args: list = [since, today]
    if drawing_id is not None:
        sql += " AND r.DrawingId=?"
        args.append(drawing_id)
    out = []
    for h in conn.execute(sql + " GROUP BY r.DrawingId", args).fetchall():
        rev = _rev(conn, h["DrawingId"], h["RevNo"])
        d = _drawing(conn, h["DrawingId"])
        for p in conn.execute(_SELECT + " JOIN TB_DWG_PlanLink l ON l.PlanId=p.PlanId WHERE l.DrawingId=? "
                              "AND p.PlanStatus IN ('WORK','DONE','DELAY')", (h["DrawingId"],)):
            out.append({"drawing_id": d["DrawingId"], "drawing_no": d["DrawingNo"], "rev_no": rev["RevNo"],
                        "issue_dt": rev["IssueDt"], "plan_id": p["PlanId"], "plan_label": _label(p), "plan_status": p["PlanStatus"]})
    return out


# ---------------- DWG-01 list ----------------
def list_drawings(conn, hull=None, disc=None, status=None, q=None) -> list[dict]:
    sql = """SELECT d.*, b.BlockCd, u.display_name AS DesignerNm,
                    (SELECT MAX(RevNo) FROM TB_DWG_Revision r WHERE r.DrawingId=d.DrawingId) AS LatestRevNo,
                    (SELECT COUNT(*) FROM TB_DWG_PlanLink l WHERE l.DrawingId=d.DrawingId) AS LinkCnt
             FROM TB_DWG_Drawing d LEFT JOIN TB_MST_Block b ON b.BlockId=d.BlockId
             LEFT JOIN users u ON u.emp_no=d.DesignerEmpNo WHERE 1=1"""
    args: list = []
    for col, v in (("d.HullNo", hull), ("d.Discipline", disc), ("d.DwgStatus", status)):
        if v:
            sql += f" AND {col}=?"
            args.append(v)
    if q:
        sql += " AND instr(lower(d.DrawingNo || d.DrawingNm), lower(?)) > 0"
        args.append(q)
    return [{"drawing_id": r["DrawingId"], "drawing_no": r["DrawingNo"], "drawing_nm": r["DrawingNm"], "hull_no": r["HullNo"],
             "block_id": r["BlockId"], "block_cd": r["BlockCd"], "discipline": r["Discipline"], "dwg_status": r["DwgStatus"],
             "current_rev_no": r["CurrentRevNo"], "latest_rev_no": r["LatestRevNo"], "designer_emp_no": r["DesignerEmpNo"],
             "designer_nm": r["DesignerNm"], "link_count": r["LinkCnt"]}
            for r in conn.execute(sql + " ORDER BY d.DrawingId", args)]


# ---------------- detail ----------------
def get_drawing(conn, drawing_id) -> dict:
    d = _drawing(conn, drawing_id)
    b = conn.execute("SELECT BlockCd, BlockNm FROM TB_MST_Block WHERE BlockId=?", (d["BlockId"],)).fetchone() if d["BlockId"] else None
    revs = conn.execute("""SELECT r.*, u.display_name AS AuthorNm FROM TB_DWG_Revision r LEFT JOIN users u ON u.emp_no=r.AuthorEmpNo
                           WHERE r.DrawingId=? ORDER BY r.RevNo DESC""", (drawing_id,)).fetchall()
    aps = conn.execute("""SELECT a.*, u.display_name AS ApproverNm FROM TB_DWG_Approval a LEFT JOIN users u ON u.emp_no=a.ApproverEmpNo
                          WHERE a.DrawingId=? ORDER BY a.RevNo DESC, a.StepNo""", (drawing_id,)).fetchall()
    designer = conn.execute("SELECT display_name FROM users WHERE emp_no=?", (d["DesignerEmpNo"],)).fetchone() if d["DesignerEmpNo"] else None
    return {
        "drawing_id": d["DrawingId"], "drawing_no": d["DrawingNo"], "drawing_nm": d["DrawingNm"], "hull_no": d["HullNo"],
        "block_id": d["BlockId"], "block_cd": b["BlockCd"] if b else None, "block_nm": b["BlockNm"] if b else None,
        "discipline": d["Discipline"], "dwg_status": d["DwgStatus"], "current_rev_no": d["CurrentRevNo"],
        "latest_rev_no": revs[0]["RevNo"] if revs else None, "designer_emp_no": d["DesignerEmpNo"],
        "designer_nm": designer[0] if designer else None, "create_user_id": d["CreateUserId"], "create_dt": d["CreateDt"],
        "modify_user_id": d["ModifyUserId"], "modify_dt": d["ModifyDt"], "today": settings.business_date,
        "revisions": [{"rev_no": r["RevNo"], "rev_status": r["RevStatus"], "change_desc": r["ChangeDesc"],
                       "has_file": bool(r["FileId"]), "file_nm": r["FileNm"], "author_emp_no": r["AuthorEmpNo"],
                       "author_nm": r["AuthorNm"], "issue_dt": r["IssueDt"], "create_dt": r["CreateDt"]} for r in revs],
        "approvals": [{"approval_id": a["ApprovalId"], "rev_no": a["RevNo"], "step_no": a["StepNo"], "approver_emp_no": a["ApproverEmpNo"],
                       "approver_nm": a["ApproverNm"], "result": a["Result"], "comment": a["Comment"], "act_dt": a["ActDt"]} for a in aps],
        **drawing_plans(conn, drawing_id),
    }


def drawing_plans(conn, drawing_id) -> dict:
    d = _drawing(conn, drawing_id)
    links = conn.execute(_SELECT.replace("SELECT p.*", "SELECT p.*, l.RequiredYN, l.NeedDt") +
                         " JOIN TB_DWG_PlanLink l ON l.PlanId=p.PlanId WHERE l.DrawingId=?", (drawing_id,)).fetchall()
    free = conn.execute(_SELECT + " WHERE p.HullNo=? AND p.PlanId NOT IN (SELECT PlanId FROM TB_DWG_PlanLink WHERE DrawingId=?)",
                        (d["HullNo"], drawing_id)).fetchall()
    return {
        "plans": [{"plan_id": r["PlanId"], "label": _label(r), "plan_status": r["PlanStatus"], "required": bool(r["RequiredYN"]),
                   "need_dt": r["NeedDt"], "plan_start_dt": r["PlanStartDt"], "plan_end_dt": r["PlanEndDt"]}
                  for r in sorted(links, key=plan_service._sort_key)],
        "available_plans": [{"plan_id": r["PlanId"], "label": _label(r), "plan_status": r["PlanStatus"]}
                            for r in sorted(free, key=plan_service._sort_key)],
        "impacts": impacts(conn, drawing_id),
    }


# ---------------- DWG-02 create/update/delete ----------------
def _validate(conn, hull_no, data):
    nm = (data.get("drawing_nm") or "").strip()
    if not nm:
        _bad("도면명을 입력하세요.", "drawing_nm")
    disc = data.get("discipline")
    if disc not in codes(conn, "DWGDISC"):
        _bad("허용되지 않는 분야입니다.", "discipline")
    bid = data.get("block_id")
    if bid is not None and not conn.execute("SELECT 1 FROM TB_MST_Block WHERE BlockId=? AND HullNo=?", (bid, hull_no)).fetchone():
        _bad("해당 호선의 블록이 아닙니다.", "block_id")
    designer = data.get("designer_emp_no") or None
    _approved_user(conn, designer, "designer_emp_no")
    return nm, disc, bid, designer


def create_drawing(conn, data: dict, user: str) -> dict:
    no = (data.get("drawing_no") or "").strip()
    if not no:
        _bad("도면번호를 입력하세요.", "drawing_no")
    hull_no = data.get("hull_no")
    try:
        with transaction(conn):
            if not hull_no or not conn.execute("SELECT 1 FROM TB_MST_Hull WHERE HullNo=?", (hull_no,)).fetchone():
                _bad("호선을 선택하세요.", "hull_no")
            nm, disc, bid, designer = _validate(conn, hull_no, data)
            if conn.execute("SELECT 1 FROM TB_DWG_Drawing WHERE DrawingNo=?", (no,)).fetchone():
                _bad("이미 존재하는 도면번호입니다.", "drawing_no", 409, "DUPLICATE")
            did = conn.execute(
                "INSERT INTO TB_DWG_Drawing (DrawingNo,DrawingNm,HullNo,BlockId,Discipline,DwgStatus,CurrentRevNo,DesignerEmpNo,UseYN,CreateUserId,CreateDt) "
                "VALUES (?,?,?,?,?,'DRAFT',0,?,1,?,?)", (no, nm, hull_no, bid, disc, designer, user, settings.business_date)).lastrowid
            conn.execute("INSERT INTO TB_DWG_Revision (DrawingId,RevNo,RevStatus,ChangeDesc,AuthorEmpNo,CreateDt) VALUES (?,0,'DRAFT','최초 작성',?,?)",
                         (did, user, settings.business_date))
    except sqlite3.IntegrityError:
        _bad("이미 존재하는 도면번호입니다.", "drawing_no", 409, "DUPLICATE")
    return get_drawing(conn, did)


def update_drawing(conn, drawing_id, data: dict, user: str) -> dict:
    with transaction(conn):
        d = _drawing(conn, drawing_id)
        if data.get("hull_no") not in (None, d["HullNo"]):
            _bad("호선은 변경할 수 없습니다.", "hull_no")
        if data.get("drawing_no") not in (None, d["DrawingNo"]):
            _bad("도면번호는 변경할 수 없습니다.", "drawing_no")
        merged = {"drawing_nm": d["DrawingNm"], "discipline": d["Discipline"], "block_id": d["BlockId"], "designer_emp_no": d["DesignerEmpNo"]}
        merged.update({k: v for k, v in data.items() if k in merged})
        nm, disc, bid, designer = _validate(conn, d["HullNo"], merged)
        conn.execute("UPDATE TB_DWG_Drawing SET DrawingNm=?,Discipline=?,BlockId=?,DesignerEmpNo=?,ModifyUserId=?,ModifyDt=? WHERE DrawingId=?",
                     (nm, disc, bid, designer, user, settings.business_date, drawing_id))
    return get_drawing(conn, drawing_id)


def delete_drawing(conn, drawing_id) -> None:
    """BR-08: revisions, approvals (via revision FK), plan links cascade; stored PDFs removed after commit."""
    with transaction(conn):
        d = _drawing(conn, drawing_id)
        files = [r[0] for r in conn.execute("SELECT FileId FROM TB_DWG_Revision WHERE DrawingId=? AND FileId IS NOT NULL", (drawing_id,))]
        conn.execute("DELETE FROM TB_DWG_Drawing WHERE DrawingId=?", (drawing_id,))
        refresh_statuses(conn, d["HullNo"])
    file_store.remove(files)


# ---------------- DWG-04 revisions ----------------
def new_revision(conn, drawing_id, change_desc: str | None, user: str) -> dict:
    desc = (change_desc or "").strip()
    if not desc:
        _bad("개정 사유를 입력하세요.", "change_desc")
    with transaction(conn):
        d = _drawing(conn, drawing_id)
        lr = _latest(conn, drawing_id)
        if lr["RevStatus"] not in ("ISSUED", "OBSOLETE"):
            _bad("최신 리비전이 배포/폐기 상태일 때만 신규 리비전을 작성할 수 있습니다.", "rev_no", 409, "INVALID_REV_STATE")
        conn.execute("INSERT INTO TB_DWG_Revision (DrawingId,RevNo,RevStatus,ChangeDesc,AuthorEmpNo,CreateDt) VALUES (?,?,'DRAFT',?,?,?)",
                     (drawing_id, lr["RevNo"] + 1, desc, user, settings.business_date))
        conn.execute("UPDATE TB_DWG_Drawing SET DwgStatus='DRAFT' WHERE DrawingId=?", (drawing_id,))  # existing ISSUED rev kept
        refresh_statuses(conn, d["HullNo"])
    return get_drawing(conn, drawing_id)


def request_approval(conn, drawing_id, rev_no, reviewer, approver) -> dict:
    if not reviewer or not approver:
        _bad("검토자와 승인자를 선택하세요.", "reviewer_emp_no" if not reviewer else "approver_emp_no")
    if reviewer == approver:
        _bad("검토자와 승인자는 서로 다른 사람이어야 합니다.", "approver_emp_no")
    with transaction(conn):
        _drawing(conn, drawing_id)
        r = _rev(conn, drawing_id, rev_no)
        if r["RevNo"] != _latest(conn, drawing_id)["RevNo"] or r["RevStatus"] != "DRAFT":
            _bad("최신 작성중(DRAFT) 리비전만 결재 요청할 수 있습니다.", "rev_no", 409, "INVALID_REV_STATE")
        _approved_user(conn, reviewer, "reviewer_emp_no")
        _approved_user(conn, approver, "approver_emp_no")
        conn.execute("DELETE FROM TB_DWG_Approval WHERE DrawingId=? AND RevNo=?", (drawing_id, rev_no))  # mockup revRequest
        conn.executemany("INSERT INTO TB_DWG_Approval (DrawingId,RevNo,StepNo,ApproverEmpNo,Result) VALUES (?,?,?,?,'WAIT')",
                         [(drawing_id, rev_no, 1, reviewer), (drawing_id, rev_no, 2, approver)])
        conn.execute("UPDATE TB_DWG_Revision SET RevStatus='REVIEW' WHERE DrawingId=? AND RevNo=?", (drawing_id, rev_no))
        conn.execute("UPDATE TB_DWG_Drawing SET DwgStatus='REVIEW' WHERE DrawingId=?", (drawing_id,))
    return get_drawing(conn, drawing_id)


def issue(conn, drawing_id, rev_no) -> dict:
    """BR-06 issueRev: previous ISSUED -> OBSOLETE, rev ISSUED (IssueDt=TODAY), CurrentRevNo, then BR-02 gate recompute."""
    with transaction(conn):  # BEGIN IMMEDIATE serialises concurrent issues
        d = _drawing(conn, drawing_id)
        r = _rev(conn, drawing_id, rev_no)
        if r["RevStatus"] != "APPROVED":
            _bad("승인(APPROVED)된 리비전만 배포할 수 있습니다.", "rev_no", 409, "INVALID_REV_STATE")
        steps = conn.execute("SELECT Result FROM TB_DWG_Approval WHERE DrawingId=? AND RevNo=?", (drawing_id, rev_no)).fetchall()
        if not steps or any(s["Result"] != "APPROVE" for s in steps):  # D11: issue requires completed approval
            _bad("결재가 완료된 리비전만 배포할 수 있습니다.", "rev_no", 409, "APPROVAL_INCOMPLETE")
        conn.execute("UPDATE TB_DWG_Revision SET RevStatus='OBSOLETE' WHERE DrawingId=? AND RevStatus='ISSUED'", (drawing_id,))
        conn.execute("UPDATE TB_DWG_Revision SET RevStatus='ISSUED', IssueDt=? WHERE DrawingId=? AND RevNo=?",
                     (settings.business_date, drawing_id, rev_no))
        conn.execute("UPDATE TB_DWG_Drawing SET CurrentRevNo=?, DwgStatus='ISSUED' WHERE DrawingId=?", (rev_no, drawing_id))
        refresh_statuses(conn, d["HullNo"])
    return get_drawing(conn, drawing_id)


# ---------------- DWG-03 PDF ----------------
def upload_pdf(conn, drawing_id, rev_no, filename, content_type, data: bytes) -> dict:
    name = file_store.validate(filename, content_type, data)
    _drawing(conn, drawing_id)
    if _rev(conn, drawing_id, rev_no)["RevStatus"] != "DRAFT":
        _bad("작성중(DRAFT) 리비전만 업로드할 수 있습니다.", "rev_no", 409, "INVALID_REV_STATE")
    new_id = file_store.write(data)
    try:
        with transaction(conn):
            r = _rev(conn, drawing_id, rev_no)
            if r["RevStatus"] != "DRAFT":
                _bad("작성중(DRAFT) 리비전만 업로드할 수 있습니다.", "rev_no", 409, "INVALID_REV_STATE")
            old = r["FileId"]
            conn.execute("UPDATE TB_DWG_Revision SET FileId=?, FileNm=? WHERE DrawingId=? AND RevNo=?", (new_id, name, drawing_id, rev_no))
    except BaseException:
        file_store.remove([new_id])
        raise
    file_store.remove([old])
    return get_drawing(conn, drawing_id)


def delete_pdf(conn, drawing_id, rev_no) -> dict:
    with transaction(conn):
        _drawing(conn, drawing_id)
        r = _rev(conn, drawing_id, rev_no)
        if r["RevStatus"] != "DRAFT":
            _bad("작성중(DRAFT) 리비전만 파일을 삭제할 수 있습니다.", "rev_no", 409, "INVALID_REV_STATE")
        if not r["FileId"]:
            raise ApiError(404, "FILE_NOT_FOUND", "업로드된 파일이 없습니다.")
        conn.execute("UPDATE TB_DWG_Revision SET FileId=NULL, FileNm=NULL WHERE DrawingId=? AND RevNo=?", (drawing_id, rev_no))
    file_store.remove([r["FileId"]])
    return get_drawing(conn, drawing_id)


def pdf_file(conn, drawing_id, rev_no):
    """Returns (path, filename). No uploaded file -> 404 NO_FILE; the UI then shows a labelled sample (DWG-T05)."""
    _drawing(conn, drawing_id)
    r = _rev(conn, drawing_id, rev_no)
    if not r["FileId"]:
        raise ApiError(404, "NO_FILE", "업로드된 PDF가 없습니다. (샘플 표시)")
    p = file_store.path_of(r["FileId"])
    if not p.is_file():
        raise ApiError(404, "FILE_NOT_FOUND", "파일을 찾을 수 없습니다.")
    return p, r["FileNm"] or f"rev{rev_no}.pdf"


# ---------------- DWG-05 plan links (reuses F05 link logic) ----------------
def link_plan(conn, drawing_id, plan_id, required: bool) -> dict:
    _drawing(conn, drawing_id)
    plan_service.link_drawing(conn, plan_id, drawing_id, required)
    return drawing_plans(conn, drawing_id)


def unlink_plan(conn, drawing_id, plan_id) -> dict:
    _drawing(conn, drawing_id)
    plan_service.unlink_drawing(conn, plan_id, drawing_id)
    return drawing_plans(conn, drawing_id)
