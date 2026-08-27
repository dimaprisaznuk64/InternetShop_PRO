import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { adminApi } from "../../../api";
import type { UserResponse } from "../../../types";
import { useAuth } from "../../../contexts/AuthContext";

const PAGE_SIZE = 20;

export function AdminUsersPage() {
  const { t } = useTranslation();
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [page, setPage] = useState(0);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminApi.listUsers({
        q: search || undefined,
        role: roleFilter || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
      setUsers(data.users);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, page]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleBlock = async (userId: string) => {
    await adminApi.blockUser(userId);
    fetchUsers();
  };

  const handleUnblock = async (userId: string) => {
    await adminApi.unblockUser(userId);
    fetchUsers();
  };

  const handleRoleChange = async (userId: string, role: string) => {
    await adminApi.changeRole(userId, role);
    fetchUsers();
  };

  return (
    <div className="admin-users container">
      <h1>{t("admin.users_page.title", { total })}</h1>

      <div className="admin-filters">
        <input
          type="text"
          placeholder={t("admin.users_page.search_placeholder")}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
        />
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(0); }}
        >
          <option value="">{t("admin.users_page.all_roles")}</option>
          <option value="user">{t("admin.users_page.role_user")}</option>
          <option value="manager">{t("admin.users_page.role_manager")}</option>
          <option value="admin">{t("admin.users_page.role_admin")}</option>
        </select>
      </div>

      {loading ? (
        <p className="admin-loading">{t("admin.users_page.loading")}</p>
      ) : users.length === 0 ? (
        <p className="admin-empty">{t("admin.users_page.empty")}</p>
      ) : (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>{t("admin.users_page.username")}</th>
                <th>{t("admin.users_page.email")}</th>
                <th>{t("admin.users_page.role")}</th>
                <th>{t("admin.users_page.status")}</th>
                <th>{t("admin.users_page.joined")}</th>
                <th>{t("admin.users_page.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => {
                const isSelf = currentUser?.id === user.id;
                return (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>
                      <select
                        className="admin-select"
                        value={user.role}
                        disabled={isSelf}
                        onChange={(e) =>
                          handleRoleChange(user.id, e.target.value)
                        }
                      >
                        <option value="user">{t("admin.users_page.role_user")}</option>
                        <option value="manager">{t("admin.users_page.role_manager")}</option>
                        <option value="admin">{t("admin.users_page.role_admin")}</option>
                      </select>
                    </td>
                    <td>
                      <span className={`badge badge--${user.is_active ? "success" : "muted"}`}>
                        {user.is_active ? t("admin.users_page.active") : t("admin.users_page.blocked")}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td className="admin-table__actions">
                      {isSelf ? (
                        <span className="badge badge--info">{t("admin.users_page.role_admin")}</span>
                      ) : user.is_active ? (
                        <button className="btn btn--sm btn--danger" onClick={() => handleBlock(user.id)}>
                          {t("admin.users_page.block")}
                        </button>
                      ) : (
                        <button className="btn btn--sm btn--success" onClick={() => handleUnblock(user.id)}>
                          {t("admin.users_page.unblock")}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="admin-pagination">
              <button
                className="btn btn--sm"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                {t("admin.users_page.previous")}
              </button>
              <span>
                {t("admin.users_page.page_of", { page: page + 1, total: totalPages })}
              </span>
              <button
                className="btn btn--sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                {t("admin.users_page.next")}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
