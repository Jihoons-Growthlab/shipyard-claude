from fastapi import APIRouter, Depends, Response

from ..db import get_db
from ..deps import CurrentUser, current_user, require_menu
from ..schemas import BlockIn, HullCreate, HullUpdate, MilestonesIn
from ..services import code_service, hull_service
from ..services.rbac_service import VIEW, WRITE

router = APIRouter(prefix="/api", tags=["hulls"])
can_view = require_menu("M11", VIEW)    # hull detail popup inherits M11 (01-system 권한 게이트)
can_write = require_menu("M11", WRITE)


@router.get("/codes")
def codes(_: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    return code_service.all_codes(conn)


@router.get("/hulls")
def list_hulls(status: str | None = None, ship_type: str | None = None, q: str | None = None,
               _=Depends(can_view), conn=Depends(get_db)):
    return hull_service.list_hulls(conn, status or None, ship_type or None, (q or "").strip() or None)


@router.post("/hulls", status_code=201)
def create_hull(body: HullCreate, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return hull_service.create_hull(conn, body.model_dump(), user.emp_no)


@router.get("/hulls/{hull_no}")
def get_hull(hull_no: str, _=Depends(can_view), conn=Depends(get_db)):
    return hull_service.get_hull(conn, hull_no)


@router.patch("/hulls/{hull_no}")
def update_hull(hull_no: str, body: HullUpdate, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return hull_service.update_hull(conn, hull_no, body.model_dump(exclude_unset=True), user.emp_no)


@router.delete("/hulls/{hull_no}", status_code=204)
def delete_hull(hull_no: str, _=Depends(can_write), conn=Depends(get_db)):
    hull_service.delete_hull(conn, hull_no)
    return Response(status_code=204)


@router.get("/hulls/{hull_no}/milestones")
def get_milestones(hull_no: str, _=Depends(can_view), conn=Depends(get_db)):
    return hull_service.get_milestones(conn, hull_no)


@router.put("/hulls/{hull_no}/milestones")
def put_milestones(hull_no: str, body: MilestonesIn, _=Depends(can_write), conn=Depends(get_db)):
    return hull_service.put_milestones(conn, hull_no, [m.model_dump() for m in body.items])


@router.get("/hulls/{hull_no}/blocks")
def list_blocks(hull_no: str, _=Depends(can_view), conn=Depends(get_db)):
    return hull_service.list_blocks(conn, hull_no)


@router.post("/hulls/{hull_no}/blocks", status_code=201)
def add_block(hull_no: str, body: BlockIn, _=Depends(can_write), conn=Depends(get_db)):
    return hull_service.add_block(conn, hull_no, body.model_dump())


@router.delete("/blocks/{block_id}", status_code=204)
def delete_block(block_id: int, _=Depends(can_write), conn=Depends(get_db)):
    hull_service.delete_block(conn, block_id)
    return Response(status_code=204)


@router.get("/hulls/{hull_no}/summary")
def hull_summary(hull_no: str, _=Depends(can_view), conn=Depends(get_db)):
    return hull_service.summary(conn, hull_no)
