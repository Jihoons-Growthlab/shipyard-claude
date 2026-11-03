from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse

from ..config import settings
from ..db import get_db
from ..deps import CurrentUser, require_menu
from ..errors import ApiError
from ..schemas import ApprovalRequestIn, DrawingIn, DrawingLinkIn, RevisionIn
from ..services import drawing_service as svc
from ..services.rbac_service import VIEW, WRITE

router = APIRouter(prefix="/api/drawings", tags=["drawings"])
can_view = require_menu("M31", VIEW)
can_write = require_menu("M31", WRITE)  # D11 CONFIRMED: edits/revisions/approval requests/issue = M31 Write


async def pdf_body(request: Request) -> bytes:
    """Raw PDF body (no multipart dependency), capped while streaming."""
    buf = bytearray()
    async for chunk in request.stream():
        buf += chunk
        if len(buf) > settings.max_pdf_bytes:
            raise ApiError(413, "FILE_TOO_LARGE", "파일 크기는 30MB 이하여야 합니다.", {"field": "pdf"})
    return bytes(buf)


@router.get("")
def list_drawings(hull_no: str | None = None, discipline: str | None = None, status: str | None = None, q: str | None = None,
                  _=Depends(can_view), conn=Depends(get_db)):
    return svc.list_drawings(conn, hull_no, discipline, status, q)


@router.post("", status_code=201)
def create(body: DrawingIn, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return svc.create_drawing(conn, body.model_dump(), user.emp_no)


@router.get("/{drawing_id}")
def detail(drawing_id: int, _=Depends(can_view), conn=Depends(get_db)):
    return svc.get_drawing(conn, drawing_id)


@router.patch("/{drawing_id}")
def update(drawing_id: int, body: DrawingIn, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return svc.update_drawing(conn, drawing_id, body.model_dump(exclude_unset=True), user.emp_no)


@router.delete("/{drawing_id}", status_code=204)
def delete(drawing_id: int, _=Depends(can_write), conn=Depends(get_db)):
    svc.delete_drawing(conn, drawing_id)
    return Response(status_code=204)


@router.get("/{drawing_id}/revisions")
def revisions(drawing_id: int, _=Depends(can_view), conn=Depends(get_db)):
    return svc.get_drawing(conn, drawing_id)["revisions"]


@router.post("/{drawing_id}/revisions", status_code=201)
def new_revision(drawing_id: int, body: RevisionIn, user: CurrentUser = Depends(can_write), conn=Depends(get_db)):
    return svc.new_revision(conn, drawing_id, body.change_desc, user.emp_no)


@router.post("/{drawing_id}/revisions/{rev_no}/pdf")
def upload_pdf(drawing_id: int, rev_no: int, request: Request, filename: str, _=Depends(can_write),
               data: bytes = Depends(pdf_body), conn=Depends(get_db)):  # RBAC resolved before the body is read
    return svc.upload_pdf(conn, drawing_id, rev_no, filename, request.headers.get("content-type"), data)


@router.get("/{drawing_id}/revisions/{rev_no}/pdf")
def get_pdf(drawing_id: int, rev_no: int, _=Depends(can_view), conn=Depends(get_db)):
    path, name = svc.pdf_file(conn, drawing_id, rev_no)
    return FileResponse(path, media_type="application/pdf",
                        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(name)}", "X-Content-Type-Options": "nosniff"})


@router.delete("/{drawing_id}/revisions/{rev_no}/pdf")
def delete_pdf(drawing_id: int, rev_no: int, _=Depends(can_write), conn=Depends(get_db)):
    return svc.delete_pdf(conn, drawing_id, rev_no)


@router.post("/{drawing_id}/revisions/{rev_no}/request-approval")
def request_approval(drawing_id: int, rev_no: int, body: ApprovalRequestIn, _=Depends(can_write), conn=Depends(get_db)):
    return svc.request_approval(conn, drawing_id, rev_no, body.reviewer_emp_no, body.approver_emp_no)


@router.post("/{drawing_id}/revisions/{rev_no}/issue")
def issue(drawing_id: int, rev_no: int, _=Depends(can_write), conn=Depends(get_db)):
    return svc.issue(conn, drawing_id, rev_no)


@router.get("/{drawing_id}/plans")
def plans(drawing_id: int, _=Depends(can_view), conn=Depends(get_db)):
    return svc.drawing_plans(conn, drawing_id)


@router.post("/{drawing_id}/plans", status_code=201)
def link_plan(drawing_id: int, body: DrawingLinkIn, _=Depends(can_write), conn=Depends(get_db)):
    return svc.link_plan(conn, drawing_id, body.plan_id, body.required)


@router.delete("/{drawing_id}/plans/{plan_id}")
def unlink_plan(drawing_id: int, plan_id: int, _=Depends(can_write), conn=Depends(get_db)):
    return svc.unlink_plan(conn, drawing_id, plan_id)
