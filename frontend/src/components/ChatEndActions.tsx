import { useNavigate } from 'react-router-dom';
import { BULKY_WASTE_APPLY_PATH } from '../constants';
import styles from './ChatEndActions.module.css';

interface ChatEndActionsProps {
  onOtherInquiry: () => void;
}

/**
 * チャット終了後の次の行動を選ばせる導線。
 * 別件の相談はヒアリングへ戻し、手続きに進む人は申し込みページへ送り出す。
 */
export function ChatEndActions({ onOtherInquiry }: ChatEndActionsProps) {
  const navigate = useNavigate();

  return (
    <section className={styles.container} data-testid="chat-end-actions">
      <h2 className={styles.heading}>次に行うことを選んでください</h2>
      <div className={styles.actionList}>
        <button
          type="button"
          className={styles.actionButton}
          onClick={onOtherInquiry}
          data-testid="other-inquiry-button"
        >
          他のお問い合わせをする
        </button>
        <button
          type="button"
          className={styles.actionButton}
          onClick={() => navigate(BULKY_WASTE_APPLY_PATH)}
          data-testid="apply-page-button"
        >
          申し込みページへ
        </button>
      </div>
    </section>
  );
}
