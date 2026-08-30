import { useState } from 'react';
import { PreHearing } from './PreHearing';
import { EndUserChat } from './EndUserChat';
import { useChat } from '../hooks/useChat';

type EndUserPhase = 'hearing' | 'chat';

/**
 * エンドユーザ画面のラッパー。
 * ヒアリング中に確立した WebSocket をチャット画面でも共有する。
 */
export function EndUserPage() {
  const [phase, setPhase] = useState<EndUserPhase>('hearing');
  const { messages, isConnected, sendMessage, connect, disconnect, reset } = useChat();

  const handleHearingStart = () => {
    // 接続済み・接続試行中の抑止は useChat.connect 側で行う。
    // 失敗・切断後は再度呼べるようにし、入力中 Inquiry の再作成を可能にする。
    connect(0, 'enduser');
  };

  const handleHearingComplete = (summary: string, categoryId: string | null) => {
    // 同一接続で要約を送り、INPUTTING → WAITING へ遷移させる
    sendMessage(summary, categoryId ?? undefined);
    setPhase('chat');
  };

  const handleOtherInquiry = () => {
    // 前回の会話を破棄して別の問い合わせとして作り直す。
    // PreHearing はアンマウント済みのため、再表示時に回答状態も初期化される
    reset();
    setPhase('hearing');
  };

  if (phase === 'hearing') {
    return (
      <PreHearing
        onComplete={handleHearingComplete}
        onHearingStart={handleHearingStart}
        isConnected={isConnected}
      />
    );
  }

  return (
    <EndUserChat
      messages={messages}
      isConnected={isConnected}
      sendMessage={sendMessage}
      disconnect={disconnect}
      onOtherInquiry={handleOtherInquiry}
    />
  );
}
