from fastapi import APIRouter, Depends, Response

from ..db import get_db
from ..deps import CurrentUser, current_user, require_menu
from ..schemas import LinkIn, PlanIn, PredsIn
from ..services import plan_service
from ..services.rbac_service import VIEW, WRITE

router = APIRouter(prefix="/api", tags=["planning"])
can_view = require_menu("M21", VIEW)
can_write = require_menu("M21", WRITE)


@router.get("/procs")
def procs(_: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    return [{"proc_cd": r["ProcCd"], "proc_nm": r["ProcNm"], "proc_group": r["ProcGroup"], "std_days": r["StdDays"], "seq": r["Seq"]}
            for r in conn.execute("SELECT * FROM TB_PRC_Proc WHERE UseYN=1 ORDER BY Seq")]


@router.get("/plan-hulls")
def plan_hulls(_=Depends(can_view), conn=Depends(get_db)):
    return plan_service.plan_hulls(conn)


@router.get("/hulls/{hull_no}/plans")
def list_plans(hull_no: str, block_id: int | None = None, _=Depends(can_view), conn=Depends(get_db)):
    return plan_service.list_plans(conn, hull_no, block_id)


@router.post("/hulls/{hull_no}/plans", status_code=201)
def create_plan(hull_no: str, body: PlanIn, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return plan_service.create_plan(conn, hull_no, body.model_dump(), user.emp_no)


@router.get("/plans/{plan_id}")
def get_plan(plan_id: int, _=Depends(can_view), conn=Depends(get_db)):
    return plan_service.get_plan(conn, plan_id)


@router.patch("/plans/{plan_id}")
def update_plan(plan_id: int, body: PlanIn, _=Depends(can_write), conn=Depends(get_db)):
    return plan_service.update_plan(conn, plan_id, body.model_dump(exclude_unset=True))


@router.delete("/plans/{plan_id}", status_code=204)
def delete_plan(plan_id: int, _=Depends(can_write), conn=Depends(get_db)):
    plan_service.delete_plan(conn, plan_id)
    return Response(status_code=204)


@router.put("/plans/{plan_id}/predecessors")
def set_preds(plan_id: int, body: PredsIn, _=Depends(can_write), conn=Depends(get_db)):
    return plan_service.set_predecessors(conn, plan_id, body.pred_plan_ids, body.confirm_late_preds)


@router.get("/plans/{plan_id}/drawings")
def plan_drawings(plan_id: int, _=Depends(can_view), conn=Depends(get_db)):
    return plan_service.plan_drawings(conn, plan_id)


@router.post("/plans/{plan_id}/drawings", status_code=201)
def link_drawing(plan_id: int, body: LinkIn, _=Depends(can_write), conn=Depends(get_db)):
    return plan_service.link_drawing(conn, plan_id, body.drawing_id, body.required)


@router.delete("/plans/{plan_id}/drawings/{drawing_id}", status_code=204)
def unlink_drawing(plan_id: int, drawing_id: int, _=Depends(can_write), conn=Depends(get_db)):
    plan_service.unlink_drawing(conn, plan_id, drawing_id)
    return Response(status_code=204)
