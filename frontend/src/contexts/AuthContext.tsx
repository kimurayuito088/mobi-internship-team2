import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { Operator } from '../types';
import { API_BASE_URL } from '../constants';

interface AuthContextType {
  operator: Operator | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

// 認証コンテキストを使用するためのフック
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth は AuthProvider 内で使用してください');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [operator, setOperator] = useState<Operator | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 起動時にセッション確認
  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/me`, { credentials: 'include' })
      .then(res => {
        if (res.ok) return res.json();
        return null;
      })
      .then(data => {
        if (data) setOperator(data);
      })
      .catch(() => {
        // セッションなし（未ログイン）
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  // ログイン処理
  const login = useCallback(async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'ログインに失敗しました');
    }

    const data = await response.json();
    setOperator(data);
  }, []);

  // ログアウト処理
  const logout = useCallback(async () => {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    setOperator(null);
  }, []);

  const value: AuthContextType = {
    operator,
    isAuthenticated: operator !== null,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
