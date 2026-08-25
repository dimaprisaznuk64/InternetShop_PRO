import clsx from "clsx";
import "./Skeleton.css";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: "text" | "circular" | "rectangular" | "card";
  className?: string;
}

export function Skeleton({
  width,
  height,
  variant = "text",
  className,
}: SkeletonProps) {
  return (
    <div
      className={clsx("skeleton", `skeleton--${variant}`, className)}
      style={{ width, height }}
    />
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="skeleton-card">
      <Skeleton variant="rectangular" className="skeleton-card__image" />
      <div className="skeleton-card__body">
        <Skeleton width="60%" height={14} />
        <Skeleton width="80%" height={18} />
        <Skeleton width="40%" height={14} />
        <Skeleton width="50%" height={20} />
      </div>
    </div>
  );
}
