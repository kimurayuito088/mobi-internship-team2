"""
認証ルーター: ログイン・ログアウト・自分の情報取得
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.middleware.auth_middleware import get_current_operator
from app.models import Operator
from app.schemas import LoginRequest, OperatorResponse
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/login", response_model=OperatorResponse)
def login(body: LoginRequest, response: Response):
    """オペレータログイン"""
    try:
        operator, session_id = auth_service.login(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # セッションIDをCookieに設定
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
    )

    return OperatorResponse(
        id=operator.id,
        username=operator.username,
        display_name=operator.display_name,
    )


@router.post("/logout")
def logout(request: Request, response: Response):
    """オペレータログアウト"""
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service.logout(session_id)

    response.delete_cookie("session_id")
    return {"message": "ログアウトしました"}


@router.get("/me", response_model=OperatorResponse)
def get_me(operator: Operator = Depends(get_current_operator)):
    """ログイン中のオペレータ情報取得"""
    return OperatorResponse(
        id=operator.id,
        username=operator.username,
        display_name=operator.display_name,
    )
