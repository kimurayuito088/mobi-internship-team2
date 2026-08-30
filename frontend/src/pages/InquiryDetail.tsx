import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { OperatorNav } from '../components/OperatorNav';
import { ChatWindow } from '../components/ChatWindow';
import { MessageInput } from '../components/MessageInput';
import { StatusBadge } from '../components/StatusBadge';
import { AssignButton } from '../components/AssignButton';
import { useChat } from '../hooks/useChat';
import { InquiryWithStatus, Message, UnreadInquiryResponse } from '../types';
import {
  API_BASE_URL,
  GROUP_POLL_INTERVAL_MS,
  SENDER_TYPE,
} from '../constants';
import { DisplayStatus } from '../types';
import styles from './InquiryDetail.module.css';

/**
 * 問い合わせ詳細（チャット）画面
 * 自分の担当する問い合わせのみメッセージ送信可能
 */
export function InquiryDetail() {
  const { id } = useParams<{ id: string }>();
  const { operator } = useAuth();
  const navigate = useNavigate();
  const { messages: wsMessages, isConnected, sendMessage, connect, disconnect } = useChat();
  const [inquiry, setInquiry] = useState<InquiryWithStatus | null>(null);
  const [historyMessages, setHistoryMessages] = useState<Message[]>([]);
  const [notificationInquiryIds, setNotificationInquiryIds] = useState<number[]>([]);
  const notifiedUnreadIdsRef = useRef<Set<number>>(new Set());
  const lastReadRequestRef = useRef(0);
  const inquiryId = Number(id);

  const allMessages = useMemo(() => {
    const messagesById = new Map<number, Message>();
    [...historyMessages, ...wsMessages]
      .filter(message => message.inquiry_id === inquiryId)
      .forEach(message => messagesById.set(message.id, message));
    return [...messagesById.values()].sort((first, second) => first.id - second.id);
  }, [historyMessages, inquiryId, wsMessages]);

  const markAsRead = useCallback(async (upToMessageId: number) => {
    if (!Number.isInteger(inquiryId) || upToMessageId <= lastReadRequestRef.current) {
      return;
    }

    lastReadRequestRef.current = upToMessageId;
    try {
      const response = await fetch(`${API_BASE_URL}/inquiries/${inquiryId}/read`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ up_to_message_id: upToMessageId }),
      });
      if (!response.ok && lastReadRequestRef.current === upToMessageId) {
        lastReadRequestRef.current = 0;
      }
    } catch {
      if (lastReadRequestRef.current === upToMessageId) {
        lastReadRequestRef.current = 0;
      }
    }
  }, [inquiryId]);

  // 問い合わせ情報取得
  useEffect(() => {
    if (!id || !operator || !Number.isInteger(inquiryId)) return;

    setInquiry(null);
    setHistoryMessages([]);
    setNotificationInquiryIds([]);
    notifiedUnreadIdsRef.current = new Set();
    lastReadRequestRef.current = 0;

    const fetchInquiry = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/inquiries/${id}`, {
          credentials: 'include',
        });
        if (!response.ok) {
          navigate('/operator/inquiries');
          return;
        }
        const data: InquiryWithStatus = await response.json();
        setInquiry(data);

        // WebSocket受信分を履歴取得中にも取りこぼさないため、先に接続する。
        if (data.display_status === 'mine') {
          connect(inquiryId, 'operator');
        }

        // メッセージ履歴取得
        const msgResponse = await fetch(`${API_BASE_URL}/inquiries/${id}/messages`, {
          credentials: 'include',
        });
        if (msgResponse.ok) {
          const msgs: Message[] = await msgResponse.json();
          setHistoryMessages(msgs);
        }
      } catch {
        navigate('/operator/inquiries');
      }
    };

    fetchInquiry();

    return () => {
      disconnect();
    };
  }, [id, inquiryId, operator, navigate, connect, disconnect]);

  const handleAssign = async (targetInquiryId: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/inquiries/${targetInquiryId}/assign`,
        {
          method: 'POST',
          credentials: 'include',
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => null);
        alert(error?.detail || '担当取得に失敗しました');

        try {
          const latestResponse = await fetch(
            `${API_BASE_URL}/inquiries/${targetInquiryId}`,
            { credentials: 'include' },
          );
          if (latestResponse.ok) {
            const latestInquiry: InquiryWithStatus = await latestResponse.json();
            setInquiry(latestInquiry);
          }
        } catch {
          // 担当取得エラーは表示済みのため、状態更新失敗による二重通知は行わない。
        }
        return;
      }

      const assignedInquiry: InquiryWithStatus = await response.json();
      setInquiry(assignedInquiry);
      connect(targetInquiryId, 'operator');
    } catch {
      alert('担当取得に失敗しました');
    }
  };

  useEffect(() => {
    if (inquiry?.display_status !== 'mine' || allMessages.length === 0) return;

    const latestMessage = allMessages[allMessages.length - 1];
    const latestEndUserMessage = [...allMessages]
      .reverse()
      .find(message => message.sender_type === SENDER_TYPE.ENDUSER);

    // 履歴表示時は最大IDまで、受信中は最新のエンドユーザー発言までを既読にする。
    const upToMessageId = Math.max(
      latestMessage.id,
      latestEndUserMessage?.id ?? 0,
    );
    void markAsRead(upToMessageId);
  }, [allMessages, inquiry?.display_status, markAsRead]);

  useEffect(() => {
    if (!operator || !Number.isInteger(inquiryId)) return;

    let isCancelled = false;
    let isFetching = false;

    const fetchUnreadInquiries = async () => {
      if (isCancelled || isFetching) return;
      isFetching = true;

      try {
        const response = await fetch(`${API_BASE_URL}/inquiries/mine/unread`, {
          credentials: 'include',
        });
        if (!response.ok || isCancelled) return;

        const data: UnreadInquiryResponse = await response.json();
        if (isCancelled) return;

        const currentUnreadIds = new Set(
          data.items
            .map(item => item.inquiry_id)
            .filter(unreadInquiryId => unreadInquiryId !== inquiryId),
        );

        notifiedUnreadIdsRef.current.forEach(notifiedId => {
          if (!currentUnreadIds.has(notifiedId)) {
            notifiedUnreadIdsRef.current.delete(notifiedId);
          }
        });

        const newlyUnreadIds = [...currentUnreadIds].filter(
          unreadInquiryId => !notifiedUnreadIdsRef.current.has(unreadInquiryId),
        );
        newlyUnreadIds.forEach(unreadInquiryId => {
          notifiedUnreadIdsRef.current.add(unreadInquiryId);
        });

        setNotificationInquiryIds(current =>
          [
            ...current.filter(notificationId => currentUnreadIds.has(notificationId)),
            ...newlyUnreadIds,
          ].filter(
            (notificationId, index, items) =>
              items.indexOf(notificationId) === index,
          ),
        );
      } catch (error) {
        if (!isCancelled) {
          console.error('未読問い合わせ取得エラー:', error);
        }
      } finally {
        isFetching = false;
      }
    };

    void fetchUnreadInquiries();
    const intervalId = setInterval(() => {
      void fetchUnreadInquiries();
    }, GROUP_POLL_INTERVAL_MS);

    return () => {
      isCancelled = true;
      clearInterval(intervalId);
    };
  }, [inquiryId, operator]);

  if (!inquiry) return null;

  // 自分の担当かつ終了していない場合のみ送信可能
  const canSend = (inquiry.display_status as DisplayStatus) === 'mine' && isConnected;

  return (
    <div className={styles.container}>
      <OperatorNav />
      <div className={styles.content}>
        <header className={styles.header}>
          <button
            className={styles.backButton}
            onClick={() => navigate('/operator/inquiries')}
            data-testid="inquiry-detail-back-button"
          >
            ← 一覧に戻る
          </button>
          <div className={styles.inquiryInfo} data-testid="inquiry-info">
            <span>問い合わせ #{inquiry.id}</span>
            <StatusBadge status={inquiry.display_status as DisplayStatus} />
            {inquiry.display_status === 'waiting' && (
              <AssignButton
                inquiryId={inquiry.id}
                onAssign={handleAssign}
                disabled={false}
              />
            )}
          </div>
        </header>

        <ChatWindow messages={allMessages} currentUserType="operator" />

        <MessageInput
          onSend={sendMessage}
          disabled={!canSend}
          placeholder={
            canSend
              ? 'メッセージを入力...'
              : (inquiry.display_status as DisplayStatus) === 'closed'
                ? 'この問い合わせは終了しています'
                : 'この問い合わせの担当ではありません'
          }
        />
      </div>
      <div className={styles.notificationArea} aria-live="polite">
        {notificationInquiryIds.map(notificationInquiryId => (
          <div
            key={notificationInquiryId}
            className={styles.notificationPopup}
            role="status"
          >
            <strong>新着メッセージ</strong>
            <p>問い合わせ #{notificationInquiryId} に新しいメッセージがあります</p>
            <button
              type="button"
              className={styles.notificationCloseButton}
              onClick={() => {
                setNotificationInquiryIds(current =>
                  current.filter(item => item !== notificationInquiryId),
                );
              }}
            >
              閉じる
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
