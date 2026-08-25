import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight, Truck, Shield, Headphones } from "lucide-react";
import { productsApi, categoriesApi } from "../../api";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import type { Product, Category } from "../../types";
import { ProductCardSkeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import "./Home.css";

export function HomePage() {
  const { t } = useTranslation();
  const { currency } = useCurrency();
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [productsRes, catsRes] = await Promise.all([
          productsApi.list({ limit: 8, sort_by: "created_at", sort_order: "desc" }),
          categoriesApi.list(),
        ]);
        setFeaturedProducts(productsRes.products);
        setCategories(catsRes.categories);
      } catch (err) {
        console.error("Failed to load homepage data", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const getCategoryIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("смартфон") || n.includes("phone") || n.includes("smartfon")) return "\uD83D\uDCF1";
    if (n.includes("ноутбук") || n.includes("laptop")) return "\uD83D\uDCBB";
    if (n.includes("аудіо") || n.includes("audio") || n.includes("слухов")) return "\uD83C\uDFA7";
    return "\uD83D\uDCE6";
  };

  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <div className="hero__content">
          <span className="hero__badge">{t("home.shop_now")}</span>
          <h1 className="hero__title">{t("home.hero_title")}</h1>
          <p className="hero__subtitle">{t("home.hero_subtitle")}</p>
          <div className="hero__actions">
            <Link to="/catalog" className="btn btn--primary btn--lg">
              {t("home.shop_now")} <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section className="section">
          <div className="container">
            <div className="section__header">
              <h2 className="section__title">{t("home.popular_categories")}</h2>
            </div>
            <div className="categories-grid">
              {categories.map((cat) => (
                <Link key={cat.id} to={`/catalog?category_id=${cat.id}`} className="category-card">
                  <span className="category-card__icon">{getCategoryIcon(cat.name)}</span>
                  <span className="category-card__name">{cat.name}</span>
                  <ArrowRight size={16} className="category-card__arrow" />
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="section section--alt">
        <div className="container">
          <div className="section__header">
            <h2 className="section__title">{t("home.featured_products")}</h2>
            <Link to="/catalog" className="section__link">
              {t("home.view_all")} <ArrowRight size={16} />
            </Link>
          </div>
          {loading ? (
            <div className="products-grid">
              {Array.from({ length: 4 }).map((_, i) => (
                <ProductCardSkeleton key={i} />
              ))}
            </div>
          ) : featuredProducts.length > 0 ? (
            <div className="products-grid">
              {featuredProducts.map((product) => (
                <Link key={product.id} to={`/catalog/${product.id}`} className="product-card">
                  <div className="product-card__image-wrap">
                    {product.images?.length > 0 ? (
                      <img
                        className="product-card__image"
                        src={product.images.find((i) => i.is_primary)?.url || product.images[0].url}
                        alt={product.name}
                        loading="lazy"
                      />
                    ) : (
                      <div className="product-card__image product-card__image--placeholder">{"\u{1F4F1}"}</div>
                    )}
                  </div>
                  <div className="product-card__body">
                    <h3 className="product-card__name">{product.name}</h3>
                    <div className="product-card__price">{formatPrice(product.price, currency)}</div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title={t("catalog.no_products")} />
          )}
        </div>
      </section>

      {/* Why Us */}
      <section className="section">
        <div className="container">
          <div className="section__header section__header--center">
            <h2 className="section__title">{t("home.why_us")}</h2>
          </div>
          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-card__icon"><Truck size={24} /></div>
              <h3 className="benefit-card__title">{t("home.fast_delivery")}</h3>
              <p className="benefit-card__desc">{t("home.fast_delivery_desc")}</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-card__icon"><Shield size={24} /></div>
              <h3 className="benefit-card__title">{t("home.warranty")}</h3>
              <p className="benefit-card__desc">{t("home.warranty_desc")}</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-card__icon"><Headphones size={24} /></div>
              <h3 className="benefit-card__title">{t("home.support")}</h3>
              <p className="benefit-card__desc">{t("home.support_desc")}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
