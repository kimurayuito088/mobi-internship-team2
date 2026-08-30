"""
問い合わせサービス: 一覧取得・担当割り当て・ステータス算出
"""

import math

from fastapi import HTTPException

from app.models import Inquiry, InquiryStatus
from app.repositories.inquiry_repository import InquiryGroupResult, InquiryRepository
from app.schemas import (
    GroupedInquiryResponse,
    InquiryGroupResponse,
    InquiryResponse,
    PaginatedInquiryResponse,
    UnreadInquiryItem,
    UnreadInquiryResponse,
)


class InquiryService:
    """問い合わせ管理のビジネスロジック"""

    def __init__(self):
        self.repository = InquiryRepository()

    def list_inquiries(
        self, page: int, per_page: int, operator_id: int
    ) -> PaginatedInquiryResponse:
        """問い合わせ一覧を取得（表示ステータス付き）"""
        inquiries, total = self.repository.find_all(page, per_page)
        total_pages = math.ceil(total / per_page) if per_page > 0 else 0

        items = [self._to_inquiry_response(inq, operator_id) for inq in inquiries]

        return PaginatedInquiryResponse(
            items=items,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        )

    def list_grouped_inquiries(
        self,
        operator_id: int,
        unanswered_limit: int,
        mine_limit: int,
        closed_limit: int,
    ) -> GroupedInquiryResponse:
        """問い合わせを未返信・自分の担当・クローズした案件の3グループで取得する"""
        grouped = self.repository.find_grouped(
            operator_id, unanswered_limit, mine_limit, closed_limit
        )
        return GroupedInquiryResponse(
            unanswered=self._to_group_response(grouped.unanswered, operator_id),
            mine=self._to_group_response(grouped.mine, operator_id),
            closed=self._to_group_response(grouped.closed, operator_id),
        )

    def _to_inquiry_response(self, inquiry: Inquiry, operator_id: int) -> InquiryResponse:
        """Inquiryを表示ステータス付きレスポンスへ変換する"""
        return InquiryResponse(
            id=inquiry.id,
            status=inquiry.status,
            assigned_operator_id=inquiry.assigned_operator_id,
            created_at=inquiry.created_at,
            closed_at=inquiry.closed_at,
            display_status=self._compute_display_status(inquiry, operator_id),
            category_id=inquiry.category_id,
            has_unread=(inquiry.assigned_operator_id == operator_id and inquiry.has_unread),
        )

    def _to_group_response(
        self, group: InquiryGroupResult, operator_id: int
    ) -> InquiryGroupResponse:
        """グループの件数メタ情報を付与する"""
        items = [self._to_inquiry_response(inquiry, operator_id) for inquiry in group.items]
        return InquiryGroupResponse(
            items=items,
            total=group.total,
            has_more=group.total > len(items),
        )

    def get_inquiry(self, inquiry_id: int) -> Inquiry:
        """問い合わせ詳細を取得"""
        inquiry = self.repository.find_by_id(inquiry_id)
        if inquiry is None:
            raise HTTPException(status_code=404, detail="問い合わせが見つかりません")
        return inquiry

    def get_inquiry_response(self, inquiry_id: int, operator_id: int) -> InquiryResponse:
        """問い合わせ詳細をログイン中オペレータ向けの未読状態付きで取得する。"""
        inquiry = self.repository.find_by_id_with_unread(inquiry_id, operator_id)
        if inquiry is None:
            raise HTTPException(status_code=404, detail="問い合わせが見つかりません")
        return self._to_inquiry_response(inquiry, operator_id)

    def assign_operator(self, inquiry_id: int, operator_id: int) -> Inquiry:
        """問い合わせに担当者を割り当て（排他制御）"""
        success = self.repository.update_assignment(inquiry_id, operator_id)
        if not success:
            raise HTTPException(
                status_code=409,
                detail="この問い合わせは既に他のオペレータが担当しています",
            )
        inquiry = self.repository.find_by_id(inquiry_id)
        if inquiry is None:
            raise HTTPException(status_code=404, detail="問い合わせが見つかりません")
        return inquiry

    def create_inquiry(self) -> Inquiry:
        """新規問い合わせを作成"""
        return self.repository.create()

    def mark_as_read(self, inquiry_id: int, operator_id: int, up_to_message_id: int) -> None:
        """担当者とメッセージの所属を確認し、既読位置を後戻りさせず更新する。"""
        inquiry = self.get_inquiry(inquiry_id)
        if inquiry.assigned_operator_id != operator_id:
            raise HTTPException(status_code=403, detail="この問い合わせの担当者ではありません")

        message = self.repository.find_message_by_id(up_to_message_id)
        if message is None or message.inquiry_id != inquiry_id:
            raise HTTPException(
                status_code=400,
                detail="指定したメッセージはこの問い合わせに所属していません",
            )

        self.repository.update_last_read_message_id(inquiry_id, up_to_message_id)

    def list_unread_inquiries(self, operator_id: int) -> UnreadInquiryResponse:
        """ログイン中オペレータが担当する未読問い合わせIDを返す。"""
        inquiry_ids = self.repository.find_unread_inquiry_ids(operator_id)
        return UnreadInquiryResponse(
            items=[UnreadInquiryItem(inquiry_id=inquiry_id) for inquiry_id in inquiry_ids]
        )

    @staticmethod
    def _compute_display_status(inquiry: Inquiry, operator_id: int) -> str:
        """オペレータの視点で表示ステータスを算出"""
        if inquiry.status == InquiryStatus.CLOSED:
            return "closed"
        # INPUTTINGは担当者の有無に関係なく「入力中」として扱うため、担当判定より前に評価する
        elif inquiry.status == InquiryStatus.INPUTTING:
            return "inputting"
        elif inquiry.status == InquiryStatus.WAITING:
            return "waiting"
        elif inquiry.assigned_operator_id == operator_id:
            return "mine"
        else:
            return "others"
