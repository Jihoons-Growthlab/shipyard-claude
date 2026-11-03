from fastapi import APIRouter, Depends

from ..db import get_db
from ..deps import require_menu
from ..services import dashboard_service
from ..services.rbac_service import VIEW

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(_=Depends(require_menu("M00", VIEW)), conn=Depends(get_db)):
    return dashboard_service.summary(conn)
