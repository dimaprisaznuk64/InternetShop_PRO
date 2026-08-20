import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { AdminCategoriesPage } from "../pages/Admin/Categories";
import { AuthProvider } from "../contexts/AuthContext";

const mockCategories = {
  categories: [
    {
      id: "c1",
      name: "Electronics",
      slug: "electronics",
      parent_id: null,
      image_url: null,
      created_at: "2024-01-01",
    },
    {
      id: "c2",
      name: "Phones",
      slug: "phones",
      parent_id: "c1",
      image_url: null,
      created_at: "2024-01-02",
    },
  ],
  total: 2,
};

vi.mock("../api", () => ({
  categoriesApi: {
    list: vi.fn(),
  },
  adminApi: {
    stats: vi.fn(),
    listUsers: vi.fn(),
    blockUser: vi.fn(),
    unblockUser: vi.fn(),
    changeRole: vi.fn(),
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    deleteCategory: vi.fn(),
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

import { categoriesApi } from "../api";

describe("AdminCategoriesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders category list", async () => {
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminCategoriesPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Categories/)).toBeInTheDocument();
      expect(screen.getAllByText("Electronics").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Phones")).toBeInTheDocument();
    });
  });

  it("shows parent category name", async () => {
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminCategoriesPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText("Electronics").length).toBe(2);
    });
  });

  it("shows empty state when no categories", async () => {
    vi.mocked(categoriesApi.list).mockResolvedValue({ categories: [] });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminCategoriesPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no categories found/i)).toBeInTheDocument();
    });
  });

  it("opens create modal", async () => {
    vi.mocked(categoriesApi.list).mockResolvedValue(mockCategories);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminCategoriesPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText("Electronics").length).toBeGreaterThanOrEqual(1);
    });

    await userEvent.click(screen.getByText("+ Add Category"));

    expect(screen.getByText("Create Category")).toBeInTheDocument();
  });
});
