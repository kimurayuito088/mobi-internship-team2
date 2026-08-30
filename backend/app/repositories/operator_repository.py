"""
オペレータリポジトリ: オペレータのCRUD操作
"""

from typing import List, Optional

from app.database import get_db, now_jst
from app.models import Operator


class OperatorRepository:
    """オペレータ管理のデータアクセス"""

    def find_all(self) -> List[Operator]:
        """全オペレータを取得"""
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM operators ORDER BY id ASC").fetchall()
            return [Operator(**dict(row)) for row in rows]

    def find_by_username(self, username: str) -> Optional[Operator]:
        """ユーザー名で検索"""
        with get_db() as conn:
            row = conn.execute("SELECT * FROM operators WHERE username = ?", (username,)).fetchone()
            if row is None:
                return None
            return Operator(**dict(row))

    def create(self, username: str, password_hash: str, display_name: str) -> Operator:
        """オペレータを作成"""
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO operators (username, password_hash, display_name, created_at) "
                "VALUES (?, ?, ?, ?)",
                (username, password_hash, display_name, now_jst()),
            )
            operator_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM operators WHERE id = ?", (operator_id,)).fetchone()
            return Operator(**dict(row))

    def delete(self, operator_id: int) -> None:
        """オペレータを削除（関連セッションも削除）"""
        with get_db() as conn:
            conn.execute("DELETE FROM sessions WHERE operator_id = ?", (operator_id,))
            conn.execute("DELETE FROM operators WHERE id = ?", (operator_id,))
