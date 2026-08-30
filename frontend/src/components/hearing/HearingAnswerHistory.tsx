import { HEARING_STEPS, HearingQuestionStepId } from '../../constants/hearingFlow';
import { HearingAnswer } from '../../types/hearing';
import styles from '../../pages/PreHearing.module.css';

const HISTORY_LABELS: Record<HearingQuestionStepId, string> = {
  [HEARING_STEPS.CATEGORY]: 'お問い合わせの種類',
  [HEARING_STEPS.BULKY_TYPE]: '粗大ゴミの区分',
  [HEARING_STEPS.MATERIAL]: '素材',
  [HEARING_STEPS.SIZE]: 'サイズの目安',
};

interface HearingAnswerHistoryProps {
  answers: HearingAnswer[];
}

export function HearingAnswerHistory({ answers }: HearingAnswerHistoryProps) {
  if (answers.length === 0) {
    return null;
  }

  return (
    <div className={styles.history} data-testid="hearing-answer-history">
      {answers.map((answer) => (
        <p key={answer.question_id} className={styles.historyItem}>
          <span className={styles.historyCheck}>✓</span>
          {HISTORY_LABELS[answer.question_id] ?? answer.question_label}: {answer.choice_label}
        </p>
      ))}
    </div>
  );
}
