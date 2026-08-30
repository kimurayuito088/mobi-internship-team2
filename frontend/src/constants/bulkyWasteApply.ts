/** 申し込みページ（モック）の受付メニュー */
export interface ApplyMenuItem {
  id: string;
  label: string;
  description: string;
}

export const APPLY_MENU_ITEMS: ApplyMenuItem[] = [
  {
    id: 'new',
    label: '新規申込み',
    description: '新規に粗大ごみをお申し込みになる方はこちらを選択してください。',
  },
  {
    id: 'change',
    label: '追加変更・一部キャンセル',
    description: 'お申し込みになった内容を変更される方はこちらを選択してください。',
  },
  {
    id: 'cancel',
    label: 'キャンセル',
    description: 'お申し込みになった内容をすべて取り消したい場合はこちらを選択してください。',
  },
];

/** ヘッダー下に並ぶ案内リンク（モックのため遷移先は用意しない） */
export const APPLY_GUIDE_LINKS: string[] = [
  '操作方法について',
  '排出品目参照一覧',
  'よくあるご質問',
];

/** モックページのため、実在しないダミーの連絡先を表示する */
export const APPLY_CONTACT = {
  officeName: '粗大ごみ受付事務所',
  phoneNumber: '000-0000-0000',
  businessHours: '月曜日〜金曜日 午前8:00〜午後6:00',
  closedDays: '土・日・祝日・12/29〜1/3を除く',
} as const;
