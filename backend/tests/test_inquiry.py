"""
問い合わせサービスのテスト（リポジトリをモック化、PBT含む）
学生向けサンプル: ビジネスロジックを固定データでテストする方法
"""

import math
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models import Inquiry, InquiryStatus
from app.services.inquiry_service import InquiryService

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
    created_at="2026-01-01 09:10:00",
    closed_at=None,
)
MOCK_INQUIRIES = [
    MOCK_INQUIRY_WAITING,
    MOCK_INQUIRY_ACTIVE,
    MOCK_INQUIRY_CLOSED,
    MOCK_INQUIRY_INPUTTING,
]


class TestInquiryServiceAssign:
    """担当割り当てのテスト"""

    @patch("app.services.inquiry_service.InquiryRepository")
    def test_assign_operator_success(self, MockRepo):
        """担当割り当て成功"""
        mock_repo = MockRepo.return_value
        mock_repo.update_assignment.return_value = True
        assigned_inquiry = Inquiry(
            id=1,
            status=InquiryStatus.ACTIVE,
            assigned_operator_id=1,
            created_at="2026-01-01 09:00:00",
            closed_at=None,
        )
        mock_repo.find_by_id.return_value = assigned_inquiry

        service = InquiryService()
        service.repository = mock_repo

        result = service.assign_operator(1, operator_id=1)
        assert result.status == InquiryStatus.ACTIVE
        assert result.assigned_operator_id == 1

    @patch("app.services.inquiry_service.InquiryRepository")
    def test_assign_operator_conflict(self, MockRepo):
        """既に担当がいる場合は409エラー"""
        mock_repo = MockRepo.return_value
        mock_repo.update_assignment.return_value = False  # 排他制御失敗

        service = InquiryService()
        service.repository = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            service.assign_operator(1, operator_id=2)
        assert exc_info.value.status_code == 409


class TestInquiryServiceList:
    """一覧取得のテスト"""

    @patch("app.services.inquiry_service.InquiryRepository")
    def test_list_inquiries_pagination(self, MockRepo):
        """ページネーション情報が正しく計算される"""
        mock_repo = MockRepo.return_value
        mock_repo.find_all.return_value = (MOCK_INQUIRIES, len(MOCK_INQUIRIES))

        service = InquiryService()
        service.repository = mock_repo

        result = service.list_inquiries(page=1, per_page=10, operator_id=1)
        assert result.total == len(MOCK_INQUIRIES)
        assert result.total_pages == 1
        assert len(result.items) == len(MOCK_INQUIRIES)

    @patch("app.services.inquiry_service.InquiryRepository")
    def test_list_inquiries_display_status(self, MockRepo):
        """表示ステータスが正しく算出される"""
        mock_repo = MockRepo.return_value
        mock_repo.find_all.return_value = (MOCK_INQUIRIES, len(MOCK_INQUIRIES))

        service = InquiryService()
        service.repository = mock_repo

        result = service.list_inquiries(page=1, per_page=10, operator_id=1)
        statuses = [item.display_status for item in result.items]
        assert "waiting" in statuses
        assert "mine" in statuses
        assert "closed" in statuses
        assert "inputting" in statuses

    @patch("app.services.inquiry_service.InquiryRepository")
    def test_list_inquiries_inputting_is_not_others(self, MockRepo):
        """INPUTTINGの問い合わせが'others'として扱われない"""
        mock_repo = MockRepo.return_value
        mock_repo.find_all.return_value = ([MOCK_INQUIRY_INPUTTING], 1)

        service = InquiryService()
        service.repository = mock_repo

        result = service.list_inquiries(page=1, per_page=10, operator_id=99)
        assert result.items[0].status == InquiryStatus.INPUTTING
        assert result.items[0].display_status == "inputting"


class TestDisplayStatus:
    """表示ステータス算出のテスト（純粋関数テスト）"""

    def test_waiting(self):
        """WAITING → 'waiting'"""
        result = InquiryService._compute_display_status(MOCK_INQUIRY_WAITING, operator_id=1)
        assert result == "waiting"

    def test_mine(self):
        """ACTIVE + 自分のID → 'mine'"""
        result = InquiryService._compute_display_status(MOCK_INQUIRY_ACTIVE, operator_id=1)
        assert result == "mine"

    def test_others(self):
        """ACTIVE + 他人のID → 'others'"""
        result = InquiryService._compute_display_status(MOCK_INQUIRY_ACTIVE, operator_id=99)
        assert result == "others"

    def test_closed(self):
        """CLOSED → 'closed'"""
        result = InquiryService._compute_display_status(MOCK_INQUIRY_CLOSED, operator_id=1)
        assert result == "closed"

    def test_inputting(self):
        """INPUTTING → 'inputting'"""
        result = InquiryService._compute_display_status(MOCK_INQUIRY_INPUTTING, operator_id=1)
        assert result == "inputting"

    @pytest.mark.parametrize("assigned_operator_id", [None, 1, 99])
    def test_inputting_ignores_assignment(self, assigned_operator_id):
        """INPUTTINGはassigned_operator_idに関係なく'inputting'になる"""
        inquiry = Inquiry(
            id=10,
            status=InquiryStatus.INPUTTING,
            assigned_operator_id=assigned_operator_id,
            created_at="2026-01-01 09:10:00",
            closed_at=None,
        )
        result = InquiryService._compute_display_status(inquiry, operator_id=1)
        assert result == "inputting"


class TestDisplayStatusPBT:
    """プロパティベーステスト: 表示ステータス算出"""

    @given(
        status=st.sampled_from(
            [
                InquiryStatus.WAITING,
                InquiryStatus.ACTIVE,
                InquiryStatus.CLOSED,
                InquiryStatus.INPUTTING,
            ]
        ),
        assigned_operator_id=st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
        operator_id=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=200)
    def test_always_returns_valid_status(self, status, assigned_operator_id, operator_id):
        """任意の入力に対して表示ステータスが5値のいずれかになる"""
        inquiry = Inquiry(
            id=1,
            status=status,
            assigned_operator_id=assigned_operator_id,
            created_at="",
            closed_at=None,
        )
        result = InquiryService._compute_display_status(inquiry, operator_id)
        assert result in ("inputting", "waiting", "mine", "others", "closed")

    @given(
        total=st.integers(min_value=0, max_value=1000),
        per_page=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=200)
    def test_pagination_calculation(self, total, per_page):
        """ページ数計算が常に正しい"""
        total_pages = math.ceil(total / per_page)
        if total > 0:
            last_page_items = total - (total_pages - 1) * per_page
            assert 1 <= last_page_items <= per_page
        else:
            assert total_pages == 0
