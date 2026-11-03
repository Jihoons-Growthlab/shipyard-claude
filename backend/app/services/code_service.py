def codes(conn, group: str) -> set[str]:
    return {r[0] for r in conn.execute("SELECT Code FROM TB_SYS_Code WHERE CodeGroup=? AND UseYN=1", (group,))}


def all_codes(conn) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    rows = conn.execute("SELECT c.CodeGroup, c.Code, c.CodeName FROM TB_SYS_Code c JOIN TB_SYS_CodeGroup g "
                        "ON g.CodeGroup=c.CodeGroup WHERE c.UseYN=1 AND g.UseYN=1 ORDER BY g.Seq, c.Seq").fetchall()
    for r in rows:
        out.setdefault(r["CodeGroup"], []).append({"code": r["Code"], "name": r["CodeName"]})
    return out
