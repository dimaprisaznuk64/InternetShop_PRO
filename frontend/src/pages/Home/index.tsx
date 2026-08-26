import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight } from "lucide-react";
import { productsApi, categoriesApi } from "../../api";
import { useCurrency, formatPrice } from "../../contexts/CurrencyContext";
import { categoryName } from "../../i18n/category";
import type { Product, Category } from "../../types";
import { ProductCardSkeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import "./Home.css";

const HERO_IMG = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=1200&q=80";

const CATEGORY_PHOTOS: Record<string, string> = {
  phones: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&q=80",
  laptops: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&q=80",
  audio: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
  accessories: "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=600&q=80",
  default: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&q=80",
};

function getCategoryPhoto(cat: Category): string {
  const slug = cat.slug?.toLowerCase() || cat.name?.toLowerCase() || "";
  for (const [key, url] of Object.entries(CATEGORY_PHOTOS)) {
    if (slug.includes(key)) return url;
  }
  return CATEGORY_PHOTOS.default;
}

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

  return (
    <div className="home">
      {/* Hero — Asymmetric Split */}
      <section className="hero container--wide">
        <div className="hero__content">
          <span className="hero__badge">{t("home.shop_now")}</span>
          <h1 className="hero__title">{t("home.hero_title")}</h1>
          <p className="hero__subtitle">{t("home.hero_subtitle")}</p>
          <div className="hero__actions">
            <Link to="/catalog" className="btn btn--primary btn--lg">
              {t("home.shop_now")} <ArrowRight size={16} />
            </Link>
          </div>
        </div>
        <div className="hero__media">
          <img src={HERO_IMG} alt="Featured" />
        </div>
      </section>

      {/* Categories — Photo Cards */}
      {categories.length > 0 && (
        <section className="section container--wide">
          <div className="section__header">
            <h2 className="section__title">{t("home.popular_categories")}</h2>
          </div>
          <div className="categories-grid">
            {categories.slice(0, 6).map((cat) => (
              <Link key={cat.id} to={`/catalog?category_id=${cat.id}`} className="category-card">
                <img className="category-card__bg" src={getCategoryPhoto(cat)} alt={categoryName(cat, t)} loading="lazy" />
                <div className="category-card__overlay" />
                <div className="category-card__content">
                  <div className="category-card__name">{categoryName(cat, t)}</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured Products — Editorial Grid */}
      <section className="section" style={{ background: "var(--color-bg-secondary)" }}>
        <div className="section__header container--wide">
          <h2 className="section__title">{t("home.featured_products")}</h2>
          <Link to="/catalog" className="section__link">
            {t("home.view_all")} <ArrowRight size={14} />
          </Link>
        </div>
        <div className="container--wide">
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
                    <div className="product-card__cta">
                      <span className="btn btn--primary btn--md btn--full" style={{ background: "rgba(255,255,255,0.95)", color: "#1a1a1a", fontSize: "0.8125rem" }}>
                        {t("home.shop_now")}
                      </span>
                    </div>
                  </div>
                  <div className="product-card__body">
                    {product.brand && <div className="product-card__brand">{product.brand}</div>}
                    <h3 className="product-card__name">{product.name}</h3>
                    <div className="product-card__price">
                      {formatPrice(product.price, currency)}
                      {product.old_price && product.old_price > product.price && (
                        <span className="product-card__old-price">{formatPrice(product.old_price, currency)}</span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title={t("catalog.no_products")} />
          )}
        </div>
      </section>

      {/* Why Us — Minimal Text Blocks */}
      <section className="section container--wide">
        <div className="section__header">
          <h2 className="section__title">{t("home.why_us")}</h2>
        </div>
        <div className="benefits">
          <div className="benefit-card">
            <h3 className="benefit-card__title">{t("home.fast_delivery")}</h3>
            <p className="benefit-card__desc">{t("home.fast_delivery_desc")}</p>
          </div>
          <div className="benefit-card">
            <h3 className="benefit-card__title">{t("home.warranty")}</h3>
            <p className="benefit-card__desc">{t("home.warranty_desc")}</p>
          </div>
          <div className="benefit-card">
            <h3 className="benefit-card__title">{t("home.support")}</h3>
            <p className="benefit-card__desc">{t("home.support_desc")}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
