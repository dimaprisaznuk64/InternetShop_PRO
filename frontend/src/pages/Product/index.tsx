import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { productsApi, reviewsApi } from "../../api";
import { useAuth } from "../../contexts/AuthContext";
import { useCart } from "../../contexts/CartContext";
import type { Product, Review } from "../../types";

export function ProductPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { addItem } = useCart();
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [addedToCart, setAddedToCart] = useState(false);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState("");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      productsApi.get(id),
      reviewsApi.listByProduct(id).catch(() => ({ reviews: [] })),
    ])
      .then(([productData, reviewData]) => {
        setProduct(productData);
        setReviews(reviewData.reviews);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleAddToCart = async () => {
    if (!product) return;
    try {
      await addItem(product.id, quantity);
      setAddedToCart(true);
      setTimeout(() => setAddedToCart(false), 2000);
    } catch (err) {
      console.error("Failed to add to cart", err);
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

  if (loading) return <p>Loading...</p>;
  if (!product) return <p>Product not found.</p>;

  return (
    <div className="product-page">
      <Link to="/catalog">&larr; Back to catalog</Link>

      <div className="product-page__content">
        <div className="product-page__images">
          {product.images?.length ? (
            product.images
              .sort((a, b) => a.position - b.position)
              .map((img) => (
                <img
                  key={img.id}
                  src={img.url}
                  alt={product.name}
                  className={img.is_primary ? "primary" : ""}
                />
              ))
          ) : (
            <div className="product-page__placeholder">No images</div>
          )}
        </div>

        <div className="product-page__details">
          <h1>{product.name}</h1>
          {product.brand && <p className="brand">{product.brand}</p>}
          <p className="price">${Number(product.price).toFixed(2)}</p>
          <p className="sku">SKU: {product.sku}</p>
          <p className="stock">
            {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
          </p>
          {product.description && <p>{product.description}</p>}

          {product.variants?.length > 0 && (
            <div className="variants">
              <h4>Variants</h4>
              <ul>
                {product.variants.map((v) => (
                  <li key={v.id}>
                    {v.name} — ${Number(v.price).toFixed(2)} ({v.stock} in
                    stock)
                  </li>
                ))}
              </ul>
            </div>
          )}

          {product.stock > 0 && (
            <div className="add-to-cart">
              <input
                type="number"
                min={1}
                max={product.stock}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
              />
              <button
                onClick={handleAddToCart}
                className="btn btn--primary"
                disabled={product.stock === 0}
              >
                {addedToCart ? "Added!" : "Add to Cart"}
              </button>
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
                <strong>Rating: {review.rating}/5</strong>
                {review.text && <p>{review.text}</p>}
                <small>{new Date(review.created_at).toLocaleDateString()}</small>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
