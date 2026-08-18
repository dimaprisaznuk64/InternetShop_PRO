import api from "./client";
import type {
  PromoCode,
  PromoCodeCreate,
  PromoCodeApply,
  DiscountType,
} from "../types";

export const promoApi = {
  list: () =>
    api
      .get<{ promo_codes: PromoCode[] }>("/api/promo-codes/")
      .then((r) => r.data),

  create: (data: PromoCodeCreate) =>
    api.post<PromoCode>("/api/promo-codes/", data).then((r) => r.data),

  apply: (code: string) =>
    api
      .post<{ code: string; discount_type: DiscountType; discount_value: string }>(
        "/api/promo-codes/apply",
        { code } as PromoCodeApply
      )
      .then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/api/promo-codes/${id}`).then((r) => r.data),
};
