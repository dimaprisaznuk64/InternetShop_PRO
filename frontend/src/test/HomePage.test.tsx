import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "../pages/Home";

describe("HomePage", () => {
  it("renders welcome heading", () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );
    expect(
      screen.getByRole("heading", { name: /technology you want to own/i })
    ).toBeInTheDocument();
  });

  it("renders link to catalog", () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );
    expect(screen.getAllByRole("link", { name: /shop now/i })[0]).toHaveAttribute(
      "href",
      "/catalog"
    );
  });
});
