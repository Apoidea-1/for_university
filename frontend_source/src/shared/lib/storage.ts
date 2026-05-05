import type { User } from "@/types/api";

const TOKEN_KEY = "networkpilot.token";
const USER_KEY = "networkpilot.user";

export const authStorage = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  getUser() {
    const rawUser = localStorage.getItem(USER_KEY);
    if (!rawUser) {
      return null;
    }

    try {
      return JSON.parse(rawUser) as User;
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  },
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  },
  setUser(user: User) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  },
  clearUser() {
    localStorage.removeItem(USER_KEY);
  },
  clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};
