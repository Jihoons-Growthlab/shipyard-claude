"""Demo seed for system tables (OBS mockup seed(), lines 252-299). Idempotent (INSERT OR IGNORE).
Domain seed (hulls/plans/drawings) is added by its own feature (F04~F07)."""
import sqlite3

from .db import transaction
from .security import hash_password

CODE_GROUPS = {
    "SHIPTYPE": ("선종", "LNG=LNG운반선,VLCC=원유운반선,CONT=컨테이너선,PC=PC선"),
    "HULLSTAT": ("호선상태", "PLAN=계획,DESIGN=설계,BUILD=건조,LAUNCH=진수,TRIAL=시운전,DELIVER=인도"),
    "MILESTONE": ("주요일정", "CUT=강재절단,KEEL=기공(Keel Laying),LAUNCH=진수,TRIAL=시운전,DELIVER=인도"),
    "BLOCKTYPE": ("블록유형", "FLAT=평블록,CURVE=곡블록,ENGINE=엔진룸"),
    "PLANSTAT": ("공정상태", "PLAN=계획,READY=착수가능,WORK=진행,DONE=완료,DELAY=지연"),
    "DWGDISC": ("도면분야", "HULL=선체,MACH=기계,ELEC=전장,PIPE=배관,OUTFIT=의장"),
    "DWGSTAT": ("도면상태", "DRAFT=작성중,REVIEW=검토중,APPROVED=승인,ISSUED=배포,OBSOLETE=폐기"),
}
# Demo-only TOTP secret from the mockup (never exposed by the API). Real enrollment is D05 (Phase S).
DEMO_TOTP_SECRET = "JBSWY3DPEHPK3PXP"
USERS = [  # emp_no, last, first, birth, phone, password, status, totp
    ("admin", "김", "관리", "1980-03-12", "010-1111-0001", "admin1234", "approved", True),
    ("park.pm", "박", "공정", "1985-07-21", "010-2222-0002", "pm1234", "approved", False),
    ("lee.dwg", "이", "도면", "1988-11-02", "010-3333-0003", "dwg1234", "approved", True),
    ("han.wk", "한", "현장", "1990-05-30", "010-4444-0004", "wk1234", "approved", False),
    ("choi.qa", "최", "품질", "1983-09-09", "010-5555-0005", "qa1234", "approved", False),
    ("jung.new", "정", "신입", "1995-01-17", "010-6666-0006", "new12345", "pending", False),
]
GROUPS = [("ADMIN", "시스템관리자"), ("PROC", "공정관리자"), ("DWG", "도면관리자"), ("VIEW", "조회전용")]
GROUP_USERS = [("ADMIN", "admin"), ("PROC", "park.pm"), ("DWG", "lee.dwg"), ("PROC", "han.wk"), ("VIEW", "choi.qa")]
MENUS = [  # M12/M32/M40 purged in mockup (details are modals)
    ("M00", None, "대시보드", "dashboard"), ("M10", None, "호선관리", None), ("M11", "M10", "호선 목록", "hull-list"),
    ("M20", None, "공정관리", None), ("M21", "M20", "공정 계획", "plan-gantt"), ("M22", "M20", "공정 실적", "progress"),
    ("M30", None, "도면관리", None), ("M31", "M30", "도면 목록", "dwg-list"), ("M33", "M30", "결재함", "dwg-approval"),
    ("M90", None, "시스템", None), ("M91", "M90", "회원관리", "user-mgmt"),
]
AUTH_MENU = {
    "ADMIN": "*:Admin",
    "PROC": "M00:View,M10:Write,M11:Write,M20:Write,M21:Write,M22:Write,M30:View,M31:View",
    "DWG": "M00:View,M10:View,M11:View,M20:View,M21:View,M30:Write,M31:Write,M33:Write",
    "VIEW": "M00:View,M10:View,M11:View,M20:View,M21:View,M22:View,M30:View,M31:View,M33:View",
}


