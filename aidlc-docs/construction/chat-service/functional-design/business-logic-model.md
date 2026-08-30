# ビジネスロジックモデル

## 1. 認証フロー

### ログイン
```
1. オペレータがユーザー名とパスワードを入力
2. AuthService.login(username, password) を呼び出し
3. AuthRepository.find_operator_by_username(username) でオペレータ検索
4. オペレータ未存在 → 認証失敗エラー返却
5. bcrypt でパスワードハッシュ照合
6. パスワード不一致 → 認証失敗エラー返却
7. AuthRepository.create_session(operator_id) でセッション作成
   - session_id = UUID v4 を生成
   - expires_at = 現在時刻 + 8時間
8. レスポンスの Set-Cookie ヘッダーに session_id を設定
9. オペレータ情報を返却
```

### ログアウト
```
1. リクエストのCookieから session_id を取得
2. AuthRepository.delete_session(session_id) でセッション削除
3. レスポンスの Set-Cookie でCookieをクリア
```

### 認証確認（ミドルウェア）
```
1. リクエストのCookieから session_id を取得
2. session_id が無い → 未認証エラー(401)
3. AuthRepository.get_session(session_id) でセッション取得
4. セッション未存在 or 有効期限切れ → 未認証エラー(401)
5. セッションからoperator_idを取得しリクエストコンテキストに設定
```

---

## 2. 問い合わせライフサイクル

### 問い合わせ作成（初回メッセージ送信時）
```
1. エンドユーザがWebSocket接続を確立（DB書き込みなし）
2. エンドユーザが最初のメッセージを送信
3. ChatService.create_inquiry_on_connect() を呼び出し
4. Inquiry を status=0 (WAITING) で作成
5. inquiry_id を返却しクライアントに通知
6. メッセージを保存・ブロードキャスト
```

- `InquiryRepository.create()` は引数を省略すると status=0 (WAITING) で作成する（DBの `DEFAULT 0` も WAITING のまま）
- status=3 (INPUTTING) で作成する場合は `InquiryRepository.create(initial_status=InquiryStatus.INPUTTING)` のように明示指定する
- 初期ステータスとして指定できるのは WAITING と INPUTTING のみ。ACTIVE・CLOSED・不明値は `ValueError` を送出し INSERT しない
- WebSocket接続時にINPUTTINGの問い合わせを自動作成する処理は未実装

### 問い合わせ担当取得
```
1. オペレータが「担当する」ボタンを押下
2. InquiryService.assign_operator(inquiry_id, operator_id) を呼び出し
3. InquiryRepository.find_by_id(inquiry_id) で問い合わせ取得
4. inquiry.status が 0 (WAITING) でない → ConflictError（排他制御）
5. inquiry.assigned_operator_id が NULL でない → ConflictError（排他制御）
6. InquiryRepository.update_assignment(inquiry_id, operator_id) で更新
   - status を 1 (ACTIVE) に変更
   - assigned_operator_id を設定
7. 更新された Inquiry を返却
```

### 問い合わせ終了
```
1. セッション終了イベント発生（タブ閉じ / タイムアウト / 明示終了）
2. inquiry.status を 2 (CLOSED) に更新
3. inquiry.closed_at に現在時刻を設定
4. システムメッセージ「ユーザーが退出しました」をDBに保存（sender_type=2 (SYSTEM)）
5. オペレータのWebSocket接続にシステムメッセージをブロードキャスト
6. エンドユーザのWebSocket接続を切断
```

### 問い合わせ一覧取得
```
1. InquiryService.list_inquiries(page, per_page, operator_id) を呼び出し
2. InquiryRepository.find_all(page, per_page) で全件取得（ORDER BY id DESC）
3. 各問い合わせに対して表示ステータスを算出（判定順は上から順に評価）:
   - status == 2 (CLOSED) → 「終了」(closed)
   - status == 3 (INPUTTING) → 「入力中」(inputting)
   - status == 0 (WAITING) → 「担当者未決定」(waiting)
   - assigned_operator_id == operator_id → 「自分の担当」(mine)
   - 上記以外 → 「自分の担当外」(others)
4. ページングメタ情報と共に返却
```

- INPUTTING は担当判定より前に評価するため、assigned_operator_id の値に関係なく `others` にはならない
- 一覧画面の3枠レイアウトやグループ一覧APIは未実装

