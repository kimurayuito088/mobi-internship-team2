import { useState } from 'react';
import { ChatWindow } from '../components/ChatWindow';
import { MessageInput } from '../components/MessageInput';
import { ConnectionStatus } from '../components/ConnectionStatus';
import { EndButton } from '../components/EndButton';
import { ChatEndActions } from '../components/ChatEndActions';
import { Message } from '../types';
import styles from './EndUserChat.module.css';

interface EndUserChatProps {
  messages: Message[];
  isConnected: boolean;
  sendMessage: (content: string) => void;
  disconnect: () => void;
  onOtherInquiry: () => void;
}

/**
 * エンドユーザ向けチャット画面
 * ヒアリング完了後、親が保持する WebSocket 接続をそのまま利用する
 */
export function EndUserChat({
  messages,
  isConnected,
  sendMessage,
  disconnect,
  onOtherInquiry,
}: EndUserChatProps) {
  const [isClosed, setIsClosed] = useState(false);

  const handleEnd = () => {
    setIsClosed(true);
    disconnect();
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>お問い合わせチャット</h1>
        <div className={styles.headerActions}>
          <ConnectionStatus isConnected={isConnected && !isClosed} />
          <EndButton onEnd={handleEnd} disabled={isClosed} />
        </div>
      </header>

      <ChatWindow messages={messages} currentUserType="enduser" />

      {isClosed ? (
        <div className={styles.closedArea}>
          <p className={styles.closedMessage}>
            チャットが終了しました。ご利用ありがとうございました。
          </p>
          <ChatEndActions onOtherInquiry={onOtherInquiry} />
        </div>
      ) : (
        <MessageInput
          onSend={sendMessage}
          disabled={!isConnected || isClosed}
          placeholder="メッセージを入力..."
        />
      )}
    </div>
  );
}
