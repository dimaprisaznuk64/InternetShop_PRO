import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../../contexts/CartContext";
import { useAuth } from "../../contexts/AuthContext";

export function CartPage() {
  const { cart, loading, updateItem, removeItem, clear } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) navigate("/login");
  }, [user, navigate]);

  if (loading) return <p>Loading cart...</p>;
  if (!cart || cart.items.length === 0) {
    return (
      <div className="cart-empty">
        <h2>Your cart is empty</h2>
        <Link to="/catalog" className="btn btn--primary">
          Browse Catalog
        </Link>
      </div>
    );
  }

  const itemCount = cart.items.reduce((s, i) => s + i.quantity, 0);

  return (
    <div className="cart-page">
      <div className="cart-header">
        <h1>Shopping Cart</h1>
        <span className="cart-header__count">
          {itemCount} {itemCount === 1 ? "item" : "items"}
        </span>
      </div>

      <div className="cart-items">
        {cart.items.map((item) => (
          <div key={item.id} className="cart-item">
            <Link to={`/catalog/${item.product_id}`} className="cart-item__image">
              {item.product_image ? (
                <img src={item.product_image} alt={item.product_name} />
              ) : (
                <div className="cart-item__placeholder">No image</div>
              )}
            </Link>

            <div className="cart-item__details">
              <Link to={`/catalog/${item.product_id}`} className="cart-item__name">
                {item.product_name}
              </Link>
              {item.variant_name && (
                <span className="cart-item__variant">{item.variant_name}</span>
              )}
              <span className="cart-item__sku">
                SKU: {item.product_sku}
              </span>
            </div>

            <div className="cart-item__price">
              ${Number(item.product_price).toFixed(2)}
            </div>

            <div className="cart-item__quantity">
              <input
                type="number"
                min={1}
                max={item.product_stock}
                value={item.quantity}
                onChange={(e) =>
                  updateItem(item.id, Number(e.target.value))
                }
              />
            </div>

            <div className="cart-item__total">
              ${Number(item.line_total).toFixed(2)}
            </div>

            <button
              className="cart-item__remove btn btn--ghost btn--sm"
              onClick={() => removeItem(item.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className="cart-summary">
        <div className="cart-summary__info">
          <div className="cart-summary__row">
            <span>Items:</span>
            <span>{itemCount}</span>
          </div>
          <div className="cart-summary__row cart-summary__row--total">
            <span>Subtotal:</span>
            <strong>${Number(cart.subtotal).toFixed(2)}</strong>
          </div>
        </div>
        <div className="cart-actions">
          <button onClick={() => clear()} className="btn btn--ghost">
            Clear Cart
          </button>
          <Link to="/checkout" className="btn btn--primary">
            Proceed to Checkout
          </Link>
        </div>
      </div>
    </div>
  );
}
