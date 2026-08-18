import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { type ReactNode } from "react";
import { AuthProvider, useAuth } from "../contexts/AuthContext";

const mockLoginResponse = {
  access_token: "test-access",
  refresh_token: "test-refresh",
  token_type: "bearer",
};

const mockUser = {
  id: "u1",
  email: "test@test.com",
  username: "tester",
  role: "user" as const,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockAdmin = { ...mockUser, id: "u2", role: "admin" as const };

vi.mock("../api", () => ({
  authApi: {
    me: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn(),
}));

import { authApi, setTokens, clearTokens, getAccessToken } from "../api";

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with user=null when no token", async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
  });

  it("fetches user on mount when token exists", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).toEqual(mockUser));
    expect(result.current.isAdmin).toBe(false);
  });

  it("sets isAdmin=true for admin role", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockAdmin);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isAdmin).toBe(true));
  });

  it("login calls login, setTokens and fetches user", async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);
    vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse);
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login("test@test.com", "pass123");
    });

    expect(authApi.login).toHaveBeenCalledWith({
      email: "test@test.com",
      password: "pass123",
    });
    expect(setTokens).toHaveBeenCalledWith("test-access", "test-refresh");
    expect(result.current.user).toEqual(mockUser);
  });

  it("register calls register then login", async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);
    vi.mocked(authApi.register).mockResolvedValue(mockUser);
    vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse);
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.register("test@test.com", "tester", "pass123");
    });

    expect(authApi.register).toHaveBeenCalledWith({
      email: "test@test.com",
      username: "tester",
      password: "pass123",
    });
    expect(authApi.login).toHaveBeenCalled();
  });

  it("logout clears tokens and user", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).toEqual(mockUser));

    act(() => {
      result.current.logout();
    });

    expect(clearTokens).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
  });

  it("throws if useAuth used outside provider", () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within AuthProvider");
  });
});
