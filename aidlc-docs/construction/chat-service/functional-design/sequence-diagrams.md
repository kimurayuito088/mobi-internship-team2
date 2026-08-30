# シーケンス図

## 1. オペレータログイン

```mermaid
sequenceDiagram
    actor OP as オペレータ
    participant FE as OperatorLogin
    participant AR as auth_router
    participant AS as AuthService
    participant AREP as AuthRepository
    participant DB as SQLite

    OP->>FE: ユーザー名・パスワード入力
    FE->>AR: POST /api/auth/login
    AR->>AS: login(username, password)
    AS->>AREP: find_operator_by_username(username)
    AREP->>DB: SELECT * FROM operators WHERE username = ?
    DB-->>AREP: Operator or None
    alt オペレータ未存在
        AREP-->>AS: None
        AS-->>AR: 認証失敗エラー
        AR-->>FE: 401 Unauthorized
        FE-->>OP: エラーメッセージ表示
    else パスワード不一致
        AS->>AS: bcrypt.verify(password, hash)
        AS-->>AR: 認証失敗エラー
        AR-->>FE: 401 Unauthorized
        FE-->>OP: エラーメッセージ表示
    else 認証成功
        AS->>AS: bcrypt.verify(password, hash) = True
        AS->>AREP: create_session(operator_id)
        AREP->>AREP: session_id = uuid4()
        AREP->>DB: INSERT INTO sessions (id, operator_id, expires_at)
        DB-->>AREP: OK
        AREP-->>AS: session_id
        AS-->>AR: Operator情報
        AR-->>FE: 200 OK + Set-Cookie: session_id
        FE->>FE: AuthContext更新
        FE-->>OP: 問い合わせ一覧に遷移
    end
```

## 2. 問い合わせ一覧取得（ページング付き）

```mermaid
sequenceDiagram
    actor OP as オペレータ
    participant FE as InquiryList
    participant MW as auth_middleware
    participant IR as inquiry_router
    participant IS as InquiryService
    participant IREP as InquiryRepository
    participant DB as SQLite

    OP->>FE: 問い合わせ一覧画面表示
    FE->>IR: GET /api/inquiries?page=1&per_page=10
    IR->>MW: セッション検証
    MW->>DB: SELECT * FROM sessions WHERE id = ?
    DB-->>MW: Session
    MW-->>IR: operator_id = 1
    IR->>IS: list_inquiries(page=1, per_page=10, operator_id=1)
    IS->>IREP: find_all(page=1, per_page=10)
    IREP->>DB: SELECT * FROM inquiries LIMIT 10 OFFSET 0
    DB-->>IREP: list[Inquiry], total_count
    IREP-->>IS: inquiries, total
    IS->>IS: 各inquiryの表示ステータス算出
    IS-->>IR: PaginatedResult
    IR-->>FE: 200 OK {items, page, per_page, total, total_pages}
    FE-->>OP: 一覧表示（ステータスバッジ付き）
```

## 3. 問い合わせ担当取得（排他制御）

```mermaid
sequenceDiagram
    actor OP as オペレータ
    participant FE as InquiryList
    participant IR as inquiry_router
    participant IS as InquiryService
    participant IREP as InquiryRepository
    participant DB as SQLite

    OP->>FE: 「担当する」ボタン押下
    FE->>IR: POST /api/inquiries/5/assign
    IR->>IS: assign_operator(inquiry_id=5, operator_id=1)
    IS->>IREP: update_assignment(inquiry_id=5, operator_id=1)
    IREP->>DB: UPDATE inquiries SET assigned_operator_id=1, status=1<br/>WHERE id=5 AND assigned_operator_id IS NULL AND status=0
    alt 更新成功（affected_rows = 1）
        DB-->>IREP: OK (1 row affected)
        IREP-->>IS: True
        IS-->>IR: 更新されたInquiry
        IR-->>FE: 200 OK
        FE-->>OP: ステータス「自分の担当」に更新
    else 排他制御失敗（他のオペレータが先に取得）
        DB-->>IREP: OK (0 rows affected)
        IREP-->>IS: False
        IS-->>IR: ConflictError
        IR-->>FE: 409 Conflict
        FE-->>OP: エラーメッセージ表示
    end
```

## 4. エンドユーザ チャット開始

