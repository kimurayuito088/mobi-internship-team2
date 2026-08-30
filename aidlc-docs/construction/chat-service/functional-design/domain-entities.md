# ドメインエンティティ定義

## エンティティ一覧

| エンティティ | 説明 |
|-------------|------|
| Operator | オペレータ（ログインユーザー） |
| Session | オペレータのログインセッション |
| Inquiry | 問い合わせ（エンドユーザとオペレータの会話単位） |
| Message | チャットメッセージ |

---

## エンティティ詳細

### Operator（オペレータ）

| フィールド | 型 | 制約 | 説明 |
|-----------|------|------|------|
| id | INTEGER | PK, AUTO INCREMENT | オペレータID |
| username | TEXT | UNIQUE, NOT NULL | ログインユーザー名 |
| password_hash | TEXT | NOT NULL | パスワードハッシュ |
| display_name | TEXT | NOT NULL | 表示名 |
| created_at | DATETIME | NOT NULL | 作成日時（JST） |

---

### Session（ログインセッション）

| フィールド | 型 | 制約 | 説明 |
|-----------|------|------|------|
| id | TEXT | PK | セッションID（UUID v4、アプリケーション側で生成） |
| operator_id | INTEGER | FK(operators.id), NOT NULL | オペレータID |
| created_at | DATETIME | NOT NULL | セッション作成日時（JST） |
| expires_at | DATETIME | NOT NULL | セッション有効期限 |

---

### Inquiry（問い合わせ）

| フィールド | 型 | 制約 | 説明 |
|-----------|------|------|------|
| id | INTEGER | PK, AUTO INCREMENT | 問い合わせID |
| status | INTEGER | NOT NULL, DEFAULT 0 | ステータスコード |
| assigned_operator_id | INTEGER | FK(operators.id), NULLABLE | 担当オペレータID |
| created_at | DATETIME | NOT NULL | 作成日時（JST） |
| closed_at | DATETIME | NULLABLE | 終了日時 |

**ステータスコード:**
| コード | 定数名 | 表示名 | 説明 |
|--------|--------|--------|------|
| 0 | `STATUS_WAITING` | 担当者未決定 | 誰も担当していない |
| 1 | `STATUS_ACTIVE` | 対応中（担当有り） | オペレータが担当し対応中 |
| 2 | `STATUS_CLOSED` | 終了 | セッション終了済み |
| 3 | `STATUS_INPUTTING` | 入力中 | エンドユーザが入力中（未使用の値3を割り当て、既存コードの値は変更しない） |

**オペレータから見たステータス表示:**
| DB上のstatus | assigned_operator_id | 表示 |
|-------------|---------------------|------|
| 0 (WAITING) | NULL | 「担当者未決定」 |
| 1 (ACTIVE) | 自分のID | 「自分の担当」 |
| 1 (ACTIVE) | 他人のID | 「自分の担当外」 |
| 2 (CLOSED) | 任意 | 「終了」 |
| 3 (INPUTTING) | 任意 | 「入力中」（assigned_operator_id に関係なく「入力中」） |

**INPUTTING（入力中）の現状:**
| 項目 | 内容 |
|------|------|
| DBのデフォルト値 | `DEFAULT 0`（WAITING）のまま。INPUTTING で作成する場合は INSERT 時に明示指定する |
| 作成方法 | `InquiryRepository.create(initial_status=InquiryStatus.INPUTTING)` |
| 初期ステータスに指定可能な値 | WAITING と INPUTTING のみ（ACTIVE・CLOSED・不明値は `ValueError`） |
| 担当取得 | 不可（担当取得SQLは `status = 0 (WAITING)` のみを対象とする） |
| 未実装 | WebSocket接続時のINPUTTING自動設定、初回メッセージでのWAITINGへの変更、INPUTTINGのタイムアウト・切断処理は未実装 |
| DBマイグレーション | 不要（`status` は CHECK 制約のない INTEGER 列のため値3をそのまま保存できる） |

---

### Message（メッセージ）

| フィールド | 型 | 制約 | 説明 |
|-----------|------|------|------|
| id | INTEGER | PK, AUTO INCREMENT | メッセージID |
| inquiry_id | INTEGER | FK(inquiries.id), NOT NULL | 問い合わせID |
| sender_type | INTEGER | NOT NULL | 送信者タイプコード |
| sender_name | TEXT | NULLABLE | 送信者表示名（オペレータ名、システムメッセージ用） |
| content | TEXT | NOT NULL | メッセージ内容 |
| created_at | DATETIME | NOT NULL | 送信日時（JST） |

**sender_type コード:**
| コード | 定数名 | 説明 |
|--------|--------|------|
| 0 | `SENDER_ENDUSER` | エンドユーザからのメッセージ |
| 1 | `SENDER_OPERATOR` | オペレータからのメッセージ |
| 2 | `SENDER_SYSTEM` | システムメッセージ（退出通知等） |

---

## エンティティ間リレーション

```
+----------+       1:N        +---------+
| Operator | <-----------+    | Session |
+----------+             |    +---------+
     |                   |
     | 1:N               |
     v                   |
+---------+              |
| Inquiry | -------------+
+---------+    assigned_operator_id
     |
     | 1:N
     v
+---------+
| Message |
+---------+
```

- Operator 1:N Session（1人のオペレータが複数セッションを持ちうる）
- Operator 1:N Inquiry（1人のオペレータが複数の問い合わせを担当）
- Inquiry 1:N Message（1つの問い合わせに複数のメッセージ）

---

## データベーススキーマ（SQLite DDL）

```sql
CREATE TABLE operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,  -- アプリケーション側で UUID v4 を生成して INSERT
    operator_id INTEGER NOT NULL REFERENCES operators(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER NOT NULL DEFAULT 0,  -- 0:waiting, 1:active, 2:closed, 3:inputting
    assigned_operator_id INTEGER REFERENCES operators(id),
    created_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inquiry_id INTEGER NOT NULL REFERENCES inquiries(id),
    sender_type INTEGER NOT NULL,  -- 0:enduser, 1:operator, 2:system
    sender_name TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- インデックス
CREATE INDEX idx_sessions_operator_id ON sessions(operator_id);
CREATE INDEX idx_inquiries_status ON inquiries(status);
CREATE INDEX idx_inquiries_assigned_operator_id ON inquiries(assigned_operator_id);
CREATE INDEX idx_messages_inquiry_id ON messages(inquiry_id);
```

### SQLite 固有の補足
- `INTEGER PRIMARY KEY AUTOINCREMENT`: SQLite では `INTEGER PRIMARY KEY` だけで自動採番されるが、`AUTOINCREMENT` を付けると過去のIDを再利用しないことを保証する
- `TEXT` 型: SQLite の TEXT にはサイズ制限がない。メッセージ長などの制約はアプリケーション層のバリデーションで行う
- `DATETIME` / `TEXT` 型の時刻カラム: SQLite には専用の日時型がないため、TEXT として ISO 8601 形式で格納する（Python の datetime ライブラリと互換）
- `status` 列に CHECK 制約はないため、新しいステータスコード（例: 3 = INPUTTING）を追加しても `ALTER TABLE` や既存データの移行は不要
- **全時刻はアプリケーション側で JST 文字列を生成して INSERT する**（`DEFAULT CURRENT_TIMESTAMP` は使用しない）。`database.py` の `now_jst()` ヘルパーを使用する
- セッションID（UUID）: アプリケーション（Python）側で `uuid.uuid4()` により生成し、TEXT 型カラムに格納する
