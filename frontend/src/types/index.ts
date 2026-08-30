// オペレータ
export interface Operator {
  id: number;
  username: string;
  display_name: string;
}

// メッセージ
export interface Message {
  id: number;
  inquiry_id: number;
  sender_type: number; // 0:enduser, 1:operator, 2:system
  sender_name: string | null;
  content: string;
  created_at: string; // ISO 8601
}

// 問い合わせ
export interface Inquiry {
  id: number;
  status: number; // 0:waiting, 1:active, 2:closed, 3:inputting
  assigned_operator_id: number | null;
  created_at: string;
  closed_at: string | null;
  category_id: string | null;
}

// 表示用ステータス
export type DisplayStatus = 'inputting' | 'waiting' | 'mine' | 'others' | 'closed';

// 表示用拡張型
export interface InquiryWithStatus extends Inquiry {
  display_status: DisplayStatus;
  has_unread: boolean;
}

// ページングレスポンス
export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

// グループ一覧の1枠分
export interface InquiryGroup {
  items: InquiryWithStatus[];
  total: number;
  has_more: boolean;
}

// グループ一覧レスポンス
export interface GroupedInquiryResponse {
  unanswered: InquiryGroup;
  mine: InquiryGroup;
  closed: InquiryGroup;
}

export interface UnreadInquiryResponse {
  items: Array<{
    inquiry_id: number;
  }>;
}

// オペレータ作成レスポンス（パスワード付き）
export interface OperatorCreateResponse {
  operator: Operator;
  generated_password: string;
}

export type { HearingAnswer, PreHearingPhase } from './hearing';
