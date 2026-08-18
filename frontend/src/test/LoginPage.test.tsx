import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "../pages/Auth/LoginPage";
import { AuthProvider } from "../contexts/AuthContext";

vi.mock("../api", () => ({
  authApi: {
    me: vi.fn().mockRejectedValue(new Error("not logged in")),
    login: vi.fn(),
    register: vi.fn(),
  },
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  getAccessToken: vi.fn().mockReturnValue(null),
}));

import { authApi } from "../api";

function renderWithAuth(ui: React.ReactElement) {
  return render(
    <MemoryRouter>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders login form", async () => {
    renderWithAuth(<LoginPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /login/i })).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
  });

  it("shows link to register page", async () => {
    renderWithAuth(<LoginPage />);
    await waitFor(() => {
      expect(screen.getByRole("link", { name: /register/i })).toHaveAttribute(
        "href",
        "/register"
      );
    });
  });

  it("calls login on form submit", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: "a",
      refresh_token: "b",
      token_type: "bearer",
    });
    vi.mocked(authApi.me).mockResolvedValue({
      id: "1",
      email: "t@t.com",
      username: "test",
      role: "user",
      is_active: true,
      created_at: "",
      updated_at: "",
    });

    renderWithAuth(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), "t@t.com");
    await user.type(screen.getByLabelText(/password/i), "pass123");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        email: "t@t.com",
        password: "pass123",
      });
    });
  });

  it("shows error on failed login", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.login).mockRejectedValue(new Error("401"));

    renderWithAuth(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), "bad@bad.com");
    await user.type(screen.getByLabelText(/password/i), "wrong");
    await user.click(screen.getByRole("button", { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });
});
