import api from "./client";
import type { Review, ReviewCreate } from "../types";

export const reviewsApi = {
  listByProduct: (productId: string) =>
    api
      .get<{ reviews: Review[] }>(`/api/reviews/product/${productId}`)
      .then((r) => r.data),

  create: (data: ReviewCreate) =>
    api.post<Review>("/api/reviews/", data).then((r) => r.data),

  delete: (reviewId: string) =>
    api.delete(`/api/reviews/${reviewId}`).then((r) => r.data),

  moderate: (reviewId: string) =>
    api
      .patch<Review>(`/api/reviews/${reviewId}/moderate`)
      .then((r) => r.data),
};
