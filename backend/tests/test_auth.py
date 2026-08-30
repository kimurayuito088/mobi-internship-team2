"""
認証サービスのテスト（リポジトリをモック化）
学生向けサンプル: unittest.mock を使ったモックの書き方
"""

from unittest.mock import patch

import bcrypt
import pytest

from app.models import Operator, Session
from app.services.auth_service import AuthService

# テスト用の固定データ
MOCK_PASSWORD = "password123"
MOCK_HASH = bcrypt.hashpw(MOCK_PASSWORD.encode(), bcrypt.gensalt()).decode()
MOCK_OPERATOR = Operator(
    id=1,
    username="admin",
    password_hash=MOCK_HASH,
    display_name="管理者",
    created_at="2026-01-01 09:00:00",
)
MOCK_SESSION = Session(
    id="test-session-id-1234",
    operator_id=1,
    created_at="2026-01-01 09:00:00",
    expires_at="2026-12-31 23:59:59",  # 未来の日付（有効期限内）
)


class TestAuthServiceLogin:
    """ログイン機能のテスト"""

    @patch("app.services.auth_service.AuthRepository")
    def test_login_success(self, MockRepo):
        """正しいID/PWでログインできる"""
        # モックの設定
        mock_repo = MockRepo.return_value
        mock_repo.find_operator_by_username.return_value = MOCK_OPERATOR
        mock_repo.create_session.return_value = "new-session-id"

        service = AuthService()
        service.repository = mock_repo

        operator, session_id = service.login("admin", MOCK_PASSWORD)

        assert operator.username == "admin"
        assert session_id == "new-session-id"
        mock_repo.find_operator_by_username.assert_called_once_with("admin")
        mock_repo.create_session.assert_called_once_with(1)

    @patch("app.services.auth_service.AuthRepository")
    def test_login_user_not_found(self, MockRepo):
        """存在しないユーザー名でログイン失敗"""
        mock_repo = MockRepo.return_value
        mock_repo.find_operator_by_username.return_value = None

        service = AuthService()
        service.repository = mock_repo

        with pytest.raises(ValueError, match="ユーザー名またはパスワード"):
            service.login("nonexistent", "password")

    @patch("app.services.auth_service.AuthRepository")
    def test_login_wrong_password(self, MockRepo):
        """間違ったパスワードでログイン失敗"""
        mock_repo = MockRepo.return_value
        mock_repo.find_operator_by_username.return_value = MOCK_OPERATOR

        service = AuthService()
        service.repository = mock_repo

        with pytest.raises(ValueError, match="ユーザー名またはパスワード"):
            service.login("admin", "wrongpassword")


class TestAuthServiceSession:
    """セッション管理のテスト"""

    @patch("app.services.auth_service.AuthRepository")
    def test_get_current_operator_valid(self, MockRepo):
        """有効なセッションでオペレータ取得"""
        mock_repo = MockRepo.return_value
        mock_repo.get_session.return_value = MOCK_SESSION
        mock_repo.find_operator_by_id.return_value = MOCK_OPERATOR

        service = AuthService()
        service.repository = mock_repo

        operator = service.get_current_operator("test-session-id-1234")
        assert operator is not None
        assert operator.username == "admin"

    @patch("app.services.auth_service.AuthRepository")
    def test_get_current_operator_invalid_session(self, MockRepo):
        """存在しないセッションIDでNone"""
        mock_repo = MockRepo.return_value
        mock_repo.get_session.return_value = None

        service = AuthService()
        service.repository = mock_repo

        operator = service.get_current_operator("invalid-id")
        assert operator is None

    @patch("app.services.auth_service.AuthRepository")
    def test_get_current_operator_none(self, MockRepo):
        """session_id=NoneでNone"""
        service = AuthService()
        operator = service.get_current_operator(None)
        assert operator is None

    @patch("app.services.auth_service.AuthRepository")
    def test_logout(self, MockRepo):
        """ログアウトでdelete_sessionが呼ばれる"""
        mock_repo = MockRepo.return_value

        service = AuthService()
        service.repository = mock_repo

        service.logout("test-session-id")
        mock_repo.delete_session.assert_called_once_with("test-session-id")
