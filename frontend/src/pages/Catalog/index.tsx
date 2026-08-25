import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { SlidersHorizontal, X, ChevronLeft, ChevronRight, ArrowUpDown } from "lucide-react";
import { productsApi, categoriesApi } from "../../api";
import type { Product, Category } from "../../types";
import { ProductCardSkeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import { useIsMobile } from "../../hooks";
import "./Catalog.css";

const SORT_OPTIONS = [
  { value: "created_at", labelKey: "catalog.sort_newest", order: "desc" },
  { value: "price", labelKey: "catalog.sort_price_asc", order: "asc" },
  { value: "price", labelKey: "catalog.sort_price_desc", order: "desc" },
];

export function CatalogPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const isMobile = useIsMobile();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [brands, setBrands] = useState<string[]>([]);

  const q = searchParams.get("q") || "";
  const categoryId = searchParams.get("category_id") || "";
  const minPrice = searchParams.get("min_price") || "";
  const maxPrice = searchParams.get("max_price") || "";
  const inStock = searchParams.get("in_stock") || "";
  const brand = searchParams.get("brand") || "";
  const sortBy = searchParams.get("sort_by") || "created_at";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const limit = 20;
  const offset = (page - 1) * limit;

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await productsApi.list({
        q: q || undefined,
        category_id: categoryId || undefined,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        in_stock: inStock === "true" ? true : inStock === "false" ? false : undefined,
        brand: brand || undefined,
        sort_by: sortBy,
        sort_order: sortOrder as "asc" | "desc",
        limit,
        offset,
      });
      setProducts(data.products);
      setTotal(data.total);

      const uniqueBrands = [
        ...new Set(data.products.map((p) => p.brand).filter(Boolean) as string[]),
      ];
      if (uniqueBrands.length > 0) {
        setBrands((prev) => [...new Set([...prev, ...uniqueBrands])]);
      }
    } catch (err) {
      console.error("Failed to load products", err);
    } finally {
      setLoading(false);
    }
  }, [q, categoryId, minPrice, maxPrice, inStock, brand, sortBy, sortOrder, offset]);

  useEffect(() => {
    categoriesApi.list().then((data) => setCategories(data.categories)).catch(console.error);
  }, []);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  const totalPages = Math.ceil(total / limit);

  const setParam = (key: string, value: string | null) => {
    setSearchParams((prev) => {
      if (value === null || value === "") prev.delete(key);
      else prev.set(key, value);
      prev.delete("page");
      return prev;
    });
  };

  const clearAllFilters = () => {
    if (q) setSearchParams({ q });
    else setSearchParams({});
  };

  const hasActiveFilters = categoryId || minPrice || maxPrice || inStock || brand;

  const activeFilterCount = [categoryId, minPrice, maxPrice, inStock, brand].filter(Boolean).length;

  const currentSortLabel = SORT_OPTIONS.find((o) => o.value === sortBy && o.order === sortOrder)
    || SORT_OPTIONS[0];

  const getPrimaryImage = (product: Product) =>
    product.images?.find((i) => i.is_primary)?.url || product.images?.[0]?.url;

  const Sidebar = () => (
    <div className="catalog__sidebar">
      <div className="filter-section">
        <h4 className="filter-section__title">{t("catalog.category")}</h4>
        <div className="filter-list">
          <button
            className={`filter-list__item ${!categoryId ? "filter-list__item--active" : ""}`}
            onClick={() => setParam("category_id", null)}
          >
            {t("catalog.all")}
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              className={`filter-list__item ${categoryId === cat.id ? "filter-list__item--active" : ""}`}
              onClick={() => setParam("category_id", cat.id)}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <h4 className="filter-section__title">{t("catalog.price")}</h4>
        <div className="filter-price">
          <input
            type="number"
            className="filter-price__input"
            defaultValue={minPrice}
            placeholder={t("catalog.min")}
            min="0"
            step="1"
            onBlur={(e) => setParam("min_price", e.target.value || null)}
          />
          <span className="filter-price__dash">&mdash;</span>
          <input
            type="number"
            className="filter-price__input"
            defaultValue={maxPrice}
            placeholder={t("catalog.max")}
            min="0"
            step="1"
            onBlur={(e) => setParam("max_price", e.target.value || null)}
          />
        </div>
      </div>

      <div className="filter-section">
        <h4 className="filter-section__title">{t("catalog.availability")}</h4>
        <div className="filter-list">
          <button
            className={`filter-list__item ${!inStock ? "filter-list__item--active" : ""}`}
            onClick={() => setParam("in_stock", null)}
          >
            {t("catalog.all")}
          </button>
          <button
            className={`filter-list__item ${inStock === "true" ? "filter-list__item--active" : ""}`}
            onClick={() => setParam("in_stock", "true")}
          >
            {t("catalog.in_stock")}
          </button>
          <button
            className={`filter-list__item ${inStock === "false" ? "filter-list__item--active" : ""}`}
            onClick={() => setParam("in_stock", "false")}
          >
            {t("catalog.out_of_stock")}
          </button>
        </div>
      </div>

      {brands.length > 0 && (
        <div className="filter-section">
          <h4 className="filter-section__title">{t("catalog.brand")}</h4>
          <div className="filter-list">
            <button
              className={`filter-list__item ${!brand ? "filter-list__item--active" : ""}`}
              onClick={() => setParam("brand", null)}
            >
              {t("catalog.all")}
            </button>
            {brands.map((b) => (
              <button
                key={b}
                className={`filter-list__item ${brand === b ? "filter-list__item--active" : ""}`}
                onClick={() => setParam("brand", b)}
              >
                {b}
              </button>
            ))}
          </div>
        </div>
      )}

      {hasActiveFilters && (
        <button className="btn btn--ghost btn--sm btn--full" onClick={clearAllFilters}>
          {t("catalog.clear_all")}
        </button>
      )}
    </div>
  );

  return (
    <div className="catalog">
      <div className="catalog__header">
        <div>
          <h1 className="catalog__title">{t("catalog.title")}</h1>
          {!loading && (
            <p className="catalog__count">{t("catalog.products_found", { count: total })}</p>
          )}
        </div>

        <div className="catalog__toolbar">
          <div className="catalog__sort">
            <button className="catalog__sort-btn">
              <ArrowUpDown size={14} />
              {t(currentSortLabel.labelKey)}
            </button>
            <div className="catalog__sort-dropdown">
              {SORT_OPTIONS.map((opt, i) => (
                <button
                  key={i}
                  className={`catalog__sort-option ${sortBy === opt.value && sortOrder === opt.order ? "catalog__sort-option--active" : ""}`}
                  onClick={() => {
                    setParam("sort_by", opt.value);
                    setParam("sort_order", opt.order);
                  }}
                >
                  {t(opt.labelKey)}
                </button>
              ))}
            </div>
          </div>

          {isMobile && (
            <button
              className="catalog__filter-toggle btn btn--ghost btn--sm"
              onClick={() => setMobileFiltersOpen(true)}
            >
              <SlidersHorizontal size={16} />
              {t("catalog.filters")}
              {activeFilterCount > 0 && <span className="catalog__filter-count">{activeFilterCount}</span>}
            </button>
          )}
        </div>
      </div>

      {/* Active filters chips */}
      {hasActiveFilters && !isMobile && (
        <div className="catalog__chips">
          {categoryId && (
            <span className="chip">
              {categories.find((c) => c.id === categoryId)?.name || categoryId}
              <button onClick={() => setParam("category_id", null)}><X size={12} /></button>
            </span>
          )}
          {brand && (
            <span className="chip">
              {brand}
              <button onClick={() => setParam("brand", null)}><X size={12} /></button>
            </span>
          )}
          {(minPrice || maxPrice) && (
            <span className="chip">
              {minPrice || "0"} &mdash; {maxPrice || "\u221E"} {"\u20B4"}
              <button onClick={() => { setParam("min_price", null); setParam("max_price", null); }}><X size={12} /></button>
            </span>
          )}
          {inStock && (
            <span className="chip">
              {inStock === "true" ? t("catalog.in_stock") : t("catalog.out_of_stock")}
              <button onClick={() => setParam("in_stock", null)}><X size={12} /></button>
            </span>
          )}
        </div>
      )}

      <div className="catalog__layout">
        {!isMobile && <aside className="catalog__sidebar-wrap"><Sidebar /></aside>}

        <div className="catalog__products">
          {loading ? (
            <div className="products-grid">
              {Array.from({ length: 8 }).map((_, i) => (
                <ProductCardSkeleton key={i} />
              ))}
            </div>
          ) : products.length === 0 ? (
            <EmptyState
              title={t("catalog.no_products")}
              action={hasActiveFilters ? { label: t("catalog.clear_all"), onClick: clearAllFilters } : undefined}
            />
          ) : (
            <>
              <div className="products-grid">
                {products.map((product) => (
                  <Link key={product.id} to={`/catalog/${product.id}`} className="product-card">
                    <div className="product-card__image-wrap">
                      {getPrimaryImage(product) ? (
                        <img
                          className="product-card__image"
                          src={getPrimaryImage(product)}
                          alt={product.name}
                          loading="lazy"
                        />
                      ) : (
                        <div className="product-card__image product-card__image--placeholder">{"\u{1F4F1}"}</div>
                      )}
                      {product.stock === 0 && (
                        <span className="product-card__out-of-stock">{t("catalog.out_of_stock")}</span>
                      )}
                    </div>
                    <div className="product-card__body">
                      {product.brand && <span className="product-card__brand">{product.brand}</span>}
                      <h3 className="product-card__name">{product.name}</h3>
                      <div className="product-card__price">{Number(product.price).toLocaleString()} \u20B4</div>
                    </div>
                  </Link>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="pagination__btn"
                    disabled={page <= 1}
                    onClick={() => setSearchParams((prev) => { prev.set("page", String(page - 1)); return prev; })}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="pagination__info">
                    {page} / {totalPages}
                  </span>
                  <button
                    className="pagination__btn"
                    disabled={page >= totalPages}
                    onClick={() => setSearchParams((prev) => { prev.set("page", String(page + 1)); return prev; })}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Mobile filter drawer */}
      {isMobile && mobileFiltersOpen && (
        <div className="filter-drawer">
          <div className="filter-drawer__overlay" onClick={() => setMobileFiltersOpen(false)} />
          <div className="filter-drawer__panel">
            <div className="filter-drawer__header">
              <h3>{t("catalog.filters")}</h3>
              <button onClick={() => setMobileFiltersOpen(false)}><X size={20} /></button>
            </div>
            <div className="filter-drawer__body">
              <Sidebar />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
