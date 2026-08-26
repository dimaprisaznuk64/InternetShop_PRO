import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { OrderDetailPage } from "../pages/Orders/OrderDetail";
import type { Order } from "../types";

const mockOrder: Order = {
  id: "ord-1111-1111",
  user_id: "u1",
  status: "pending" as const,
  total: "99.99",
  delivery_method: "standard",
  delivery_address: "123 Main St",
  promo_code_id: null,
  notes: null,
  created_at: "2026-08-15T10:00:00Z",
  updated_at: "2026-08-15T10:00:00Z",
  items: [
    {
      id: "item-1",
      product_id: "p1",
      variant_id: null,
      quantity: 2,
      price: "49.99",
    },
  ] as Order["items"],
};

vi.mock("../api", () => ({
  ordersApi: {
    list: vi.fn(),
    get: vi.fn(),
    checkout: vi.fn(),
    adminList: vi.fn(),
    updateStatus: vi.fn(),
    cancel: vi.fn(),
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

vi.mock("../../contexts/CurrencyContext", () => ({
  useCurrency: () => ({ currency: "UAH", setCurrency: vi.fn() }),
  formatPrice: (v: number | string) => `${v} UAH`,
  CurrencyProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { ordersApi } from "../api";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/orders/:id" element={<OrderDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("OrderDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.WebSocket = vi.fn() as unknown as typeof WebSocket;
  });

  it("renders order detail without crashing", async () => {
    vi.mocked(ordersApi.get).mockResolvedValue(mockOrder);

    renderAt("/orders/ord-1111");

    await waitFor(() => {
      expect(screen.getByText(/99.99/)).toBeInTheDocument();
    });
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("renders cancelled state without crashing", async () => {
    vi.mocked(ordersApi.get).mockResolvedValue({ ...mockOrder, status: "cancelled" });
    renderAt("/orders/ord-1111");
    await waitFor(() => {
      expect(screen.getByText("Cancelled")).toBeInTheDocument();
    });
  });
});
