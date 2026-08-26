import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Heart, ShoppingCart, Star, ChevronRight, Minus, Plus, Check } from "lucide-react";
import { productsApi, reviewsApi, favoritesApi } from "../../api";
import { useAuth } from "../../contexts/AuthContext";
import { useCart } from "../../contexts/CartContext";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import { categoryName } from "../../i18n/category";
import type { Product, Review, ProductVariant } from "../../types";
import { PageLoader } from "../../components/ui/Spinner";
import "./Product.css";

export function ProductPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { addItem } = useCart();
  const { currency } = useCurrency();
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [addedToCart, setAddedToCart] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [selectedImage, setSelectedImage] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      productsApi.get(id),
      reviewsApi.listByProduct(id).catch(() => ({ reviews: [] })),
      user
        ? favoritesApi.list().catch(() => ({ favorites: [] }))
        : Promise.resolve({ favorites: [] }),
    ])
      .then(([productData, reviewData, favData]) => {
        setProduct(productData);
        setReviews(reviewData.reviews);
        if (productData.variants?.length) {
          setSelectedVariant(productData.variants[0]);
        }
        setIsFavorite(favData.favorites.some((f) => f.product_id === productData.id));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id, user]);

  const currentPrice = selectedVariant ? Number(selectedVariant.price) : Number(product?.price ?? 0);
  const currentStock = selectedVariant ? selectedVariant.stock : product?.stock ?? 0;

  const handleAddToCart = async () => {
    if (!product) return;
    try {
      await addItem(product.id, quantity, selectedVariant?.id);
      setAddedToCart(true);
      setTimeout(() => setAddedToCart(false), 2000);
    } catch (err) {
      console.error("Failed to add to cart", err);
    }
  };

  const handleToggleFavorite = async () => {
    if (!product) return;
    try {
      if (isFavorite) await favoritesApi.remove(product.id);
      else await favoritesApi.add(product.id);
      setIsFavorite(!isFavorite);
    } catch (err) {
      console.error("Failed to toggle favorite", err);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      const review = await reviewsApi.create({ product_id: id, rating, text: reviewText || undefined });
      setReviews((prev) => [...prev, review]);
      setReviewText("");
      setRating(5);
    } catch (err) {
      console.error("Failed to submit review", err);
    }
  };

  const averageRating = reviews.length > 0
    ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
    : null;

  const handleVariantSelect = useCallback((variant: ProductVariant) => {
    setSelectedVariant(variant);
    setSelectedImage(0);
    setQuantity(1);
  }, []);

  const isLightColor = (hex: string): boolean => {
    const c = hex.replace("#", "");
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    return (r * 299 + g * 587 + b * 114) / 1000 > 150;
  };

  if (loading) return <PageLoader />;
  if (!product) return <div className="product-page__error">Product not found</div>;

  const sortedImages = [...(product.images ?? [])].sort((a, b) => a.position - b.position);
  const filteredImages = selectedVariant
    ? sortedImages.filter((img) => img.variant_id === selectedVariant.id || !img.variant_id)
    : sortedImages;
  const displayImages = filteredImages.length > 0 ? filteredImages : sortedImages;

  return (
    <div className="product-page container">
      {/* Breadcrumbs */}
      <nav className="breadcrumb">
        <Link to="/">{t("nav.home")}</Link>
        <ChevronRight size={14} />
        <Link to="/catalog">{t("nav.catalog")}</Link>
        {product.category && (
          <>
            <ChevronRight size={14} />
            <Link to={`/catalog?category_id=${product.category.id}`}>{categoryName(product.category, t)}</Link>
          </>
        )}
        <ChevronRight size={14} />
        <span className="breadcrumb__current">{product.name}</span>
      </nav>

      <div className="product-page__content">
        {/* Images */}
        <div className="product-page__gallery">
          {displayImages.length > 0 ? (
            <>
              <div className="product-page__main-image">
                <img src={displayImages[selectedImage]?.url} alt={product.name} />
              </div>
              {displayImages.length > 1 && (
                <div className="product-page__thumbnails">
                  {displayImages.map((img, i) => (
                    <button
                      key={img.id}
                      className={`product-page__thumb ${i === selectedImage ? "product-page__thumb--active" : ""}`}
                      onClick={() => setSelectedImage(i)}
                    >
                      <img src={img.url} alt={`Photo ${i + 1}`} />
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="product-page__no-image">{"\u{1F4F1}"}</div>
          )}
        </div>

        {/* Details */}
        <div className="product-page__info">
          {product.brand && <span className="product-page__brand">{product.brand}</span>}
          <h1 className="product-page__name">{product.name}</h1>

          {averageRating !== null && (
            <div className="product-page__rating">
              <div className="product-page__stars">
                {[1, 2, 3, 4, 5].map((n) => (
                  <Star key={n} size={16} className={n <= Math.round(averageRating) ? "star-filled" : "star-empty"} fill={n <= Math.round(averageRating) ? "currentColor" : "none"} />
                ))}
              </div>
              <span className="product-page__rating-text">
                {averageRating.toFixed(1)} ({reviews.length} {reviews.length === 1 ? "review" : "reviews"})
              </span>
            </div>
          )}

          <div className="product-page__price">{formatPrice(currentPrice, currency)}</div>

          <div className="product-page__meta">
            <span>SKU: {product.sku}</span>
            <span className={currentStock > 0 ? "stock--available" : "stock--unavailable"}>
              {currentStock > 0 ? `${t("product.in_stock")} (${currentStock})` : t("product.out_of_stock")}
            </span>
          </div>

          {product.description && (
            <p className="product-page__desc">{product.description}</p>
          )}

          {/* Color Variants */}
          {product.variants?.length ? (
            <div className="product-page__variants">
              <h4 className="product-page__section-title">
                {t("product.color")}: <span>{selectedVariant?.name}</span>
              </h4>
              <div className="product-page__color-list">
                {product.variants.map((v) => (
                  <button
                    key={v.id}
                    className={`color-swatch ${selectedVariant?.id === v.id ? "color-swatch--active" : ""} ${v.stock === 0 ? "color-swatch--disabled" : ""}`}
                    style={{ backgroundColor: v.color || "#ccc" }}
                    onClick={() => handleVariantSelect(v)}
                    disabled={v.stock === 0}
                    title={v.name}
                  >
                    {selectedVariant?.id === v.id && (
                      <span className="color-swatch__check" style={{ color: isLightColor(v.color || "#ccc") ? "#000" : "#fff" }}>
                        &#10003;
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {/* Add to cart */}
          {currentStock > 0 && (
            <div className="product-page__purchase">
              <div className="product-page__quantity">
                <button
                  className="quantity-btn"
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  disabled={quantity <= 1}
                >
                  <Minus size={16} />
                </button>
                <span className="quantity-value">{quantity}</span>
                <button
                  className="quantity-btn"
                  onClick={() => setQuantity(Math.min(currentStock, quantity + 1))}
                  disabled={quantity >= currentStock}
                >
                  <Plus size={16} />
                </button>
              </div>
              <button className="btn btn--primary btn--lg product-page__add-btn" onClick={handleAddToCart}>
                {addedToCart ? <><Check size={18} /> {t("product.added")}</> : <><ShoppingCart size={18} /> {t("product.add_to_cart")}</>}
              </button>
              {user && (
                <button className={`product-page__fav-btn ${isFavorite ? "product-page__fav-btn--active" : ""}`} onClick={handleToggleFavorite}>
                  <Heart size={20} fill={isFavorite ? "currentColor" : "none"} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Reviews */}
      <section className="product-page__reviews">
        <h2 className="product-page__reviews-title">{t("product.reviews")} ({reviews.length})</h2>

        {user && (
          <form onSubmit={handleSubmitReview} className="review-form">
            <div className="review-form__rating">
              <span>{t("product.rating")}:</span>
              <div className="review-form__stars">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} type="button" className={`review-form__star ${n <= rating ? "review-form__star--active" : ""}`} onClick={() => setRating(n)}>
                    <Star size={20} fill={n <= rating ? "currentColor" : "none"} />
                  </button>
                ))}
              </div>
            </div>
            <textarea className="review-form__textarea" placeholder={t("product.write_review")} value={reviewText} onChange={(e) => setReviewText(e.target.value)} rows={3} />
            <button type="submit" className="btn btn--primary btn--sm">{t("product.submit_review")}</button>
          </form>
        )}

        {reviews.length === 0 ? (
          <p className="product-page__no-reviews">{t("product.no_reviews")}</p>
        ) : (
          <div className="reviews-list">
            {reviews.map((review) => (
              <div key={review.id} className="review-card">
                <div className="review-card__header">
                  <div className="review-card__stars">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star key={n} size={14} className={n <= review.rating ? "star-filled" : "star-empty"} fill={n <= review.rating ? "currentColor" : "none"} />
                    ))}
                  </div>
                  <span className="review-card__date">{new Date(review.created_at).toLocaleDateString()}</span>
                </div>
                {review.text && <p className="review-card__text">{review.text}</p>}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
