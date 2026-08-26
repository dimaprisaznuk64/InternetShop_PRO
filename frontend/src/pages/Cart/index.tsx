import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Trash2, Minus, Plus, ShoppingBag, ArrowRight } from "lucide-react";
import { useCart } from "../../contexts/CartContext";
import { useAuth } from "../../contexts/AuthContext";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import { EmptyState } from "../../components/ui/EmptyState";
import { ListRowSkeleton } from "../../components/ui/Skeleton";
import "./Cart.css";

export function CartPage() {
  const { t } = useTranslation();
  const { cart, loading, updateItem, removeItem, clear } = useCart();
  const { user } = useAuth();
  const { currency } = useCurrency();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) navigate("/login");
  }, [user, navigate]);

  if (loading) {
    return (
      <div className="cart-page container">
        <ListRowSkeleton rows={3} />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="cart-page container">
        <EmptyState
          icon={<ShoppingBag size={48} />}
          title={t("cart.empty")}
          action={{ label: t("cart.continue_shopping"), onClick: () => navigate("/catalog") }}
        />
      </div>
    );
  }

  const itemCount = cart.items.reduce((s, i) => s + i.quantity, 0);

  return (
    <div className="cart-page container">
      <div className="cart-page__header">
        <h1 className="cart-page__title">{t("cart.title")}</h1>
        <span className="cart-page__count">{itemCount} {itemCount === 1 ? "item" : "items"}</span>
      </div>

      <div className="cart-page__layout">
        <div className="cart-page__items">
          {cart.items.map((item) => (
            <div key={item.id} className="cart-item">
              <Link to={`/catalog/${item.product_id}`} className="cart-item__image">
                {item.product_image ? (
                  <img src={item.product_image} alt={item.product_name} />
                ) : (
                  <div className="cart-item__no-image">{"\u{1F4F1}"}</div>
                )}
              </Link>

              <div className="cart-item__info">
                <Link to={`/catalog/${item.product_id}`} className="cart-item__name">
                  {item.product_name}
                </Link>
                {item.variant_name && (
                  <span className="cart-item__variant">{item.variant_name}</span>
                )}
                <span className="cart-item__sku">SKU: {item.product_sku}</span>
                <span className="cart-item__unit-price">{formatPrice(item.product_price, currency)}</span>
              </div>

              <div className="cart-item__controls">
                <div className="cart-item__quantity">
                  <button
                    className="quantity-btn"
                    onClick={() => updateItem(item.id, Math.max(1, item.quantity - 1))}
                    disabled={item.quantity <= 1}
                  >
                    <Minus size={14} />
                  </button>
                  <span className="quantity-value">{item.quantity}</span>
                  <button
                    className="quantity-btn"
                    onClick={() => updateItem(item.id, Math.min(item.product_stock, item.quantity + 1))}
                    disabled={item.quantity >= item.product_stock}
                  >
                    <Plus size={14} />
                  </button>
                </div>
                <span className="cart-item__total">{formatPrice(item.line_total, currency)}</span>
                <button className="cart-item__remove" onClick={() => removeItem(item.id)}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
          <button className="btn btn--ghost btn--sm cart-page__clear" onClick={() => clear()}>
            {t("cart.remove")} all
          </button>
        </div>

        <div className="cart-page__summary">
          <div className="cart-summary">
            <h3 className="cart-summary__title">{t("cart.subtotal")}</h3>
            <div className="cart-summary__row">
              <span>{t("cart.subtotal")} ({itemCount} items)</span>
              <span>{formatPrice(cart.subtotal, currency)}</span>
            </div>
            <div className="cart-summary__row">
              <span>{t("cart.shipping")}</span>
              <span className="cart-summary__free">{t("cart.free")}</span>
            </div>
            <div className="cart-summary__divider" />
            <div className="cart-summary__row cart-summary__row--total">
              <span>{t("cart.total")}</span>
              <span>{formatPrice(cart.subtotal, currency)}</span>
            </div>
            <Link to="/checkout" className="btn btn--primary btn--full btn--lg cart-summary__checkout">
              {t("cart.checkout")} <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
