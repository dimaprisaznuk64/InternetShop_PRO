import { useState, useEffect, useCallback } from "react";
import { adminApi } from "../../../api";
import type { UserResponse } from "../../../types";

const PAGE_SIZE = 20;

export function AdminUsersPage() {
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
    <div className="admin-users">
      <h1>Users ({total})</h1>

      <div className="admin-filters">
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
        />
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(0); }}
        >
          <option value="">All roles</option>
          <option value="user">User</option>
          <option value="manager">Manager</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {loading ? (
        <p className="admin-loading">Loading...</p>
      ) : users.length === 0 ? (
        <p className="admin-empty">No users found.</p>
      ) : (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>
                    <select
                      className="admin-select"
                      value={user.role}
                      onChange={(e) =>
                        handleRoleChange(user.id, e.target.value)
                      }
                    >
                      <option value="user">user</option>
                      <option value="manager">manager</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td>
                    <span className={`badge badge--${user.is_active ? "success" : "muted"}`}>
                      {user.is_active ? "Active" : "Blocked"}
                    </span>
                  </td>
                  <td>{new Date(user.created_at).toLocaleDateString()}</td>
                  <td className="admin-table__actions">
                    {user.is_active ? (
                      <button className="btn btn--sm btn--danger" onClick={() => handleBlock(user.id)}>
                        Block
                      </button>
                    ) : (
                      <button className="btn btn--sm btn--success" onClick={() => handleUnblock(user.id)}>
                        Unblock
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="admin-pagination">
              <button
                className="btn btn--sm"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span>
                Page {page + 1} of {totalPages}
              </span>
              <button
                className="btn btn--sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