---

## 3. チャットメッセージフロー

### エンドユーザからのメッセージ送信
```
1. エンドユーザがWebSocket経由でメッセージ送信
2. ChatService.send_message(inquiry_id, 0 (ENDUSER), content) を呼び出し
3. 問い合わせのステータス確認:
   - status == 2 (CLOSED) → メッセージ拒否
4. Message エンティティを作成（sender_type=0 (ENDUSER)）
5. ChatRepository.save_message(message) でDB保存
6. ConnectionManager.broadcast(inquiry_id, message) で全接続に配信
```

### オペレータからのメッセージ送信
```
1. オペレータがWebSocket経由でメッセージ送信
2. ChatService.send_message(inquiry_id, 1 (OPERATOR), content) を呼び出し
3. 権限確認:
   - 問い合わせの assigned_operator_id が送信者と一致するか確認
   - 不一致 → メッセージ拒否（送信権限エラー）
4. 問い合わせのステータス確認:
   - status == 2 (CLOSED) → メッセージ拒否
5. Message エンティティを作成（sender_type=1 (OPERATOR), sender_name=operator.display_name）
6. ChatRepository.save_message(message) でDB保存
7. ConnectionManager.broadcast(inquiry_id, message) で全接続に配信
```

### メッセージ履歴取得
```
1. GET /api/inquiries/:id/messages を呼び出し
2. 認証確認（オペレータのみ）
3. ChatService.get_messages(inquiry_id) を呼び出し
4. ChatRepository.find_by_inquiry_id(inquiry_id) で全メッセージ取得
5. メッセージ一覧を返却
```

---

## 4. セッション管理フロー

### セッション終了: 明示的な「終了」ボタン
```
1. エンドユーザが「終了」ボタンを押下
2. WebSocket経由で終了イベントをサーバーに送信
3. サーバーが問い合わせ終了処理を実行（上記「問い合わせ終了」フロー）
4. エンドユーザのWebSocket接続を切断
5. エンドユーザ画面に「チャットが終了しました」を表示
```

### セッション終了: タブ閉じ
```
1. ブラウザのタブが閉じられる
2. WebSocket接続が切断される（onclose イベント）
3. サーバーが切断を検知
4. 問い合わせ終了処理を実行
```

### セッション終了: タイムアウト（30分）
```
1. サーバー側でWebSocket接続のハートビートを監視
2. 最後のメッセージ送信 or WebSocketのpingから30分経過を検知
3. サーバーからタイムアウト通知をWebSocket経由で送信
4. 問い合わせ終了処理を実行
5. WebSocket接続を切断
```

### タイムアウト実装方式
- 各問い合わせの最終アクティビティ時刻を `ConnectionManager` でインメモリ管理
- 定期的なチェック（例: 60秒間隔のバックグラウンドタスク）でタイムアウトを検知
- タイムアウト閾値は設定値として管理（デフォルト30分、変更容易に）


---

## 5. オペレータ管理フロー

### オペレータ追加
```
1. ログイン済みオペレータがオペレータ管理画面の「+ オペレータを追加」ボタンを押下
2. username（ログインID）と display_name（表示名）を入力
3. POST /api/operators を呼び出し
4. OperatorService.create_operator(username, display_name) を呼び出し
5. username の重複チェック:
   - 重複あり → ConflictError（409）を返却
6. パスワード自動生成（英数字12文字ランダム）
7. bcrypt でパスワードハッシュ化
8. OperatorRepository.create(operator) でDB保存
9. 生成されたパスワード（平文）をレスポンスとして返却
10. フロントエンドでパスワードを画面に表示
```

### オペレータ一覧取得
```
1. GET /api/operators を呼び出し
2. OperatorService.list_operators() を呼び出し
3. OperatorRepository.find_all() で全件取得
4. オペレータ一覧を返却（パスワードハッシュは含めない）
```

### オペレータ削除
```
1. ログイン済みオペレータが削除ボタンを押下
2. DELETE /api/operators/:id を呼び出し
3. OperatorService.delete_operator(target_id, current_operator_id) を呼び出し
4. 自分自身の削除チェック:
   - target_id == current_operator_id → ForbiddenError（403）
5. OperatorRepository.delete(target_id) でDB削除
6. 成功レスポンスを返却
```
