import { Loader2 } from "lucide-react";
import clsx from "clsx";

interface SpinnerProps {
  size?: number;
  className?: string;
}

export function Spinner({ size = 24, className }: SpinnerProps) {
  return (
    <Loader2
      size={size}
      className={clsx("spinner", className)}
      style={{ animation: "spin 0.6s linear infinite" }}
    />
  );
}

export function PageLoader() {
  return (
    <div style={{
      display: "flex", justifyContent: "center", alignItems: "center",
      minHeight: "50vh", flexDirection: "column", gap: "var(--space-3)"
    }}>
      <Spinner size={32} />
      <span style={{ color: "var(--color-text-secondary)", fontSize: "var(--font-size-sm)" }}>
        Завантаження...
      </span>
    </div>
  );
}
