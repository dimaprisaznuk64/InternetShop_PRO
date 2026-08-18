import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { type ReactNode } from "react";
import { CartProvider, useCart } from "../contexts/CartContext";
import { AuthProvider } from "../contexts/AuthContext";

const mockUser = {
  id: "u1",
  email: "test@test.com",
  username: "tester",
  role: "user" as const,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockCart = {
  id: "c1",
  user_id: "u1",
  items: [
    {
      id: "item1",
      cart_id: "c1",
      product_id: "p1",
      variant_id: null,
      quantity: 2,
      product: {
        id: "p1",
        name: "Widget",
        slug: "widget",
        description: null,
        price: "19.99",
        sku: "W001",
        stock: 10,
        category_id: "cat1",
        brand: null,
        is_active: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        images: [],
        variants: [],
      },
    },
  ],
  subtotal: "39.98",
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
    me: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn(),
}));

import { cartApi, authApi, getAccessToken } from "../api";

function wrapper({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <CartProvider>{children}</CartProvider>
    </AuthProvider>
  );
}

describe("CartContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches cart on mount when user is logged in", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    const { result } = renderHook(() => useCart(), { wrapper });

    await waitFor(() => expect(result.current.cart).not.toBeNull());
    expect(result.current.cart).toEqual(mockCart);
    expect(result.current.itemCount).toBe(2);
  });

  it("cart is null when no user", async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);
    const { result } = renderHook(() => useCart(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.cart).toBeNull();
    expect(result.current.itemCount).toBe(0);
  });

  it("addItem calls cartApi and updates cart", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    const updatedCart = { ...mockCart, items: [...mockCart.items] };
    vi.mocked(cartApi.addItem).mockResolvedValue(updatedCart);

    const { result } = renderHook(() => useCart(), { wrapper });
    await waitFor(() => expect(result.current.cart).toEqual(mockCart));

    await act(async () => {
      await result.current.addItem("p2", 1);
    });

    expect(cartApi.addItem).toHaveBeenCalledWith({
      product_id: "p2",
      quantity: 1,
      variant_id: null,
    });
    expect(result.current.cart).toEqual(updatedCart);
  });

  it("updateItem calls cartApi and updates cart", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    const updatedCart = { ...mockCart, subtotal: "59.97" };
    vi.mocked(cartApi.updateItem).mockResolvedValue(updatedCart);

    const { result } = renderHook(() => useCart(), { wrapper });
    await waitFor(() => expect(result.current.cart).toEqual(mockCart));

    await act(async () => {
      await result.current.updateItem("item1", 3);
    });

    expect(cartApi.updateItem).toHaveBeenCalledWith("item1", { quantity: 3 });
  });

  it("removeItem calls cartApi and updates cart", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);

    const emptyCart = { ...mockCart, items: [], subtotal: "0" };
    vi.mocked(cartApi.removeItem).mockResolvedValue(emptyCart);

    const { result } = renderHook(() => useCart(), { wrapper });
    await waitFor(() => expect(result.current.cart).toEqual(mockCart));

    await act(async () => {
      await result.current.removeItem("item1");
    });

    expect(cartApi.removeItem).toHaveBeenCalledWith("item1");
    expect(result.current.itemCount).toBe(0);
  });

  it("clear empties the cart", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(authApi.me).mockResolvedValue(mockUser);
    vi.mocked(cartApi.get).mockResolvedValue(mockCart);
    vi.mocked(cartApi.clear).mockResolvedValue(undefined as never);

    const { result } = renderHook(() => useCart(), { wrapper });
    await waitFor(() => expect(result.current.cart).toEqual(mockCart));

    await act(async () => {
      await result.current.clear();
    });

    expect(cartApi.clear).toHaveBeenCalled();
    expect(result.current.cart).toBeNull();
  });

  it("throws if useCart used outside provider", () => {
    expect(() => {
      renderHook(() => useCart());
    }).toThrow("useCart must be used within CartProvider");
  });
});
