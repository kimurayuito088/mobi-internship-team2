# フロントエンドコンポーネント設計

## コンポーネント階層構造

```
App
├── AuthProvider（認証コンテキスト）
│   ├── [Route: /] EndUserChat
│   │   ├── ChatWindow
│   │   │   └── MessageBubble（繰り返し）
│   │   ├── MessageInput
│   │   ├── ConnectionStatus
│   │   └── EndButton
│   │
│   ├── [Route: /operator/login] OperatorLogin
│   │   ├── LoginForm
│   │   └── ErrorMessage
│   │
│   └── [ProtectedRoute: /operator/*]
│       ├── OperatorNav
│       ├── [Route: /operator/inquiries] InquiryList
│       │   ├── InquiryTable
│       │   │   ├── InquiryRow（繰り返し）
│       │   │   │   ├── StatusBadge
│       │   │   │   └── AssignButton（条件付き）
│       │   │   └── EmptyState
│       │   └── Pagination
│       │
│       └── [Route: /operator/inquiries/:id] InquiryDetail
│           ├── InquiryInfo
│           ├── ChatWindow
│           │   └── MessageBubble（繰り返し）
│           └── MessageInput（担当者のみ有効）
│
│       ├── [Route: /operator/users/add] OperatorAdd
│       │   └── OperatorAddForm
│       │
│       └── [Route: /operator/users] OperatorList
│           ├── OperatorAddButton（「+ オペレータを追加」ボタン）
│           ├── OperatorTable
│           │   └── OperatorRow（繰り返し）
│           └── EmptyState
```

---

## ページごとの Props / State 定義

### EndUserChat

**State:**
| 名前 | 型 | 初期値 | 説明 |
|------|------|--------|------|
| messages | Message[] | [] | チャットメッセージ一覧 |
| isConnected | boolean | false | WebSocket接続状態 |
| isClosed | boolean | false | セッション終了フラグ |
| inquiryId | number \| null | null | 問い合わせID |

**使用フック:** useChat

**API連携:**
- WebSocket: `ws://host/ws/chat/enduser/{inquiry_id}`

---

### OperatorLogin

**State:**
| 名前 | 型 | 初期値 | 説明 |
|------|------|--------|------|
| username | string | '' | ユーザー名入力 |
| password | string | '' | パスワード入力 |
| error | string \| null | null | エラーメッセージ |
| isLoading | boolean | false | ログイン処理中フラグ |

**API連携:**
- POST `/api/auth/login`

---

### InquiryList

**State:**
| 名前 | 型 | 初期値 | 説明 |
|------|------|--------|------|
| inquiries | InquiryWithStatus[] | [] | 問い合わせ一覧 |
| currentPage | number | 1 | 現在のページ |
| totalPages | number | 0 | 総ページ数 |
| isLoading | boolean | false | データ取得中フラグ |
| hasNewInquiry | boolean | false | 新着問い合わせ通知フラグ |

**API連携:**
- GET `/api/inquiries?page={page}&per_page=10`
- POST `/api/inquiries/:id/assign`

---

### InquiryDetail

**State:**
| 名前 | 型 | 初期値 | 説明 |
|------|------|--------|------|
| inquiry | Inquiry \| null | null | 問い合わせ情報 |
| messages | Message[] | [] | メッセージ一覧 |
| isConnected | boolean | false | WebSocket接続状態 |
| isClosed | boolean | false | 問い合わせ終了フラグ |
| canSend | boolean | false | メッセージ送信可能フラグ |

**使用フック:** useChat

**API連携:**
- GET `/api/inquiries/:id`
- GET `/api/inquiries/:id/messages`
- WebSocket: `ws://host/ws/chat/operator/{inquiry_id}`

---

## 共通コンポーネント Props

### ChatWindow
| Props | 型 | 説明 |
|-------|------|------|
| messages | Message[] | 表示するメッセージ一覧 |
| currentUserType | 'enduser' \| 'operator' | メッセージの左右配置判定用 |

### MessageInput
| Props | 型 | 説明 |
|-------|------|------|
| onSend | (content: string) => void | 送信コールバック |
| disabled | boolean | 無効状態（終了済み/担当外） |
| placeholder | string | プレースホルダーテキスト |

