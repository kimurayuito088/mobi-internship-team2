"""
問い合わせリポジトリのテスト（一時ファイルのSQLiteを使用）
学生向けサンプル: 実DBへの保存・取得を検証する方法
"""

import pytest

from app import config
from app.database import CREATE_TABLES_SQL, get_db
from app.models import InquiryStatus
from app.repositories.inquiry_repository import InquiryRepository

# テストで使用しない未定義のステータス値
UNKNOWN_STATUS = 99


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """テストごとに独立した一時DBを用意する"""
    db_path = tmp_path / "test_chat_service.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    with get_db() as conn:
        conn.executescript(CREATE_TABLES_SQL)
    return db_path


def count_inquiries() -> int:
    """問い合わせの総件数を取得する"""
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]


def fetch_status(inquiry_id: int) -> int:
    """DBに保存されているstatus列の値を直接取得する"""
    with get_db() as conn:
        row = conn.execute("SELECT status FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
        return row[0]


class TestInquiryRepositoryCreate:
    """問い合わせ作成のテスト"""

    def test_create_without_argument_is_waiting(self, temp_db):
        """引数を省略した場合は既存動作どおりWAITINGで作成される"""
        repository = InquiryRepository()

        inquiry = repository.create()

        assert inquiry.status == InquiryStatus.WAITING
        assert fetch_status(inquiry.id) == InquiryStatus.WAITING

    def test_create_with_inputting_saves_status_3(self, temp_db):
        """INPUTTINGを指定するとstatus=3でDBに保存される"""
        repository = InquiryRepository()

        inquiry = repository.create(initial_status=InquiryStatus.INPUTTING)

        assert inquiry.status == InquiryStatus.INPUTTING
        assert fetch_status(inquiry.id) == 3

    def test_created_inputting_can_be_fetched(self, temp_db):
        """保存後に取得したInquiry.statusがINPUTTINGになる"""
        repository = InquiryRepository()

        created = repository.create(initial_status=InquiryStatus.INPUTTING)
        fetched = repository.find_by_id(created.id)

        assert fetched is not None
        assert fetched.status == InquiryStatus.INPUTTING

    def test_db_default_status_is_waiting(self, temp_db):
        """status列を指定しないINSERTではDBのDEFAULT 0（WAITING）が使われる"""
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO inquiries (created_at) VALUES (?)", ("2026-01-01 09:00:00",)
            )
            inquiry_id = cursor.lastrowid

        assert fetch_status(inquiry_id) == InquiryStatus.WAITING

    @pytest.mark.parametrize(
        "invalid_status",
        [InquiryStatus.ACTIVE, InquiryStatus.CLOSED, UNKNOWN_STATUS],
    )
    def test_create_with_invalid_initial_status_raises(self, temp_db, invalid_status):
        """ACTIVE・CLOSED・不明な値は初期ステータスに指定できない"""
        repository = InquiryRepository()

        with pytest.raises(ValueError):
            repository.create(initial_status=invalid_status)

    @pytest.mark.parametrize(
        "invalid_status",
        [InquiryStatus.ACTIVE, InquiryStatus.CLOSED, UNKNOWN_STATUS],
    )
    def test_create_with_invalid_initial_status_does_not_insert(self, temp_db, invalid_status):
        """不正値の場合は問い合わせレコードが作成されない"""
        repository = InquiryRepository()

        with pytest.raises(ValueError):
            repository.create(initial_status=invalid_status)

        assert count_inquiries() == 0


class TestInquiryRepositoryUpdateStatusToWaiting:
    """INPUTTING → WAITING 更新のテスト"""

    def test_update_inputting_to_waiting(self, temp_db):
        """INPUTTINGの問い合わせをWAITINGに更新できる"""
        repository = InquiryRepository()
        inquiry = repository.create(initial_status=InquiryStatus.INPUTTING)

        updated = repository.update_status_to_waiting(inquiry.id)

        assert updated is True
        assert fetch_status(inquiry.id) == InquiryStatus.WAITING

    def test_update_inputting_to_waiting_saves_category(self, temp_db):
        """WAITING遷移時に種類IDを保存する"""
        repository = InquiryRepository()
        inquiry = repository.create(initial_status=InquiryStatus.INPUTTING)

        updated = repository.update_status_to_waiting(
            inquiry.id, category_id="change_collection_date"
        )
        fetched = repository.find_by_id(inquiry.id)

        assert updated is True
        assert fetched is not None
        assert fetched.category_id == "change_collection_date"

    def test_create_leaves_category_unset(self, temp_db):
        """作成直後の種類は未設定"""
        repository = InquiryRepository()
        inquiry = repository.create(initial_status=InquiryStatus.INPUTTING)

        assert inquiry.category_id is None

    def test_update_waiting_returns_false(self, temp_db):
        """WAITINGの問い合わせは更新されない"""
        repository = InquiryRepository()
        inquiry = repository.create()

        updated = repository.update_status_to_waiting(inquiry.id)

        assert updated is False
        assert fetch_status(inquiry.id) == InquiryStatus.WAITING
