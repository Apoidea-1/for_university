import {
  createContext,
  type PropsWithChildren,
  useEffect,
  useMemo,
  useState,
} from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ApiError } from "@/api/client";
import { getCurrentUser, logout as logoutRequest } from "@/api/auth";
import type { User } from "@/types/api";
import { ThemeContext, type Theme } from "@/hooks/useTheme";

interface AuthContextValue {
  user: User | null;
  isBootstrapping: boolean;
  setSession: (user: User | null) => void;
  logout: () => Promise<void>;
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
  const [user, setUser] = useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsBootstrapping(true);

    getCurrentUser()
      .then((currentUser) => {
        if (!cancelled) {
          setUser(currentUser);
        }
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          setUser(null);
          return;
        }
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) {
          setIsBootstrapping(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isBootstrapping,
      setSession(nextUser) {
        setUser(nextUser);
        setIsBootstrapping(false);
      },
      async logout() {
        try {
          await logoutRequest();
        } catch {
          // Keep local state authoritative even if the network request races.
        }
        setUser(null);
        queryClient.clear();
      },
    }),
    [isBootstrapping, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function ThemeProvider({ children }: PropsWithChildren) {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      return (localStorage.getItem("np-theme") as Theme) ?? "dark";
    } catch {
      return "dark";
    }
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "cream") {
      root.dataset.theme = "cream";
    } else {
      delete root.dataset.theme;
    }
    try {
      localStorage.setItem("np-theme", theme);
    } catch {}
  }, [theme]);

  const value = useMemo(
    () => ({
      theme,
      toggle: () => {
        const root = document.documentElement;
        root.classList.add("np-switching");
        setTheme((t) => (t === "dark" ? "cream" : "dark"));
        setTimeout(() => root.classList.remove("np-switching"), 480);
      },
    }),
    [theme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
