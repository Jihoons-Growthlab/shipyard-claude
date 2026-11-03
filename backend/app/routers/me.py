from fastapi import APIRouter, Depends

from ..db import get_db, transaction
from ..deps import CurrentUser, current_user
from ..errors import ApiError
from ..schemas import MenuAccessIn
from ..security import utcnow_iso
from ..services import rbac_service

router = APIRouter(prefix="/api/me", tags=["shell"])


@router.get("/menu")
def menu(user: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    return rbac_service.visible_menu(conn, user.emp_no)


@router.post("/menu-access", status_code=204)
def menu_access(body: MenuAccessIn, user: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    """SHELL-08: log screen entry; also the direct-access gate (403 without View)."""
    if rbac_service.level(conn, user.emp_no, body.menu_id) < rbac_service.VIEW:
        raise ApiError(403, "FORBIDDEN", "권한이 없습니다.", {"menu_id": body.menu_id})
    with transaction(conn):
        conn.execute("INSERT INTO TB_SYS_LogMenuAccess (MenuId, LogId, InDt) VALUES (?,?,?)",
                     (body.menu_id, user.log_id, utcnow_iso()))
