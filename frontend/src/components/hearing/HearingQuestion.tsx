import { HearingChoice, HearingQuestionDef } from '../../constants/hearingFlow';
import { HearingChoiceButton } from './HearingChoiceButton';
import styles from '../../pages/PreHearing.module.css';

interface HearingQuestionProps {
  question: HearingQuestionDef;
  onSelect: (choice: HearingChoice) => void;
  disabled: boolean;
}

export function HearingQuestion({ question, onSelect, disabled }: HearingQuestionProps) {
  return (
    <section data-testid="hearing-question">
      <h2 className={styles.questionText}>{question.text}</h2>
      <div className={styles.choiceList}>
        {question.choices.map((choice) => (
          <HearingChoiceButton
            key={choice.id}
            label={choice.label}
            onClick={() => onSelect(choice)}
            disabled={disabled}
          />
        ))}
      </div>
    </section>
  );
}
