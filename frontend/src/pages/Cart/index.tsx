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

  return (
    <div className="cart-page">
      <h1>Shopping Cart</h1>

      <table className="cart-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {cart.items.map((item) => (
            <tr key={item.id}>
              <td>{item.product?.name ?? item.product_id}</td>
              <td>
                ${Number(item.product?.price ?? 0).toFixed(2)}
              </td>
              <td>
                <input
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(e) =>
                    updateItem(item.id, Number(e.target.value))
                  }
                />
              </td>
              <td>
                $
                {(
                  Number(item.product?.price ?? 0) * item.quantity
                ).toFixed(2)}
              </td>
              <td>
                <button onClick={() => removeItem(item.id)}>Remove</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="cart-summary">
        <p className="cart-subtotal">
          Subtotal: <strong>${Number(cart.subtotal).toFixed(2)}</strong>
        </p>
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
