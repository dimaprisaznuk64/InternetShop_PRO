import clsx from "clsx";
import "./Badge.css";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "primary" | "success" | "warning" | "danger" | "info";
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
}

export function Badge({
  children,
  variant = "default",
  size = "sm",
  dot,
  className,
}: BadgeProps) {
  return (
    <span className={clsx("badge", `badge--${variant}`, `badge--${size}`, className)}>
      {dot && <span className="badge__dot" />}
      {children}
    </span>
  );
}
