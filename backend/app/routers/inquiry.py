"""
問い合わせルーター: 一覧取得・詳細取得・担当取得・メッセージ取得
"""

from typing import List

from fastapi import APIRouter, Depends, Query, Response, status

from app.config import (
    DEFAULT_CLOSED_LIMIT,
    DEFAULT_MINE_LIMIT,
    DEFAULT_PER_PAGE,
    DEFAULT_UNANSWERED_LIMIT,
    MAX_GROUP_LIMIT,
    MAX_PER_PAGE,
)
from app.middleware.auth_middleware import get_current_operator
from app.models import Operator
from app.repositories.inquiry_repository import InquiryRepository
from app.schemas import (
    GroupedInquiryResponse,
    InquiryResponse,
    MessageResponse,
    PaginatedInquiryResponse,
    ReadInquiryRequest,
    UnreadInquiryResponse,
)
from app.services.inquiry_service import InquiryService

router = APIRouter()
inquiry_service = InquiryService()
inquiry_repository = InquiryRepository()


@router.get("", response_model=PaginatedInquiryResponse)
def list_inquiries(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE),
    operator: Operator = Depends(get_current_operator),
):
    """問い合わせ一覧取得（ページング付き）"""
    return inquiry_service.list_inquiries(page, per_page, operator.id)


@router.get("/grouped", response_model=GroupedInquiryResponse)
def list_grouped_inquiries(
    unanswered_limit: int = Query(default=DEFAULT_UNANSWERED_LIMIT, ge=1, le=MAX_GROUP_LIMIT),
    mine_limit: int = Query(default=DEFAULT_MINE_LIMIT, ge=1, le=MAX_GROUP_LIMIT),
    closed_limit: int = Query(default=DEFAULT_CLOSED_LIMIT, ge=1, le=MAX_GROUP_LIMIT),
    operator: Operator = Depends(get_current_operator),
):
    """問い合わせを未返信・自分の担当・クローズした案件の3グループで取得する"""
    return inquiry_service.list_grouped_inquiries(
        operator.id, unanswered_limit, mine_limit, closed_limit
    )


@router.get("/mine/unread", response_model=UnreadInquiryResponse)
def list_unread_inquiries(
    operator: Operator = Depends(get_current_operator),
):
    """ログイン中オペレータが担当する未読問い合わせIDを取得する。"""
    return inquiry_service.list_unread_inquiries(operator.id)


@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(
    inquiry_id: int,
    operator: Operator = Depends(get_current_operator),
):
    """問い合わせ詳細取得"""
    return inquiry_service.get_inquiry_response(inquiry_id, operator.id)


@router.post("/{inquiry_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_inquiry_as_read(
    inquiry_id: int,
    request: ReadInquiryRequest,
    operator: Operator = Depends(get_current_operator),
) -> Response:
    """指定メッセージまでを既読にする。"""
    inquiry_service.mark_as_read(inquiry_id, operator.id, request.up_to_message_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{inquiry_id}/assign", response_model=InquiryResponse)
def assign_inquiry(
    inquiry_id: int,
    operator: Operator = Depends(get_current_operator),
):
    """問い合わせ担当取得"""
    inquiry = inquiry_service.assign_operator(inquiry_id, operator.id)
    return inquiry_service._to_inquiry_response(inquiry, operator.id)


@router.get("/{inquiry_id}/messages", response_model=List[MessageResponse])
def get_inquiry_messages(
    inquiry_id: int,
    _operator: Operator = Depends(get_current_operator),
):
    """問い合わせのメッセージ一覧取得"""
    # 問い合わせ存在確認
    inquiry_service.get_inquiry(inquiry_id)

    messages = inquiry_repository.find_messages_by_inquiry_id(inquiry_id)
    return [
        MessageResponse(
            id=msg.id,
            inquiry_id=msg.inquiry_id,
            sender_type=msg.sender_type,
            sender_name=msg.sender_name,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]
