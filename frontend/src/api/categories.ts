import api from "./client";
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
} from "../types";

export const categoriesApi = {
  list: () =>
    api.get<{ categories: Category[] }>("/api/categories/").then((r) => r.data),

  get: (id: string) =>
    api.get<Category>(`/api/categories/${id}`).then((r) => r.data),

  create: (data: CategoryCreate) =>
    api.post<Category>("/api/categories/", data).then((r) => r.data),

  update: (id: string, data: CategoryUpdate) =>
    api.put<Category>(`/api/categories/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/api/categories/${id}`).then((r) => r.data),
};
