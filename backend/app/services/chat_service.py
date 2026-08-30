"""
チャットサービス: メッセージ送受信・問い合わせ終了処理
"""

import logging

from app.models import Inquiry, InquiryStatus, SenderType, normalize_hearing_category_id
from app.repositories.chat_repository import ChatRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

# 問い合わせ受付直後にエンドユーザへ案内するメッセージ
WAITING_FOR_OPERATOR_MESSAGE = (
    "お問い合わせを受け付けました。オペレーターにおつなぎしますので、しばらくお待ちください。"
)

# 退出時にチャットへ残すメッセージ
USER_LEFT_MESSAGE = "ユーザーが退出しました"


class ChatService:
    """チャット関連のビジネスロジック"""

    def __init__(self):
        self.chat_repository = ChatRepository()
        self.inquiry_repository = InquiryRepository()

    def create_inquiry_on_connect(self) -> Inquiry:
        """WebSocket接続時に入力中ステータスで問い合わせを作成"""
        return self.inquiry_repository.create(initial_status=InquiryStatus.INPUTTING)

    async def send_message(
        self,
        inquiry_id: int,
        sender_type: int,
        content: str,
        sender_name: str | None = None,
        operator_id: int | None = None,
        category_id: str | None = None,
    ) -> dict | None:
        """
        メッセージを送信・保存・ブロードキャスト
        権限チェック含む。拒否時はNoneを返す。
        """
        # 問い合わせ取得
        inquiry = self.inquiry_repository.find_by_id(inquiry_id)
        if inquiry is None:
            return None

        # 終了済みチェック
        if inquiry.status == InquiryStatus.CLOSED:
            return None

        # オペレータの権限チェック
        if sender_type == SenderType.OPERATOR:
            if inquiry.assigned_operator_id != operator_id:
                return None

        # エンドユーザのメッセージ送信で入力中 → 担当者未決定へ遷移
        became_waiting = False
        if sender_type == SenderType.ENDUSER and inquiry.status == InquiryStatus.INPUTTING:
            self.inquiry_repository.update_status_to_waiting(
                inquiry_id, normalize_hearing_category_id(category_id)
            )
            became_waiting = True

        # メッセージ保存
        message = self.chat_repository.save_message(
            inquiry_id=inquiry_id,
            sender_type=sender_type,
            sender_name=sender_name,
            content=content,
        )

        # ブロードキャスト用データ
        message_data = {
            "type": "message",
            "id": message.id,
            "inquiry_id": message.inquiry_id,
            "sender_type": message.sender_type,
            "sender_name": message.sender_name,
            "content": message.content,
            "created_at": message.created_at,
        }

        await manager.broadcast(inquiry_id, message_data)

        # 担当待ちになった直後だけ案内する（2通目以降では送らない）
        # 案内は付加的なので、失敗しても要約送信の成功は呼び出し元へ返す
        if became_waiting:
            try:
                await self.send_system_message(inquiry_id, WAITING_FOR_OPERATOR_MESSAGE)
            except Exception:
                logger.exception(
                    "担当待ち案内の送信に失敗しました (inquiry_id=%s)",
                    inquiry_id,
                )

        return message_data

    async def send_system_message(self, inquiry_id: int, content: str) -> dict:
        """システムメッセージを保存してブロードキャストする"""
        message = self.chat_repository.save_message(
            inquiry_id=inquiry_id,
            sender_type=SenderType.SYSTEM,
            sender_name=None,
            content=content,
        )

        system_message = {
            "type": "message",
            "id": message.id,
            "inquiry_id": message.inquiry_id,
            "sender_type": message.sender_type,
            "sender_name": message.sender_name,
            "content": message.content,
            "created_at": message.created_at,
        }
        await manager.broadcast(inquiry_id, system_message)
        return system_message

    async def close_inquiry(self, inquiry_id: int) -> None:
        """問い合わせを終了する（共通処理）"""
        # ステータス更新
        self.inquiry_repository.update_status_closed(inquiry_id)

        # 退出を知らせるシステムメッセージ
        await self.send_system_message(inquiry_id, USER_LEFT_MESSAGE)

        # 終了通知
        await manager.broadcast(inquiry_id, {"type": "closed"})
