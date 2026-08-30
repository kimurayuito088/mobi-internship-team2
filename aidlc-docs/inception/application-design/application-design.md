# アプリケーション設計 統合ドキュメント

## 設計方針

| 項目 | 決定事項 |
|------|---------|
| フロントエンド構成 | 同一Reactアプリ（ルーティングで画面分離） |
| APIスタイル | REST API + WebSocket（別エンドポイント） |
| バックエンドアーキテクチャ | 3層構造（Router → Service → Repository） |
| WebSocket管理 | インメモリ管理 |
| フロントエンド状態管理 | useState / useContext のみ |

---

## システム全体構成

```
+--------------------------------------------------+
|                  React SPA (TypeScript)           |
|                                                  |
|  +-----------+  +----------+  +--------------+   |
|  | EndUser   |  | Operator |  | Operator     |   |
|  | Chat      |  | Login    |  | Dashboard    |   |
|  | (/)       |  | (/opera- |  | (/operator/  |   |
|  |           |  | tor/     |  |  inquiries)  |   |
|  |           |  | login)   |  |              |   |
|  +-----------+  +----------+  +--------------+   |
|                                                  |
|  [AuthProvider] [useChat Hook]                   |
+-------------------+------------------------------+
                    |
          HTTP + WebSocket
                    |
+-------------------v------------------------------+
|              FastAPI Backend (Python)             |
|                                                  |
|  +----------+  +-----------+  +-----------+      |
|  | auth     |  | inquiry   |  | chat      |      |
|  | _router  |  | _router   |  | _ws       |      |
|  +----+-----+  +-----+-----+  +-----+-----+     |
|       |               |               |          |
|  +----v-----+  +------v----+  +------v----+      |
|  | Auth     |  | Inquiry   |  | Chat      |      |
|  | Service  |  | Service   |  | Service   |      |
|  +----+-----+  +-----+-----+  +--+----+--+      |
|       |               |          |    |          |
|  +----v-----+  +------v----+  +--v-+  +--v---+  |
|  | Auth     |  | Inquiry   |  |Chat|  |Conn  |  |
|  | Repo     |  | Repo      |  |Repo|  |Mgr   |  |
|  +----+-----+  +-----+-----+  +--+-+  +------+  |
|       |               |          |               |
+-------+---------------+----------+---------------+
        |               |          |
+-------v---------------v----------v---------------+
|                   SQLite DB                       |
|                                                  |
|  [operators] [sessions] [inquiries] [messages]   |
+--------------------------------------------------+
```

---

## コンポーネント概要

### フロントエンド（7コンポーネント）
| ID | コンポーネント | 主な責務 |
|----|--------------|---------|
| FE-001 | EndUserChat | エンドユーザチャット画面 |
| FE-002 | OperatorLogin | オペレータログイン画面 |
| FE-003 | InquiryList | 問い合わせ一覧（ページング付き） |
| FE-004 | InquiryDetail | 問い合わせ詳細チャット画面 |
| FE-005 | AppShell | ルーティング・認証管理 |
| FE-006 | OperatorAdd | オペレータ追加画面 |
| FE-007 | OperatorList | オペレータ一覧・削除画面 |

### バックエンド（6コンポーネント）
| ID | コンポーネント | 主な責務 |
|----|--------------|---------|
| BE-001 | auth | オペレータ認証・セッション管理 |
| BE-002 | inquiry | 問い合わせ管理・担当割り当て |
| BE-003 | chat | リアルタイムメッセージ送受信 |
| BE-004 | connection_manager | WebSocket接続のインメモリ管理 |
| BE-005 | database | SQLite接続・マイグレーション |
| BE-006 | operator | オペレータ管理（追加・削除・一覧） |

---

## API エンドポイント一覧

### REST API
| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| POST | `/api/auth/login` | ログイン | 不要 |
| POST | `/api/auth/logout` | ログアウト | 必要 |
| GET | `/api/auth/me` | 自分の情報取得 | 必要 |
| GET | `/api/inquiries` | 問い合わせ一覧 | 必要 |
| GET | `/api/inquiries/:id` | 問い合わせ詳細 | 必要 |
| GET | `/api/inquiries/:id/messages` | メッセージ一覧取得 | 必要 |
| POST | `/api/inquiries/:id/assign` | 担当取得 | 必要 |
| GET | `/api/operators` | オペレータ一覧取得 | 必要 |
| POST | `/api/operators` | オペレータ追加 | 必要 |
| DELETE | `/api/operators/:id` | オペレータ削除 | 必要 |

### WebSocket
| パス | 説明 | 認証 |
|------|------|------|
| `ws://host/ws/chat/enduser/{inquiry_id}` | エンドユーザ用（初回メッセージ送信時に問い合わせ作成） | 不要 |
| `ws://host/ws/chat/operator/{inquiry_id}` | オペレータ用 | 必要 |

---

## 主要なビジネスルール

1. **担当割り当て排他制御**: 問い合わせの担当者が未設定の場合のみ担当を取得できる
2. **チャット送信権限**: 自分の担当する問い合わせのみメッセージ送信可能
3. **セッション終了条件**: タブ閉じ/タイムアウト(30分)/明示終了の3パターン
4. **ステータス算出**: ログイン中オペレータの視点で動的に算出される

---

## 詳細設計ドキュメント参照

- コンポーネント定義詳細: [components.md](./components.md)
- メソッドシグネチャ: [component-methods.md](./component-methods.md)
- サービスオーケストレーション: [services.md](./services.md)
- 依存関係・データフロー: [component-dependency.md](./component-dependency.md)
