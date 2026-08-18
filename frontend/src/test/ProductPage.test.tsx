import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProductPage } from "../pages/Product";
import { CartProvider } from "../contexts/CartContext";
import { AuthProvider } from "../contexts/AuthContext";

const mockProduct = {
  id: "p1",
  name: "Test Widget",
  slug: "test-widget",
  description: "A widget for testing",
  price: "49.99",
  sku: "TW001",
  stock: 15,
  category_id: "cat1",
  brand: "TestBrand",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  images: [],
  variants: [
    {
      id: "v1",
      product_id: "p1",
      name: "Small",
      sku: "TW001-S",
      price: "49.99",
      stock: 8,
      attributes: '{"size":"S"}',
    },
    {
      id: "v2",
      product_id: "p1",
      name: "Large",
      sku: "TW001-L",
      price: "59.99",
      stock: 7,
      attributes: '{"size":"L"}',
    },
  ],
};

vi.mock("../api", () => ({
  productsApi: { get: vi.fn(), list: vi.fn() },
  reviewsApi: {
    listByProduct: vi.fn().mockResolvedValue({ reviews: [] }),
    create: vi.fn(),
  },
  authApi: { me: vi.fn().mockRejectedValue(new Error("no token")) },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue(null),
}));

import { productsApi } from "../api";

function renderProduct(id = "p1") {
  return render(
    <MemoryRouter initialEntries={[`/catalog/${id}`]}>
      <AuthProvider>
        <CartProvider>
          <Routes>
            <Route path="/catalog/:id" element={<ProductPage />} />
          </Routes>
        </CartProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("ProductPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders product details", async () => {
    vi.mocked(productsApi.get).mockResolvedValue(mockProduct);

    renderProduct();

    await waitFor(() => {
      expect(screen.getByText("Test Widget")).toBeInTheDocument();
      expect(screen.getByText("TestBrand")).toBeInTheDocument();
      expect(screen.getByText("SKU: TW001")).toBeInTheDocument();
      expect(screen.getByText("A widget for testing")).toBeInTheDocument();
    });

    expect(screen.getAllByText(/49\.99/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("15 in stock")).toBeInTheDocument();
  });

  it("renders product variants", async () => {
    vi.mocked(productsApi.get).mockResolvedValue(mockProduct);

    renderProduct();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Variants" })).toBeInTheDocument();
      expect(screen.getByText(/Small.*49\.99/)).toBeInTheDocument();
      expect(screen.getByText(/Large.*59\.99/)).toBeInTheDocument();
    });
  });

  it("shows out of stock message for zero stock", async () => {
    vi.mocked(productsApi.get).mockResolvedValue({
      ...mockProduct,
      stock: 0,
    });

    renderProduct();

    await waitFor(() => {
      expect(screen.getByText("Out of stock")).toBeInTheDocument();
    });
  });

  it("shows reviews section heading", async () => {
    vi.mocked(productsApi.get).mockResolvedValue(mockProduct);

    renderProduct();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /reviews/i })).toBeInTheDocument();
    });
  });

  it("shows back to catalog link", async () => {
    vi.mocked(productsApi.get).mockResolvedValue(mockProduct);

    renderProduct();

    await waitFor(() => {
      expect(screen.getByText(/back to catalog/i)).toHaveAttribute(
        "href",
        "/catalog"
      );
    });
  });
});
