from fastapi import APIRouter, Depends

from ..db import get_db
from ..deps import require_menu
from ..schemas import ProgressIn
from ..services import progress_service
from ..services.rbac_service import VIEW, WRITE

router = APIRouter(prefix="/api", tags=["progress"])
can_view = require_menu("M22", VIEW)
can_write = require_menu("M22", WRITE)


@router.get("/progress-hulls")
def progress_hulls(_=Depends(can_view), conn=Depends(get_db)):
    return progress_service.progress_hulls(conn)


@router.get("/hulls/{hull_no}/progress-targets")
def targets(hull_no: str, include_done: bool = False, _=Depends(can_view), conn=Depends(get_db)):
    return progress_service.targets(conn, hull_no, include_done)


@router.get("/plans/{plan_id}/progress")
def history(plan_id: int, _=Depends(can_view), conn=Depends(get_db)):
    return progress_service.history(conn, plan_id)


@router.put("/plans/{plan_id}/progress/{work_dt}")
def save(plan_id: int, work_dt: str, body: ProgressIn, _=Depends(can_write), conn=Depends(get_db)):
    return progress_service.save(conn, plan_id, work_dt, body.model_dump())


@router.delete("/progress/{progress_id}")
def delete(progress_id: int, _=Depends(can_write), conn=Depends(get_db)):
    return progress_service.delete(conn, progress_id)
