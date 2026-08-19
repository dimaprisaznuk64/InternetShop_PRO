import api from "./client";
import type {
  AdminStats,
  UserResponse,
  AdminUserListResponse,
  Category,
  CategoryCreate,
  CategoryUpdate,
  PromoCode,
  PromoCodeCreate,
} from "../types";

export const adminApi = {
  stats: () =>
    api.get<AdminStats>("/api/admin/stats").then((r) => r.data),

  // ─── Users ───────────────────────────────────────────────────────
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

  // ─── Categories (admin) ──────────────────────────────────────────
  createCategory: (data: CategoryCreate) =>
    api.post<Category>("/api/categories/", data).then((r) => r.data),

  updateCategory: (id: string, data: CategoryUpdate) =>
    api.put<Category>(`/api/categories/${id}`, data).then((r) => r.data),

  deleteCategory: (id: string) =>
    api.delete(`/api/categories/${id}`).then((r) => r.data),

  // ─── Promo Codes ─────────────────────────────────────────────────
  listPromoCodes: () =>
    api
      .get<{ promo_codes: PromoCode[]; total: number }>("/api/promo-codes/")
      .then((r) => r.data),

  createPromoCode: (data: PromoCodeCreate) =>
    api.post<PromoCode>("/api/promo-codes/", data).then((r) => r.data),

  deletePromoCode: (id: string) =>
    api.delete(`/api/promo-codes/${id}`).then((r) => r.data),
};
