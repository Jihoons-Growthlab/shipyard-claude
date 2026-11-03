from fastapi import APIRouter, Depends

from ..db import get_db
from ..deps import CurrentUser, require_menu
from ..schemas import ApprovalDecisionIn
from ..services import approval_service as svc
from ..services.rbac_service import VIEW, WRITE, level

router = APIRouter(prefix="/api/approvals", tags=["approvals"])
can_view = require_menu("M33", VIEW)
can_write = require_menu("M33", WRITE)  # D11: plus assigned-current-approver check in the service


@router.get("/inbox")
def inbox(user: CurrentUser = Depends(can_view), conn=Depends(get_db)):
    # can_issue is a UI hint only; the F07 issue endpoint enforces M31 Write + completed approval.
    return {**svc.inbox(conn, user.emp_no), "can_issue": level(conn, user.emp_no, "M31") >= WRITE}


@router.post("/{approval_id}/decision")
def decision(approval_id: int, body: ApprovalDecisionIn, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return svc.decide(conn, approval_id, body.result, body.comment, user.emp_no)


@router.get("/history")
def history(_=Depends(can_view), conn=Depends(get_db)):
    return svc.history(conn)
