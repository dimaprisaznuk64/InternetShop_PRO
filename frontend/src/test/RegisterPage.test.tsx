import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { RegisterPage } from "../pages/Auth/RegisterPage";
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

const emailInput = () => screen.getByPlaceholderText("you@example.com");
const usernameInput = () => screen.getByPlaceholderText("username");
const passwordInputs = () => screen.getAllByPlaceholderText("••••••••");

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders register form with all fields", () => {
    renderWithAuth(<RegisterPage />);
    expect(screen.getByRole("heading", { name: /create account/i })).toBeInTheDocument();
    expect(emailInput()).toBeInTheDocument();
    expect(usernameInput()).toBeInTheDocument();
    expect(passwordInputs()[0]).toBeInTheDocument();
    expect(passwordInputs()[1]).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("shows link to login page", () => {
    renderWithAuth(<RegisterPage />);
    expect(screen.getByRole("link", { name: /login/i })).toHaveAttribute(
      "href",
      "/login"
    );
  });

  it("shows password mismatch error", async () => {
    const user = userEvent.setup();
    renderWithAuth(<RegisterPage />);

    await user.type(emailInput(), "test@test.com");
    await user.type(usernameInput(), "tester");
    await user.type(passwordInputs()[0], "pass123");
    await user.type(passwordInputs()[1], "pass456");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it("shows password toggle button", () => {
    const { container } = renderWithAuth(<RegisterPage />);
    expect(container.querySelector(".auth-field__toggle")).toBeInTheDocument();
  });

  it("calls register on valid form submit", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.register).mockResolvedValue({
      id: "1",
      email: "new@new.com",
      username: "newuser",
      role: "user",
      is_active: true,
      created_at: "",
      updated_at: "",
    });
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: "a",
      refresh_token: "b",
      token_type: "bearer",
    });
    vi.mocked(authApi.me).mockResolvedValue({
      id: "1",
      email: "new@new.com",
      username: "newuser",
      role: "user",
      is_active: true,
      created_at: "",
      updated_at: "",
    });

    renderWithAuth(<RegisterPage />);

    await user.type(emailInput(), "new@new.com");
    await user.type(usernameInput(), "newuser");
    await user.type(passwordInputs()[0], "pass123");
    await user.type(passwordInputs()[1], "pass123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith({
        email: "new@new.com",
        username: "newuser",
        password: "pass123",
      });
    });
  });

  it("shows error on failed registration", async () => {
    const user = userEvent.setup();
    vi.mocked(authApi.register).mockRejectedValue(new Error("409"));

    renderWithAuth(<RegisterPage />);

    await user.type(emailInput(), "dup@dup.com");
    await user.type(usernameInput(), "dup");
    await user.type(passwordInputs()[0], "pass123");
    await user.type(passwordInputs()[1], "pass123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
    });
  });
});
