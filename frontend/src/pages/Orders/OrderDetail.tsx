import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ordersApi } from "../../api";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import { useOrderWS } from "../../hooks/useOrderWS";
import { OrderDetailSkeleton } from "../../components/ui/Skeleton";
import type { Order } from "../../types";

const CANCELABLE_STATUSES = new Set(["pending", "paid"]);

const STATUS_STEPS = [
  { key: "pending", labelKey: "orders.step_accepted" },
  { key: "paid", labelKey: "orders.step_paid" },
  { key: "processing", labelKey: "orders.step_assembling" },
  { key: "shipped", labelKey: "orders.step_shipped" },
  { key: "completed", labelKey: "orders.step_delivered" },
];

function statusToIndex(status: string): number {
  const idx = STATUS_STEPS.findIndex((s) => s.key === status);
  return idx >= 0 ? idx : 0;
}

export function OrderDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { currency } = useCurrency();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  const { status: wsStatus, setStatus: setWsStatus, wsState } = useOrderWS(id);

  useEffect(() => {
    if (!id) return;
    ordersApi
      .get(id)
      .then((o) => {
        setOrder(o);
        setWsStatus(o.status);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id, setWsStatus]);

  const handleCancel = async () => {
    if (!order) return;
    if (!window.confirm(t("orders.confirmCancel"))) return;
    setCancelling(true);
    try {
      const updated = await ordersApi.cancel(order.id);
      setOrder(updated);
      setWsStatus(updated.status);
    } catch (err: any) {
      alert(err?.response?.data?.detail || t("orders.cancelFailed"));
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <OrderDetailSkeleton />;
  if (!order) return <p>{t("orders.notFound")}</p>;

  const activeStatus = wsStatus || order.status;
  const activeIdx = statusToIndex(activeStatus);
  const isCancelled = activeStatus === "cancelled";

  // 30-minute cancellation window for paid orders (matches backend ORDER_CANCEL_WINDOW_MINUTES)
  const CANCEL_WINDOW_MIN = 30;
  const deadline = new Date(order.created_at).getTime() + CANCEL_WINDOW_MIN * 60_000;
  const minutesLeft = Math.max(0, Math.ceil((deadline - Date.now()) / 60_000));
  const windowExpired = activeStatus === "paid" && minutesLeft <= 0;
  const canCancel =
    CANCELABLE_STATUSES.has(activeStatus) &&
    !(activeStatus === "paid" && windowExpired);

  return (
    <div className="order-detail container">
      <nav className="breadcrumb">
        <Link to="/">{t("common.home")}</Link>
        <span>/</span>
        <Link to="/orders">{t("nav.orders")}</Link>
        <span>/</span>
        <span>{order.id.slice(0, 8)}...</span>
      </nav>

      <div className="admin-page-header">
        <h1>{t("orders.title")} #{order.id.slice(0, 8)}</h1>
        {canCancel && (
          <button className="btn btn--danger" onClick={handleCancel} disabled={cancelling}>
            {cancelling ? t("common.loading") : t("common.cancel")}
          </button>
        )}
      </div>

      {activeStatus === "pending" && (
        <p className="order-tracker__hint">{t("orders.cancel_hint", { minutes: CANCEL_WINDOW_MIN })}</p>
      )}
      {windowExpired && (
        <p className="order-tracker__hint order-tracker__hint--expired">{t("orders.cancel_expired")}</p>
      )}

      {/* Real-time progress tracker */}
      <div className="order-tracker">
        <div className="order-tracker__ws">
          {wsState === "connected" && (
            <span className="order-tracker__live">{t("orders.live") || "LIVE"}</span>
          )}
          {wsState === "connecting" && (
            <span className="order-tracker__connecting">{t("common.loading")}</span>
          )}
        </div>

        <div className="order-tracker__steps">
          {STATUS_STEPS.map((step, i) => {
            let cls = "order-tracker__step";
            if (isCancelled) {
              cls += i === 0 ? " order-tracker__step--active" : "";
            } else if (i < activeIdx) {
              cls += " order-tracker__step--done";
            } else if (i === activeIdx) {
              cls += " order-tracker__step--active";
            }
            return (
              <div key={step.key} className={cls}>
                <div className="order-tracker__dot">
                  {i < activeIdx && !isCancelled ? "\u2713" : ""}
                </div>
                <div className="order-tracker__label">{t(step.labelKey)}</div>
                {i < STATUS_STEPS.length - 1 && (
                  <div className={`order-tracker__line ${i < activeIdx && !isCancelled ? "order-tracker__line--done" : ""}`} />
                )}
              </div>
            );
          })}
        </div>

        {isCancelled && (
          <div className="order-tracker__cancelled">{t("orders.cancelled")}</div>
        )}
      </div>

      <div className="order-detail__grid">
        <div className="order-detail__section">
          <h3>{t("orders.status")}</h3>
          <span className={`status-badge status-badge--${activeStatus}`}>
            {t(`orders.status_${activeStatus}`, activeStatus)}
          </span>
          <p className="order-detail__date">
            {t("orders.created")}: {new Date(order.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="order-detail__section">
          <h3>{t("checkout.delivery")}</h3>
          <p>{t("checkout.delivery_method")}: {order.delivery_method || t("orders.standard")}</p>
          <p>{t("checkout.delivery_address")}: {order.delivery_address || "\u2014"}</p>
        </div>

        <div className="order-detail__section">
          <h3>{t("cart.total")}</h3>
          <p className="order-detail__total">{formatPrice(order.total, currency)}</p>
          {order.notes && <p className="order-detail__notes">{t("orders.note")}: {order.notes}</p>}
        </div>
      </div>

      {order.items.length > 0 && (
        <>
          <h3>{t("orders.items")}</h3>
          <table className="orders-table">
            <thead>
              <tr>
                <th>{t("orders.product")}</th>
                <th>{t("orders.variant")}</th>
                <th>{t("orders.price")}</th>
                <th>{t("orders.qty")}</th>
                <th>{t("orders.total")}</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <Link to={`/catalog/${item.product_id}`}>
                      {item.product?.name ?? item.product_id}
                    </Link>
                  </td>
                  <td>{item.variant?.name ?? "\u2014"}</td>
                  <td>{formatPrice(item.price, currency)}</td>
                  <td>{item.quantity}</td>
                  <td>{formatPrice(Number(item.price) * item.quantity, currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