def seed_system(conn: sqlite3.Connection) -> None:
    with transaction(conn):
        for i, (g, (name, spec)) in enumerate(CODE_GROUPS.items(), 1):
            conn.execute("INSERT OR IGNORE INTO TB_SYS_CodeGroup VALUES (?,?,?,1)", (g, name, i))
            for j, pair in enumerate(spec.split(","), 1):
                c, n = pair.split("=")
                conn.execute("INSERT OR IGNORE INTO TB_SYS_Code VALUES (?,?,?,?,1)", (g, c, n, j))
        for emp, ln, fn, bd, ph, pw, st, otp in USERS:
            if conn.execute("SELECT 1 FROM users WHERE emp_no=?", (emp,)).fetchone():
                continue
            conn.execute(
                "INSERT INTO users (id,email,password_hash,display_name,emp_no,status,auth_provider,last_name,first_name,"
                "birth_date,phone,totp_enabled,totp_secret,created_at) VALUES (?,?,?,?,?,?, 'local',?,?,?,?,?,?, '2026-01-05')",
                ("u-" + emp, f"{emp}@swp.co.kr", hash_password(pw), ln + fn, emp, st, ln, fn, bd, ph,
                 int(otp), DEMO_TOTP_SECRET if otp else None),
            )
        conn.executemany("INSERT OR IGNORE INTO TB_SYS_AuthGroup VALUES (?,?)", GROUPS)
        conn.executemany("INSERT OR IGNORE INTO TB_SYS_AuthUser VALUES (?,?)", GROUP_USERS)
        for seq, (mid, parent, title, token) in enumerate(MENUS, 1):
            conn.execute("INSERT OR IGNORE INTO TB_SYS_MenuInfo VALUES (?, 'SHIP', ?,?,?,?,1)", (mid, parent, title, token, seq))
        for g, spec in AUTH_MENU.items():
            for item in spec.split(","):
                m, gbn = item.split(":")
                targets = [x[0] for x in MENUS] if m == "*" else [m]
                for t in targets:
                    conn.execute("INSERT OR IGNORE INTO TB_SYS_AuthMenu VALUES (?,?,?)", (t, g, gbn))


# ---- F04 domain seed (OBS seed() lines 300~321): process master, hulls, milestones, blocks ----
PROCS = [("CUT", "강재절단", "HULL", 14), ("SUBASM", "소조립", "HULL", 20), ("ASM", "대조립", "HULL", 28),
         ("PAINT", "도장", "PAINT", 16), ("ERECT", "탑재", "HULL", 42), ("LAUNCH", "진수", "HULL", 3),
         ("TRIAL", "시운전", "TRIAL", 45)]
HULLS = [
    ("8001", "SWP LNG 174K 1호", "LNG", "BUILD", "Nordic Gas Shipping", "DNV", 295, 46, 26, 98000, "1도크", "2025-03-10", "2027-06-30", "LNG 17.4만㎥급",
     ["2026-06-15", "2026-09-14", "2027-02-10", "2027-03-20", "2027-06-30"]),
    ("8002", "Ocean Titan", "VLCC", "BUILD", "Pacific Tankers", "LR", 336, 60, 30.4, 310000, "2도크", "2025-06-20", "2027-09-30", "31만DWT급 원유운반선",
     ["2026-09-01", "2026-12-01", "2027-04-20", "2027-06-01", "2027-09-30"]),
    ("8003", "Blue Horizon 15K", "CONT", "DESIGN", "Asia Container Line", "KR", 366, 51, 30, 180000, "3도크", "2026-04-15", "2028-03-31", "15,000TEU급",
     ["2027-01-10", "2027-04-12", "2027-12-01", "2028-01-20", "2028-03-31"]),
    ("8004", "Star Chemi", "PC", "PLAN", "Helios Marine", "ABS", 183, 32, 19, 50000, "", "2026-09-01", "2028-09-30", "5만DWT PC선",
     ["2027-06-01", "2027-09-01", "2028-06-01", "2028-07-20", "2028-09-30"]),
    ("8005", "Aurora LNG", "LNG", "TRIAL", "Nordic Gas Shipping", "DNV", 295, 46, 26, 98000, "1도크", "2024-09-12", "2026-12-15", "LNG 17.4만㎥급",
     ["2026-02-01", "2026-04-20", "2026-08-12", "2026-11-15", "2026-12-15"]),
]
MILESTONES = ["CUT", "KEEL", "LAUNCH", "TRIAL", "DELIVER"]
BLOCKS = [("101", "선수부 블록", "FLAT", 420), ("201", "중앙부 블록", "FLAT", 610), ("301", "선미 곡블록", "CURVE", 380),
          ("401", "엔진룸 블록", "ENGINE", 520), ("501", "상부구조 블록", "CURVE", 300)]
