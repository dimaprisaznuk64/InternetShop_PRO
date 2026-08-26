import api from "./client";
import type {
  Product,
  ProductListResponse,
  ProductCreate,
  ProductUpdate,
  ProductFilterParams,
  ProductImage,
  ProductImageCreate,
  ProductVariant,
  ProductVariantCreate,
  ProductVariantUpdate,
} from "../types";

export const productsApi = {
  list: (params?: ProductFilterParams) =>
    api.get<ProductListResponse>("/api/products/", { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Product>(`/api/products/${id}`).then((r) => r.data),

  create: (data: ProductCreate) =>
    api.post<Product>("/api/products/", data).then((r) => r.data),

  update: (id: string, data: ProductUpdate) =>
    api.put<Product>(`/api/products/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/api/products/${id}`).then((r) => r.data),

  // Images
  listImages: (productId: string) =>
    api
      .get<{ images: ProductImage[] }>(`/api/products/${productId}/images/`)
      .then((r) => r.data),

  addImage: (productId: string, data: ProductImageCreate) =>
    api
      .post<ProductImage>(`/api/products/${productId}/images/`, data)
      .then((r) => r.data),

  deleteImage: (productId: string, imageId: string) =>
    api
      .delete(`/api/products/${productId}/images/${imageId}`)
      .then((r) => r.data),

  // Variants
  listVariants: (productId: string) =>
    api
      .get<{ variants: ProductVariant[] }>(
        `/api/products/${productId}/variants/`
      )
      .then((r) => r.data),

  getVariant: (productId: string, variantId: string) =>
    api
      .get<ProductVariant>(
        `/api/products/${productId}/variants/${variantId}`
      )
      .then((r) => r.data),

  createVariant: (productId: string, data: ProductVariantCreate) =>
    api
      .post<ProductVariant>(`/api/products/${productId}/variants/`, data)
      .then((r) => r.data),

  updateVariant: (
    productId: string,
    variantId: string,
    data: ProductVariantUpdate
  ) =>
    api
      .put<ProductVariant>(
        `/api/products/${productId}/variants/${variantId}`,
        data
      )
      .then((r) => r.data),

  deleteVariant: (productId: string, variantId: string) =>
    api
      .delete(`/api/products/${productId}/variants/${variantId}`)
      .then((r) => r.data),

  priceHistory: (productId: string, days: number = 90) =>
    api
      .get<{ date: string; old_price: number; new_price: number }[]>(
        `/api/products/${productId}/price-history`,
        { params: { days } }
      )
      .then((r) => r.data),
};
