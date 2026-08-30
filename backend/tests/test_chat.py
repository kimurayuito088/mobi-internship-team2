"""
チャットサービスのテスト（リポジトリをモック化）
学生向けサンプル: asyncテストとモックの組み合わせ
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models import Inquiry, InquiryStatus, Message, SenderType
from app.services.chat_service import ChatService

# テスト用の固定データ
MOCK_INQUIRY_WAITING = Inquiry(
    id=1,
    status=InquiryStatus.WAITING,
    assigned_operator_id=None,
    created_at="2026-01-01 09:00:00",
    closed_at=None,
)
MOCK_INQUIRY_ACTIVE = Inquiry(
    id=2,
    status=InquiryStatus.ACTIVE,
    assigned_operator_id=1,
    created_at="2026-01-01 09:05:00",
    closed_at=None,
)
MOCK_INQUIRY_CLOSED = Inquiry(
    id=3,
    status=InquiryStatus.CLOSED,
    assigned_operator_id=1,
    created_at="2026-01-01 08:00:00",
    closed_at="2026-01-01 08:30:00",
)
MOCK_INQUIRY_INPUTTING = Inquiry(
    id=4,
    status=InquiryStatus.INPUTTING,
    assigned_operator_id=None,
    created_at="2026-01-01 09:20:00",
    closed_at=None,
)
MOCK_MESSAGE = Message(
    id=1,
    inquiry_id=1,
    sender_type=SenderType.ENDUSER,
    sender_name=None,
    content="テストメッセージ",
    created_at="2026-01-01 09:00:30",
)


class TestChatServiceSendMessage:
    """メッセージ送信のテスト"""

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_enduser_can_send_to_waiting(self, MockInqRepo, MockChatRepo, mock_manager):
        """エンドユーザはWAITING状態の問い合わせに送信可能"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_WAITING

        mock_chat_repo = MockChatRepo.return_value
        mock_chat_repo.save_message.return_value = MOCK_MESSAGE

        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo

        result = await service.send_message(
            inquiry_id=1,
            sender_type=SenderType.ENDUSER,
            content="テストメッセージ",
        )
        assert result is not None
        assert result["content"] == "テストメッセージ"
        mock_chat_repo.save_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_operator_cannot_send_without_assignment(
        self, MockInqRepo, MockChatRepo, mock_manager
    ):
        """オペレータは担当していない問い合わせに送信不可"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_WAITING  # 担当者なし

        service = ChatService()
        service.inquiry_repository = mock_inq_repo

        result = await service.send_message(
            inquiry_id=1,
            sender_type=SenderType.OPERATOR,
            content="テスト",
            operator_id=1,
        )
        assert result is None  # 送信拒否

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_operator_can_send_when_assigned(self, MockInqRepo, MockChatRepo, mock_manager):
        """オペレータは自分の担当する問い合わせに送信可能"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_ACTIVE  # operator_id=1が担当

        mock_chat_repo = MockChatRepo.return_value
        mock_chat_repo.save_message.return_value = MOCK_MESSAGE

        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo

        result = await service.send_message(
            inquiry_id=2,
            sender_type=SenderType.OPERATOR,
            content="対応します",
            sender_name="管理者",
            operator_id=1,
        )
        assert result is not None
        mock_chat_repo.save_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_cannot_send_to_closed(self, MockInqRepo, MockChatRepo, mock_manager):
        """終了した問い合わせには送信不可"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_CLOSED

        service = ChatService()
        service.inquiry_repository = mock_inq_repo

        result = await service.send_message(
            inquiry_id=3,
            sender_type=SenderType.ENDUSER,
            content="まだいますか？",
        )
        assert result is None


class TestChatServiceCreateInquiryOnConnect:
    """WebSocket接続時の問い合わせ作成テスト"""

    @patch("app.services.chat_service.InquiryRepository")
    def test_create_inquiry_on_connect_uses_inputting(self, MockInqRepo):
        """接続時はINPUTTINGステータスで作成する"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.create.return_value = MOCK_INQUIRY_INPUTTING

        service = ChatService()
        service.inquiry_repository = mock_inq_repo

        result = service.create_inquiry_on_connect()

        assert result.status == InquiryStatus.INPUTTING
        mock_inq_repo.create.assert_called_once_with(initial_status=InquiryStatus.INPUTTING)


