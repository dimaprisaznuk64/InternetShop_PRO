import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { CommandPalette, useCommandPalette } from "../ui/CommandPalette";

export function Layout() {
  const { open, setOpen } = useCommandPalette();

  return (
    <div className="app">
      <Header />
      <main className="main">
        <Outlet />
      </main>
      <Footer />
      <CommandPalette open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
