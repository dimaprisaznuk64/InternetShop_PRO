import { useState, useEffect, useCallback } from "react";
import { adminApi, categoriesApi } from "../../../api";
import { getApiErrorMessage } from "../../../api/client";
import type { Category, CategoryCreate, CategoryUpdate } from "../../../types";

export function AdminCategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [formData, setFormData] = useState<CategoryCreate>({
    name: "",
    slug: "",
    parent_id: null,
    image_url: null,
  });
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await categoriesApi.list();
      setCategories(data.categories);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const getParentName = (parentId: string | null) => {
    if (!parentId) return "—";
    return categories.find((c) => c.id === parentId)?.name ?? "—";
  };

  const openCreate = () => {
    setEditingCategory(null);
    setFormData({ name: "", slug: "", parent_id: null, image_url: null });
    setFormError("");
    setShowModal(true);
  };

  const openEdit = (cat: Category) => {
    setEditingCategory(cat);
    setFormData({
      name: cat.name,
      slug: cat.slug,
      parent_id: cat.parent_id,
      image_url: cat.image_url,
    });
    setFormError("");
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      if (editingCategory) {
        const update: CategoryUpdate = { ...formData };
        await adminApi.updateCategory(editingCategory.id, update);
      } else {
        await adminApi.createCategory(formData);
      }
      setShowModal(false);
      fetchCategories();
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, "Save failed");
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this category? Products in this category will lose their category.")) return;
    await adminApi.deleteCategory(id);
    fetchCategories();
  };

  return (
    <div className="admin-categories container">
      <div className="admin-page-header">
        <h1>Categories ({categories.length})</h1>
        <button className="btn btn--primary" onClick={openCreate}>
          + Add Category
        </button>
      </div>

      {loading ? (
        <p className="admin-loading">Loading...</p>
      ) : categories.length === 0 ? (
        <p className="admin-empty">No categories found.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Slug</th>
              <th>Parent</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <tr key={cat.id}>
                <td>{cat.name}</td>
                <td className="admin-table__mono">{cat.slug}</td>
                <td>{getParentName(cat.parent_id)}</td>
                <td className="admin-table__actions">
                  <button className="btn btn--sm btn--ghost" onClick={() => openEdit(cat)}>
                    Edit
                  </button>
                  <button className="btn btn--sm btn--danger" onClick={() => handleDelete(cat.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__header">
              <h2>{editingCategory ? "Edit Category" : "Create Category"}</h2>
              <button className="modal__close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={handleSubmit} className="modal__body">
              {formError && <p className="error">{formError}</p>}
              <label>
                Name *
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </label>
              <label>
                Slug *
                <input
                  type="text"
                  required
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                />
              </label>
              <label>
                Parent Category
                <select
                  value={formData.parent_id ?? ""}
                  onChange={(e) =>
                    setFormData({ ...formData, parent_id: e.target.value || null })
                  }
                >
                  <option value="">None (top-level)</option>
                  {categories
                    .filter((c) => c.id !== editingCategory?.id)
                    .map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
              </label>
              <label>
                Image URL
                <input
                  type="text"
                  value={formData.image_url ?? ""}
                  onChange={(e) =>
                    setFormData({ ...formData, image_url: e.target.value || null })
                  }
                />
              </label>
              <div className="modal__footer">
                <button type="button" className="btn btn--ghost" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn--primary" disabled={saving}>
                  {saving ? "Saving..." : editingCategory ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