```mermaid
sequenceDiagram
    actor EU as エンドユーザ
    participant FE as EndUserChat
    participant CW as chat_ws
    participant CS as ChatService
    participant IS as InquiryService
    participant IREP as InquiryRepository
    participant CM as ConnectionManager
    participant DB as SQLite

    EU->>FE: ページアクセス (/)
    FE->>CW: WebSocket接続確立
    CW->>CS: create_inquiry_on_connect()
    CS->>IS: create_inquiry()
    IS->>IREP: create(Inquiry(status=0))
    IREP->>DB: INSERT INTO inquiries (status) VALUES (0)
    DB-->>IREP: inquiry_id = 10
    IREP-->>IS: Inquiry(id=10)
    IS-->>CS: Inquiry(id=10)
    CS->>CM: connect(websocket, inquiry_id=10, user_type=enduser)
    CM-->>CS: OK
    CS-->>CW: inquiry_id = 10
    CW-->>FE: 接続確立完了 + inquiry_id
    FE-->>EU: チャット画面表示（入力可能）
```

## 5. メッセージ送受信

```mermaid
sequenceDiagram
    actor EU as エンドユーザ
    participant FE_EU as EndUserChat
    participant CW as chat_ws
    participant CS as ChatService
    participant CREP as ChatRepository
    participant CM as ConnectionManager
    participant FE_OP as InquiryDetail
    actor OP as オペレータ
    participant DB as SQLite

    EU->>FE_EU: メッセージ入力・送信
    FE_EU->>CW: WebSocket: {type: message, content: "こんにちは"}
    CW->>CS: send_message(inquiry_id=10, sender_type=0, content)
    CS->>CS: ステータス確認（status != 2）
    CS->>CREP: save_message(Message)
    CREP->>DB: INSERT INTO messages (inquiry_id, sender_type, content)
    DB-->>CREP: message_id
    CREP-->>CS: Message
    CS->>CM: broadcast(inquiry_id=10, message)
    CM-->>FE_EU: WebSocket: Message（自分のメッセージ確認）
    CM-->>FE_OP: WebSocket: Message（エンドユーザからの新着）
    FE_EU-->>EU: メッセージ表示（右側）
    FE_OP-->>OP: メッセージ表示（左側）

    OP->>FE_OP: 返信メッセージ入力・送信
    FE_OP->>CW: WebSocket: {type: message, content: "お問い合わせありがとうございます"}
    CW->>CS: send_message(inquiry_id=10, sender_type=1, content)
    CS->>CS: 権限確認（assigned_operator_id == operator_id）
    CS->>CS: ステータス確認（status != 2）
    CS->>CREP: save_message(Message)
    CREP->>DB: INSERT INTO messages
    DB-->>CREP: message_id
    CREP-->>CS: Message
    CS->>CM: broadcast(inquiry_id=10, message)
    CM-->>FE_OP: WebSocket: Message（自分のメッセージ確認）
    CM-->>FE_EU: WebSocket: Message（オペレータからの返信）
    FE_OP-->>OP: メッセージ表示（右側）
    FE_EU-->>EU: メッセージ表示（左側）
```

## 6. セッション終了（明示的な終了ボタン）

```mermaid
sequenceDiagram
    actor EU as エンドユーザ
    participant FE_EU as EndUserChat
    participant CW as chat_ws
    participant CS as ChatService
    participant IREP as InquiryRepository
    participant CREP as ChatRepository
    participant CM as ConnectionManager
    participant FE_OP as InquiryDetail
    actor OP as オペレータ
    participant DB as SQLite

    EU->>FE_EU: 「終了」ボタン押下
    FE_EU->>CW: WebSocket: {type: close}
    CW->>CS: close_inquiry(inquiry_id=10)
    CS->>IREP: update_status(inquiry_id=10, status=2)
    IREP->>DB: UPDATE inquiries SET status=2, closed_at=NOW() WHERE id=10
    DB-->>IREP: OK
    CS->>CREP: save_message(system_message)
    CREP->>DB: INSERT INTO messages (sender_type=2, content="ユーザーが退出しました")
    DB-->>CREP: OK
    CS->>CM: broadcast(inquiry_id=10, system_message)
    CM-->>FE_OP: WebSocket: システムメッセージ
    FE_OP-->>OP: 「ユーザーが退出しました」表示 + 送信無効化
    CS->>CM: disconnect(enduser_ws, inquiry_id=10)
    CM-->>FE_EU: WebSocket: close
    FE_EU-->>EU: 「チャットが終了しました」表示 + 送信無効化
```

## 7. セッションタイムアウト

