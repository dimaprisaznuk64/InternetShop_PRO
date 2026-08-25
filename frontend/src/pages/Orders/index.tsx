import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Package, ChevronRight, ShoppingBag } from "lucide-react";
import { ordersApi } from "../../api";
import type { Order } from "../../types";
import { PageLoader } from "../../components/ui/Spinner";
import { EmptyState } from "../../components/ui/EmptyState";
import "./Orders.css";

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  pending: { label: "Pending", className: "status--pending" },
  paid: { label: "Paid", className: "status--paid" },
  processing: { label: "Processing", className: "status--processing" },
  shipped: { label: "Shipped", className: "status--shipped" },
  completed: { label: "Completed", className: "status--completed" },
  cancelled: { label: "Cancelled", className: "status--cancelled" },
};

export function OrdersPage() {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ordersApi.list().then((data) => setOrders(data.orders)).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoader />;

  if (orders.length === 0) {
    return (
      <div className="orders-page">
        <EmptyState
          icon={<ShoppingBag size={48} />}
          title="No orders yet"
          action={{ label: t("cart.continue_shopping"), onClick: () => window.location.href = "/catalog" }}
        />
      </div>
    );
  }

  return (
    <div className="orders-page">
      <h1 className="orders-page__title">{t("nav.orders")}</h1>
      <div className="orders-list">
        {orders.map((order) => {
          const status = STATUS_MAP[order.status] || { label: order.status, className: "" };
          return (
            <Link key={order.id} to={`/orders/${order.id}`} className="order-card">
              <div className="order-card__main">
                <div className="order-card__icon"><Package size={20} /></div>
                <div className="order-card__info">
                  <span className="order-card__id">#{order.id.slice(0, 8)}</span>
                  <span className="order-card__date">{new Date(order.created_at).toLocaleDateString()}</span>
                </div>
                <span className={`order-card__status ${status.className}`}>{status.label}</span>
                <span className="order-card__total">{Number(order.total).toLocaleString()} &#8372;</span>
                <ChevronRight size={16} className="order-card__arrow" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
