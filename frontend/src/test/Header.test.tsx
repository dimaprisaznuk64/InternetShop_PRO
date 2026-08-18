import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Header } from "../components/layout/Header";
import { AuthProvider } from "../contexts/AuthContext";
import { CartProvider } from "../contexts/CartContext";

vi.mock("../api", () => ({
  authApi: { me: vi.fn().mockRejectedValue(new Error("no token")) },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue(null),
}));

describe("Header", () => {
  it("renders logo and login/register links when not authenticated", async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <Header />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );
    expect(screen.getByText("InternetShop")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /login/i })).toHaveAttribute(
      "href",
      "/login"
    );
    expect(screen.getByRole("link", { name: /register/i })).toHaveAttribute(
      "href",
      "/register"
    );
  });

  it("renders catalog link always", async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <Header />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: /catalog/i })).toHaveAttribute(
      "href",
      "/catalog"
    );
  });
});
