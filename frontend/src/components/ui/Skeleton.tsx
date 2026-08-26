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

export function OrderCardSkeleton() {
  return (
    <div className="skeleton-order">
      <Skeleton variant="circular" width={40} height={40} />
      <div className="skeleton-order__info">
        <Skeleton width={90} height={14} />
        <Skeleton width={120} height={12} />
      </div>
      <Skeleton width={70} height={14} />
      <Skeleton width={80} height={16} />
    </div>
  );
}

export function OrderDetailSkeleton() {
  return (
    <div className="skeleton-order-detail container">
      <Skeleton width={220} height={16} />
      <Skeleton width={280} height={32} />
      <Skeleton variant="rectangular" height={140} />
      <div className="skeleton-order-detail__grid">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} variant="rectangular" height={110} />
        ))}
      </div>
      <Skeleton variant="rectangular" height={180} />
    </div>
  );
}

export function ListRowSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="skeleton-list">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton-list__row">
          <Skeleton variant="circular" width={36} height={36} />
          <div className="skeleton-list__lines">
            <Skeleton width={`${70 - i * 8}%`} height={14} />
            <Skeleton width={`${45 - i * 5}%`} height={12} />
          </div>
          <Skeleton width={60} height={14} />
        </div>
      ))}
    </div>
  );
}