BLOCK_COUNT = {"8001": 5, "8002": 4, "8003": 3, "8004": 2, "8005": 3}


def seed_hulls(conn: sqlite3.Connection, today: str = "2026-10-19") -> None:
    from datetime import date, timedelta

    def add(d, n):
        return (date.fromisoformat(d) + timedelta(days=n)).isoformat()

    with transaction(conn):
        for i, p in enumerate(PROCS, 1):
            conn.execute("INSERT OR IGNORE INTO TB_PRC_Proc VALUES (?,?,?,?,?,1)", (*p, i))
        for h in HULLS:
            if conn.execute("SELECT 1 FROM TB_MST_Hull WHERE HullNo=?", (h[0],)).fetchone():
                continue
            conn.execute(
                "INSERT INTO TB_MST_Hull (HullNo,HullNm,ShipType,HullStatus,OwnerNm,ClassSociety,LengthM,BreadthM,DepthM,"
                "DeadWeight,DockNo,ContractDt,DeliveryDt,Remark,UseYN,CreateUserId,CreateDt) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,'admin','2026-01-10')", h[:14])
            for i, (m, pd) in enumerate(zip(MILESTONES, h[14])):
                actual = add(pd, 4 if i == 1 else 2 if i == 0 else 0) if pd <= today else None
                conn.execute("INSERT INTO TB_MST_HullMilestone VALUES (?,?,?,?,NULL)", (h[0], m, pd, actual))
            for cd, nm, bt, w in BLOCKS[:BLOCK_COUNT[h[0]]]:
                conn.execute("INSERT INTO TB_MST_Block (HullNo,BlockCd,BlockNm,BlockType,ParentBlockId,WeightTon,UseYN) "
                             "VALUES (?,?,?,?,NULL,?,1)", (h[0], cd, nm, bt, w))


# ---- F05 seed (OBS seed() lines 324~402): plans, deps, daily progress, drawings/revisions/approvals/links ----
PLAN_START = [("8001", "2026-06-15", 20), ("8002", "2026-09-01", 20), ("8003", "2027-01-10", 20), ("8005", "2026-02-01", 15)]
CHAIN = ["CUT", "SUBASM", "ASM", "PAINT", "ERECT"]
DUR = {"CUT": 14, "SUBASM": 20, "ASM": 28, "PAINT": 16, "ERECT": 42}
MGR = ["park.pm", "han.wk"]
DISC = [("HULL", "선체 구조도", "CUT"), ("PIPE", "배관 계통도", "ASM"), ("ELEC", "전장 배선도", "ERECT")]


def _dstat(hn, bi, dc):
    if hn == "8001":
        return "REVIEW" if dc == "ELEC" and bi == 4 else "APPROVED" if dc == "ELEC" and bi == 3 else "ISSUED"
    if hn == "8002":
        return ("REVIEW" if dc == "HULL" else "DRAFT") if bi == 3 else ("REVIEW" if dc == "ELEC" and bi == 2 else "ISSUED")
    if hn == "8003":
        return ("APPROVED" if bi == 0 else "REVIEW" if bi == 1 else "DRAFT") if dc == "HULL" else "DRAFT"
    if hn == "8004":
        return "DRAFT" if dc == "HULL" else None
    return "ISSUED"


