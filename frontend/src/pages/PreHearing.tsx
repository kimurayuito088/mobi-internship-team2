import { HearingHeader } from '../components/hearing/HearingHeader';
import { HearingProgress } from '../components/hearing/HearingProgress';
import { HearingAnswerHistory } from '../components/hearing/HearingAnswerHistory';
import { HearingQuestion } from '../components/hearing/HearingQuestion';
import { HearingConfirm } from '../components/hearing/HearingConfirm';
import { HEARING_STEPS } from '../constants/hearingFlow';
import { usePreHearing } from '../hooks/usePreHearing';
import styles from './PreHearing.module.css';

interface PreHearingProps {
  onComplete: (hearingSummary: string, categoryId: string | null) => void;
  onHearingStart: () => void;
  isConnected: boolean;
}

export function PreHearing({ onComplete, onHearingStart, isConnected }: PreHearingProps) {
  const {
    currentStep,
    currentQuestion,
    answers,
    detailText,
    phase,
    error,
    selectChoice,
    setDetailText,
    confirm,
    restart,
    summaryText,
  } = usePreHearing({ onComplete, onHearingStart });

  const categoryChoiceId = answers.find((answer) => answer.question_id === HEARING_STEPS.CATEGORY)?.choice_id ?? null;
  const isBusy = phase === 'submitting';
  // 接続完了前に要約送信すると INPUTTING → WAITING 遷移が落ちるため待つ
  const canConfirm = isConnected && !isBusy;

  return (
    <div className={styles.container} data-testid="pre-hearing">
      <HearingHeader />
      <HearingProgress currentStep={currentStep} categoryChoiceId={categoryChoiceId} />
      <div className={styles.body}>
        <HearingAnswerHistory answers={answers} />

        {phase === 'question' && currentQuestion && (
          <HearingQuestion
            question={currentQuestion}
            onSelect={selectChoice}
            disabled={isBusy}
          />
        )}

        {(phase === 'confirm' || phase === 'submitting') && (
          <>
            {phase === 'submitting' && (
              <p className={styles.loading} data-testid="hearing-loading">
                送信中です...
              </p>
            )}
            {phase === 'confirm' && !isConnected && (
              <p className={styles.loading} data-testid="hearing-connecting">
                接続中です...
              </p>
            )}
            <HearingConfirm
              summaryText={summaryText}
              detailText={detailText}
              onDetailChange={setDetailText}
              onConfirm={confirm}
              onRestart={restart}
              confirmDisabled={!canConfirm}
              restartDisabled={isBusy}
            />
          </>
        )}

        {phase === 'error' && (
          <div className={styles.errorBox} data-testid="hearing-error">
            <p className={styles.errorMessage}>{error}</p>
            <div className={styles.confirmActions}>
              <button
                type="button"
                className={styles.primaryButton}
                onClick={confirm}
                disabled={!isConnected}
                aria-label="再試行"
              >
                再試行
              </button>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={restart}
                aria-label="最初からやり直す"
              >
                最初からやり直す
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
