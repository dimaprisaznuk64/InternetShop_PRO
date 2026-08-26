import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OrdersPage } from "../pages/Orders";
import { AuthProvider } from "../contexts/AuthContext";
import type { Order } from "../types";

const mockOrders: Order[] = [
  {
    id: "ord-1111-1111-1111",
    user_id: "u1",
    status: "pending" as const,
    total: "99.99",
    delivery_method: "standard",
    delivery_address: "123 Main St",
    promo_code_id: null,
    notes: null,
    created_at: "2026-08-15T10:00:00Z",
    updated_at: "2026-08-15T10:00:00Z",
    items: [],
  },
  {
    id: "ord-2222-2222-2222",
    user_id: "u1",
    status: "completed" as const,
    total: "45.00",
    delivery_method: "express",
    delivery_address: "456 Oak Ave",
    promo_code_id: null,
    notes: null,
    created_at: "2026-08-10T14:30:00Z",
    updated_at: "2026-08-12T09:00:00Z",
    items: [],
  },
];

vi.mock("../api", () => ({
  ordersApi: {
    list: vi.fn(),
    get: vi.fn(),
    checkout: vi.fn(),
    adminList: vi.fn(),
    updateStatus: vi.fn(),
  },
  authApi: {
    me: vi.fn().mockResolvedValue({
      id: "u1",
      email: "t@t.com",
      username: "test",
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

vi.mock("../contexts/CurrencyContext", () => ({
  useCurrency: () => ({ currency: "USD", setCurrency: vi.fn() }),
  formatPrice: (v: number | string) => `$${v}`,
}));

import { ordersApi } from "../api";

describe("OrdersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading then renders orders", async () => {
    vi.mocked(ordersApi.list).mockResolvedValue({
      orders: mockOrders,
      total: 2,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <OrdersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Orders")).toBeInTheDocument();
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
      expect(screen.getByText("$99.99")).toBeInTheDocument();
    });
  });

  it("shows empty message when no orders", async () => {
    vi.mocked(ordersApi.list).mockResolvedValue({ orders: [], total: 0 });

    render(
      <MemoryRouter>
        <AuthProvider>
          <OrdersPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no orders yet/i)).toBeInTheDocument();
    });
  });
});
