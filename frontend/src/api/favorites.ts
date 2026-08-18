import api from "./client";
import type { Favorite } from "../types";

export const favoritesApi = {
  list: () =>
    api.get<{ favorites: Favorite[] }>("/api/favorites/").then((r) => r.data),

  add: (productId: string) =>
    api.post<Favorite>(`/api/favorites/${productId}`).then((r) => r.data),

  remove: (productId: string) =>
    api.delete(`/api/favorites/${productId}`).then((r) => r.data),
};
