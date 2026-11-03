"""F04 hulls / milestones / blocks. Cascade deletes rely on FK rules in migrations (BR-08), inside one transaction."""
import re
import sqlite3
from datetime import date

from ..config import settings
from ..db import transaction
from ..errors import ApiError
from . import code_service, file_store
from .metrics import weighted_progress

# API snake_case <-> DB PascalCase (single adapter, 01-system 공통 데이터 계약)
HULL_FIELDS = {
    "hull_no": "HullNo", "hull_nm": "HullNm", "ship_type": "ShipType", "hull_status": "HullStatus",
    "owner_nm": "OwnerNm", "class_society": "ClassSociety", "length_m": "LengthM", "breadth_m": "BreadthM",
    "depth_m": "DepthM", "dead_weight": "DeadWeight", "dock_no": "DockNo", "contract_dt": "ContractDt",
    "delivery_dt": "DeliveryDt", "remark": "Remark", "use_yn": "UseYN", "create_user_id": "CreateUserId",
    "create_dt": "CreateDt", "modify_user_id": "ModifyUserId", "modify_dt": "ModifyDt",
}
EDITABLE = [k for k in HULL_FIELDS if k not in ("hull_no", "create_user_id", "create_dt", "modify_user_id", "modify_dt")]
MILESTONES = ["CUT", "KEEL", "LAUNCH", "TRIAL", "DELIVER"]
HULL_NO_RE = re.compile(r"^[A-Za-z0-9._-]{1,20}$")


def _bad(msg, field=None, status=400, code="VALIDATION_ERROR"):
    raise ApiError(status, code, msg, {"field": field} if field else {})


def _date(v, field):
    if v in (None, ""):
        return None
    try:
        return date.fromisoformat(v).isoformat()
    except (TypeError, ValueError):
        _bad("날짜 형식(YYYY-MM-DD)이 올바르지 않습니다.", field)


def _hull_out(r, plans) -> dict:
    d = {k: r[v] for k, v in HULL_FIELDS.items()}
    d["use_yn"] = bool(d["use_yn"])
    d["plan_count"] = len(plans)
    d["progress"] = weighted_progress(plans) if plans else None  # None => '계획 없음'
    d["delay_count"] = sum(1 for p in plans if p["PlanStatus"] == "DELAY")
    return d


def _plans_by_hull(conn, hull_no=None):
    sql = "SELECT HullNo, BlockId, PlanStartDt, PlanEndDt, ProgressRate, PlanStatus FROM TB_PRC_Plan"
    rows = conn.execute(sql + (" WHERE HullNo=?" if hull_no else ""), (hull_no,) if hull_no else ()).fetchall()
    out: dict[str, list] = {}
    for p in rows:
        out.setdefault(p["HullNo"], []).append(p)
    return out


def _get_row(conn, hull_no):
    r = conn.execute("SELECT * FROM TB_MST_Hull WHERE HullNo=?", (hull_no,)).fetchone()
    if not r:
        raise ApiError(404, "HULL_NOT_FOUND", "호선을 찾을 수 없습니다.")
    return r


def list_hulls(conn, status=None, ship_type=None, q=None) -> list[dict]:
    sql, args = "SELECT * FROM TB_MST_Hull WHERE 1=1", []
    if status:
        sql += " AND HullStatus=?"; args.append(status)
    if ship_type:
        sql += " AND ShipType=?"; args.append(ship_type)
    if q:
        sql += " AND instr(lower(HullNo || COALESCE(HullNm,'') || COALESCE(OwnerNm,'')), lower(?)) > 0"; args.append(q)
    plans = _plans_by_hull(conn)
    return [_hull_out(r, plans.get(r["HullNo"], [])) for r in conn.execute(sql + " ORDER BY HullNo", args)]


def get_hull(conn, hull_no) -> dict:
    r = _get_row(conn, hull_no)
    return _hull_out(r, _plans_by_hull(conn, hull_no).get(hull_no, []))


def _validate(conn, d: dict) -> dict:
    for f, grp in (("ship_type", "SHIPTYPE"), ("hull_status", "HULLSTAT")):
        if d.get(f) in ("",):
            d[f] = None
        if d.get(f) is not None and d[f] not in code_service.codes(conn, grp):
            _bad("허용되지 않는 코드값입니다.", f)
    for f in ("contract_dt", "delivery_dt"):
        if f in d:
            d[f] = _date(d[f], f)
    for f in ("length_m", "breadth_m", "depth_m", "dead_weight"):
        if d.get(f) is not None and d[f] < 0:
            _bad("0 이상의 값을 입력하세요.", f)
    for f in ("hull_nm", "owner_nm", "class_society", "dock_no", "remark"):
        if f in d and isinstance(d[f], str):
            d[f] = d[f].strip()
    return d


def _check_dates(c, dl):
    if c and dl and dl < c:
        _bad("인도 예정일이 계약일보다 빠릅니다.", "delivery_dt")


