import api from "./client";
import type {
  Order,
  OrderListResponse,
  CheckoutRequest,
  OrderStatusUpdate,
} from "../types";

export const ordersApi = {
  checkout: (data: CheckoutRequest) =>
    api.post<Order>("/api/orders/checkout", data).then((r) => r.data),

  list: () =>
    api.get<OrderListResponse>("/api/orders/").then((r) => r.data),

  get: (id: string) =>
    api.get<Order>(`/api/orders/${id}`).then((r) => r.data),

  // Admin
  adminList: (params?: {
    status?: string;
    user_id?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get<OrderListResponse>("/api/orders/admin/all", { params }).then((r) => r.data),

  updateStatus: (id: string, data: OrderStatusUpdate) =>
    api.patch<Order>(`/api/orders/${id}/status`, data).then((r) => r.data),

  cancel: (id: string) =>
    api.post<Order>(`/api/orders/${id}/cancel`).then((r) => r.data),
};
