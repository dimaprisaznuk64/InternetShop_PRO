import { useState, useEffect } from "react";
import { productsApi, categoriesApi } from "../../../api";
import type { Product, Category } from "../../../types";

export function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      productsApi.list({ limit: 100 }),
      categoriesApi.list(),
    ])
      .then(([productData, catData]) => {
        setProducts(productData.products);
        setCategories(catData.categories);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this product?")) return;
    await productsApi.delete(id);
    setProducts((prev) => prev.filter((p) => p.id !== id));
  };

  const getCategoryName = (categoryId: string) =>
    categories.find((c) => c.id === categoryId)?.name ?? "—";

  if (loading) return <p>Loading products...</p>;

  return (
    <div className="admin-products">
      <h1>Products ({products.length})</h1>

      <table className="admin-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>SKU</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Category</th>
            <th>Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td>{product.name}</td>
              <td>{product.sku}</td>
              <td>${Number(product.price).toFixed(2)}</td>
              <td>{product.stock}</td>
              <td>{getCategoryName(product.category_id)}</td>
              <td>{product.is_active ? "Yes" : "No"}</td>
              <td>
                <button onClick={() => handleDelete(product.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