class TestChatServiceSendMessageInputtingTransition:
    """INPUTTING → WAITING 遷移のテスト"""

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_enduser_message_transitions_inputting_to_waiting(
        self, MockInqRepo, MockChatRepo, mock_manager
    ):
        """エンドユーザの初回メッセージでINPUTTINGからWAITINGへ遷移する"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_INPUTTING
        mock_inq_repo.update_status_to_waiting.return_value = True

        mock_chat_repo = MockChatRepo.return_value
        mock_chat_repo.save_message.return_value = MOCK_MESSAGE

        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo

        result = await service.send_message(
            inquiry_id=4,
            sender_type=SenderType.ENDUSER,
            content="【事前ヒアリング】\nQ. 種類\nA. その他",
        )

        assert result is not None
        mock_inq_repo.update_status_to_waiting.assert_called_once_with(4, None)
        # 要約メッセージと、担当待ち案内のシステムメッセージ
        assert mock_chat_repo.save_message.call_count == 2

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_enduser_message_saves_hearing_category(
        self, MockInqRepo, MockChatRepo, mock_manager
    ):
        """初回送信で許可された種類IDをWAITING遷移と同時に保存する"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_INPUTTING
        mock_inq_repo.update_status_to_waiting.return_value = True

        mock_chat_repo = MockChatRepo.return_value
        mock_chat_repo.save_message.return_value = MOCK_MESSAGE
        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo

        await service.send_message(
            inquiry_id=4,
            sender_type=SenderType.ENDUSER,
            content="【事前ヒアリング】",
            category_id="ticket_price_apply",
        )

        mock_inq_repo.update_status_to_waiting.assert_called_once_with(4, "ticket_price_apply")

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_waiting_notice_failure_still_returns_user_message(
        self, MockInqRepo, MockChatRepo, mock_manager
    ):
        """案内の失敗は要約送信の成功を打ち消さない"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_INPUTTING
        mock_inq_repo.update_status_to_waiting.return_value = True

        mock_chat_repo = MockChatRepo.return_value
        mock_chat_repo.save_message.return_value = MOCK_MESSAGE
        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo
        service.send_system_message = AsyncMock(side_effect=RuntimeError("案内送信失敗"))

        result = await service.send_message(
            inquiry_id=4,
            sender_type=SenderType.ENDUSER,
            content="【事前ヒアリング】",
        )

        assert result is not None
        assert result["content"] == "テストメッセージ"

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_waiting_message_does_not_call_waiting_update(
        self, MockInqRepo, MockChatRepo, mock_manager
    ):
        """既にWAITINGの場合はステータス更新を呼ばない"""
        mock_inq_repo = MockInqRepo.return_value
        mock_inq_repo.find_by_id.return_value = MOCK_INQUIRY_WAITING

        mock_chat_repo = MockChatRepo.return_value
        mock_chat_repo.save_message.return_value = MOCK_MESSAGE

        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo

        await service.send_message(
            inquiry_id=1,
            sender_type=SenderType.ENDUSER,
            content="追加メッセージ",
        )

        mock_inq_repo.update_status_to_waiting.assert_not_called()


class TestChatServiceCloseInquiry:
    """問い合わせ終了のテスト"""

    @pytest.mark.asyncio
    @patch("app.services.chat_service.manager")
    @patch("app.services.chat_service.ChatRepository")
    @patch("app.services.chat_service.InquiryRepository")
    async def test_close_inquiry(self, MockInqRepo, MockChatRepo, mock_manager):
        """終了処理でステータス更新とシステムメッセージ保存が行われる"""
        mock_inq_repo = MockInqRepo.return_value
        mock_chat_repo = MockChatRepo.return_value

        system_msg = Message(
            id=99,
            inquiry_id=1,
            sender_type=SenderType.SYSTEM,
            sender_name=None,
            content="ユーザーが退出しました",
            created_at="2026-01-01 09:30:00",
        )
        mock_chat_repo.save_message.return_value = system_msg
        mock_manager.broadcast = AsyncMock()

        service = ChatService()
        service.inquiry_repository = mock_inq_repo
        service.chat_repository = mock_chat_repo

        await service.close_inquiry(1)

        # ステータス更新が呼ばれたか
        mock_inq_repo.update_status_closed.assert_called_once_with(1)
        # システムメッセージが保存されたか
        mock_chat_repo.save_message.assert_called_once()
        # ブロードキャストが2回呼ばれたか（メッセージ通知 + closed通知）
        assert mock_manager.broadcast.call_count == 2
