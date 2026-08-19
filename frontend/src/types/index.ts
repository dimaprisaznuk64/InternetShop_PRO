// ─── Auth ──────────────────────────────────────────────────────────
export interface UserRegister {
  email: string;
  username: string;
  password: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  role: "user" | "manager" | "admin";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

// ─── Categories ────────────────────────────────────────────────────
export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  image_url: string | null;
  created_at: string;
}

export interface CategoryCreate {
  name: string;
  slug: string;
  parent_id?: string | null;
  image_url?: string | null;
}

export interface CategoryUpdate {
  name?: string;
  slug?: string;
  parent_id?: string | null;
  image_url?: string | null;
}

// ─── Products ──────────────────────────────────────────────────────
export interface ProductImage {
  id: string;
  product_id: string;
  url: string;
  is_primary: boolean;
  position: number;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  price: string;
  stock: number;
  attributes: string | null;
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  price: string;
  sku: string;
  stock: number;
  category_id: string;
  brand: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category?: Category;
  images: ProductImage[];
  variants: ProductVariant[];
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductCreate {
  name: string;
  slug: string;
  description?: string;
  price: string;
  sku: string;
  stock: number;
  category_id: string;
  brand?: string;
  is_active?: boolean;
}

export interface ProductUpdate {
  name?: string;
  slug?: string;
  description?: string;
  price?: string;
  sku?: string;
  stock?: number;
  category_id?: string;
  brand?: string;
  is_active?: boolean;
}

export interface ProductImageCreate {
  url: string;
  is_primary?: boolean;
  position?: number;
}

export interface ProductVariantCreate {
  name: string;
  sku: string;
  price: string;
  stock: number;
  attributes?: string;
}

export interface ProductVariantUpdate {
  name?: string;
  sku?: string;
  price?: string;
  stock?: number;
  attributes?: string;
}

// ─── Cart ──────────────────────────────────────────────────────────
export interface CartItem {
  id: string;
  cart_id: string;
  product_id: string;
  variant_id: string | null;
  quantity: number;
  product?: Product;
  variant?: ProductVariant;
}

export interface Cart {
  id: string;
  user_id: string;
  items: CartItem[];
  subtotal: string;
}

export interface CartItemAdd {
  product_id: string;
  variant_id?: string | null;
  quantity: number;
}

export interface CartItemUpdate {
  quantity: number;
}

// ─── Orders ────────────────────────────────────────────────────────
export type OrderStatus =
  | "pending"
  | "paid"
  | "processing"
  | "shipped"
  | "completed"
  | "cancelled";

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  variant_id: string | null;
  quantity: number;
  price: string;
  product?: Product;
  variant?: ProductVariant;
}

export interface Order {
  id: string;
  user_id: string;
  status: OrderStatus;
  total: string;
  delivery_method: string | null;
  delivery_address: string | null;
  promo_code_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
}

export interface CheckoutRequest {
  delivery_method?: string;
  delivery_address?: string;
  promo_code?: string;
  notes?: string;
}

export interface OrderStatusUpdate {
  status: OrderStatus;
}

// ─── Payments ──────────────────────────────────────────────────────
export type PaymentStatus = "pending" | "success" | "failed" | "refunded";

export interface Payment {
  id: string;
  order_id: string;
  amount: string;
  method: string;
  status: PaymentStatus;
  provider_payment_id: string | null;
  created_at: string;
}

export interface PaymentCreate {
  order_id: string;
  method: string;
}

// ─── Favorites ─────────────────────────────────────────────────────
export interface Favorite {
  id: string;
  user_id: string;
  product_id: string;
  product?: Product;
}

// ─── Reviews ───────────────────────────────────────────────────────
export interface Review {
  id: string;
  user_id: string;
  product_id: string;
  rating: number;
  text: string | null;
  is_moderated: boolean;
  created_at: string;
}

export interface ReviewCreate {
  product_id: string;
  rating: number;
  text?: string;
}

// ─── Promo Codes ───────────────────────────────────────────────────
export type DiscountType = "percentage" | "fixed";

export interface PromoCode {
  id: string;
  code: string;
  discount_type: DiscountType;
  discount_value: string;
  min_order_amount: string | null;
  max_uses: number | null;
  used_count: number;
  expires_at: string | null;
  is_active: boolean;
}

export interface PromoCodeCreate {
  code: string;
  discount_type: DiscountType;
  discount_value: string;
  min_order_amount?: string;
  max_uses?: number;
  expires_at?: string;
}

export interface PromoCodeApply {
  code: string;
}

// ─── Admin ─────────────────────────────────────────────────────────
export interface AdminStats {
  total_users: number;
  active_users: number;
  total_products: number;
  total_orders: number;
  total_revenue: string;
  total_reviews: number;
  average_rating: number | null;
}

export interface AdminUserListResponse {
  users: UserResponse[];
  total: number;
}

export interface AdminCategoryListResponse {
  categories: Category[];
  total: number;
}

export interface AdminPromoListResponse {
  promo_codes: PromoCode[];
  total: number;
}

export interface AdminOrderListResponse {
  orders: Order[];
  total: number;
}

// ─── Pagination ────────────────────────────────────────────────────
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface ProductFilterParams extends PaginationParams {
  q?: string;
  category_id?: string;
  min_price?: string;
  max_price?: string;
  in_stock?: boolean;
  brand?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
