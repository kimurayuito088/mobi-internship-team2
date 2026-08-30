import { useCallback, useMemo, useRef, useState } from 'react';
import {
  HEARING_QUESTIONS,
  HEARING_STEPS,
  HearingChoice,
  HearingQuestionDef,
  HearingStepId,
  isHearingQuestionStep,
} from '../constants/hearingFlow';
import { HearingAnswer, PreHearingPhase } from '../types/hearing';

/** 詳細欄の見出し。チャット要約にも同じ文言を使う */
export const HEARING_DETAIL_LABEL = '詳細';

export function buildHearingSummary(answers: HearingAnswer[], detailText = ''): string {
  const lines = ['【事前ヒアリング】'];
  answers.forEach((answer, index) => {
    if (index > 0) {
      lines.push('');
    }
    lines.push(`Q. ${answer.question_label}`);
    lines.push(`A. ${answer.choice_label}`);
  });

  // 空白のみの詳細は要約に載せない（未入力でも問い合わせ可能にするため）
  const trimmedDetail = detailText.trim();
  if (trimmedDetail.length > 0) {
    lines.push('');
    lines.push(`${HEARING_DETAIL_LABEL}:`);
    lines.push(trimmedDetail);
  }

  return lines.join('\n');
}

interface UsePreHearingParams {
  onComplete: (hearingSummary: string, categoryId: string | null) => void;
  onHearingStart: () => void;
}

interface UsePreHearingReturn {
  currentStep: HearingStepId;
  currentQuestion: HearingQuestionDef | null;
  answers: HearingAnswer[];
  detailText: string;
  phase: PreHearingPhase;
  error: string | null;
  selectChoice: (choice: HearingChoice) => void;
  setDetailText: (value: string) => void;
  confirm: () => Promise<void>;
  restart: () => void;
  summaryText: string;
}

export function usePreHearing({
  onComplete,
  onHearingStart,
}: UsePreHearingParams): UsePreHearingReturn {
  const [currentStep, setCurrentStep] = useState<HearingStepId>(HEARING_STEPS.CATEGORY);
  const [answers, setAnswers] = useState<HearingAnswer[]>([]);
  const [detailText, setDetailText] = useState('');
  const [phase, setPhase] = useState<PreHearingPhase>('question');
  const [error, setError] = useState<string | null>(null);
  // answers.length はレンダー時点の値なので、setAnswers の反映前に連続入力されると
  // onHearingStart が二重実行される。ref で「開始済み」を同期的に確定させる。
  const hasStartedRef = useRef(false);

  const currentQuestion = useMemo((): HearingQuestionDef | null => {
    if (!isHearingQuestionStep(currentStep)) {
      return null;
    }
    return HEARING_QUESTIONS[currentStep];
  }, [currentStep]);

  // 確認画面の要約は選択肢のみ。詳細は下の入力欄で編集するためここでは含めない
  const summaryText = useMemo(() => buildHearingSummary(answers), [answers]);

  const selectChoice = useCallback(
    (choice: HearingChoice) => {
      if (!isHearingQuestionStep(currentStep)) {
        return;
      }
      const question = HEARING_QUESTIONS[currentStep];

      // 最初の選択肢選択時に INPUTTING 問い合わせを作成する（setState 外で副作用を実行）
      if (!hasStartedRef.current) {
        hasStartedRef.current = true;
        onHearingStart();
      }

      setAnswers((prev) => {
        // 同じ質問を選び直した場合は、それ以降の回答を破棄する
        const existingIndex = prev.findIndex((answer) => answer.question_id === question.id);
        const nextAnswers = existingIndex >= 0 ? prev.slice(0, existingIndex) : [...prev];
        nextAnswers.push({
          question_id: question.id,
          question_label: question.text,
          choice_id: choice.id,
          choice_label: choice.label,
        });
        return nextAnswers;
      });

      if (choice.nextStep === 'confirm' || choice.nextStep === 'complete') {
        setCurrentStep(HEARING_STEPS.CONFIRM);
        setPhase('confirm');
        return;
      }

      setCurrentStep(choice.nextStep);
      setPhase('question');
    },
    [currentStep, onHearingStart],
  );

  const confirm = useCallback(async () => {
    setPhase('submitting');
    setError(null);
    try {
      // 詳細は任意。空白でも問い合わせを作成し、入力があるときだけ要約に追記する
      const categoryId =
        answers.find((answer) => answer.question_id === HEARING_STEPS.CATEGORY)?.choice_id ?? null;
      onComplete(buildHearingSummary(answers, detailText), categoryId);
    } catch {
      setPhase('error');
      setError('送信に失敗しました。もう一度お試しください');
    }
  }, [answers, detailText, onComplete]);

  const restart = useCallback(() => {
    // やり直し時はフラグを戻し、切断済みの場合に再接続を試みられるようにする
    hasStartedRef.current = false;
    setCurrentStep(HEARING_STEPS.CATEGORY);
    setAnswers([]);
    setDetailText('');
    setPhase('question');
    setError(null);
  }, []);

  return {
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
  };
}
