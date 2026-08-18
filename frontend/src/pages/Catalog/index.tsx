import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { productsApi, categoriesApi } from "../../api";
import type { Product, Category } from "../../types";

const SORT_OPTIONS = [
  { value: "created_at", label: "Newest" },
  { value: "name", label: "Name" },
  { value: "price", label: "Price" },
];

export function CatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
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
    categoriesApi
      .list()
      .then((data) => setCategories(data.categories))
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const totalPages = Math.ceil(total / limit);

  const setParam = (key: string, value: string | null) => {
    setSearchParams((prev) => {
      if (value === null || value === "") {
        prev.delete(key);
      } else {
        prev.set(key, value);
      }
      prev.delete("page");
      return prev;
    });
  };

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    setParam("q", (formData.get("q") as string) || null);
  };

  const handlePriceFilter = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    setParam("min_price", (formData.get("min_price") as string) || null);
    setParam("max_price", (formData.get("max_price") as string) || null);
  };

  const clearAllFilters = () => {
    setSearchParams({});
  };

  const hasActiveFilters = q || categoryId || minPrice || maxPrice || inStock || brand;

  return (
    <div className="catalog">
      <aside className="catalog__sidebar">
        <div className="catalog__filter-section">
          <h3>Categories</h3>
          <ul>
            <li>
              <button
                className={!categoryId ? "active" : ""}
                onClick={() => setParam("category_id", null)}
              >
                All
              </button>
            </li>
            {categories.map((cat) => (
              <li key={cat.id}>
                <button
                  className={categoryId === cat.id ? "active" : ""}
                  onClick={() => setParam("category_id", cat.id)}
                >
                  {cat.name}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="catalog__filter-section">
          <h3>Price</h3>
          <form onSubmit={handlePriceFilter} className="catalog__price-filter">
            <input
              type="number"
              name="min_price"
              defaultValue={minPrice}
              placeholder="Min"
              min="0"
              step="0.01"
            />
            <span className="catalog__filter-dash">—</span>
            <input
              type="number"
              name="max_price"
              defaultValue={maxPrice}
              placeholder="Max"
              min="0"
              step="0.01"
            />
            <button type="submit" className="btn btn--ghost btn--sm">
              Apply
            </button>
          </form>
        </div>

        <div className="catalog__filter-section">
          <h3>Availability</h3>
          <ul>
            <li>
              <button
                className={!inStock ? "active" : ""}
                onClick={() => setParam("in_stock", null)}
              >
                All
              </button>
            </li>
            <li>
              <button
                className={inStock === "true" ? "active" : ""}
                onClick={() => setParam("in_stock", "true")}
              >
                In Stock
              </button>
            </li>
            <li>
              <button
                className={inStock === "false" ? "active" : ""}
                onClick={() => setParam("in_stock", "false")}
              >
                Out of Stock
              </button>
            </li>
          </ul>
        </div>

        {brands.length > 0 && (
          <div className="catalog__filter-section">
            <h3>Brand</h3>
            <ul>
              <li>
                <button
                  className={!brand ? "active" : ""}
                  onClick={() => setParam("brand", null)}
                >
                  All
                </button>
              </li>
              {brands.map((b) => (
                <li key={b}>
                  <button
                    className={brand === b ? "active" : ""}
                    onClick={() => setParam("brand", b)}
                  >
                    {b}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {hasActiveFilters && (
          <button
            className="btn btn--ghost catalog__clear-btn"
            onClick={clearAllFilters}
          >
            Clear all filters
          </button>
        )}
      </aside>

      <div className="catalog__main">
        <form onSubmit={handleSearch} className="catalog__search">
          <input
            type="text"
            name="q"
            defaultValue={q}
            placeholder="Search products..."
          />
          <button type="submit" className="btn btn--primary">
            Search
          </button>
        </form>

        <div className="catalog__toolbar">
          <span className="catalog__count">
            {total} {total === 1 ? "product" : "products"} found
          </span>
          <div className="catalog__sort">
            <label htmlFor="sort-by">Sort by:</label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setParam("sort_by", e.target.value)}
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn btn--ghost btn--sm catalog__sort-order"
              onClick={() =>
                setParam("sort_order", sortOrder === "asc" ? "desc" : "asc")
              }
              title={sortOrder === "asc" ? "Ascending" : "Descending"}
            >
              {sortOrder === "asc" ? "↑" : "↓"}
            </button>
          </div>
        </div>

        {loading ? (
          <p>Loading...</p>
        ) : products.length === 0 ? (
          <p>No products found.</p>
        ) : (
          <>
            <div className="product-grid">
              {products.map((product) => (
                <Link
                  to={`/catalog/${product.id}`}
                  key={product.id}
                  className="product-card"
                >
                  <div className="product-card__image">
                    {product.images?.[0]?.url ? (
                      <img src={product.images[0].url} alt={product.name} />
                    ) : (
                      <div className="product-card__placeholder">No image</div>
                    )}
                  </div>
                  <div className="product-card__info">
                    <h4>{product.name}</h4>
                    {product.brand && (
                      <p className="product-card__brand">{product.brand}</p>
                    )}
                    <p className="product-card__price">
                      ${Number(product.price).toFixed(2)}
                    </p>
                    <p className="product-card__stock">
                      {product.stock > 0
                        ? `${product.stock} in stock`
                        : "Out of stock"}
                    </p>
                  </div>
                </Link>
              ))}
            </div>

            <div className="pagination">
              {page > 1 && (
                <button
                  onClick={() =>
                    setSearchParams((prev) => {
                      prev.set("page", String(page - 1));
                      return prev;
                    })
                  }
                >
                  Prev
                </button>
              )}
              <span>
                Page {page} of {totalPages}
              </span>
              {page < totalPages && (
                <button
                  onClick={() =>
                    setSearchParams((prev) => {
                      prev.set("page", String(page + 1));
                      return prev;
                    })
                  }
                >
                  Next
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
