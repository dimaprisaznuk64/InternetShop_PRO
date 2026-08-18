import { useState, useEffect } from "react";
import { adminApi } from "../../../api";
import type { AdminStats } from "../../../types";

export function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi
      .stats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading statistics...</p>;
  if (!stats) return <p>Failed to load statistics.</p>;

  return (
    <div className="admin-dashboard">
      <h1>Admin Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Users</h3>
          <p>{stats.total_users}</p>
          <small>{stats.active_users} active</small>
        </div>
        <div className="stat-card">
          <h3>Products</h3>
          <p>{stats.total_products}</p>
        </div>
        <div className="stat-card">
          <h3>Orders</h3>
          <p>{stats.total_orders}</p>
        </div>
        <div className="stat-card">
          <h3>Revenue</h3>
          <p>${Number(stats.total_revenue).toFixed(2)}</p>
        </div>
        <div className="stat-card">
          <h3>Reviews</h3>
          <p>{stats.total_reviews}</p>
          <small>
            Avg: {stats.average_rating ? stats.average_rating.toFixed(1) : "N/A"}
          </small>
        </div>
      </div>
    </div>
  );
}