### MessageBubble
| Props | 型 | 説明 |
|-------|------|------|
| message | Message | メッセージデータ |
| isOwn | boolean | 自分のメッセージかどうか |
| viewMode | 'enduser' \| 'operator' | 表示モード（エンドユーザ画面ではオペレータ名の代わりに「🎧 サポート」を表示） |

### StatusBadge
| Props | 型 | 説明 |
|-------|------|------|
| status | 'inputting' \| 'waiting' \| 'mine' \| 'others' \| 'closed' | 表示ステータス |

**表示ラベル:**
| status | ラベル |
|--------|--------|
| inputting | 入力中 |
| waiting | 担当者未決定 |
| mine | 自分の担当 |
| others | 担当外 |
| closed | 終了 |

### AssignButton
| Props | 型 | 説明 |
|-------|------|------|
| inquiryId | number | 問い合わせID |
| onAssign | (inquiryId: number) => void | 担当取得コールバック |
| disabled | boolean | 無効状態 |

### Pagination
| Props | 型 | 説明 |
|-------|------|------|
| currentPage | number | 現在のページ |
| totalPages | number | 総ページ数 |
| onPageChange | (page: number) => void | ページ変更コールバック |

### ConnectionStatus
| Props | 型 | 説明 |
|-------|------|------|
| isConnected | boolean | 接続状態 |

### EndButton
| Props | 型 | 説明 |
|-------|------|------|
| onEnd | () => void | 終了コールバック |
| disabled | boolean | 無効状態 |

---

## ユーザーインタラクションフロー

### エンドユーザのフロー
```
1. ページアクセス (/)
2. WebSocket接続確立
3. メッセージ入力 → 送信（初回送信時に問い合わせ自動作成）
4. オペレータからの返信受信
5. 会話継続 or 「終了」ボタン押下
6. セッション終了 → 送信無効化
```

### オペレータのフロー
```
1. ログイン画面 (/operator/login) → ID/PW入力 → ログイン
2. 問い合わせ一覧 (/operator/inquiries) 表示
3. 「担当者未決定」の問い合わせを選択 → 「担当する」ボタン押下
4. 問い合わせ詳細 (/operator/inquiries/:id) に遷移
5. WebSocket接続確立
6. エンドユーザとのチャット開始
7. セッション終了 → システムメッセージ表示 → 送信無効化
8. 一覧に戻る or ログアウト
```

---

## フォームバリデーション

### ログインフォーム
| フィールド | バリデーション | エラーメッセージ |
|-----------|--------------|----------------|
| username | 必須 | 「ユーザー名を入力してください」 |
| password | 必須 | 「パスワードを入力してください」 |
| API応答 | 401 | 「ユーザー名またはパスワードが正しくありません」 |

### メッセージ入力
| フィールド | バリデーション | エラーメッセージ |
|-----------|--------------|----------------|
| content | 必須、空白のみ不可 | （送信ボタンを無効化で対応） |

### オペレータ追加フォーム
| フィールド | バリデーション | エラーメッセージ |
|-----------|--------------|----------------|
| username | 必須 | 「ユーザー名を入力してください」 |
| display_name | 必須 | 「表示名を入力してください」 |
| API応答 | 409 | 「このユーザー名は既に使用されています」 |

---

## 型定義（TypeScript）

```typescript
// ステータス定数
const INQUIRY_STATUS = {
  WAITING: 0,
  ACTIVE: 1,
  CLOSED: 2,
  INPUTTING: 3,
} as const;

const SENDER_TYPE = {
  ENDUSER: 0,
  OPERATOR: 1,
  SYSTEM: 2,
} as const;

// 基本型
interface Operator {
  id: number;
  username: string;
  display_name: string;
}

interface Message {
  id: number;
  inquiry_id: number;
  sender_type: number; // 0:enduser, 1:operator, 2:system
  sender_name: string | null;
  content: string;
  created_at: string; // ISO 8601
}

interface Inquiry {
  id: number;
  status: number; // 0:waiting, 1:active, 2:closed, 3:inputting
  assigned_operator_id: number | null;
  created_at: string;
  closed_at: string | null;
}

// 表示用拡張型
type DisplayStatus = 'inputting' | 'waiting' | 'mine' | 'others' | 'closed';

interface InquiryWithStatus extends Inquiry {
  display_status: DisplayStatus;
}

// ページングレスポンス
interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}
```
