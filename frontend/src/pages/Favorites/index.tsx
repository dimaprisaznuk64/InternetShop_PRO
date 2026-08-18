import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { favoritesApi } from "../../api";
import type { Favorite } from "../../types";

export function FavoritesPage() {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    favoritesApi
      .list()
      .then((data) => setFavorites(data.favorites))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleRemove = async (productId: string) => {
    await favoritesApi.remove(productId);
    setFavorites((prev) => prev.filter((f) => f.product_id !== productId));
  };

  if (loading) return <p>Loading favorites...</p>;

  if (favorites.length === 0) {
    return (
      <div className="favorites-empty">
        <h2>No favorites yet</h2>
        <Link to="/catalog" className="btn btn--primary">
          Browse Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="favorites-page">
      <h1>My Favorites</h1>
      <div className="product-grid">
        {favorites.map((fav) => (
          <div key={fav.id} className="product-card">
            <Link to={`/catalog/${fav.product_id}`}>
              <h4>{fav.product?.name ?? fav.product_id}</h4>
            </Link>
            <button onClick={() => handleRemove(fav.product_id)}>
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
