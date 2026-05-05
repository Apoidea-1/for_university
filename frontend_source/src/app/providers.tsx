import {
  createContext,
  type PropsWithChildren,
  useEffect,
  useMemo,
  useState,
} from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ApiError } from "@/api/client";
import { getCurrentUser } from "@/api/auth";
import { authStorage } from "@/shared/lib/storage";
import type { User } from "@/types/api";

interface AuthContextValue {
  token: string | null;
  user: User | null;
  isBootstrapping: boolean;
  setSession: (token: string, user?: User | null) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 20_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => authStorage.getToken());
  const [user, setUser] = useState<User | null>(() => authStorage.getUser());
  const [isBootstrapping, setIsBootstrapping] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setIsBootstrapping(false);
      setUser(null);
      authStorage.clearSession();
      return;
    }

    let cancelled = false;
    setIsBootstrapping(true);
    getCurrentUser()
      .then((currentUser) => {
        if (!cancelled) {
          authStorage.setUser(currentUser);
          setUser(currentUser);
        }
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        if (error instanceof ApiError && error.status === 401) {
          authStorage.clearSession();
          setToken(null);
          setUser(null);
          return;
        }

        setUser(authStorage.getUser());
      })
      .finally(() => {
        if (!cancelled) {
          setIsBootstrapping(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isBootstrapping,
      setSession(nextToken, nextUser) {
        authStorage.setToken(nextToken);
        setToken(nextToken);
        if (nextUser) {
          authStorage.setUser(nextUser);
          setUser(nextUser);
          setIsBootstrapping(false);
          return;
        }
        setUser(null);
        setIsBootstrapping(true);
      },
      logout() {
        authStorage.clearSession();
        setToken(null);
        setUser(null);
        queryClient.clear();
      },
    }),
    [isBootstrapping, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
