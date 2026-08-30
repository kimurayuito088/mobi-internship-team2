# サービス定義

## サービス一覧

| サービス名 | 責務 | 依存先 |
|-----------|------|--------|
| AuthService | オペレータ認証・セッション管理 | AuthRepository |
| InquiryService | 問い合わせ管理・担当割り当て | InquiryRepository |
| ChatService | メッセージ送受信・永続化 | ChatRepository, ConnectionManager |

---

## AuthService

### 責務
- オペレータのログイン認証（ID/PWの検証）
- セッションの作成・破棄
- 認証状態の確認

### オーケストレーション
```
1. ログインリクエスト受信
2. AuthRepository.find_operator_by_username() でオペレータ検索
3. パスワードハッシュ照合
4. 認証成功: AuthRepository.create_session() でセッション作成
5. セッションIDをクッキーに設定して返却
```

### エラーハンドリング
- ユーザー未存在: 認証失敗エラー
- パスワード不一致: 認証失敗エラー
- セッション無効: 未認証エラー

---

## InquiryService

### 責務
- 問い合わせ一覧の取得（ページング・ステータス付き）
- 担当者の割り当て（排他制御）
- 問い合わせの作成（ChatServiceからの内部委譲）

### オーケストレーション

#### 一覧取得
```
1. 一覧取得リクエスト受信（page, per_page, operator_id）
2. InquiryRepository.find_all() で全件取得
3. 各問い合わせに対してステータスを算出:
   - assigned_operator_id == null → 「担当者未決定」
   - assigned_operator_id == operator_id → 「自分の担当」
   - assigned_operator_id != operator_id → 「自分の担当外」
4. ページングメタ情報と共に返却
```

#### 担当割り当て
```
1. 担当取得リクエスト受信（inquiry_id, operator_id）
2. InquiryRepository.find_by_id() で問い合わせ取得
3. 既に担当者がいる場合はエラー（排他制御）
4. InquiryRepository.update_assignment() で担当者更新
5. 更新された問い合わせを返却
```

### エラーハンドリング
- 問い合わせ未存在: NotFoundエラー
- 既に担当者あり: ConflictErrorエラー（排他制御）

---

## ChatService

### 責務
- WebSocket経由のリアルタイムメッセージ送受信
- メッセージのデータベースへの永続化
- 問い合わせ単位でのメッセージブロードキャスト

### オーケストレーション

#### メッセージ送信
```
1. WebSocketでメッセージ受信
2. ChatRepository.save_message() でDB保存
3. ConnectionManager.broadcast() で同じ問い合わせの全接続に送信
```

#### WebSocket接続管理
```
エンドユーザ接続:
1. WebSocket接続確立
2. ConnectionManager.connect() で登録
3. 問い合わせが存在しない場合は新規作成（InquiryServiceに委譲）
4. 切断時: ConnectionManager.disconnect() + セッション終了処理

オペレータ接続:
1. 認証確認（セッション検証）
2. 問い合わせの担当者確認（自分の担当でなければ拒否）
3. ConnectionManager.connect() で登録
4. 切断時: ConnectionManager.disconnect()
```

### エラーハンドリング
- 未認証のオペレータ: 接続拒否
- 担当外の問い合わせ: 接続拒否（閲覧のみ可、メッセージ送信不可）
- WebSocket接続エラー: 切断処理

---

## サービス間通信パターン

```
+------------------+
|   auth_router    |
+--------+---------+
         |
         v
+------------------+
|   AuthService    |
+--------+---------+
         |
         v
+------------------+
|  AuthRepository  |
+------------------+

+-------------------+
|  inquiry_router   |
+---------+---------+
          |
          v
+-------------------+        +--------------------+
|  InquiryService   | -----> | InquiryRepository  |
+-------------------+        +--------------------+

+-------------------+
|     chat_ws       |
+---------+---------+
          |
          v
+-------------------+        +--------------------+
|   ChatService     | -----> |  ChatRepository    |
+---------+---------+        +--------------------+
          |
          v
+-------------------+
| ConnectionManager |
+-------------------+
```

通信パターン:
- Router/WebSocket Handler → Service: 直接メソッド呼び出し
- Service → Repository: 直接メソッド呼び出し
- Service → ConnectionManager: 直接メソッド呼び出し
- ChatService → InquiryService: 新規問い合わせ作成時のみ委譲