```mermaid
sequenceDiagram
    participant BG as バックグラウンドタスク<br/>(60秒間隔)
    participant CM as ConnectionManager
    participant CS as ChatService
    participant IREP as InquiryRepository
    participant CREP as ChatRepository
    participant FE_EU as EndUserChat
    participant FE_OP as InquiryDetail
    participant DB as SQLite

    BG->>CM: check_timeouts()
    CM->>CM: 最終アクティビティから30分経過の接続を検出
    CM-->>BG: timeout_connections = [inquiry_id=10]

    BG->>CS: close_inquiry(inquiry_id=10)
    CS->>IREP: update_status(inquiry_id=10, status=2)
    IREP->>DB: UPDATE inquiries SET status=2, closed_at=NOW()
    DB-->>IREP: OK
    CS->>CREP: save_message(system_message)
    CREP->>DB: INSERT INTO messages (sender_type=2, content="タイムアウトにより終了しました")
    DB-->>CREP: OK
    CS->>CM: broadcast(inquiry_id=10, system_message)
    CM-->>FE_OP: WebSocket: システムメッセージ
    CM-->>FE_EU: WebSocket: タイムアウト通知
    CS->>CM: disconnect(enduser_ws, inquiry_id=10)
    FE_EU->>FE_EU: 送信無効化
    FE_OP->>FE_OP: 送信無効化
```

## 8. オペレータ ログアウト

```mermaid
sequenceDiagram
    actor OP as オペレータ
    participant FE as OperatorNav
    participant AR as auth_router
    participant AS as AuthService
    participant AREP as AuthRepository
    participant DB as SQLite

    OP->>FE: ログアウトボタン押下
    FE->>AR: POST /api/auth/logout
    AR->>AS: logout(session_id)
    AS->>AREP: delete_session(session_id)
    AREP->>DB: DELETE FROM sessions WHERE id = ?
    DB-->>AREP: OK
    AREP-->>AS: OK
    AS-->>AR: OK
    AR-->>FE: 200 OK + Set-Cookie: clear
    FE->>FE: AuthContext クリア
    FE-->>OP: ログイン画面に遷移
```


## 9. オペレータ追加

```mermaid
sequenceDiagram
    actor OP as オペレータ
    participant FE as OperatorAdd
    participant OR as operator_router
    participant OS as OperatorService
    participant OREP as OperatorRepository
    participant DB as SQLite

    OP->>FE: username, display_name 入力
    FE->>OR: POST /api/operators {username, display_name}
    OR->>OS: create_operator(username, display_name)
    OS->>OREP: find_by_username(username)
    OREP->>DB: SELECT * FROM operators WHERE username = ?
    DB-->>OREP: result
    alt username 重複あり
        OREP-->>OS: Operator (既存)
        OS-->>OR: ConflictError
        OR-->>FE: 409 Conflict
        FE-->>OP: 「このユーザー名は既に使用されています」
    else username 利用可能
        OREP-->>OS: None
        OS->>OS: password = secrets.token (英数字12文字)
        OS->>OS: password_hash = bcrypt.hash(password)
        OS->>OREP: create(Operator{username, password_hash, display_name})
        OREP->>DB: INSERT INTO operators
        DB-->>OREP: OK
        OREP-->>OS: Operator
        OS-->>OR: {operator, password}
        OR-->>FE: 201 Created {operator, generated_password}
        FE-->>OP: パスワード表示（コピー可能）
    end
```

## 10. オペレータ削除

```mermaid
sequenceDiagram
    actor OP as オペレータ
    participant FE as OperatorList
    participant OR as operator_router
    participant OS as OperatorService
    participant OREP as OperatorRepository
    participant DB as SQLite

    OP->>FE: 削除ボタン押下（target_id=3）
    FE->>OR: DELETE /api/operators/3
    OR->>OS: delete_operator(target_id=3, current_operator_id=1)
    alt 自分自身を削除しようとした場合
        OS-->>OR: ForbiddenError
        OR-->>FE: 403 Forbidden
        FE-->>OP: エラーメッセージ
    else 他のオペレータを削除
        OS->>OREP: delete(target_id=3)
        OREP->>DB: DELETE FROM sessions WHERE operator_id = 3
        DB-->>OREP: OK
        OREP->>DB: DELETE FROM operators WHERE id = 3
        DB-->>OREP: OK
        OREP-->>OS: OK
        OS-->>OR: OK
        OR-->>FE: 204 No Content
        FE-->>OP: 一覧更新
    end
```
