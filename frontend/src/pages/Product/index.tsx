import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { productsApi, reviewsApi, favoritesApi } from "../../api";
import { useAuth } from "../../contexts/AuthContext";
import { useCart } from "../../contexts/CartContext";
import type { Product, Review, ProductVariant } from "../../types";

export function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { addItem } = useCart();
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
        setIsFavorite(
          favData.favorites.some((f) => f.product_id === productData.id)
        );
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id, user]);

  const currentPrice = selectedVariant
    ? Number(selectedVariant.price)
    : Number(product?.price ?? 0);
  const currentStock = selectedVariant
    ? selectedVariant.stock
    : product?.stock ?? 0;
  const currentSku = selectedVariant ? selectedVariant.sku : product?.sku ?? "";

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
      if (isFavorite) {
        await favoritesApi.remove(product.id);
      } else {
        await favoritesApi.add(product.id);
      }
      setIsFavorite(!isFavorite);
    } catch (err) {
      console.error("Failed to toggle favorite", err);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      const review = await reviewsApi.create({
        product_id: id,
        rating,
        text: reviewText || undefined,
      });
      setReviews((prev) => [...prev, review]);
      setReviewText("");
      setRating(5);
    } catch (err) {
      console.error("Failed to submit review", err);
    }
  };

  const averageRating =
    reviews.length > 0
      ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
      : null;

  const handleVariantSelect = useCallback(
    (variant: ProductVariant) => {
      setSelectedVariant(variant);
      setQuantity(1);
    },
    []
  );

  if (loading) return <p>Loading...</p>;
  if (!product) return <p>Product not found.</p>;

  const sortedImages = [...(product.images ?? [])].sort(
    (a, b) => a.position - b.position
  );

  return (
    <div className="product-page">
      <nav className="breadcrumb">
        <Link to="/">Home</Link>
        <span>/</span>
        <Link to="/catalog">Catalog</Link>
        {product.category && (
          <>
            <span>/</span>
            <Link to={`/catalog?category_id=${product.category.id}`}>
              {product.category.name}
            </Link>
          </>
        )}
        <span>/</span>
        <span>{product.name}</span>
      </nav>

      <div className="product-page__content">
        <div className="product-page__images">
          {sortedImages.length > 0 ? (
            <>
              <div className="product-page__main-image">
                <img
                  src={sortedImages[selectedImage]?.url}
                  alt={product.name}
                />
              </div>
              {sortedImages.length > 1 && (
                <div className="product-page__thumbnails">
                  {sortedImages.map((img, i) => (
                    <button
                      key={img.id}
                      className={`product-page__thumb ${i === selectedImage ? "active" : ""}`}
                      onClick={() => setSelectedImage(i)}
                    >
                      <img src={img.url} alt={`Photo ${i + 1}`} />
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="product-page__placeholder">No images</div>
          )}
        </div>

        <div className="product-page__details">
          <h1>{product.name}</h1>
          {product.brand && <p className="brand">{product.brand}</p>}

          {averageRating !== null && (
            <div className="product-page__rating">
              <span className="stars">
                {[1, 2, 3, 4, 5].map((n) => (
                  <span key={n} className={n <= Math.round(averageRating) ? "star filled" : "star"}>
                    ★
                  </span>
                ))}
              </span>
              <span className="rating-text">
                {averageRating.toFixed(1)} ({reviews.length}{" "}
                {reviews.length === 1 ? "review" : "reviews"})
              </span>
            </div>
          )}

          <p className="price">${currentPrice.toFixed(2)}</p>
          <p className="sku">SKU: {currentSku}</p>
          <p className="stock">
            {currentStock > 0 ? `${currentStock} in stock` : "Out of stock"}
          </p>
          {product.description && <p className="description">{product.description}</p>}

          {product.variants?.length ? (
            <div className="variants">
              <h4>Variants</h4>
              <div className="variants__list">
                {product.variants.map((v) => (
                  <button
                    key={v.id}
                    className={`variants__item ${selectedVariant?.id === v.id ? "active" : ""} ${v.stock === 0 ? "disabled" : ""}`}
                    onClick={() => handleVariantSelect(v)}
                    disabled={v.stock === 0}
                  >
                    <span className="variants__name">{v.name}</span>
                    <span className="variants__price">
                      ${Number(v.price).toFixed(2)}
                    </span>
                    <span className="variants__stock">
                      {v.stock > 0 ? `${v.stock} left` : "Out"}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {currentStock > 0 && (
            <div className="add-to-cart">
              <input
                type="number"
                min={1}
                max={currentStock}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
              />
              <button
                onClick={handleAddToCart}
                className="btn btn--primary"
              >
                {addedToCart ? "Added!" : "Add to Cart"}
              </button>
              {user && (
                <button
                  onClick={handleToggleFavorite}
                  className={`btn btn--icon ${isFavorite ? "favorited" : ""}`}
                  title={isFavorite ? "Remove from favorites" : "Add to favorites"}
                >
                  {isFavorite ? "♥" : "♡"}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <section className="reviews">
        <h3>Reviews ({reviews.length})</h3>

        {user && (
          <form onSubmit={handleSubmitReview} className="review-form">
            <label>
              Rating:
              <select
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
              >
                {[5, 4, 3, 2, 1].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <textarea
              placeholder="Your review (optional)"
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
            />
            <button type="submit" className="btn btn--primary">
              Submit Review
            </button>
          </form>
        )}

        {reviews.length === 0 ? (
          <p>No reviews yet.</p>
        ) : (
          <ul className="reviews-list">
            {reviews.map((review) => (
              <li key={review.id}>
                <div className="review-header">
                  <span className="stars">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <span key={n} className={n <= review.rating ? "star filled" : "star"}>
                        ★
                      </span>
                    ))}
                  </span>
                  <small>{new Date(review.created_at).toLocaleDateString()}</small>
                </div>
                {review.text && <p>{review.text}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
