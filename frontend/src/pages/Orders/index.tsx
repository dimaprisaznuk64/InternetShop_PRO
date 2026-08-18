import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
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

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ordersApi
      .list()
      .then((data) => setOrders(data.orders))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading orders...</p>;

  if (orders.length === 0) {
    return (
      <div className="orders-empty">
        <h2>No orders yet</h2>
        <Link to="/catalog" className="btn btn--primary">
          Browse Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="orders-page">
      <h1>My Orders</h1>

      <table className="orders-table">
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Status</th>
            <th>Total</th>
            <th>Date</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td>{order.id.slice(0, 8)}...</td>
              <td>
                <span
                  className="status-badge"
                  style={{
                    backgroundColor: STATUS_COLORS[order.status] || "#999",
                  }}
                >
                  {order.status}
                </span>
              </td>
              <td>${Number(order.total).toFixed(2)}</td>
              <td>{new Date(order.created_at).toLocaleDateString()}</td>
              <td>
                <Link to={`/orders/${order.id}`}>Details</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
