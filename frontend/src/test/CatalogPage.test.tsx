import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CatalogPage } from "../pages/Catalog";
import { AuthProvider } from "../contexts/AuthContext";

const mockProducts = {
  products: [
    {
      id: "p1",
      name: "Laptop Pro",
      slug: "laptop-pro",
      description: "A powerful laptop",
      price: "1299.99",
      sku: "LP001",
      stock: 5,
      category_id: "cat1",
      brand: "TechBrand",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      images: [],
      variants: [],
    },
    {
      id: "p2",
      name: "Mouse Basic",
      slug: "mouse-basic",
      description: null,
      price: "12.50",
      sku: "MB001",
      stock: 0,
      category_id: "cat2",
      brand: null,
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      images: [],
      variants: [],
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
};

const mockCategories = {
  categories: [
    {
      id: "cat1",
      name: "Laptops",
      slug: "laptops",
      parent_id: null,
      image_url: null,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "cat2",
      name: "Accessories",
      slug: "accessories",
      parent_id: null,
      image_url: null,
      created_at: "2026-01-01T00:00:00Z",
    },
  ],
};

vi.mock("../api", () => ({
  productsApi: { list: vi.fn(), get: vi.fn() },
  categoriesApi: { list: vi.fn() },
  authApi: { me: vi.fn().mockRejectedValue(new Error("no token")) },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue(null),
}));

import { productsApi, categoriesApi } from "../api";

describe("CatalogPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders products and categories", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Laptop Pro")).toBeInTheDocument();
      expect(screen.getByText("Mouse Basic")).toBeInTheDocument();
      expect(screen.getByText("Laptops")).toBeInTheDocument();
      expect(screen.getByText("Accessories")).toBeInTheDocument();
    });

    expect(screen.getAllByText(/1299\.99/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/12\.50/).length).toBeGreaterThanOrEqual(1);
  });

  it("shows out of stock for zero stock products", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText("Out of stock").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows search form", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search products/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
    });
  });

  it("shows no products message when empty", async () => {
    vi.mocked(productsApi.list).mockResolvedValue({
      products: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no products found/i)).toBeInTheDocument();
    });
  });

  it("shows product count", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("2 products found")).toBeInTheDocument();
    });
  });

  it("shows brand on product cards", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText("TechBrand").length).toBeGreaterThanOrEqual(2);
    });
  });

  it("shows sort controls", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Sort by:")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Newest")).toBeInTheDocument();
    });
  });

  it("shows price filter inputs", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText("Min")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Max")).toBeInTheDocument();
    });
  });

  it("shows availability filter buttons", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "In Stock" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Out of Stock" })).toBeInTheDocument();
    });
  });

  it("passes filter params to API", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter initialEntries={["/catalog?q=laptop&category_id=cat1&sort_by=price&sort_order=asc"]}>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(productsApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          q: "laptop",
          category_id: "cat1",
          sort_by: "price",
          sort_order: "asc",
        })
      );
    });
  });

  it("shows stock count for in-stock products", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <CatalogPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("5 in stock")).toBeInTheDocument();
    });
  });
});
