import { HEARING_DETAIL_LABEL } from '../../hooks/usePreHearing';
import styles from '../../pages/PreHearing.module.css';

interface HearingConfirmProps {
  summaryText: string;
  detailText: string;
  onDetailChange: (value: string) => void;
  onConfirm: () => void;
  onRestart: () => void;
  confirmDisabled: boolean;
  restartDisabled: boolean;
}

export function HearingConfirm({
  summaryText,
  detailText,
  onDetailChange,
  onConfirm,
  onRestart,
  confirmDisabled,
  restartDisabled,
}: HearingConfirmProps) {
  return (
    <section data-testid="hearing-confirm">
      <h2 className={styles.confirmTitle}>以下の内容でよろしいですか？</h2>
      <pre className={styles.summaryBox} data-testid="hearing-summary">
        {summaryText}
      </pre>

      <div className={styles.detailField}>
        <label className={styles.detailLabel} htmlFor="hearing-detail">
          {HEARING_DETAIL_LABEL}
          <span className={styles.detailOptional}>（任意）</span>
        </label>
        <textarea
          id="hearing-detail"
          className={styles.detailTextarea}
          value={detailText}
          onChange={(event) => onDetailChange(event.target.value)}
          disabled={restartDisabled}
          placeholder="補足があれば入力してください"
          rows={4}
          aria-label={`${HEARING_DETAIL_LABEL}（任意）`}
          data-testid="hearing-detail-input"
        />
      </div>

      <div className={styles.confirmActions}>
        <button
          type="button"
          className={styles.primaryButton}
          onClick={onConfirm}
          disabled={confirmDisabled}
          aria-label="この内容で問い合わせる"
          data-testid="hearing-confirm-button"
        >
          この内容で問い合わせる
        </button>
        <button
          type="button"
          className={styles.secondaryButton}
          onClick={onRestart}
          disabled={restartDisabled}
          aria-label="最初からやり直す"
          data-testid="hearing-restart-button"
        >
          最初からやり直す
        </button>
      </div>
    </section>
  );
}
