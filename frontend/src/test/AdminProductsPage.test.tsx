import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AdminProductsPage } from "../pages/Admin/Products";
import { AuthProvider } from "../contexts/AuthContext";

const mockProducts = {
  products: [
    {
      id: "p1",
      name: "iPhone 15",
      slug: "iphone-15",
      description: "Smartphone",
      price: "999.99",
      sku: "IPH-15",
      stock: 25,
      category_id: "c1",
      brand: "Apple",
      is_active: true,
      created_at: "2024-01-01",
      updated_at: "2024-01-01",
      images: [],
      variants: [],
    },
    {
      id: "p2",
      name: "Galaxy S24",
      slug: "galaxy-s24",
      description: "Smartphone",
      price: "849.00",
      sku: "GAL-S24",
      stock: 10,
      category_id: "c1",
      brand: "Samsung",
      is_active: false,
      created_at: "2024-01-02",
      updated_at: "2024-01-02",
      images: [],
      variants: [],
    },
  ],
  total: 2,
  limit: 10,
  offset: 0,
};

const mockCategories = {
  categories: [{ id: "c1", name: "Electronics", slug: "electronics", parent_id: null, image_url: null, created_at: "" }],
  total: 1,
};

vi.mock("../api", () => ({
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

import { productsApi, categoriesApi } from "../api";

describe("AdminProductsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders product list", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminProductsPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Products/)).toBeInTheDocument();
      expect(screen.getByText("iPhone 15")).toBeInTheDocument();
      expect(screen.getByText("Galaxy S24")).toBeInTheDocument();
      expect(screen.getByText("IPH-15")).toBeInTheDocument();
    });
  });

  it("shows empty state when no products", async () => {
    vi.mocked(productsApi.list).mockResolvedValue({ products: [], total: 0, limit: 10, offset: 0 });
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminProductsPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no products found/i)).toBeInTheDocument();
    });
  });

  it("opens create modal", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminProductsPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("iPhone 15")).toBeInTheDocument();
    });

    const addBtn = screen.getByText("+ Add Product");
    await userEvent.click(addBtn);

    expect(screen.getByText("Create Product")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create/i })).toBeInTheDocument();
  });

  it("opens edit modal for a product", async () => {
    vi.mocked(productsApi.list).mockResolvedValue(mockProducts);
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);
    vi.mocked(productsApi.update).mockResolvedValue(mockProducts.products[0]);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminProductsPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("iPhone 15")).toBeInTheDocument();
    });

    const editButtons = screen.getAllByText("Edit");
    await userEvent.click(editButtons[0]);

    expect(screen.getByText("Edit Product")).toBeInTheDocument();
  });
});
