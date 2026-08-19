import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AdminPromoPage } from "../pages/Admin/Promo";
import { AuthProvider } from "../contexts/AuthContext";

const mockPromoCodes = {
  promo_codes: [
    {
      id: "promo1",
      code: "WELCOME10",
      discount_type: "percentage" as const,
      discount_value: "10",
      min_order_amount: null,
      max_uses: 100,
      used_count: 25,
      expires_at: null,
      is_active: true,
    },
    {
      id: "promo2",
      code: "SALE20",
      discount_type: "fixed" as const,
      discount_value: "20",
      min_order_amount: "50",
      max_uses: 50,
      used_count: 50,
      expires_at: "2024-12-31T23:59:59Z",
      is_active: true,
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

describe("AdminPromoPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders promo code list", async () => {
    vi.mocked(adminApi.listPromoCodes).mockResolvedValue(mockPromoCodes);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPromoPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Promo Codes/)).toBeInTheDocument();
      expect(screen.getByText("WELCOME10")).toBeInTheDocument();
      expect(screen.getByText("SALE20")).toBeInTheDocument();
    });
  });

  it("displays discount values correctly", async () => {
    vi.mocked(adminApi.listPromoCodes).mockResolvedValue(mockPromoCodes);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPromoPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("10%")).toBeInTheDocument();
      expect(screen.getByText("$20.00")).toBeInTheDocument();
    });
  });

  it("shows empty state when no promo codes", async () => {
    vi.mocked(adminApi.listPromoCodes).mockResolvedValue({ promo_codes: [], total: 0 });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPromoPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no promo codes found/i)).toBeInTheDocument();
    });
  });

  it("opens create modal", async () => {
    vi.mocked(adminApi.listPromoCodes).mockResolvedValue(mockPromoCodes);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminPromoPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("WELCOME10")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("+ Add Promo Code"));

    expect(screen.getByText("Create Promo Code")).toBeInTheDocument();
  });
});
