import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { TrendingDown, TrendingUp } from "lucide-react";
import { productsApi } from "../../api";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import "./PriceHistory.css";

interface PricePoint {
  date: string;
  old_price: number;
  new_price: number;
}

interface Props {
  productId: string;
}

export function PriceHistory({ productId }: Props) {
  const { t } = useTranslation();
  const { currency } = useCurrency();
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);

  useEffect(() => {
    setLoading(true);
    productsApi
      .priceHistory(productId, days)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [productId, days]);

  if (loading) {
    return <div className="ph ph--loading">{t("common.loading")}</div>;
  }

  if (history.length === 0) {
    return null;
  }

  const allPrices = history.flatMap((h) => [h.old_price, h.new_price]);
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);
  const priceRange = maxPrice - minPrice || 1;

  const latestChange = history[history.length - 1];
  const isDown = latestChange.new_price < latestChange.old_price;

  return (
    <div className="ph">
      <div className="ph__header">
        <h3 className="ph__title">{t("product.priceHistory")}</h3>
        <div className="ph__filters">
          {[30, 90, 365].map((d) => (
            <button
              key={d}
              className={`ph__filter ${d === days ? "ph__filter--active" : ""}`}
              onClick={() => setDays(d)}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      <div className="ph__trend">
        {isDown ? (
          <span className="ph__trend--down">
            <TrendingDown size={14} /> {t("product.priceDropped")}
          </span>
        ) : (
          <span className="ph__trend--up">
            <TrendingUp size={14} /> {t("product.priceIncreased")}
          </span>
        )}
      </div>

      <div className="ph__chart">
        <svg viewBox={`0 0 600 120`} className="ph__svg" preserveAspectRatio="none">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((frac) => (
            <line
              key={frac}
              x1={0}
              y1={120 - frac * 110}
              x2={600}
              y2={120 - frac * 110}
              stroke="var(--color-border)"
              strokeWidth={0.5}
              strokeDasharray={frac > 0 && frac < 1 ? "4 4" : "0"}
            />
          ))}

          {/* Area fill */}
          <path
            d={
              history.length === 1
                ? `M0,${120 - ((history[0].new_price - minPrice) / priceRange) * 110} L600,${120 - ((history[0].new_price - minPrice) / priceRange) * 110} L600,120 L0,120 Z`
                : history
                    .map((h, i) => {
                      const x = (i / (history.length - 1)) * 600;
                      const y = 120 - ((h.new_price - minPrice) / priceRange) * 110;
                      return `${i === 0 ? "M" : "L"}${x},${y}`;
                    })
                    .join(" ") +
                  ` L600,120 L0,120 Z`
            }
            fill="var(--color-accent-subtle)"
            opacity={0.3}
          />

          {/* Line */}
          <path
            d={
              history.length === 1
                ? `M0,${120 - ((history[0].new_price - minPrice) / priceRange) * 110} L600,${120 - ((history[0].new_price - minPrice) / priceRange) * 110}`
                : history
                    .map((h, i) => {
                      const x = (i / (history.length - 1)) * 600;
                      const y = 120 - ((h.new_price - minPrice) / priceRange) * 110;
                      return `${i === 0 ? "M" : "L"}${x},${y}`;
                    })
                    .join(" ")
            }
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth={2}
            strokeLinejoin="round"
          />

          {/* Dots */}
          {history.map((h, i) => {
            const x = (i / Math.max(history.length - 1, 1)) * 600;
            const y = 120 - ((h.new_price - minPrice) / priceRange) * 110;
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={3}
                fill="var(--color-accent)"
                stroke="var(--color-surface)"
                strokeWidth={1.5}
              />
            );
          })}
        </svg>
      </div>

      <div className="ph__axis">
        <span>{new Date(history[0].date).toLocaleDateString()}</span>
        <span>{new Date(history[history.length - 1].date).toLocaleDateString()}</span>
      </div>

      <div className="ph__legend">
        <span className="ph__legend-item">
          {t("product.current")}: <strong>{formatPrice(history[history.length - 1].new_price, currency)}</strong>
        </span>
        {isDown && (
          <span className="ph__legend-item ph__legend-item--down">
            -{((1 - latestChange.new_price / latestChange.old_price) * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );
}
