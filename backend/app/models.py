"""
データモデル定義（データクラス）
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Operator:
    """オペレータ"""

    id: int
    username: str
    password_hash: str
    display_name: str
    created_at: str


@dataclass
class Session:
    """ログインセッション"""

    id: str
    operator_id: int
    created_at: str
    expires_at: str


@dataclass
class Inquiry:
    """問い合わせ"""

    id: int
    status: int  # 0:waiting, 1:active, 2:closed, 3:inputting
    assigned_operator_id: Optional[int]
    created_at: str
    closed_at: Optional[str]
    # 事前ヒアリングの種類。送信完了まで未設定
    category_id: Optional[str] = None
    last_read_message_id: int = 0
    has_unread: bool = False


@dataclass
class Message:
    """チャットメッセージ"""

    id: int
    inquiry_id: int
    sender_type: int  # 0:enduser, 1:operator, 2:system
    sender_name: Optional[str]
    content: str
    created_at: str


# ステータス定数
class InquiryStatus:
    WAITING = 0
    ACTIVE = 1
    CLOSED = 2
    # 既存データとの互換性を保つため、未使用の値3を「入力中」に割り当てる
    INPUTTING = 3


# 送信者タイプ定数
class SenderType:
    ENDUSER = 0
    OPERATOR = 1
    SYSTEM = 2


# フロントの hearingFlow の CATEGORY_CHOICE_IDS と同じ ID。一覧の短いラベル解決に使う
class HearingCategoryId:
    UNKNOWN_WASTE_TYPE = "unknown_waste_type"
    TICKET_PRICE_APPLY = "ticket_price_apply"
    CHANGE_COLLECTION_DATE = "change_collection_date"
    BRING_TO_FACILITY = "bring_to_facility"
    FEE_REDUCTION = "fee_reduction"
    BUSINESS_WASTE = "business_waste"
    OTHER = "other"


ALLOWED_HEARING_CATEGORY_IDS = frozenset(
    {
        HearingCategoryId.UNKNOWN_WASTE_TYPE,
        HearingCategoryId.TICKET_PRICE_APPLY,
        HearingCategoryId.CHANGE_COLLECTION_DATE,
        HearingCategoryId.BRING_TO_FACILITY,
        HearingCategoryId.FEE_REDUCTION,
        HearingCategoryId.BUSINESS_WASTE,
        HearingCategoryId.OTHER,
    }
)


def normalize_hearing_category_id(raw: object) -> str | None:
    """許可された種類 ID だけを残し、それ以外は未設定として扱う"""
    if not isinstance(raw, str):
        return None
    category_id = raw.strip()
    if category_id not in ALLOWED_HEARING_CATEGORY_IDS:
        return None
    return category_id
