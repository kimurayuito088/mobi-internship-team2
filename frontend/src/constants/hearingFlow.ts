export const HEARING_STEPS = {
  CATEGORY: 'category',
  BULKY_TYPE: 'bulky_type',
  MATERIAL: 'material',
  SIZE: 'size',
  CONFIRM: 'confirm',
} as const;

export type HearingStepId = (typeof HEARING_STEPS)[keyof typeof HEARING_STEPS];

/** 質問定義を持つステップ。confirm は確認画面専用で質問マップに含めない */
export type HearingQuestionStepId = Exclude<HearingStepId, typeof HEARING_STEPS.CONFIRM>;

export function isHearingQuestionStep(step: HearingStepId): step is HearingQuestionStepId {
  return step !== HEARING_STEPS.CONFIRM;
}

export interface HearingChoice {
  id: string;
  label: string;
  nextStep: HearingStepId | 'complete';
}

export interface HearingQuestionDef {
  id: HearingQuestionStepId;
  text: string;
  choices: HearingChoice[];
}

/** 1問目の choice_id。進捗と分岐の判定に使う */
export const CATEGORY_CHOICE_IDS = {
  UNKNOWN_WASTE_TYPE: 'unknown_waste_type',
  TICKET_PRICE_APPLY: 'ticket_price_apply',
  CHANGE_COLLECTION_DATE: 'change_collection_date',
  BRING_TO_FACILITY: 'bring_to_facility',
  FEE_REDUCTION: 'fee_reduction',
  BUSINESS_WASTE: 'business_waste',
  OTHER: 'other',
} as const;

export type HearingPath = 'unknown' | 'ticket' | 'short';

/**
 * 未選択時は最短経路として扱う。選んだあとにドットが増える方が、
 * 他経路で余ったドットが消えるより分かりやすいため。
 */
export function getHearingPath(categoryChoiceId: string | null): HearingPath {
  if (categoryChoiceId === CATEGORY_CHOICE_IDS.UNKNOWN_WASTE_TYPE) {
    return 'unknown';
  }
  if (categoryChoiceId === CATEGORY_CHOICE_IDS.TICKET_PRICE_APPLY) {
    return 'ticket';
  }
  return 'short';
}

/** オペレーター一覧向けの短い種類ラベル。未設定は呼び出し側でプレースホルダを出す */
export const HEARING_CATEGORY_SHORT_LABELS: Record<string, string> = {
  [CATEGORY_CHOICE_IDS.UNKNOWN_WASTE_TYPE]: '区分',
  [CATEGORY_CHOICE_IDS.TICKET_PRICE_APPLY]: '処理券',
  [CATEGORY_CHOICE_IDS.CHANGE_COLLECTION_DATE]: '収集日',
  [CATEGORY_CHOICE_IDS.BRING_TO_FACILITY]: '持込',
  [CATEGORY_CHOICE_IDS.FEE_REDUCTION]: '減免',
  [CATEGORY_CHOICE_IDS.BUSINESS_WASTE]: '事業ごみ',
  [CATEGORY_CHOICE_IDS.OTHER]: 'その他',
};

export const HEARING_CATEGORY_EMPTY_LABEL = '—';

export function getHearingCategoryShortLabel(categoryId: string | null | undefined): string {
  if (!categoryId) {
    return HEARING_CATEGORY_EMPTY_LABEL;
  }
  return HEARING_CATEGORY_SHORT_LABELS[categoryId] ?? HEARING_CATEGORY_EMPTY_LABEL;
}

export const HEARING_QUESTIONS: Record<HearingQuestionStepId, HearingQuestionDef> = {
  category: {
    id: 'category',
    text: 'お問い合わせの種類を選んでください',
    choices: [
      { id: CATEGORY_CHOICE_IDS.UNKNOWN_WASTE_TYPE, label: 'ごみの区分がわからない', nextStep: 'bulky_type' },
      { id: CATEGORY_CHOICE_IDS.TICKET_PRICE_APPLY, label: '処理券の料金を知りたい・申し込みたい', nextStep: 'size' },
      { id: CATEGORY_CHOICE_IDS.CHANGE_COLLECTION_DATE, label: '収集日を変更したい', nextStep: 'confirm' },
      { id: CATEGORY_CHOICE_IDS.BRING_TO_FACILITY, label: '処理場へ持ち込みたい', nextStep: 'confirm' },
      { id: CATEGORY_CHOICE_IDS.FEE_REDUCTION, label: '手数料の減免について知りたい', nextStep: 'confirm' },
      { id: CATEGORY_CHOICE_IDS.BUSINESS_WASTE, label: 'お店・事業から出たごみについて', nextStep: 'confirm' },
      { id: CATEGORY_CHOICE_IDS.OTHER, label: 'その他', nextStep: 'confirm' },
    ],
  },
  bulky_type: {
    id: 'bulky_type',
    text: 'ごみの区分を選んでください',
    choices: [
      { id: 'electric_gas_oil_kitchen', label: '電気・ガス・石油・厨房器具', nextStep: 'material' },
      { id: 'furniture_bedding_fittings', label: '家具・寝具・建具', nextStep: 'material' },
      { id: 'oa_equipment', label: 'OA機器', nextStep: 'material' },
      { id: 'hobby_sports_leisure', label: '趣味・スポーツ・レジャー用品', nextStep: 'material' },
      { id: 'other_work_tools', label: 'その他・作業用具', nextStep: 'material' },
      { id: 'bulky_type_unknown', label: 'わからない', nextStep: 'material' },
    ],
  },
  material: {
    id: 'material',
    text: '素材を選択してください',
    choices: [
      { id: 'wood', label: '木製（タンス・机・棚など）', nextStep: 'confirm' },
      { id: 'metal', label: '金属製（自転車・ガスコンロなど）', nextStep: 'confirm' },
      { id: 'plastic', label: 'プラスチック製', nextStep: 'confirm' },
      { id: 'fabric', label: '布・繊維製（マットレス・ソファ・カーペットなど）', nextStep: 'confirm' },
      { id: 'glass_ceramic', label: 'ガラス・陶磁器', nextStep: 'confirm' },
      { id: 'unknown', label: 'わからない', nextStep: 'confirm' },
    ],
  },
  size: {
    id: 'size',
    text: 'サイズの目安を選んでください',
    choices: [
      { id: 'up_to_30cm', label: '〜30cm', nextStep: 'confirm' },
      { id: 'over_30cm', label: '30cm〜', nextStep: 'confirm' },
    ],
  },
};

/** 区分不明は質問3問 + 確認、処理券は質問2問 + 確認、それ以外は質問1問 + 確認 */
export const HEARING_PATH_STEP_COUNT: Record<HearingPath, number> = {
  unknown: 4,
  ticket: 3,
  short: 2,
};
