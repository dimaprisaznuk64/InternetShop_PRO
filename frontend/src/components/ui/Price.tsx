import clsx from "clsx";

interface PriceProps {
  value: string | number;
  currency?: string;
  oldPrice?: string | number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Price({
  value,
  currency = "₴",
  oldPrice,
  size = "md",
  className,
}: PriceProps) {
  const num = typeof value === "string" ? parseFloat(value) : value;
  const formatted = num.toLocaleString("uk-UA", { minimumFractionDigits: 0, maximumFractionDigits: 2 });

  return (
    <div className={clsx("price", `price--${size}`, className)}>
      {oldPrice && (
        <span className="price__old">
          {parseFloat(typeof oldPrice === "string" ? oldPrice : String(oldPrice)).toLocaleString("uk-UA")} {currency}
        </span>
      )}
      <span className={clsx("price__current", oldPrice && "price__current--sale")}>
        {formatted} {currency}
      </span>
    </div>
  );
}
