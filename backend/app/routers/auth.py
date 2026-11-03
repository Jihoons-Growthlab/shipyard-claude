from fastapi import APIRouter, Depends, Request

from ..db import get_db
from ..deps import CurrentUser, client_ip, current_user, otp_claims
from ..schemas import LoginIn, OtpIn, RegisterIn
from ..services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginIn, request: Request, conn=Depends(get_db)):
    return auth_service.login(conn, body.emp_no, body.password, client_ip(request))


@router.post("/otp/verify")
def otp_verify(body: OtpIn, request: Request, claims: dict = Depends(otp_claims), conn=Depends(get_db)):
    return auth_service.verify_otp(conn, claims, body.code, client_ip(request))


@router.post("/register", status_code=201)
def register(body: RegisterIn, conn=Depends(get_db)):
    return auth_service.register(conn, body.model_dump())


@router.post("/logout", status_code=204)
def logout(user: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    auth_service.logout(conn, user.log_id)


@router.get("/me")
def me(user: CurrentUser = Depends(current_user), conn=Depends(get_db)):
    return auth_service.public_user(conn, user.row)
