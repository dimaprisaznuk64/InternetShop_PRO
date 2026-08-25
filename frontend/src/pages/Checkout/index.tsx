import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ordersApi, promoApi } from "../../api";
import { getApiErrorMessage } from "../../api/client";
import { useCart } from "../../contexts/CartContext";

export function CheckoutPage() {
  const { cart } = useCart();
  const navigate = useNavigate();
  const [deliveryMethod, setDeliveryMethod] = useState("standard");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [notes, setNotes] = useState("");
  const [promoResult, setPromoResult] = useState<{
    discount_type: string;
    discount_value: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!cart || cart.items.length === 0) {
      navigate("/cart");
    }
  }, [cart, navigate]);

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) return;
    try {
      const result = await promoApi.apply(promoCode);
      setPromoResult(result);
      setError("");
    } catch {
      setError("Invalid promo code");
      setPromoResult(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deliveryAddress.trim()) {
      setError("Delivery address is required");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await ordersApi.checkout({
        delivery_method: deliveryMethod,
        delivery_address: deliveryAddress,
        promo_code: promoCode || undefined,
        notes: notes || undefined,
      });
      navigate("/orders");
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, "Checkout failed");
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!cart || cart.items.length === 0) {
    return null;
  }

  return (
    <div className="checkout-page">
      <h1>Checkout</h1>

      <form onSubmit={handleSubmit} className="checkout-form">
        <div className="checkout-section">
          <h3>Delivery</h3>
          <label>
            Method:
            <select
              value={deliveryMethod}
              onChange={(e) => setDeliveryMethod(e.target.value)}
            >
              <option value="standard">Standard</option>
              <option value="express">Express</option>
              <option value="pickup">Pickup</option>
            </select>
          </label>
          <label>
            Address:
            <input
              type="text"
              value={deliveryAddress}
              onChange={(e) => setDeliveryAddress(e.target.value)}
              placeholder="Street, city, zip"
              required
            />
          </label>
        </div>

        <div className="checkout-section">
          <h3>Promo Code</h3>
          <div className="promo-row">
            <input
              type="text"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
              placeholder="Enter promo code"
            />
            <button type="button" onClick={handleApplyPromo}>
              Apply
            </button>
          </div>
          {promoResult && (
            <p className="promo-success">
              Discount: {promoResult.discount_type} — {promoResult.discount_value}
            </p>
          )}
        </div>

        <div className="checkout-section">
          <h3>Notes</h3>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes"
          />
        </div>

        {error && <p className="error">{error}</p>}

        <div className="checkout-summary">
          <p>
            Total items:{" "}
            {cart.items.reduce((s, i) => s + i.quantity, 0)}
          </p>
          <p>
            Subtotal: <strong>${Number(cart.subtotal).toFixed(2)}</strong>
          </p>
          <button
            type="submit"
            className="btn btn--primary"
            disabled={loading}
          >
            {loading ? "Processing..." : "Place Order"}
          </button>
        </div>
      </form>
    </div>
  );
}
