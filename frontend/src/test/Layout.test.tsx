import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Layout } from "../components/layout/Layout";
import { AuthProvider } from "../contexts/AuthContext";
import { CartProvider } from "../contexts/CartContext";

vi.mock("../api", () => ({
  authApi: { me: vi.fn().mockRejectedValue(new Error("no token")) },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue(null),
}));

describe("Layout", () => {
  it("renders header, main content, and footer", () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <CartProvider>
            <Layout />
          </CartProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getAllByText("InternetShop").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/InternetShop PRO/)
    ).toBeInTheDocument();
  });
});
