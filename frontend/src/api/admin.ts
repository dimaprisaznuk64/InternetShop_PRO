import api from "./client";
import type { AdminStats, UserResponse, AdminUserListResponse } from "../types";

export const adminApi = {
  stats: () =>
    api.get<AdminStats>("/api/admin/stats").then((r) => r.data),

  listUsers: (params?: {
    q?: string;
    role?: string;
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }) =>
    api.get<AdminUserListResponse>("/api/admin/users", { params }).then((r) => r.data),

  blockUser: (userId: string) =>
    api.patch<UserResponse>(`/api/admin/users/${userId}/block`).then((r) => r.data),

  unblockUser: (userId: string) =>
    api.patch<UserResponse>(`/api/admin/users/${userId}/unblock`).then((r) => r.data),

  changeRole: (userId: string, role: string) =>
    api
      .patch<UserResponse>(`/api/admin/users/${userId}/role`, null, {
        params: { role },
      })
      .then((r) => r.data),
};
