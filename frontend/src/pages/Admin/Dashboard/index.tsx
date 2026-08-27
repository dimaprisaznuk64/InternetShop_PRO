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
          <small>{stats.active_users} {t("admin.dashboard_stats.active")}</small>
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
          <h3>{t("admin.dashboard_stats.revenue")}</h3>
          <p>&#8372;{Number(stats.total_revenue).toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <span className="stat-card__icon"><Star size={20} /></span>
          <h3>{t("admin.dashboard_stats.reviews")}</h3>
          <p>{stats.total_reviews}</p>
          <small>
            {t("admin.dashboard_stats.avg")}: {stats.average_rating ? Number(stats.average_rating).toFixed(1) : t("admin.dashboard_stats.na")}
          </small>
        </div>
      </div>

      <div className="admin-dashboard__grid">
        <section className="admin-card">
          <h2>{t("admin.dashboard_sections.recent_orders")}</h2>
          {recentOrders.length === 0 ? (
            <p className="admin-empty">{t("admin.dashboard_sections.no_orders")}</p>
          ) : (
            <table className="admin-table admin-table--compact">
              <thead>
                <tr>
                  <th>{t("admin.dashboard_sections.id")}</th>
                  <th>{t("admin.dashboard_sections.total")}</th>
                  <th>{t("admin.dashboard_sections.status")}</th>
                  <th>{t("admin.dashboard_sections.date")}</th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.map((order) => (
                  <tr key={order.id}>
                    <td className="admin-table__mono">{order.id.slice(0, 8)}...</td>
                    <td>&#8372;{Number(order.total).toLocaleString()}</td>
                    <td>
                      <span className={`status-badge status-badge--${order.status}`}>
                        {t(`orders.status_${order.status}`)}
                      </span>
                    </td>
                    <td>{new Date(order.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Link to="/admin/orders" className="admin-card__footer">
            {t("admin.dashboard_sections.view_all_orders")} <ArrowRight size={14} />
          </Link>
        </section>

        <section className="admin-card">
          <h2>{t("admin.dashboard_sections.latest_products")}</h2>
          {topProducts.length === 0 ? (
            <p className="admin-empty">{t("admin.dashboard_sections.no_products")}</p>
          ) : (
            <table className="admin-table admin-table--compact">
              <thead>
                <tr>
                  <th>{t("admin.dashboard_sections.name")}</th>
                  <th>{t("admin.dashboard_sections.price")}</th>
                  <th>{t("admin.dashboard_sections.stock")}</th>
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
            {t("admin.dashboard_sections.view_all_products")} <ArrowRight size={14} />
          </Link>
        </section>
      </div>
    </div>
  );
}
