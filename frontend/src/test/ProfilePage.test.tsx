import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProfilePage } from "../pages/Profile";
import { AuthProvider } from "../contexts/AuthContext";

vi.mock("../api", () => ({
  profileApi: {
    get: vi.fn(),
    update: vi.fn(),
    changePassword: vi.fn(),
    delete: vi.fn(),
  },
  authApi: {
    me: vi.fn().mockResolvedValue({
      id: "u1",
      email: "test@test.com",
      username: "tester",
      role: "user",
      is_active: true,
      created_at: "",
      updated_at: "",
    }),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue("token"),
}));

import { profileApi } from "../api";

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays profile data", async () => {
    vi.mocked(profileApi.get).mockResolvedValue({
      id: "u1",
      email: "test@test.com",
      username: "tester",
      role: "user",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfilePage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /tester/i })).toBeInTheDocument();
      expect(screen.getByDisplayValue("tester")).toBeInTheDocument();
      expect(screen.getByDisplayValue("test@test.com")).toBeInTheDocument();
    });
  });

  it("shows update and change password buttons", async () => {
    vi.mocked(profileApi.get).mockResolvedValue({
      id: "u1",
      email: "test@test.com",
      username: "tester",
      role: "user",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfilePage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /edit profile/i })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: /change password/i })).toBeInTheDocument();
      const saveButtons = screen.getAllByRole("button", { name: /save/i });
      expect(saveButtons.length).toBe(2);
    });
  });
});
