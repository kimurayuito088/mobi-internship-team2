"""
Pydantic スキーマ（リクエスト/レスポンス定義）
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# === 認証 ===


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class OperatorResponse(BaseModel):
    id: int
    username: str
    display_name: str


# === 問い合わせ ===


class InquiryResponse(BaseModel):
    id: int
    status: int
    assigned_operator_id: Optional[int]
    created_at: str
    closed_at: Optional[str]
    display_status: Optional[str] = None  # フロント表示用
    category_id: Optional[str] = None  # 事前ヒアリングの種類。未送信は null
    has_unread: bool = False


class PaginatedInquiryResponse(BaseModel):
    items: List[InquiryResponse]
    page: int
    per_page: int
    total: int
    total_pages: int


class InquiryGroupResponse(BaseModel):
    items: List[InquiryResponse]
    total: int
    has_more: bool


class GroupedInquiryResponse(BaseModel):
    unanswered: InquiryGroupResponse
    mine: InquiryGroupResponse
    closed: InquiryGroupResponse


class ReadInquiryRequest(BaseModel):
    up_to_message_id: int = Field(..., ge=1)


class UnreadInquiryItem(BaseModel):
    inquiry_id: int


class UnreadInquiryResponse(BaseModel):
    items: List[UnreadInquiryItem]


# === メッセージ ===


class MessageResponse(BaseModel):
    id: int
    inquiry_id: int
    sender_type: int
    sender_name: Optional[str]
    content: str
    created_at: str


# === オペレータ管理 ===


class OperatorCreateRequest(BaseModel):
    username: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)


class OperatorCreateResponse(BaseModel):
    operator: OperatorResponse
    generated_password: str
