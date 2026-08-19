import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminOrdersPage } from "../pages/Admin/Orders";
import { AuthProvider } from "../contexts/AuthContext";

const mockOrders = {
  orders: [
    {
      id: "order-1111-2222-3333",
      user_id: "user-aaaa-bbbb-cccc",
      status: "paid" as const,
      total: "199.99",
      delivery_method: "courier",
      delivery_address: "123 Main St",
      promo_code_id: null,
      notes: null,
      created_at: "2024-06-15T10:00:00Z",
      updated_at: "2024-06-15T10:00:00Z",
      items: [],
    },
  ],
  total: 1,
};

vi.mock("../api", () => ({
  ordersApi: {
    adminList: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
    updateStatus: vi.fn(),
  },
  adminApi: {
    stats: vi.fn(),
    listUsers: vi.fn(),
    blockUser: vi.fn(),
    unblockUser: vi.fn(),
    changeRole: vi.fn(),
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

import { ordersApi } from "../api";

describe("AdminOrdersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders order list with status", async () => {
    vi.mocked(ordersApi.adminList).mockResolvedValue(mockOrders);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminOrdersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Orders/)).toBeInTheDocument();
      expect(screen.getByText("$199.99")).toBeInTheDocument();
    });
  });

  it("shows empty state when no orders", async () => {
    vi.mocked(ordersApi.adminList).mockResolvedValue({ orders: [], total: 0 });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminOrdersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no orders found/i)).toBeInTheDocument();
    });
  });

  it("displays status filter", async () => {
    vi.mocked(ordersApi.adminList).mockResolvedValue(mockOrders);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminOrdersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("All statuses")).toBeInTheDocument();
    });
  });
});
