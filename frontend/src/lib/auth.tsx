'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface LocalUser {
  id: string;
  email: string;
}

interface AuthContextType {
  user: LocalUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Single local user — no Supabase, no login required
const LOCAL_USER: LocalUser = {
  id: 'local-user',
  email: 'local@orpaq.ai',
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<LocalUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Auto-login the local user
    setUser(LOCAL_USER);
    setLoading(false);
  }, []);

  const signIn = async (_email: string, _password: string) => {
    setUser(LOCAL_USER);
    return { error: null };
  };

  const signUp = async (_email: string, _password: string) => {
    setUser(LOCAL_USER);
    return { error: null };
  };

  const signOut = async () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
