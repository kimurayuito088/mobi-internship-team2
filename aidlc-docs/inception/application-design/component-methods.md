# コンポーネントメソッド

## バックエンド

### BE-001: 認証モジュール (auth)

#### Router (auth_router)
| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/api/auth/login` | オペレータログイン |
| `POST` | `/api/auth/logout` | オペレータログアウト |
| `GET` | `/api/auth/me` | ログイン中のオペレータ情報取得 |

#### Service (AuthService)
| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `login(username, password)` | str, str | Operator | 認証してセッション作成 |
| `logout(session_id)` | str | None | セッション破棄 |
| `get_current_operator(session_id)` | str | Operator | セッションからオペレータ取得 |

#### Repository (AuthRepository)
| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `find_operator_by_username(username)` | str | Operator \| None | ユーザー名でオペレータ検索 |
| `create_session(operator_id)` | int | str | セッション作成、session_id返却 |
| `get_session(session_id)` | str | Session \| None | セッション取得 |
| `delete_session(session_id)` | str | None | セッション削除 |

---

### BE-002: 問い合わせ管理モジュール (inquiry)

#### Router (inquiry_router)
| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/api/inquiries` | 問い合わせ一覧取得（ページング付き） |
| `GET` | `/api/inquiries/:id` | 問い合わせ詳細取得 |
| `GET` | `/api/inquiries/:id/messages` | 問い合わせのメッセージ一覧取得 |
| `POST` | `/api/inquiries/:id/assign` | 問い合わせ担当取得 |

#### Service (InquiryService)
| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `list_inquiries(page, per_page, operator_id)` | int, int, int | PaginatedResult | 一覧取得（ステータス付き） |
| `get_inquiry(inquiry_id)` | int | Inquiry | 詳細取得 |
| `assign_operator(inquiry_id, operator_id)` | int, int | Inquiry | 担当割り当て（排他制御） |

#### Repository (InquiryRepository)
| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `find_all(page, per_page)` | int, int | list[Inquiry], int | ページング付き全件取得 |
| `find_by_id(inquiry_id)` | int | Inquiry \| None | ID検索 |
| `create(inquiry)` | Inquiry | Inquiry | 作成（WebSocket接続時に内部的に呼ばれる） |
| `update_assignment(inquiry_id, operator_id)` | int, int | bool | 担当者更新（排他制御） |

---

### BE-003: チャットモジュール (chat)

#### WebSocket Handler (chat_ws)
| エンドポイント | 説明 |
|--------------|------|
| `ws://host/ws/chat/enduser/{inquiry_id}` | エンドユーザ用WebSocket（初回メッセージ送信時に問い合わせ作成） |
| `ws://host/ws/chat/operator/{inquiry_id}` | オペレータ用WebSocket |

#### Service (ChatService)
| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `send_message(inquiry_id, sender_type, content)` | int, str, str | Message | メッセージ送信・保存・ブロードキャスト |
| `get_messages(inquiry_id)` | int | list[Message] | 問い合わせの全メッセージ取得 |
| `create_inquiry_on_connect()` | - | Inquiry | 初回メッセージ送信時に問い合わせ作成 |

#### Repository (ChatRepository)
| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `save_message(message)` | Message | Message | メッセージ保存 |
| `find_by_inquiry_id(inquiry_id)` | int | list[Message] | 問い合わせIDで検索 |

---

### BE-004: WebSocket接続管理 (connection_manager)

| メソッド | 入力 | 出力 | 説明 |
|---------|------|------|------|
| `connect(websocket, inquiry_id, user_type)` | WebSocket, int, str | None | 接続登録 |
| `disconnect(websocket, inquiry_id)` | WebSocket, int | None | 接続解除 |
| `broadcast(inquiry_id, message)` | int, str | None | 問い合わせグループへブロードキャスト |
| `get_connections(inquiry_id)` | int | list[WebSocket] | 問い合わせの接続一覧取得 |

---

## フロントエンド

### FE-005: 認証コンテキスト (AuthProvider)

| メソッド/状態 | 型 | 説明 |
|-------------|------|------|
| `operator` | Operator \| null | ログイン中のオペレータ情報 |
| `isAuthenticated` | boolean | 認証状態 |
| `login(username, password)` | Promise<void> | ログイン処理 |
| `logout()` | Promise<void> | ログアウト処理 |

### WebSocket フック (useChat)

| メソッド/状態 | 型 | 説明 |
|-------------|------|------|
| `messages` | Message[] | チャットメッセージ一覧 |
| `sendMessage(content)` | (string) => void | メッセージ送信 |
| `isConnected` | boolean | WebSocket接続状態 |
| `connect(inquiryId, userType)` | (number, string) => void | WebSocket接続開始 |
| `disconnect()` | () => void | WebSocket接続終了 |
