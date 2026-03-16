"use client";
import React, { createContext, useCallback, useContext, useMemo } from 'react';

interface LoginErrors {
  general?: string;
  username?: string;
  password?: string;
}

interface AuthContextValue {
  getAccessToken: () => string | null;
  isTokenValid: (token?: string | null) => boolean;
  validateCredentials: (username: string, password: string) => LoginErrors;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const getAccessToken = useCallback((): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }, []);

  const isTokenValid = useCallback((token?: string | null): boolean => {
    try {
      const t = token ?? getAccessToken();
      if (!t) return false;
      const parts = t.split('.');
      if (parts.length !== 3) return false;
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const json = typeof window !== 'undefined'
        ? decodeURIComponent(
            atob(base64)
              .split('')
              .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
              .join('')
          )
        : Buffer.from(base64, 'base64').toString('utf-8');
      const payload = JSON.parse(json) as { exp?: number };
      if (!payload.exp) return true;
      const nowSeconds = Math.floor(Date.now() / 1000);
      return payload.exp > nowSeconds;
    } catch {
      return false;
    }
  }, [getAccessToken]);

  const validateCredentials = useCallback((username: string, password: string): LoginErrors => {
    const errs: LoginErrors = {};
    if (!username || username.trim() === '') {
      errs.username = 'No users entered on trusted details';
    }
    if (!password || password.trim() === '') {
      errs.password = 'Please enter a valid password';
    } else if (password.length < 6) {
      errs.password = 'Password must be at least 6 characters';
    }
    return errs;
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    getAccessToken,
    isTokenValid,
    validateCredentials,
  }), [getAccessToken, isTokenValid, validateCredentials]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
