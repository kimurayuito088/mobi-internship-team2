import styles from '../../pages/PreHearing.module.css';

interface HearingChoiceButtonProps {
  label: string;
  onClick: () => void;
  disabled: boolean;
}

export function HearingChoiceButton({ label, onClick, disabled }: HearingChoiceButtonProps) {
  return (
    <button
      type="button"
      className={styles.choiceButton}
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      data-testid="hearing-choice-button"
    >
      {label}
    </button>
  );
}
