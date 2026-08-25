import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { adminApi, ordersApi, productsApi } from "../../../api";
import type { AdminStats, Order, Product } from "../../../types";

export function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [topProducts, setTopProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      adminApi.stats(),
      ordersApi.adminList({ limit: 5 }),
      productsApi.list({ limit: 5, sort_by: "created_at", sort_order: "desc" }),
    ])
      .then(([statsData, ordersData, productsData]) => {
        setStats(statsData);
        setRecentOrders(ordersData.orders);
        setTopProducts(productsData.products);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="admin-loading">Loading dashboard...</p>;
  if (!stats) return <p className="admin-error">Failed to load statistics.</p>;

  return (
    <div className="admin-dashboard container">
      <h1>Dashboard</h1>

      <div className="stats-grid">
        <Link to="/admin/users" className="stat-card stat-card--link">
          <h3>Users</h3>
          <p>{stats.total_users}</p>
          <small>{stats.active_users} active</small>
        </Link>
        <Link to="/admin/products" className="stat-card stat-card--link">
          <h3>Products</h3>
          <p>{stats.total_products}</p>
        </Link>
        <Link to="/admin/orders" className="stat-card stat-card--link">
          <h3>Orders</h3>
          <p>{stats.total_orders}</p>
        </Link>
        <div className="stat-card">
          <h3>Revenue</h3>
          <p>${Number(stats.total_revenue).toFixed(2)}</p>
        </div>
        <div className="stat-card">
          <h3>Reviews</h3>
          <p>{stats.total_reviews}</p>
          <small>
            Avg: {stats.average_rating ? Number(stats.average_rating).toFixed(1) : "N/A"}
          </small>
        </div>
      </div>

      <div className="admin-dashboard__grid">
        <section className="admin-card">
          <h2>Recent Orders</h2>
          {recentOrders.length === 0 ? (
            <p className="admin-empty">No orders yet.</p>
          ) : (
            <table className="admin-table admin-table--compact">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.id.slice(0, 8)}...</td>
                    <td>${Number(order.total).toFixed(2)}</td>
                    <td>
                      <span className={`status-badge status-badge--${order.status}`}>
                        {order.status}
                      </span>
                    </td>
                    <td>{new Date(order.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Link to="/admin/orders" className="admin-card__footer">
            View all orders
          </Link>
        </section>

        <section className="admin-card">
          <h2>Latest Products</h2>
          {topProducts.length === 0 ? (
            <p className="admin-empty">No products yet.</p>
          ) : (
            <table className="admin-table admin-table--compact">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Stock</th>
                </tr>
              </thead>
              <tbody>
                {topProducts.map((product) => (
                  <tr key={product.id}>
                    <td>{product.name}</td>
                    <td>${Number(product.price).toFixed(2)}</td>
                    <td>{product.stock}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Link to="/admin/products" className="admin-card__footer">
            View all products
          </Link>
        </section>
      </div>
    </div>
  );
}
