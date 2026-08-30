import {
  getHearingPath,
  HEARING_PATH_STEP_COUNT,
  HEARING_STEPS,
  HearingPath,
  HearingStepId,
} from '../../constants/hearingFlow';
import styles from '../../pages/PreHearing.module.css';

interface HearingProgressProps {
  currentStep: HearingStepId;
  categoryChoiceId: string | null;
}

const PATH_STEP_INDEX: Record<HearingPath, Record<HearingStepId, number>> = {
  unknown: {
    [HEARING_STEPS.CATEGORY]: 0,
    [HEARING_STEPS.BULKY_TYPE]: 1,
    [HEARING_STEPS.MATERIAL]: 2,
    [HEARING_STEPS.SIZE]: 2,
    [HEARING_STEPS.CONFIRM]: 3,
  },
  ticket: {
    [HEARING_STEPS.CATEGORY]: 0,
    [HEARING_STEPS.BULKY_TYPE]: 0,
    [HEARING_STEPS.MATERIAL]: 0,
    [HEARING_STEPS.SIZE]: 1,
    [HEARING_STEPS.CONFIRM]: 2,
  },
  short: {
    [HEARING_STEPS.CATEGORY]: 0,
    [HEARING_STEPS.BULKY_TYPE]: 0,
    [HEARING_STEPS.MATERIAL]: 0,
    [HEARING_STEPS.SIZE]: 0,
    [HEARING_STEPS.CONFIRM]: 1,
  },
};

export function HearingProgress({ currentStep, categoryChoiceId }: HearingProgressProps) {
  const path = getHearingPath(categoryChoiceId);
  const total = HEARING_PATH_STEP_COUNT[path];
  const currentIndex = PATH_STEP_INDEX[path][currentStep];

  return (
    <div
      className={styles.progress}
      role="progressbar"
      aria-label="ヒアリングの進捗"
      aria-valuenow={currentIndex + 1}
      aria-valuemin={1}
      aria-valuemax={total}
    >
      {Array.from({ length: total }, (_, index) => (
        <span
          key={index}
          className={index <= currentIndex ? styles.progressDotActive : styles.progressDot}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}
