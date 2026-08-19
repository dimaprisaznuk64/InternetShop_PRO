import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminUsersPage } from "../pages/Admin/Users";
import { AuthProvider } from "../contexts/AuthContext";

const mockUsers = {
  users: [
    {
      id: "u1",
      email: "john@test.com",
      username: "john",
      role: "user" as const,
      is_active: true,
      created_at: "2024-01-01",
      updated_at: "2024-01-01",
    },
    {
      id: "u2",
      email: "admin@test.com",
      username: "admin",
      role: "admin" as const,
      is_active: true,
      created_at: "2024-01-02",
      updated_at: "2024-01-02",
    },
  ],
  total: 2,
};

vi.mock("../api", () => ({
  adminApi: {
    stats: vi.fn(),
    listUsers: vi.fn(),
    blockUser: vi.fn(),
    unblockUser: vi.fn(),
    changeRole: vi.fn(),
    listPromoCodes: vi.fn(),
    createPromoCode: vi.fn(),
    deletePromoCode: vi.fn(),
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    deleteCategory: vi.fn(),
  },
  authApi: {
    me: vi.fn().mockResolvedValue({
      id: "u1",
      email: "admin@test.com",
      username: "admin",
      role: "admin",
      is_active: true,
      created_at: "",
      updated_at: "",
    }),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue("token"),
}));

import { adminApi } from "../api";

describe("AdminUsersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders user list", async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue(mockUsers);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUsersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Users/)).toBeInTheDocument();
      expect(screen.getByText("john")).toBeInTheDocument();
      expect(screen.getByText("admin@test.com")).toBeInTheDocument();
    });
  });

  it("shows empty state when no users", async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({ users: [], total: 0 });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUsersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no users found/i)).toBeInTheDocument();
    });
  });

  it("displays user status as Active or Blocked", async () => {
    vi.mocked(adminApi.listUsers).mockResolvedValue({
      users: [
        {
          id: "u1",
          email: "a@test.com",
          username: "activeuser",
          role: "user" as const,
          is_active: true,
          created_at: "2024-01-01",
          updated_at: "2024-01-01",
        },
        {
          id: "u2",
          email: "b@test.com",
          username: "blockeduser",
          role: "user" as const,
          is_active: false,
          created_at: "2024-01-02",
          updated_at: "2024-01-02",
        },
      ],
      total: 2,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUsersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText("Active").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Blocked")).toBeInTheDocument();
    });
  });
});
