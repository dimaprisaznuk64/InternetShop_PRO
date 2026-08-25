import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Heart, HeartOff } from "lucide-react";
import { favoritesApi } from "../../api";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import type { Favorite } from "../../types";
import { PageLoader } from "../../components/ui/Spinner";
import { EmptyState } from "../../components/ui/EmptyState";
import "./Favorites.css";

export function FavoritesPage() {
  const { t } = useTranslation();
  const { currency } = useCurrency();
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    favoritesApi.list().then((data) => setFavorites(data.favorites)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleRemove = async (productId: string) => {
    await favoritesApi.remove(productId);
    setFavorites((prev) => prev.filter((f) => f.product_id !== productId));
  };

  if (loading) return <PageLoader />;

  if (favorites.length === 0) {
    return (
      <div className="favorites-page container">
        <EmptyState
          icon={<Heart size={48} />}
          title="No favorites yet"
          action={{ label: t("catalog.title"), onClick: () => window.location.href = "/catalog" }}
        />
      </div>
    );
  }

  return (
    <div className="favorites-page container">
      <h1 className="favorites-page__title">{t("nav.favorites")} ({favorites.length})</h1>
      <div className="favorites-grid">
        {favorites.map((fav) => (
          <div key={fav.id} className="fav-card">
            <Link to={`/catalog/${fav.product_id}`} className="fav-card__link">
              {fav.product?.images?.[0]?.url ? (
                <img className="fav-card__image" src={fav.product.images[0].url} alt={fav.product?.name || ""} loading="lazy" />
              ) : (
                <div className="fav-card__no-image">{"\u{1F4F1}"}</div>
              )}
              <div className="fav-card__body">
                <h3 className="fav-card__name">{fav.product?.name || fav.product_id}</h3>
                {fav.product?.price && (
                  <span className="fav-card__price">{formatPrice(fav.product.price, currency)}</span>
                )}
              </div>
            </Link>
            <button className="fav-card__remove" onClick={() => handleRemove(fav.product_id)} title="Remove">
              <HeartOff size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
