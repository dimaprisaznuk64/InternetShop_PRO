import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Truck, Store, Tag, CheckCircle, AlertCircle } from "lucide-react";
import { ordersApi, promoApi } from "../../api";
import { getApiErrorMessage } from "../../api/client";
import { useCart } from "../../contexts/CartContext";
import { PageLoader } from "../../components/ui/Spinner";
import "./Checkout.css";

export function CheckoutPage() {
  const { t } = useTranslation();
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
    if (!cart || cart.items.length === 0) navigate("/cart");
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
      setError(getApiErrorMessage(err, "Checkout failed"));
    } finally {
      setLoading(false);
    }
  };

  if (!cart || cart.items.length === 0) return <PageLoader />;

  return (
    <div className="checkout-page">
      <h1 className="checkout-page__title">{t("checkout.title")}</h1>

      <form onSubmit={handleSubmit} className="checkout-page__layout">
        <div className="checkout-page__form">
          {/* Delivery Method */}
          <div className="checkout-section">
            <h3 className="checkout-section__title">{t("checkout.delivery_method")}</h3>
            <div className="delivery-options">
              {[
                { value: "standard", icon: <Truck size={20} />, label: "Standard Delivery", desc: "2-5 business days" },
                { value: "express", icon: <Truck size={20} />, label: "Express Delivery", desc: "1-2 business days" },
                { value: "pickup", icon: <Store size={20} />, label: "Pickup", desc: "From store" },
              ].map((opt) => (
                <label key={opt.value} className={`delivery-option ${deliveryMethod === opt.value ? "delivery-option--active" : ""}`}>
                  <input type="radio" name="delivery" value={opt.value} checked={deliveryMethod === opt.value} onChange={(e) => setDeliveryMethod(e.target.value)} />
                  <div className="delivery-option__icon">{opt.icon}</div>
                  <div>
                    <div className="delivery-option__label">{opt.label}</div>
                    <div className="delivery-option__desc">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Address */}
          <div className="checkout-section">
            <h3 className="checkout-section__title">{t("checkout.delivery_address")}</h3>
            <input
              type="text"
              className="checkout-input"
              value={deliveryAddress}
              onChange={(e) => setDeliveryAddress(e.target.value)}
              placeholder="Street, city, zip"
              required
            />
          </div>

          {/* Promo */}
          <div className="checkout-section">
            <h3 className="checkout-section__title">{t("cart.promo_code")}</h3>
            <div className="promo-row">
              <input
                type="text"
                className="checkout-input"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                placeholder={t("cart.promo_code")}
              />
              <button type="button" className="btn btn--secondary btn--sm" onClick={handleApplyPromo}>
                <Tag size={14} /> {t("cart.apply")}
              </button>
            </div>
            {promoResult && (
              <div className="checkout-success">
                <CheckCircle size={14} /> Discount applied: {promoResult.discount_type} — {promoResult.discount_value}
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="checkout-section">
            <h3 className="checkout-section__title">{t("checkout.notes")}</h3>
            <textarea
              className="checkout-input checkout-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes..."
              rows={3}
            />
          </div>

          {error && (
            <div className="checkout-error">
              <AlertCircle size={14} /> {error}
            </div>
          )}
        </div>

        {/* Summary */}
        <div className="checkout-page__summary">
          <div className="checkout-summary">
            <h3 className="checkout-summary__title">{t("checkout.confirmation")}</h3>

            <div className="checkout-summary__items">
              {cart.items.map((item) => (
                <div key={item.id} className="checkout-summary__item">
                  <span className="checkout-summary__item-name">{item.product_name} x{item.quantity}</span>
                  <span>{Number(item.line_total).toLocaleString()} \u20B4</span>
                </div>
              ))}
            </div>

            <div className="checkout-summary__divider" />

            <div className="checkout-summary__row">
              <span>{t("cart.subtotal")}</span>
              <span>{Number(cart.subtotal).toLocaleString()} \u20B4</span>
            </div>
            <div className="checkout-summary__row">
              <span>{t("cart.shipping")}</span>
              <span className="checkout-summary__free">{t("cart.free")}</span>
            </div>
            {promoResult && (
              <div className="checkout-summary__row checkout-summary__discount">
                <span>{t("cart.discount")}</span>
                <span>-{promoResult.discount_value}</span>
              </div>
            )}
            <div className="checkout-summary__divider" />
            <div className="checkout-summary__row checkout-summary__row--total">
              <span>{t("cart.total")}</span>
              <span>{Number(cart.subtotal).toLocaleString()} \u20B4</span>
            </div>

            <button type="submit" className="btn btn--primary btn--full btn--lg" disabled={loading}>
              {loading ? t("common.loading") : t("checkout.place_order")}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
