"""
アプリケーション設定値
変更が必要な場合はここを修正する
"""

# データベースファイルパス
DB_PATH = "chat_service.db"

# セッション有効期限（秒）: 8時間
SESSION_EXPIRY_SECONDS = 8 * 60 * 60

# ページング設定
DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 100

# グループ一覧のデフォルト取得件数（各グループ独立）
DEFAULT_UNANSWERED_LIMIT = 20
DEFAULT_MINE_LIMIT = 10
DEFAULT_CLOSED_LIMIT = 10
MAX_GROUP_LIMIT = 100

# タイムアウト設定
TIMEOUT_SECONDS = 30 * 60  # 30分
TIMEOUT_CHECK_INTERVAL_SECONDS = 60  # 60秒間隔でチェック

# パスワード自動生成設定
GENERATED_PASSWORD_LENGTH = 12

# CORS設定
CORS_ORIGINS = ["http://localhost:3000"]
