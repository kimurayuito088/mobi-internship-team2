import { useState, useCallback, useRef, useEffect } from 'react';
import { Message } from '../types';
import { WS_BASE_URL, WS_CONNECT_TIMEOUT_MS } from '../constants';

interface UseChatReturn {
  messages: Message[];
  isConnected: boolean;
  sendMessage: (content: string, categoryId?: string) => void;
  connect: (inquiryId: number, userType: 'enduser' | 'operator') => void;
  disconnect: () => void;
  reset: () => void;
}

/**
 * チャット用WebSocket通信フック
 * WebSocket接続の確立・切断・メッセージ送受信を管理する
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const inquiryIdRef = useRef<number>(0);
  const connectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearConnectTimer = useCallback(() => {
    if (connectTimerRef.current !== null) {
      clearTimeout(connectTimerRef.current);
      connectTimerRef.current = null;
    }
  }, []);

  const connect = useCallback((inquiryId: number, userType: 'enduser' | 'operator') => {
    // 二重接続で既存の INPUTTING 問い合わせが切断終了されないようにする
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
      return;
    }

    const path = userType === 'enduser'
      ? `${WS_BASE_URL}/chat/enduser/${inquiryId}`
      : `${WS_BASE_URL}/chat/operator/${inquiryId}`;

    const ws = new WebSocket(path);
    wsRef.current = ws;
    inquiryIdRef.current = inquiryId;

    // CONNECTING のまま放置されると connect の早期 return で再接続不能になるため、
    // 期限切れなら自前で close して onclose 経由で参照を解放する
    connectTimerRef.current = setTimeout(() => {
      connectTimerRef.current = null;
      if (ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    }, WS_CONNECT_TIMEOUT_MS);

    ws.onopen = () => {
      clearConnectTimer();
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      // close() 後も CLOSING の間はイベントが届くため、
      // 破棄済みソケットの受信で reset 後の履歴を汚染しないようにする
      if (wsRef.current !== ws) {
        return;
      }

      const data = JSON.parse(event.data);

      if (data.type === 'connected') {
        inquiryIdRef.current = data.inquiry_id;
      } else if (data.type === 'message') {
        const msg: Message = {
          id: data.id,
          inquiry_id: data.inquiry_id,
          sender_type: data.sender_type,
          sender_name: data.sender_name,
          content: data.content,
          created_at: data.created_at,
        };
        setMessages(prev => [...prev, msg]);
      } else if (data.type === 'closed') {
        setIsConnected(false);
      }
    };

    ws.onclose = () => {
      clearConnectTimer();
      // 切断後の再接続のため、閉じたソケット参照を捨てる
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
      setIsConnected(false);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };
  }, [clearConnectTimer]);

  const disconnect = useCallback(() => {
    clearConnectTimer();
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'close' }));
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, [clearConnectTimer]);

  // 別の問い合わせを始める際に前回の会話が混ざらないよう、接続と履歴の両方を破棄する
  const reset = useCallback(() => {
    disconnect();
    setMessages([]);
  }, [disconnect]);

  const sendMessage = useCallback((content: string, categoryId?: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload: { type: 'message'; content: string; category_id?: string } = {
        type: 'message',
        content,
      };
      if (categoryId) {
        payload.category_id = categoryId;
      }
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  useEffect(() => {
    return () => {
      if (connectTimerRef.current !== null) {
        clearTimeout(connectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { messages, isConnected, sendMessage, connect, disconnect, reset };
}