def seed_plans(conn: sqlite3.Connection, today: str = "2026-10-19") -> None:
    import math
    from datetime import date, timedelta

    from .services.plan_service import refresh_statuses

    def add(d, n):
        return (date.fromisoformat(d) + timedelta(days=n)).isoformat()

    def diff(a, b):
        return (date.fromisoformat(b) - date.fromisoformat(a)).days

    def jsround(x):
        return math.floor(x + 0.5)

    if conn.execute("SELECT 1 FROM TB_PRC_Plan LIMIT 1").fetchone() or conn.execute("SELECT 1 FROM TB_DWG_Drawing LIMIT 1").fetchone():
        return
    with transaction(conn):
        plans = {}  # (hull, block_id, proc) -> dict

        def mk(hn, bid, proc, s, e, mgr):
            st, pr, a_s, a_e = "PLAN", 0, None, None
            if e < today:
                st, pr, a_s, a_e = "DONE", 100, s, e
            elif s <= today:
                st, pr, a_s = "WORK", min(95, max(5, jsround((diff(s, today) + 1) / (diff(s, e) + 1) * 20) * 5)), s
            p = {"HullNo": hn, "BlockId": bid, "ProcCd": proc, "PlanStartDt": s, "PlanEndDt": e, "ActualStartDt": a_s,
                 "ActualEndDt": a_e, "ProgressRate": pr, "PlanStatus": st, "ManagerEmpNo": mgr, "Remark": None}
            p["PlanId"] = conn.execute(
                "INSERT INTO TB_PRC_Plan (HullNo,BlockId,ProcCd,PlanStartDt,PlanEndDt,ActualStartDt,ActualEndDt,ProgressRate,"
                "PlanStatus,ManagerEmpNo,Remark,CreateUserId,CreateDt) VALUES (?,?,?,?,?,?,?,?,?,?,NULL,'park.pm','2026-02-01')",
                (hn, bid, proc, s, e, a_s, a_e, pr, st, mgr)).lastrowid
            plans[(hn, bid, proc)] = p
            return p

        dep = lambda pid, pred: conn.execute("INSERT INTO TB_PRC_PlanDep (PlanId, PredPlanId, LagDays) VALUES (?,?,0)", (pid, pred))
        for hn, s0, step in PLAN_START:
            blocks = conn.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo=? ORDER BY BlockId", (hn,)).fetchall()
            erects = []
            for bi, b in enumerate(blocks):
                cur, prev = add(s0, bi * step), None
                for pc in CHAIN:
                    e = add(cur, DUR[pc] - 1)
                    p = mk(hn, b[0], pc, cur, e, MGR[bi % 2])
                    if prev:
                        dep(p["PlanId"], prev["PlanId"])
                    prev, cur = p, add(e, 1)
                    if pc == "ERECT":
                        erects.append(p)
            ms = {r[0]: r[1] for r in conn.execute("SELECT MilestoneCd, PlanDt FROM TB_MST_HullMilestone WHERE HullNo=?", (hn,))}
            launch = mk(hn, None, "LAUNCH", ms["LAUNCH"], add(ms["LAUNCH"], 2), "park.pm")
            trial = mk(hn, None, "TRIAL", add(ms["LAUNCH"], 5), ms["TRIAL"], "park.pm")
            for p in erects:
                dep(launch["PlanId"], p["PlanId"])
            dep(trial["PlanId"], launch["PlanId"])
        # scenario override: 8001-301 painting delayed (60%), following erection waits
        b301 = conn.execute("SELECT BlockId FROM TB_MST_Block WHERE HullNo='8001' AND BlockCd='301'").fetchone()[0]
        paint, erect = plans[("8001", b301, "PAINT")], plans[("8001", b301, "ERECT")]
        paint.update(ProgressRate=60, ActualStartDt="2026-09-27", ActualEndDt=None, PlanStatus="DELAY", Remark="도장 부스 가동 지연")
        erect.update(ProgressRate=0, ActualStartDt=None, PlanStatus="PLAN")
        for p in (paint, erect):
            conn.execute("UPDATE TB_PRC_Plan SET ProgressRate=?, ActualStartDt=?, ActualEndDt=?, PlanStatus=?, Remark=? WHERE PlanId=?",
                         (p["ProgressRate"], p["ActualStartDt"], p["ActualEndDt"], p["PlanStatus"], p["Remark"], p["PlanId"]))
        # daily progress
        for p in sorted(plans.values(), key=lambda x: x["PlanId"]):
            pid = p["PlanId"]
            if p["PlanStatus"] == "DONE":
                conn.execute("INSERT INTO TB_PRC_Progress (PlanId,WorkDt,ProgressRate,ManHour,WorkerCnt,WorkerEmpNo,Remark,CreateDt) "
                             "VALUES (?,?,100,?,8,?,'완료',?)", (pid, p["ActualEndDt"], 80 + pid % 40, p["ManagerEmpNo"], p["ActualEndDt"]))
            elif p["ProgressRate"] > 0:
                for k in (2, 1, 0):
                    conn.execute("INSERT INTO TB_PRC_Progress (PlanId,WorkDt,ProgressRate,ManHour,WorkerCnt,WorkerEmpNo,Remark,CreateDt) "
                                 "VALUES (?,?,?,?,?,?,NULL,?)",
                                 (pid, add(today, -k), max(1, p["ProgressRate"] - k * 3), 60 + (pid * 7 + k * 11) % 50,
                                  6 + (pid + k) % 4, p["ManagerEmpNo"], add(today, -k)))
        # drawings / revisions / approvals / plan links
        for h in HULLS:
            hn, contract = h[0], h[11]
            blocks = conn.execute("SELECT BlockId, BlockCd, BlockNm FROM TB_MST_Block WHERE HullNo=? ORDER BY BlockId", (hn,)).fetchall()
            for bi, b in enumerate(blocks):
                for di, (dc, nm, pc) in enumerate(DISC):
                    st = _dstat(hn, bi, dc)
                    if not st:
                        continue
                    no = f"{hn}-{dc}-{b['BlockCd']}"
                    plan = plans.get((hn, b["BlockId"], pc))
                    base = add(plan["PlanStartDt"], -12) if plan else add(contract, 30)
                    r = (bi + di + int(hn) % 7) % 3 if st == "ISSUED" else (1 if hn == "8001" and dc == "ELEC" else 0)
                    if no == "8001-HULL-201":
                        r = 2
                    did = conn.execute(
                        "INSERT INTO TB_DWG_Drawing (DrawingNo,DrawingNm,HullNo,BlockId,Discipline,DwgStatus,CurrentRevNo,DesignerEmpNo,UseYN,CreateUserId,CreateDt) "
                        "VALUES (?,?,?,?,?,?,0,'lee.dwg',1,'lee.dwg','2026-02-10')",
                        (no, f"{b['BlockNm']} {nm}", hn, b["BlockId"], dc, st)).lastrowid
                    cur_rev = 0
                    for k in range(r + 1):
                        rs = st if k == r else ("ISSUED" if st != "ISSUED" and k == r - 1 else "OBSOLETE")
                        idt = add(base, -15 * (r - k)) if rs in ("ISSUED", "OBSOLETE") else None
                        desc = ("최초 발행" if st == "ISSUED" or r > 0 else "최초 작성") if k == 0 else (["", "설계 변경 반영", "현장 요청 사항 반영"][k] if k < 3 else "개정")
                        if no == "8001-HULL-201" and k == 2:
                            idt, desc = "2026-10-12", "하중조건 변경에 따른 보강재 추가"
                        conn.execute("INSERT INTO TB_DWG_Revision (DrawingId,RevNo,RevStatus,ChangeDesc,FileId,FileNm,AuthorEmpNo,IssueDt,CreateDt) "
                                     "VALUES (?,?,?,?,NULL,?,'lee.dwg',?,?)", (did, k, rs, desc, f"{no}_R{k}.dwg", idt, idt or today))
                        if rs == "ISSUED":
                            cur_rev = k
                        if k == r and st in ("REVIEW", "APPROVED", "ISSUED"):
                            s1 = ("APPROVE" if no == "8002-HULL-401" else "WAIT") if st == "REVIEW" else "APPROVE"
                            s2 = "WAIT" if st == "REVIEW" else "APPROVE"
                            for step, who, res, cm, hh in ((1, "lee.dwg", s1, "검토 완료", "10:00"), (2, "admin", s2, "승인", "16:00")):
                                conn.execute("INSERT INTO TB_DWG_Approval (DrawingId,RevNo,StepNo,ApproverEmpNo,Result,Comment,ActDt) VALUES (?,?,?,?,?,?,?)",
                                             (did, k, step, who, res, cm if res == "APPROVE" else None,
                                              f"{idt or '2026-10-17'} {hh}" if res == "APPROVE" else None))
                    conn.execute("UPDATE TB_DWG_Drawing SET CurrentRevNo=? WHERE DrawingId=?", (cur_rev, did))
                    if plan:
                        conn.execute("INSERT INTO TB_DWG_PlanLink (DrawingId,PlanId,RequiredYN,NeedDt) VALUES (?,?,?,?)",
                                     (did, plan["PlanId"], int(dc != "ELEC"), plan["PlanStartDt"]))
        refresh_statuses(conn)
