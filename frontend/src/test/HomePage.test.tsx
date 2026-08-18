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
      screen.getByRole("heading", { name: /welcome to internetshop/i })
    ).toBeInTheDocument();
  });

  it("renders link to catalog", () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: /browse catalog/i })).toHaveAttribute(
      "href",
      "/catalog"
    );
  });
});
