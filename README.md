# コンタクトセンター チャットサービス

モビルス株式会社の短期インターン向けの学習素材として作成されたコンタクトセンター向けリアルタイムチャットサービスです。

## 機能概要

- **エンドユーザ向けチャット**: Webページにアクセスするだけでオペレータとチャットできる
- **オペレータ向け管理画面**: ログインして問い合わせに対応する
- **リアルタイム通信**: WebSocketによる即時メッセージ配信
- **問い合わせ管理**: 担当制（早い者勝ち）、ステータス管理
- **オペレータ管理**: オペレータの追加・削除

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | React 18 + TypeScript + Vite |
| バックエンド | Python + FastAPI |
| リアルタイム通信 | WebSocket |
| データベース | SQLite |
| テスト | pytest + hypothesis (PBT) |

## ディレクトリ構成

```
├── frontend/          # React フロントエンド
│   ├── src/
│   │   ├── components/    # 共通UIコンポーネント
│   │   ├── pages/         # ページコンポーネント
│   │   ├── contexts/      # React Context
│   │   ├── hooks/         # カスタムフック
│   │   └── types/         # TypeScript型定義
│   └── package.json
│
├── backend/           # Python バックエンド
│   ├── app/
│   │   ├── routers/       # APIルーター
│   │   ├── services/      # ビジネスロジック
│   │   ├── repositories/  # データアクセス
│   │   ├── websocket/     # WebSocketハンドラー
│   │   └── middleware/    # ミドルウェア
│   ├── tests/             # テスト
│   └── requirements.txt
│
└── docs/              # 開発ガイド
```

## 開発ガイド

- [開発ルール](docs/development-rules.md) — 技術選定・外部サービス利用・コーディング規約
- [Git フローガイド](docs/git-flow-guide.md) — ブランチ戦略と作業フローの説明

## セットアップと起動

### 初回セットアップ（推奨）

リポジトリのルートにあるセットアップスクリプトを実行すると、必要なツール（Homebrew、Node.js、Python）のインストールから依存パッケージの導入まで自動で行われます。

```bash
./setup.sh
```

> macOS 向けのスクリプトです。Homebrew、nvm（Node.js 24）、Python 3.12、仮想環境作成、npm install がまとめて実行されます。

### バックエンド起動

```bash
cd backend
source venv/bin/activate
python -m app.main
```

バックエンドが `http://localhost:8000` で起動します。

### フロントエンド起動（別ターミナル）

```bash
cd frontend
nvm use 24
npm run dev
```

フロントエンドが `http://localhost:3000` で起動します。

### 初期ログイン情報

| ユーザー名 | パスワード |
|-----------|-----------|
| admin | password123 |

## 画面一覧

| パス | 画面 | 説明 |
|------|------|------|
| `/` | エンドユーザチャット | チャット画面（認証不要） |
| `/operator/login` | ログイン | オペレータログイン |
| `/operator/inquiries` | 問い合わせ一覧 | 全問い合わせを表示 |
| `/operator/inquiries/:id` | 問い合わせ詳細 | チャット対応画面 |
| `/operator/users` | オペレータ一覧 | オペレータ管理 |
| `/operator/users/add` | オペレータ追加 | 新規オペレータ作成 |

## 問い合わせステータス

| コード | 定数名 | 表示名 |
|-------:|--------|--------|
| 0 | `WAITING` | 担当者未決定 |
| 1 | `ACTIVE` | 自分の担当 / 担当外（担当者によって表示が変わる） |
| 2 | `CLOSED` | 終了 |
| 3 | `INPUTTING` | 入力中 |

オペレータから見た表示ステータス（`display_status`）は、バックエンドで以下の順に判定します。

| DB上のstatus | 表示ステータス |
|-------------|---------------|
| 2 (CLOSED) | `closed` |
| 3 (INPUTTING) | `inputting` |
| 0 (WAITING) | `waiting` |
| 1 (ACTIVE) かつ自分が担当 | `mine` |
| 1 (ACTIVE) かつ他人が担当 | `others` |

### 入力中（INPUTTING）の現状

- `inquiries.status` は CHECK 制約のない `INTEGER` 列のため、ステータス追加に伴う DB スキーマ変更や既存データ移行は不要です
- DB のデフォルト値は `DEFAULT 0`（WAITING）のままです。既存の問い合わせ作成処理（引数省略）は引き続き WAITING で作成します
- エンドユーザが WebSocket（`inquiry_id=0`）に接続すると `INPUTTING` で問い合わせが作成されます
- エンドユーザの初回メッセージ送信時に `INPUTTING` → `WAITING` へ遷移します
- 入力中の問い合わせは担当取得できません（担当取得の対象は WAITING のみ）
- タブ閉じ・WebSocket 切断時は `INPUTTING` を含む問い合わせを `CLOSED` にします
- 入力中のタイムアウト自動終了は未実装です

## API エンドポイント

### REST API

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/auth/login` | ログイン |
| POST | `/api/auth/logout` | ログアウト |
| GET | `/api/auth/me` | 自分の情報取得 |
| GET | `/api/inquiries` | 問い合わせ一覧 |
| GET | `/api/inquiries/:id` | 問い合わせ詳細 |
| GET | `/api/inquiries/:id/messages` | メッセージ一覧 |
| POST | `/api/inquiries/:id/assign` | 担当取得 |
| GET | `/api/operators` | オペレータ一覧 |
| POST | `/api/operators` | オペレータ追加 |
| DELETE | `/api/operators/:id` | オペレータ削除 |

### WebSocket

| パス | 説明 |
|------|------|
| `/ws/chat/enduser/{inquiry_id}` | エンドユーザ用 |
| `/ws/chat/operator/{inquiry_id}` | オペレータ用 |

## テスト実行

```bash
cd backend
source venv/bin/activate
pytest -v
```

## データベースの確認方法

### ファイルの場所

SQLite のデータベースファイルはバックエンド起動時に自動作成されます。

```
backend/chat_service.db
```

### データの参照方法

macOS に標準で入っている `sqlite3` コマンドで中身を確認できます。

```bash
# backend/ ディレクトリに移動
cd backend

# sqlite3 で接続
sqlite3 chat_service.db
```

接続後に使えるコマンド：

```sql
-- テーブル一覧を表示
.tables

-- テーブルの構造を確認
.schema operators
.schema inquiries
.schema messages

-- オペレータ一覧を見る
SELECT * FROM operators;

-- 問い合わせ一覧を見る（新しい順）
SELECT * FROM inquiries ORDER BY id DESC;

-- 特定の問い合わせのメッセージを見る
SELECT * FROM messages WHERE inquiry_id = 1 ORDER BY created_at;

-- 見やすい表示モードに切り替え
.mode column
.headers on
SELECT * FROM inquiries;

-- 終了
.quit
```

### データのリセット

データを全て削除してやり直したい場合は、DB ファイルを削除してバックエンドを再起動してください。

```bash
rm backend/chat_service.db
# バックエンドを再起動すると、テーブル作成 + 初期オペレータ(admin)が再作成される
```