def create_hull(conn, data: dict, user: str) -> dict:
    hull_no = (data.get("hull_no") or "").strip()
    if not hull_no:
        _bad("호선번호를 입력하세요.", "hull_no")
    if not HULL_NO_RE.match(hull_no):
        _bad("호선번호는 영문/숫자/._- 1~20자입니다.", "hull_no")
    d = _validate(conn, {k: data.get(k) for k in EDITABLE})
    d["hull_status"] = d.get("hull_status") or "PLAN"
    d["use_yn"] = 1 if d.get("use_yn") is None else int(bool(d["use_yn"]))
    _check_dates(d["contract_dt"], d["delivery_dt"])
    cols = ["HullNo"] + [HULL_FIELDS[k] for k in EDITABLE] + ["CreateUserId", "CreateDt"]
    vals = [hull_no] + [d[k] for k in EDITABLE] + [user, settings.business_date]
    try:
        with transaction(conn):
            if conn.execute("SELECT 1 FROM TB_MST_Hull WHERE HullNo=?", (hull_no,)).fetchone():
                _bad("이미 존재하는 호선번호입니다.", "hull_no", 409, "DUPLICATE")
            conn.execute(f"INSERT INTO TB_MST_Hull ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals)
            conn.executemany("INSERT INTO TB_MST_HullMilestone (HullNo, MilestoneCd, PlanDt) VALUES (?,?,?)",
                             [(hull_no, m, d["delivery_dt"] if m == "DELIVER" else None) for m in MILESTONES])
    except sqlite3.IntegrityError:
        _bad("이미 존재하는 호선번호입니다.", "hull_no", 409, "DUPLICATE")
    return get_hull(conn, hull_no)


def update_hull(conn, hull_no: str, data: dict, user: str) -> dict:
    if "hull_no" in data and data["hull_no"] not in (None, hull_no):
        _bad("호선번호는 수정할 수 없습니다.", "hull_no")
    d = _validate(conn, {k: v for k, v in data.items() if k in EDITABLE})
    if "hull_status" in d and d["hull_status"] is None:
        _bad("상태를 선택하세요.", "hull_status")
    if "use_yn" in d:
        d["use_yn"] = int(bool(d["use_yn"]))
    with transaction(conn):
        cur = _get_row(conn, hull_no)
        _check_dates(d.get("contract_dt", cur["ContractDt"]), d.get("delivery_dt", cur["DeliveryDt"]))
        sets = [f"{HULL_FIELDS[k]}=?" for k in d] + ["ModifyUserId=?", "ModifyDt=?"]
        conn.execute(f"UPDATE TB_MST_Hull SET {','.join(sets)} WHERE HullNo=?",
                     [*d.values(), user, settings.business_date, hull_no])
    return get_hull(conn, hull_no)


def delete_hull(conn, hull_no: str) -> None:
    """BR-08: milestones, blocks, plans, deps, progress, drawings, revisions(+file metadata), approvals, links via FK CASCADE.
    Stored PDFs (D12) are removed after the DB commit."""
    with transaction(conn):
        _get_row(conn, hull_no)
        files = [r[0] for r in conn.execute("""SELECT r.FileId FROM TB_DWG_Revision r JOIN TB_DWG_Drawing d ON d.DrawingId=r.DrawingId
                                               WHERE d.HullNo=? AND r.FileId IS NOT NULL""", (hull_no,))]
        conn.execute("DELETE FROM TB_MST_Hull WHERE HullNo=?", (hull_no,))
    file_store.remove(files)


# ---- milestones ----
def get_milestones(conn, hull_no) -> list[dict]:
    _get_row(conn, hull_no)
    rows = {r["MilestoneCd"]: r for r in conn.execute("SELECT * FROM TB_MST_HullMilestone WHERE HullNo=?", (hull_no,))}
    names = {c["code"]: c["name"] for c in code_service.all_codes(conn).get("MILESTONE", [])}
    out = []
    for m in MILESTONES:
        r = rows.get(m)
        plan, actual = (r["PlanDt"], r["ActualDt"]) if r else (None, None)
        diff = (date.fromisoformat(actual) - date.fromisoformat(plan)).days if plan and actual else None
        out.append({"milestone_cd": m, "name": names.get(m, m), "plan_dt": plan, "actual_dt": actual, "diff_days": diff})
    return out


def put_milestones(conn, hull_no, items: list[dict]) -> list[dict]:
    seen = set()
    clean = []
    for it in items:
        m = it.get("milestone_cd")
        if m not in MILESTONES or m in seen:
            _bad("허용되지 않거나 중복된 일정 코드입니다.", "milestone_cd")
        seen.add(m)
        clean.append((hull_no, m, _date(it.get("plan_dt"), "plan_dt"), _date(it.get("actual_dt"), "actual_dt")))
    with transaction(conn):
        _get_row(conn, hull_no)
        conn.executemany(
            "INSERT INTO TB_MST_HullMilestone (HullNo, MilestoneCd, PlanDt, ActualDt) VALUES (?,?,?,?) "
            "ON CONFLICT(HullNo, MilestoneCd) DO UPDATE SET PlanDt=excluded.PlanDt, ActualDt=excluded.ActualDt", clean)
    return get_milestones(conn, hull_no)


# ---- blocks ----
def _block_out(b, plans, dwg_count) -> dict:
    bp = [p for p in plans if p["BlockId"] == b["BlockId"]]
    return {"block_id": b["BlockId"], "hull_no": b["HullNo"], "block_cd": b["BlockCd"], "block_nm": b["BlockNm"],
            "block_type": b["BlockType"], "parent_block_id": b["ParentBlockId"], "weight_ton": b["WeightTon"],
            "use_yn": bool(b["UseYN"]), "plan_count": len(bp), "progress": weighted_progress(bp) if bp else None,
            "drawing_count": dwg_count.get(b["BlockId"], 0)}


def list_blocks(conn, hull_no) -> list[dict]:
    _get_row(conn, hull_no)
    plans = _plans_by_hull(conn, hull_no).get(hull_no, [])
    dwg = {r[0]: r[1] for r in conn.execute(
        "SELECT BlockId, COUNT(*) FROM TB_DWG_Drawing WHERE HullNo=? AND BlockId IS NOT NULL GROUP BY BlockId", (hull_no,))}
    rows = conn.execute("SELECT * FROM TB_MST_Block WHERE HullNo=? ORDER BY BlockCd", (hull_no,)).fetchall()
    return [_block_out(b, plans, dwg) for b in rows]


def add_block(conn, hull_no, data: dict) -> dict:
    cd = (data.get("block_cd") or "").strip()
    if not cd:
        _bad("블록코드를 입력하세요.", "block_cd")
    bt = data.get("block_type") or None
    if bt is not None and bt not in code_service.codes(conn, "BLOCKTYPE"):
        _bad("허용되지 않는 코드값입니다.", "block_type")
    w = data.get("weight_ton")
    if w is not None and w < 0:
        _bad("0 이상의 값을 입력하세요.", "weight_ton")
    try:
        with transaction(conn):
            _get_row(conn, hull_no)
            if conn.execute("SELECT 1 FROM TB_MST_Block WHERE HullNo=? AND BlockCd=?", (hull_no, cd)).fetchone():
                _bad("이미 존재하는 블록코드입니다.", "block_cd", 409, "DUPLICATE")
            bid = conn.execute("INSERT INTO TB_MST_Block (HullNo,BlockCd,BlockNm,BlockType,ParentBlockId,WeightTon,UseYN) "
                               "VALUES (?,?,?,?,NULL,?,1)", (hull_no, cd, (data.get("block_nm") or "").strip(), bt, w)).lastrowid
    except sqlite3.IntegrityError:
        _bad("이미 존재하는 블록코드입니다.", "block_cd", 409, "DUPLICATE")
    return next(b for b in list_blocks(conn, hull_no) if b["block_id"] == bid)


def delete_block(conn, block_id: int) -> None:
    """BR-08: block plans (+progress/deps/links) cascade; drawings kept with BlockId=NULL (FK SET NULL)."""
    with transaction(conn):
        b = conn.execute("SELECT HullNo FROM TB_MST_Block WHERE BlockId=?", (block_id,)).fetchone()
        if not b:
            raise ApiError(404, "BLOCK_NOT_FOUND", "블록을 찾을 수 없습니다.")
        conn.execute("DELETE FROM TB_MST_Block WHERE BlockId=?", (block_id,))
        from .plan_service import refresh_statuses  # successors may become READY once deleted predecessors vanish
        refresh_statuses(conn, b["HullNo"])


# ---- summary (HULL-07) ----
def summary(conn, hull_no) -> dict:
    _get_row(conn, hull_no)
    plans = _plans_by_hull(conn, hull_no).get(hull_no, [])
    plan_status = {k: 0 for k in ("PLAN", "READY", "WORK", "DONE", "DELAY")}
    for p in plans:
        plan_status[p["PlanStatus"]] = plan_status.get(p["PlanStatus"], 0) + 1
    dwg_status = {k: 0 for k in ("ISSUED", "APPROVED", "REVIEW", "DRAFT")}
    total_dwg = 0
    for r in conn.execute("SELECT DwgStatus, COUNT(*) FROM TB_DWG_Drawing WHERE HullNo=? GROUP BY DwgStatus", (hull_no,)):
        total_dwg += r[1]
        if r[0] in dwg_status:
            dwg_status[r[0]] = r[1]
    return {"hull_no": hull_no, "plan_count": len(plans), "progress": weighted_progress(plans) if plans else None,
            "plan_status": plan_status, "drawing_count": total_dwg, "drawing_status": dwg_status}
