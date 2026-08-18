import api from "./client";
import type { Payment, PaymentCreate } from "../types";

export const paymentsApi = {
  create: (data: PaymentCreate) =>
    api.post<Payment>("/api/payments/", data).then((r) => r.data),

  list: () =>
    api.get<{ payments: Payment[] }>("/api/payments/").then((r) => r.data),

  get: (id: string) =>
    api.get<Payment>(`/api/payments/${id}`).then((r) => r.data),
};
