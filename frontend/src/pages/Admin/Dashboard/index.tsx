import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Users as UsersIcon, Package, ShoppingCart, DollarSign, Star, ArrowRight } from "lucide-react";
import { adminApi, ordersApi, productsApi } from "../../../api";
import type { AdminStats, Order, Product } from "../../../types";

export function DashboardPage() {
  const { t } = useTranslation();
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

  if (loading) return <p className="admin-loading">{t("common.loading")}...</p>;
  if (!stats) return <p className="admin-error">{t("common.error")}</p>;

  return (
    <div className="admin-dashboard container">
      <h1 style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700, marginBottom: "var(--space-6)" }}>
        {t("admin.dashboard")}
      </h1>

      <div className="stats-grid">
        <Link to="/admin/users" className="stat-card stat-card--link">
          <span className="stat-card__icon"><UsersIcon size={20} /></span>
          <h3>{t("admin.users")}</h3>
          <p>{stats.total_users}</p>
          <small>{stats.active_users} active</small>
        </Link>
        <Link to="/admin/products" className="stat-card stat-card--link">
          <span className="stat-card__icon"><Package size={20} /></span>
          <h3>{t("admin.products")}</h3>
          <p>{stats.total_products}</p>
        </Link>
        <Link to="/admin/orders" className="stat-card stat-card--link">
          <span className="stat-card__icon"><ShoppingCart size={20} /></span>
          <h3>{t("admin.orders")}</h3>
          <p>{stats.total_orders}</p>
        </Link>
        <div className="stat-card">
          <span className="stat-card__icon"><DollarSign size={20} /></span>
          <h3>Revenue</h3>
          <p>&#8372;{Number(stats.total_revenue).toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <span className="stat-card__icon"><Star size={20} /></span>
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
                    <td className="admin-table__mono">{order.id.slice(0, 8)}...</td>
                    <td>&#8372;{Number(order.total).toLocaleString()}</td>
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
            View all orders <ArrowRight size={14} />
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
                    <td>&#8372;{Number(product.price).toLocaleString()}</td>
                    <td>{product.stock}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Link to="/admin/products" className="admin-card__footer">
            View all products <ArrowRight size={14} />
          </Link>
        </section>
      </div>
    </div>
  );
}
