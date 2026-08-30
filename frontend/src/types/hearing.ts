import { HearingQuestionStepId } from '../constants/hearingFlow';

export interface HearingAnswer {
  question_id: HearingQuestionStepId;
  question_label: string;
  choice_id: string;
  choice_label: string;
}

export type PreHearingPhase = 'question' | 'confirm' | 'submitting' | 'error';
