import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ordersApi } from "../../api";
import type { Order } from "../../types";

const STATUS_COLORS: Record<string, string> = {
  pending: "#f0ad4e",
  paid: "#5bc0de",
  processing: "#0275d8",
  shipped: "#5cb85c",
  completed: "#333",
  cancelled: "#d9534f",
};

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    ordersApi
      .get(id)
      .then(setOrder)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p>Loading order...</p>;
  if (!order) return <p>Order not found.</p>;

  return (
    <div className="order-detail">
      <nav className="breadcrumb">
        <Link to="/">Home</Link>
        <span>/</span>
        <Link to="/orders">Orders</Link>
        <span>/</span>
        <span>{order.id.slice(0, 8)}...</span>
      </nav>

      <h1>Order {order.id.slice(0, 8)}...</h1>

      <div className="order-detail__grid">
        <div className="order-detail__section">
          <h3>Status</h3>
          <span
            className="status-badge"
            style={{ backgroundColor: STATUS_COLORS[order.status] || "#999" }}
          >
            {order.status}
          </span>
          <p className="order-detail__date">
            Created: {new Date(order.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="order-detail__section">
          <h3>Delivery</h3>
          <p>Method: {order.delivery_method || "Standard"}</p>
          <p>Address: {order.delivery_address || "—"}</p>
        </div>

        <div className="order-detail__section">
          <h3>Total</h3>
          <p className="order-detail__total">${Number(order.total).toFixed(2)}</p>
          {order.notes && <p className="order-detail__notes">Note: {order.notes}</p>}
        </div>
      </div>

      {order.items.length > 0 && (
        <>
          <h3>Items</h3>
          <table className="orders-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Variant</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Total</th>
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
                  <td>{item.variant?.name ?? "—"}</td>
                  <td>${Number(item.price).toFixed(2)}</td>
                  <td>{item.quantity}</td>
                  <td>
                    ${(Number(item.price) * item.quantity).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
