import api from "./client";
import type { Cart, CartItemAdd, CartItemUpdate } from "../types";

export const cartApi = {
  get: () =>
    api.get<Cart>("/api/cart/").then((r) => r.data),

  addItem: (data: CartItemAdd) =>
    api.post<Cart>("/api/cart/items", data).then((r) => r.data),

  updateItem: (itemId: string, data: CartItemUpdate) =>
    api.put<Cart>(`/api/cart/items/${itemId}`, data).then((r) => r.data),

  removeItem: (itemId: string) =>
    api.delete(`/api/cart/items/${itemId}`).then((r) => r.data),

  clear: () =>
    api.delete("/api/cart/").then((r) => r.data),
};
