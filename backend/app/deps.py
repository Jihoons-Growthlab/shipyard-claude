import sqlite3
from dataclasses import dataclass

import jwt
from fastapi import Depends, Request

from .db import get_db
from .errors import ApiError
from .security import STAGE_OTP, decode_token
from .services import auth_service, rbac_service


@dataclass
class CurrentUser:
    emp_no: str
    log_id: int
    row: sqlite3.Row


def _bearer(request: Request) -> str:
    h = request.headers.get("Authorization", "")
    if not h.lower().startswith("bearer "):
        raise ApiError(401, "UNAUTHORIZED", "로그인이 필요합니다.")
    return h[7:].strip()


def _claims(request: Request) -> dict:
    try:
        return decode_token(_bearer(request))
    except jwt.PyJWTError:
        raise ApiError(401, "UNAUTHORIZED", "세션이 만료되었거나 유효하지 않습니다.")


def current_user(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> CurrentUser:
    claims = _claims(request)
    u = auth_service.resolve_session(conn, claims)
    if u is None:
        raise ApiError(401, "UNAUTHORIZED", "세션이 만료되었거나 유효하지 않습니다.")
    return CurrentUser(emp_no=u["emp_no"], log_id=claims["lid"], row=u)


def otp_claims(request: Request) -> dict:
    claims = _claims(request)
    if claims.get("stage") != STAGE_OTP:
        raise ApiError(401, "UNAUTHORIZED", "OTP 인증 단계가 아닙니다.")
    return claims


def require_menu(menu_id: str, min_level: int):
    """Server-side RBAC gate: 403 unless the user's best AuthGbn on menu_id >= min_level."""
    def dep(user: CurrentUser = Depends(current_user), conn: sqlite3.Connection = Depends(get_db)) -> CurrentUser:
        if rbac_service.level(conn, user.emp_no, menu_id) < min_level:
            raise ApiError(403, "FORBIDDEN", "권한이 없습니다.", {"menu_id": menu_id})
        return user
    return dep


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
