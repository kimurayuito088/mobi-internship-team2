// 問い合わせステータスコード
export const INQUIRY_STATUS = {
  WAITING: 0,
  ACTIVE: 1,
  CLOSED: 2,
  // 既存データとの互換性を保つため、未使用の値3を「入力中」に割り当てる
  INPUTTING: 3,
} as const;

// メッセージ送信者タイプコード
export const SENDER_TYPE = {
  ENDUSER: 0,
  OPERATOR: 1,
  SYSTEM: 2,
} as const;

// API ベースURL（Viteプロキシ経由）
export const API_BASE_URL = '/api';

// WebSocket ベースURL
export const WS_BASE_URL = `ws://${window.location.host}/ws`;

// WebSocket 接続確立の待ち時間上限（ブラウザ既定のタイムアウトは数十秒〜数分あり、
// CONNECTING のまま固まると再接続もできなくなるため独自に打ち切る）
export const WS_CONNECT_TIMEOUT_MS = 10000;

// 粗大ごみ申し込みページ（モック）のパス
export const BULKY_WASTE_APPLY_PATH = '/bulky-waste/apply';

// ページング設定
export const PER_PAGE = 10;

// グループ一覧の取得件数（バックエンドのデフォルトと揃える）
export const UNANSWERED_LIMIT = 20;
export const MINE_LIMIT = 10;
export const CLOSED_LIMIT = 10;

// 問い合わせ一覧の自動更新間隔（ミリ秒）
export const GROUP_POLL_INTERVAL_MS = 5000;
