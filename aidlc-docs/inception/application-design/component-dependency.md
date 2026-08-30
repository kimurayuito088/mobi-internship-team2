# コンポーネント依存関係

## 依存関係マトリクス

### バックエンド依存関係

| コンポーネント | 依存先 | 依存タイプ |
|--------------|--------|-----------|
| auth_router | AuthService | 直接呼び出し |
| AuthService | AuthRepository | 直接呼び出し |
| AuthRepository | database | DB接続 |
| inquiry_router | InquiryService | 直接呼び出し |
| inquiry_router | AuthService | 認証ミドルウェア |
| InquiryService | InquiryRepository | 直接呼び出し |
| InquiryRepository | database | DB接続 |
| chat_ws | ChatService | 直接呼び出し |
| chat_ws | AuthService | オペレータ認証確認 |
| ChatService | ChatRepository | 直接呼び出し |
| ChatService | ConnectionManager | WebSocket管理 |
| ChatService | InquiryService | 問い合わせ作成委譲 |
| ChatRepository | database | DB接続 |

### フロントエンド依存関係

| コンポーネント | 依存先 | 依存タイプ |
|--------------|--------|-----------|
| OperatorLogin | AuthProvider | 認証状態管理 |
| InquiryList | AuthProvider | 認証情報参照 |
| InquiryDetail | AuthProvider | 認証情報参照 |
| InquiryDetail | useChat | WebSocket通信 |
| EndUserChat | useChat | WebSocket通信 |
| AppShell | AuthProvider | 認証ガード |

---

## データフロー図

### エンドユーザのチャットフロー

```
+------------+     WebSocket      +-----------+     save      +--------+
| EndUser    | -----------------> | chat_ws   | ----------->  | SQLite |
| Browser    | <----------------- |           | <-----------  |        |
+------------+     broadcast      +-----+-----+     query     +--------+
                                        |
                                        v
                                  +-----+-----+
                                  | Connection|
                                  | Manager   |
                                  +-----------+
```

### オペレータのチャットフロー

```
+------------+     WebSocket      +-----------+     save      +--------+
| Operator   | -----------------> | chat_ws   | ----------->  | SQLite |
| Browser    | <----------------- |    +      | <-----------  |        |
+------------+     broadcast      | auth check|     query     +--------+
                                  +-----+-----+
                                        |
                                        v
                                  +-----+-----+
                                  | Connection|
                                  | Manager   |
                                  +-----------+
```

### 問い合わせ担当取得フロー

```
+------------+      POST         +----------+     update    +--------+
| Operator   | ----------------> | inquiry  | ----------->  | SQLite |
| Browser    | <---------------- | _router  | <-----------  |        |
+------------+    response       +----+-----+    result     +--------+
                                      |
                                      v
                                 +----+-----+
                                 | Inquiry  |
                                 | Service  |
                                 | (排他    |
                                 |  制御)   |
                                 +----------+
```

### 認証フロー

```
+------------+      POST         +----------+     query     +--------+
| Operator   | ----------------> | auth     | ----------->  | SQLite |
| Browser    | <---------------- | _router  | <-----------  |        |
+------------+  Set-Cookie       +----+-----+    result     +--------+
                                      |
                                      v
                                 +----+-----+
                                 | Auth     |
                                 | Service  |
                                 | (PW hash |
                                 |  検証)   |
                                 +----------+
```
