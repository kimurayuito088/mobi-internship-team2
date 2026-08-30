"""
SQLite データベース接続・テーブル作成・シードデータ投入
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import bcrypt

from app import config

# JST タイムゾーン
JST = timezone(timedelta(hours=9))

# テーブル作成SQL
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    operator_id INTEGER NOT NULL REFERENCES operators(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER NOT NULL DEFAULT 0,
    assigned_operator_id INTEGER REFERENCES operators(id),
    created_at TEXT NOT NULL,
    closed_at TEXT,
    category_id TEXT,
    last_read_message_id INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inquiry_id INTEGER NOT NULL REFERENCES inquiries(id),
    sender_type INTEGER NOT NULL,
    sender_name TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_operator_id ON sessions(operator_id);
CREATE INDEX IF NOT EXISTS idx_inquiries_status ON inquiries(status);
CREATE INDEX IF NOT EXISTS idx_inquiries_assigned_operator_id ON inquiries(assigned_operator_id);
CREATE INDEX IF NOT EXISTS idx_messages_inquiry_id ON messages(inquiry_id);
"""


def get_connection() -> sqlite3.Connection:
    """SQLite接続を取得する"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # dict風にアクセスできるようにする
    conn.execute("PRAGMA journal_mode=WAL")  # 同時アクセスのパフォーマンス向上
    conn.execute("PRAGMA foreign_keys=ON")  # 外部キー制約を有効化
    return conn


def now_jst() -> str:
    """現在時刻をJSTのISO 8601文字列で返す"""
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def get_db():
    """データベース接続のコンテキストマネージャ"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """テーブル作成とシードデータ投入"""
    with get_db() as conn:
        conn.executescript(CREATE_TABLES_SQL)
        _migrate_inquiries(conn)

        # シードデータ: 初期オペレータが存在しない場合のみ投入
        cursor = conn.execute("SELECT COUNT(*) FROM operators")
        count = cursor.fetchone()[0]

        if count == 0:
            # 初期オペレータ（パスワード: "password123"）
            password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()

            conn.execute(
                "INSERT INTO operators (username, password_hash, display_name, created_at) "
                "VALUES (?, ?, ?, ?)",
                ("admin", password_hash, "管理者", now_jst()),
            )
            print("初期オペレータを作成しました: username=admin, password=password123")


def _migrate_inquiries(conn: sqlite3.Connection) -> None:
    """既存DBを保持したまま、問い合わせの追加カラムを足す。"""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(inquiries)").fetchall()}
    # CREATE TABLE IF NOT EXISTS では後から増えた列が付かないため、既存DB向けに足す
    if "category_id" not in columns:
        conn.execute("ALTER TABLE inquiries ADD COLUMN category_id TEXT")
    if "last_read_message_id" not in columns:
        conn.execute(
            "ALTER TABLE inquiries ADD COLUMN last_read_message_id INTEGER NOT NULL DEFAULT 0"
        )
