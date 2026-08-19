import { useState, useEffect, useCallback } from "react";
import { adminApi } from "../../../api";
import type { PromoCode, PromoCodeCreate } from "../../../types";

export function AdminPromoPage() {
  const [promoCodes, setPromoCodes] = useState<PromoCode[]>([]);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<PromoCodeCreate>({
    code: "",
    discount_type: "percentage",
    discount_value: "10",
    min_order_amount: "",
    max_uses: undefined,
    expires_at: "",
  });
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchPromoCodes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminApi.listPromoCodes();
      setPromoCodes(data.promo_codes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPromoCodes();
  }, [fetchPromoCodes]);

  const openCreate = () => {
    setFormData({
      code: "",
      discount_type: "percentage",
      discount_value: "10",
      min_order_amount: "",
      max_uses: undefined,
      expires_at: "",
    });
    setFormError("");
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const payload: PromoCodeCreate = {
        code: formData.code.toUpperCase(),
        discount_type: formData.discount_type,
        discount_value: formData.discount_value,
      };
      if (formData.min_order_amount) payload.min_order_amount = formData.min_order_amount;
      if (formData.max_uses) payload.max_uses = formData.max_uses;
      if (formData.expires_at) payload.expires_at = formData.expires_at;

      await adminApi.createPromoCode(payload);
      setShowModal(false);
      fetchPromoCodes();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Create failed";
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this promo code?")) return;
    await adminApi.deletePromoCode(id);
    fetchPromoCodes();
  };

  const isExpired = (expiresAt: string | null) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  return (
    <div className="admin-promo">
      <div className="admin-page-header">
        <h1>Promo Codes ({promoCodes.length})</h1>
        <button className="btn btn--primary" onClick={openCreate}>
          + Add Promo Code
        </button>
      </div>

      {loading ? (
        <p className="admin-loading">Loading...</p>
      ) : promoCodes.length === 0 ? (
        <p className="admin-empty">No promo codes found.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Discount</th>
              <th>Min Order</th>
              <th>Uses</th>
              <th>Expires</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {promoCodes.map((promo) => (
              <tr key={promo.id}>
                <td className="admin-table__mono">{promo.code}</td>
                <td>
                  {promo.discount_type === "percentage"
                    ? `${promo.discount_value}%`
                    : `$${Number(promo.discount_value).toFixed(2)}`}
                </td>
                <td>
                  {promo.min_order_amount
                    ? `$${Number(promo.min_order_amount).toFixed(2)}`
                    : "—"}
                </td>
                <td>
                  {promo.used_count}
                  {promo.max_uses ? ` / ${promo.max_uses}` : ""}
                </td>
                <td>
                  {promo.expires_at
                    ? new Date(promo.expires_at).toLocaleDateString()
                    : "—"}
                </td>
                <td>
                  <span
                    className={`badge badge--${
                      !promo.is_active
                        ? "muted"
                        : isExpired(promo.expires_at)
                          ? "warning"
                          : "success"
                    }`}
                  >
                    {!promo.is_active ? "Inactive" : isExpired(promo.expires_at) ? "Expired" : "Active"}
                  </span>
                </td>
                <td className="admin-table__actions">
                  <button className="btn btn--sm btn--danger" onClick={() => handleDelete(promo.id)}>
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
              <h2>Create Promo Code</h2>
              <button className="modal__close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={handleSubmit} className="modal__body">
              {formError && <p className="error">{formError}</p>}
              <label>
                Code *
                <input
                  type="text"
                  required
                  placeholder="e.g. SALE20"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                />
              </label>
              <label>
                Discount Type *
                <select
                  value={formData.discount_type}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      discount_type: e.target.value as "percentage" | "fixed",
                    })
                  }
                >
                  <option value="percentage">Percentage (%)</option>
                  <option value="fixed">Fixed ($)</option>
                </select>
              </label>
              <label>
                Discount Value *
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.discount_value}
                  onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}
                />
              </label>
              <label>
                Min Order Amount
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="No minimum"
                  value={formData.min_order_amount ?? ""}
                  onChange={(e) =>
                    setFormData({ ...formData, min_order_amount: e.target.value || undefined })
                  }
                />
              </label>
              <label>
                Max Uses
                <input
                  type="number"
                  min="1"
                  placeholder="Unlimited"
                  value={formData.max_uses ?? ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_uses: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </label>
              <label>
                Expires At
                <input
                  type="datetime-local"
                  value={formData.expires_at ?? ""}
                  onChange={(e) =>
                    setFormData({ ...formData, expires_at: e.target.value || undefined })
                  }
                />
              </label>
              <div className="modal__footer">
                <button type="button" className="btn btn--ghost" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn--primary" disabled={saving}>
                  {saving ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
