# ユニット定義

## ユニット構成

本プロジェクトは**単一ユニット**として開発する。フロントエンド（React）とバックエンド（FastAPI）を1つのユニットにまとめ、一括で設計・実装を行う。

---

## Unit-001: チャットサービス（chat-service）

| 項目 | 内容 |
|------|------|
| ユニット名 | chat-service |
| タイプ | フルスタックアプリケーション（モノリス） |
| 責務 | エンドユーザ/オペレータ向けチャットサービスの全機能 |
| 開発順序 | フロントエンド先行（UI → バックエンド） |

### 含まれるコンポーネント

**フロントエンド:**
- FE-001: EndUserChat
- FE-002: OperatorLogin
- FE-003: InquiryList
- FE-004: InquiryDetail
- FE-005: AppShell
- FE-006: OperatorAdd
- FE-007: OperatorList

**バックエンド:**
- BE-001: auth
- BE-002: inquiry
- BE-003: chat
- BE-004: connection_manager
- BE-005: database
- BE-006: operator

---

## 開発順序（フロントエンド先行）

### Phase 1: フロントエンド実装
- UI・画面遷移を先に実装
- モックデータで動作確認
- 画面レイアウト・コンポーネント構成の確定

### Phase 2: バックエンド実装
- REST API エンドポイントの実装
- WebSocket ハンドラーの実装
- SQLite データベース・リポジトリの実装
- フロントエンドとの結合

---

## コード構成戦略（Greenfield）

```text
/
├── frontend/                    # React (TypeScript) フロントエンド
│   ├── public/
│   ├── src/
│   │   ├── components/          # 共通UIコンポーネント
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── AssignButton.tsx
│   │   │   ├── ConnectionStatus.tsx
│   │   │   ├── EndButton.tsx
│   │   │   ├── OperatorNav.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── pages/               # ページコンポーネント
│   │   │   ├── EndUserChat.tsx
│   │   │   ├── OperatorLogin.tsx
│   │   │   ├── InquiryList.tsx
│   │   │   ├── InquiryDetail.tsx
│   │   │   ├── OperatorAdd.tsx
│   │   │   └── OperatorList.tsx
│   │   ├── contexts/            # React Context
│   │   │   └── AuthContext.tsx
│   │   ├── hooks/               # カスタムフック
│   │   │   └── useChat.ts
│   │   ├── types/               # 型定義
│   │   │   └── index.ts
│   │   ├── constants.ts         # 定数定義
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/                     # Python FastAPI バックエンド
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI アプリエントリポイント
│   │   ├── config.py            # 設定値管理
│   │   ├── database.py          # DB接続・マイグレーション
│   │   ├── models.py            # dataclass モデル定義
│   │   ├── schemas.py           # Pydantic スキーマ
│   │   ├── routers/             # APIルーター
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── inquiry.py
│   │   │   └── operator.py
│   │   ├── services/            # ビジネスロジック
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── inquiry_service.py
│   │   │   ├── chat_service.py
│   │   │   └── operator_service.py
│   │   ├── repositories/        # データアクセス（生sqlite3使用）
│   │   │   ├── __init__.py
│   │   │   ├── auth_repository.py
│   │   │   ├── inquiry_repository.py
│   │   │   ├── chat_repository.py
│   │   │   └── operator_repository.py
│   │   ├── websocket/           # WebSocket ハンドラー
│   │   │   ├── __init__.py
│   │   │   ├── chat_ws.py
│   │   │   └── connection_manager.py
│   │   └── middleware/          # ミドルウェア
│   │       ├── __init__.py
│   │       └── auth_middleware.py
│   ├── tests/                   # テスト
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_inquiry.py
│   │   ├── test_chat.py
│   │   └── test_operator.py
│   └── requirements.txt
│
├── aidlc-docs/                  # AI-DLC ドキュメント（コードではない）
├── setup.sh                     # 環境セットアップスクリプト
├── .gitignore
└── README.md
```
