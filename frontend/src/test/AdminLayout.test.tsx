import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminLayout } from "../components/layout/AdminLayout";

vi.mock("../api", () => ({
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

describe("AdminLayout", () => {
  it("renders sidebar with navigation links", () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText("Admin Panel")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Products")).toBeInTheDocument();
    expect(screen.getByText("Categories")).toBeInTheDocument();
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Orders")).toBeInTheDocument();
    expect(screen.getByText("Promo Codes")).toBeInTheDocument();
  });

  it("renders all 6 navigation links", () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminLayout />
      </MemoryRouter>
    );

    const links = screen.getAllByRole("link");
    expect(links.length).toBe(6);
  });
});
