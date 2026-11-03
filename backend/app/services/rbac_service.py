"""BR-09: highest AuthGbn across the user's groups (View=1, Write=2, Admin=3)."""
import sqlite3

LEVELS = {"View": 1, "Write": 2, "Admin": 3}
VIEW, WRITE, ADMIN = 1, 2, 3


def groups_of(conn: sqlite3.Connection, emp_no: str) -> list[dict]:
    rows = conn.execute(
        "SELECT g.AuthCd, g.AuthNm FROM TB_SYS_AuthUser u JOIN TB_SYS_AuthGroup g ON g.AuthCd=u.AuthCd "
        "WHERE u.EmpNo=? ORDER BY g.AuthCd", (emp_no,)).fetchall()
    return [{"code": r["AuthCd"], "name": r["AuthNm"]} for r in rows]


def menu_levels(conn: sqlite3.Connection, emp_no: str) -> dict[str, int]:
    rows = conn.execute(
        "SELECT am.MenuId, am.AuthGbn FROM TB_SYS_AuthMenu am JOIN TB_SYS_AuthUser au ON au.AuthCd=am.AuthCd "
        "JOIN TB_SYS_MenuInfo mi ON mi.MenuId=am.MenuId WHERE au.EmpNo=? AND mi.UseYN=1", (emp_no,)).fetchall()
    out: dict[str, int] = {}
    for r in rows:
        out[r["MenuId"]] = max(out.get(r["MenuId"], 0), LEVELS.get(r["AuthGbn"], 0))
    return out


def level(conn: sqlite3.Connection, emp_no: str, menu_id: str) -> int:
    return menu_levels(conn, emp_no).get(menu_id, 0)


def visible_menu(conn: sqlite3.Connection, emp_no: str) -> list[dict]:
    lv = menu_levels(conn, emp_no)
    rows = conn.execute("SELECT * FROM TB_SYS_MenuInfo WHERE UseYN=1 ORDER BY Seq").fetchall()
    gbn = {1: "View", 2: "Write", 3: "Admin"}
    return [
        {"menu_id": r["MenuId"], "parent_id": r["ParentId"], "title": r["Title"], "token": r["TokenUrl"],
         "seq": r["Seq"], "level": lv[r["MenuId"]], "auth_gbn": gbn[lv[r["MenuId"]]],
         "can_write": lv[r["MenuId"]] >= WRITE}
        for r in rows
        if lv.get(r["MenuId"], 0) > 0 and (r["ParentId"] is None or lv.get(r["ParentId"], 0) > 0)
    ]
