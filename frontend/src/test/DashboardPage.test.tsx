import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DashboardPage } from "../pages/Admin/Dashboard";
import { AuthProvider } from "../contexts/AuthContext";

const mockStats = {
  total_users: 150,
  active_users: 120,
  total_products: 85,
  total_orders: 340,
  total_revenue: "12499.50",
  total_reviews: 67,
  average_rating: 4.30,
};

const mockOrders = { orders: [], total: 0 };
const mockProducts = { products: [], total: 0, limit: 20, offset: 0 };

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
  ordersApi: {
    adminList: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
    updateStatus: vi.fn(),
  },
  productsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  categoriesApi: {
    list: vi.fn(),
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

import { adminApi, ordersApi, productsApi } from "../api";

describe("Admin DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays stats", async () => {
    vi.mocked(adminApi.stats).mockResolvedValue(mockStats);
    vi.mocked(ordersApi.adminList).mockResolvedValue(mockOrders);
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
      expect(screen.getByText("150")).toBeInTheDocument();
      expect(screen.getByText("85")).toBeInTheDocument();
      expect(screen.getByText("340")).toBeInTheDocument();
      expect(screen.getByText("67")).toBeInTheDocument();
    });
  });

  it("shows error when stats fail", async () => {
    vi.mocked(adminApi.stats).mockRejectedValue(new Error("500"));
    vi.mocked(ordersApi.adminList).mockResolvedValue(mockOrders);
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });
  });

  it("renders recent orders and latest products sections", async () => {
    vi.mocked(adminApi.stats).mockResolvedValue(mockStats);
    vi.mocked(ordersApi.adminList).mockResolvedValue(mockOrders);
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Recent Orders")).toBeInTheDocument();
      expect(screen.getByText("Latest Products")).toBeInTheDocument();
    });
  });
});
