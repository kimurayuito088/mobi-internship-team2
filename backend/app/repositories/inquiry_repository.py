"""
問い合わせリポジトリ: 問い合わせのCRUD操作
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.database import get_db, now_jst
from app.models import Inquiry, InquiryStatus, Message, SenderType


def _inquiry_from_row(row, has_unread: bool = False) -> Inquiry:
    data = dict(row)
    return Inquiry(
        id=data["id"],
        status=data["status"],
        assigned_operator_id=data["assigned_operator_id"],
        created_at=data["created_at"],
        closed_at=data["closed_at"],
        category_id=data.get("category_id"),
        last_read_message_id=data.get("last_read_message_id") or 0,
        has_unread=has_unread,
    )


@dataclass
class InquiryGroupResult:
    """グループ一覧の1枠分（件数とLIMIT適用後の行）"""

    items: List[Inquiry]
    total: int


@dataclass
class GroupedInquiryResult:
    """未返信・自分の担当・クローズした案件の3グループ"""

    unanswered: InquiryGroupResult
    mine: InquiryGroupResult
    closed: InquiryGroupResult


# 新規作成時に許可する初期ステータス
# 状態遷移ルールが未確定のため、ACTIVE・CLOSEDを初期状態として作成させない
ALLOWED_INITIAL_STATUSES = frozenset(
    {
        InquiryStatus.WAITING,
        InquiryStatus.INPUTTING,
    }
)


class InquiryRepository:
    """問い合わせ関連のデータアクセス"""

    def find_all(self, page: int, per_page: int) -> Tuple[List[Inquiry], int]:
        """ページング付きで全件取得（ID降順）"""
        with get_db() as conn:
            # 総件数取得
            total = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]

            # ページング付きデータ取得（ID降順）
            offset = (page - 1) * per_page
            rows = conn.execute(
                "SELECT * FROM inquiries ORDER BY id DESC LIMIT ? OFFSET ?",
                (per_page, offset),
            ).fetchall()

            inquiries = [_inquiry_from_row(row) for row in rows]
            return inquiries, total

    def find_grouped(
        self,
        operator_id: int,
        unanswered_limit: int,
        mine_limit: int,
        closed_limit: int,
    ) -> GroupedInquiryResult:
        """
        3グループを同一接続内でCOUNT + LIMIT付きSELECTする。
        ACTIVEかつ他人担当の問い合わせはどのグループにも含めない。
        """
        with get_db() as conn:
            unanswered_total = conn.execute(
                "SELECT COUNT(*) FROM inquiries WHERE status IN (?, ?)",
                (InquiryStatus.WAITING, InquiryStatus.INPUTTING),
            ).fetchone()[0]
            unanswered_rows = conn.execute(
                """SELECT * FROM inquiries
                   WHERE status IN (?, ?)
                   ORDER BY CASE WHEN status = ? THEN 0 ELSE 1 END,
                            created_at ASC, id ASC
                   LIMIT ?""",
                (
                    InquiryStatus.WAITING,
                    InquiryStatus.INPUTTING,
                    InquiryStatus.WAITING,
                    unanswered_limit,
                ),
            ).fetchall()

            mine_total = conn.execute(
                "SELECT COUNT(*) FROM inquiries WHERE status = ? AND assigned_operator_id = ?",
                (InquiryStatus.ACTIVE, operator_id),
            ).fetchone()[0]
            mine_rows = conn.execute(
                """SELECT i.*
                   FROM inquiries i
                   WHERE i.status = ? AND i.assigned_operator_id = ?
                   ORDER BY i.created_at ASC, i.id ASC
                   LIMIT ?""",
                (InquiryStatus.ACTIVE, operator_id, mine_limit),
            ).fetchall()

            closed_total = conn.execute(
                "SELECT COUNT(*) FROM inquiries WHERE status = ?",
                (InquiryStatus.CLOSED,),
            ).fetchone()[0]
            closed_rows = conn.execute(
                """SELECT * FROM inquiries
                   WHERE status = ?
                   ORDER BY closed_at DESC, id DESC
                   LIMIT ?""",
                (InquiryStatus.CLOSED, closed_limit),
            ).fetchall()

            unread_inquiry_ids = {
                row["id"]
                for row in conn.execute(
                    """SELECT i.id
                       FROM inquiries i
                       WHERE i.assigned_operator_id = ?
                         AND i.status = ?
                         AND EXISTS (
                             SELECT 1
                             FROM messages m
                             WHERE m.inquiry_id = i.id
                               AND m.sender_type = ?
                               AND m.id > i.last_read_message_id
                         )""",
                    (
                        operator_id,
                        InquiryStatus.ACTIVE,
                        SenderType.ENDUSER,
                    ),
                ).fetchall()
            }

            return GroupedInquiryResult(
                unanswered=InquiryGroupResult(
                    items=[
                        _inquiry_from_row(row, has_unread=row["id"] in unread_inquiry_ids)
                        for row in unanswered_rows
                    ],
                    total=unanswered_total,
                ),
                mine=InquiryGroupResult(
                    items=[
                        _inquiry_from_row(row, has_unread=row["id"] in unread_inquiry_ids)
                        for row in mine_rows
                    ],
                    total=mine_total,
                ),
                closed=InquiryGroupResult(
                    items=[
                        _inquiry_from_row(row, has_unread=row["id"] in unread_inquiry_ids)
                        for row in closed_rows
                    ],
                    total=closed_total,
                ),
            )

    def find_by_id(self, inquiry_id: int) -> Optional[Inquiry]:
        """IDで問い合わせを検索"""
        with get_db() as conn:
            row = conn.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
            if row is None:
                return None
            return _inquiry_from_row(row)

    def find_by_id_with_unread(self, inquiry_id: int, operator_id: int) -> Optional[Inquiry]:
        """IDで問い合わせを未読状態付きで検索する。"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT i.*,
                          EXISTS (
                              SELECT 1
                              FROM messages m
                              WHERE i.assigned_operator_id = ?
                                AND m.inquiry_id = i.id
                                AND m.sender_type = ?
                                AND m.id > i.last_read_message_id
                          ) AS has_unread
                   FROM inquiries i
                   WHERE i.id = ?""",
                (operator_id, SenderType.ENDUSER, inquiry_id),
            ).fetchone()
            if row is None:
                return None
            return _inquiry_from_row(row, has_unread=bool(row["has_unread"]))

    def create(self, initial_status: int = InquiryStatus.WAITING) -> Inquiry:
        """
        新規問い合わせを作成
        初期ステータスはWAITING（デフォルト）またはINPUTTINGのみ指定可能
        それ以外の値はINSERTせずValueErrorを送出する
        """
        if initial_status not in ALLOWED_INITIAL_STATUSES:
            raise ValueError(
                f"初期ステータスに指定できない値です: {initial_status}"
                f"（許可値: {sorted(ALLOWED_INITIAL_STATUSES)}）"
            )

        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO inquiries (status, created_at) VALUES (?, ?)",
                (initial_status, now_jst()),
            )
            inquiry_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
            return _inquiry_from_row(row)

    def update_assignment(self, inquiry_id: int, operator_id: int) -> bool:
        """
        担当者を更新（排他制御付き）
        成功時: True, 失敗時（既に担当あり）: False
        """
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE inquiries
                   SET assigned_operator_id = ?, status = ?
                   WHERE id = ? AND assigned_operator_id IS NULL AND status = ?""",
                (operator_id, InquiryStatus.ACTIVE, inquiry_id, InquiryStatus.WAITING),
            )
            return cursor.rowcount > 0

    def update_status_to_waiting(self, inquiry_id: int, category_id: str | None = None) -> bool:
        """
        INPUTTING の問い合わせのみ WAITING に更新する。
        更新できた場合 True、対象外（既に別ステータス）の場合 False。
        category_id は WAITING 遷移時だけ書き、既存値は上書きしない用途。
        """
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE inquiries
                   SET status = ?, category_id = COALESCE(?, category_id)
                   WHERE id = ? AND status = ?""",
                (InquiryStatus.WAITING, category_id, inquiry_id, InquiryStatus.INPUTTING),
            )
            return cursor.rowcount > 0

    def update_status_closed(self, inquiry_id: int) -> None:
        """問い合わせを終了状態に更新"""
        with get_db() as conn:
            conn.execute(
                """UPDATE inquiries
                   SET status = ?, closed_at = ?
                   WHERE id = ?""",
                (InquiryStatus.CLOSED, now_jst(), inquiry_id),
            )

    def find_messages_by_inquiry_id(self, inquiry_id: int) -> List[Message]:
        """問い合わせIDに紐づくメッセージを全件取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE inquiry_id = ? ORDER BY created_at ASC, id ASC",
                (inquiry_id,),
            ).fetchall()
            return [Message(**dict(row)) for row in rows]

    def find_message_by_id(self, message_id: int) -> Optional[Message]:
        """IDでメッセージを検索する。"""
        with get_db() as conn:
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
            if row is None:
                return None
            return Message(**dict(row))

    def update_last_read_message_id(self, inquiry_id: int, message_id: int) -> bool:
        """現在の既読位置より新しい場合だけ既読位置を更新する。"""
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE inquiries
                   SET last_read_message_id = ?
                   WHERE id = ? AND last_read_message_id < ?""",
                (message_id, inquiry_id, message_id),
            )
            return cursor.rowcount > 0

    def find_unread_inquiry_ids(self, operator_id: int) -> List[int]:
        """担当案件のうちエンドユーザーメッセージが未読の問い合わせIDを取得する。"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT i.id
                   FROM inquiries i
                   WHERE i.assigned_operator_id = ?
                     AND i.status = ?
                     AND EXISTS (
                         SELECT 1
                         FROM messages m
                         WHERE m.inquiry_id = i.id
                           AND m.sender_type = ?
                           AND m.id > i.last_read_message_id
                     )
                   ORDER BY i.id ASC""",
                (
                    operator_id,
                    InquiryStatus.ACTIVE,
                    SenderType.ENDUSER,
                ),
            ).fetchall()
            return [row["id"] for row in rows]
