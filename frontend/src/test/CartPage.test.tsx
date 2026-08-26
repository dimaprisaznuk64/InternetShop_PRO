import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CartPage } from "../pages/Cart";
import { CartProvider } from "../contexts/CartContext";
import { AuthProvider } from "../contexts/AuthContext";

const mockCart = {
  id: "c1",
  items_count: 2,
  items: [
    {
      id: "item1",
      product_id: "p1",
      variant_id: null,
      quantity: 2,
      product_name: "Test Product",
      product_price: "25.00",
      product_sku: "T001",
      product_image: null,
      product_stock: 10,
      variant_name: null,
      line_total: "50.00",
    },
  ],
  subtotal: "50.00",
};

vi.mock("../api", () => ({
  cartApi: {
    get: vi.fn(),
    addItem: vi.fn(),
    updateItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
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

import { cartApi } from "../api";

describe("CartPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty cart message when cart is empty", async () => {
    vi.mocked(cartApi.get).mockResolvedValue({
      id: "c1",
      items_count: 0,
      items: [],
      subtotal: "0.00",
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <CartPage />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument();
    });
  });

  it("displays cart items with correct info", async () => {
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <CartPage />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Test Product")).toBeInTheDocument();
      expect(screen.getByText("25 ₴")).toBeInTheDocument();
      expect(screen.getByText("Shopping Cart")).toBeInTheDocument();
    });

    const total50 = screen.getAllByText((_content, el) =>
      (el?.classList.contains("cart-item__total") &&
        el?.textContent?.includes("50")) ?? false
    );
    expect(total50.length).toBeGreaterThanOrEqual(1);
  });

  it("shows proceed to checkout link", async () => {
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <CartPage />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("link", { name: /checkout/i })).toHaveAttribute(
        "href",
        "/checkout"
      );
    });
  });

  it("shows item count in header", async () => {
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <CartPage />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("2 items")).toBeInTheDocument();
    });
  });
});
