"""
オペレータ管理サービスのテスト（リポジトリをモック化）
学生向けサンプル: パスワード自動生成やバリデーションのテスト方法
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.models import Operator
from app.services.operator_service import OperatorService

# テスト用の固定データ
MOCK_OPERATOR_ADMIN = Operator(
    id=1,
    username="admin",
    password_hash="hashed",
    display_name="管理者",
    created_at="2026-01-01 09:00:00",
)
MOCK_OPERATOR_NEW = Operator(
    id=2,
    username="newuser",
    password_hash="hashed",
    display_name="新規ユーザー",
    created_at="2026-01-01 10:00:00",
)


class TestOperatorServiceCreate:
    """オペレータ追加のテスト"""

    @patch("app.services.operator_service.bcrypt")
    @patch("app.services.operator_service.OperatorRepository")
    def test_create_operator_success(self, MockRepo, mock_bcrypt):
        """オペレータ追加が成功し、パスワードが12文字英数字で自動生成される"""
        mock_repo = MockRepo.return_value
        mock_repo.find_by_username.return_value = None  # 重複なし
        mock_repo.create.return_value = MOCK_OPERATOR_NEW
        mock_bcrypt.hashpw.return_value = b"hashed"
        mock_bcrypt.gensalt.return_value = b"salt"

        service = OperatorService()
        service.repository = mock_repo

        operator, password = service.create_operator("newuser", "新規ユーザー")

        assert operator.username == "newuser"
        assert len(password) == 12
        assert password.isalnum()
        mock_repo.find_by_username.assert_called_once_with("newuser")
        mock_repo.create.assert_called_once()

    @patch("app.services.operator_service.OperatorRepository")
    def test_create_operator_duplicate_username(self, MockRepo):
        """既存のusernameと重複する場合は409エラー"""
        mock_repo = MockRepo.return_value
        mock_repo.find_by_username.return_value = MOCK_OPERATOR_ADMIN  # 重複あり

        service = OperatorService()
        service.repository = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            service.create_operator("admin", "重複テスト")
        assert exc_info.value.status_code == 409


class TestOperatorServiceDelete:
    """オペレータ削除のテスト"""

    @patch("app.services.operator_service.OperatorRepository")
    def test_delete_operator_success(self, MockRepo):
        """他のオペレータを削除できる"""
        mock_repo = MockRepo.return_value

        service = OperatorService()
        service.repository = mock_repo

        service.delete_operator(target_id=2, current_operator_id=1)
        mock_repo.delete.assert_called_once_with(2)

    @patch("app.services.operator_service.OperatorRepository")
    def test_delete_self_forbidden(self, MockRepo):
        """自分自身は削除できない（403）"""
        service = OperatorService()

        with pytest.raises(HTTPException) as exc_info:
            service.delete_operator(target_id=1, current_operator_id=1)
        assert exc_info.value.status_code == 403


class TestOperatorServiceList:
    """オペレータ一覧のテスト"""

    @patch("app.services.operator_service.OperatorRepository")
    def test_list_operators(self, MockRepo):
        """一覧取得でリポジトリのfind_allが呼ばれる"""
        mock_repo = MockRepo.return_value
        mock_repo.find_all.return_value = [MOCK_OPERATOR_ADMIN, MOCK_OPERATOR_NEW]

        service = OperatorService()
        service.repository = mock_repo

        operators = service.list_operators()
        assert len(operators) == 2
        assert operators[0].username == "admin"
        mock_repo.find_all.assert_called_once()
