import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { productsApi, categoriesApi } from "../../api";
import type { Product, Category } from "../../types";

export function CatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const q = searchParams.get("q") || "";
  const categoryId = searchParams.get("category_id") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const limit = 20;
  const offset = (page - 1) * limit;

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await productsApi.list({
        q: q || undefined,
        category_id: categoryId || undefined,
        limit,
        offset,
      });
      setProducts(data.products);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load products", err);
    } finally {
      setLoading(false);
    }
  }, [q, categoryId, offset]);

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

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const search = formData.get("q") as string;
    setSearchParams((prev) => {
      prev.set("q", search);
      prev.delete("page");
      return prev;
    });
  };

  return (
    <div className="catalog">
      <div className="catalog__sidebar">
        <h3>Categories</h3>
        <ul>
          <li>
            <button
              className={!categoryId ? "active" : ""}
              onClick={() =>
                setSearchParams((prev) => {
                  prev.delete("category_id");
                  return prev;
                })
              }
            >
              All
            </button>
          </li>
          {categories.map((cat) => (
            <li key={cat.id}>
              <button
                className={categoryId === cat.id ? "active" : ""}
                onClick={() =>
                  setSearchParams((prev) => {
                    prev.set("category_id", cat.id);
                    prev.delete("page");
                    return prev;
                  })
                }
              >
                {cat.name}
              </button>
            </li>
          ))}
        </ul>
      </div>

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
                    <p className="product-card__price">
                      ${Number(product.price).toFixed(2)}
                    </p>
                    <p className="product-card__stock">
                      {product.stock > 0 ? "In stock" : "Out of stock"}
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
