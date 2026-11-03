from fastapi import APIRouter, Depends, Response

from ..db import get_db
from ..deps import CurrentUser, current_user, require_menu
from ..schemas import ApproveIn, UserIn
from ..services import user_service
from ..services.rbac_service import ADMIN

router = APIRouter(prefix="/api/users", tags=["users"])
groups_router = APIRouter(prefix="/api/auth-groups", tags=["users"])
_admin = require_menu("M91", ADMIN)  # F09: 회원관리는 M91 Admin 전용


@router.post("/{emp_no}/approve")
def approve(emp_no: str, body: ApproveIn, _=Depends(_admin), conn=Depends(get_db)):
    return user_service.approve(conn, emp_no, body.groups)


@router.post("/{emp_no}/reject")
def reject(emp_no: str, _=Depends(_admin), conn=Depends(get_db)):
    return user_service.reject(conn, emp_no)


@router.get("/options")
def user_options(_: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    """Approved members for assignee selects (PLAN-02 담당자)."""
    return [{"emp_no": r["emp_no"], "display_name": r["display_name"]}
            for r in conn.execute("SELECT emp_no, display_name FROM users WHERE status='approved' ORDER BY display_name")]


@router.get("")
def list_users(status: str | None = None, q: str | None = None, _=Depends(_admin), conn=Depends(get_db)):
    return user_service.list_users(conn, status, q)


@router.post("", status_code=201)
def create_user(body: UserIn, _=Depends(_admin), conn=Depends(get_db)):
    return user_service.create_user(conn, body.model_dump())


@router.get("/{emp_no}")
def get_user(emp_no: str, _=Depends(_admin), conn=Depends(get_db)):
    return user_service.get_user(conn, emp_no)


@router.patch("/{emp_no}")
def update_user(emp_no: str, body: UserIn, _=Depends(_admin), conn=Depends(get_db)):
    return user_service.update_user(conn, emp_no, body.model_dump())


@router.delete("/{emp_no}", status_code=204)
def delete_user(emp_no: str, user: CurrentUser = Depends(_admin), conn=Depends(get_db)):
    user_service.delete_user(conn, emp_no, user.emp_no)
    return Response(status_code=204)


@groups_router.get("")
def auth_groups(_=Depends(_admin), conn=Depends(get_db)):
    return user_service.auth_groups(conn)
