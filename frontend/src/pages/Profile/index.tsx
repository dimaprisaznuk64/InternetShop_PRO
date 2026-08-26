import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { User, Calendar, Lock, CheckCircle, AlertCircle } from "lucide-react";
import { profileApi } from "../../api";
import type { UserResponse } from "../../types";
import { Skeleton } from "../../components/ui/Skeleton";
import "./Profile.css";

export function ProfilePage() {
  const { t } = useTranslation();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    profileApi.get()
      .then((data) => { setUser(data); setUsername(data.username); setEmail(data.email); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setMessage("");
    try {
      const updated = await profileApi.update({ username, email });
      setUser(updated);
      setMessage("Profile updated!");
    } catch { setError("Failed to update profile"); }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setMessage("");
    try {
      await profileApi.changePassword({ current_password: currentPassword, new_password: newPassword });
      setMessage("Password changed!");
      setCurrentPassword(""); setNewPassword("");
    } catch { setError("Failed to change password"); }
  };

  if (loading) {
    return (
      <div className="profile-page container">
        <div className="profile-header">
          <Skeleton variant="circular" width={64} height={64} />
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <Skeleton width={160} height={22} />
            <Skeleton width={220} height={14} />
          </div>
        </div>
        <div className="profile-grid">
          {[1, 2].map((i) => (
            <Skeleton key={i} variant="rectangular" height={260} />
          ))}
        </div>
      </div>
    );
  }
  if (!user) return <div className="profile-page__error">Failed to load profile</div>;

  const roleColors: Record<string, string> = { admin: "var(--color-danger)", manager: "var(--color-accent)", user: "var(--color-text-muted)" };

  return (
    <div className="profile-page container">
      <div className="profile-header">
        <div className="profile-avatar">{user.username.charAt(0).toUpperCase()}</div>
        <div>
          <h1 className="profile-name">{user.username}</h1>
          <p className="profile-email">{user.email}</p>
          <div className="profile-meta">
            <span className="profile-role" style={{ background: roleColors[user.role] || roleColors.user }}>{user.role}</span>
            <span className="profile-date"><Calendar size={14} /> Member since {new Date(user.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="profile-nav">
        <Link to="/orders" className="profile-nav__link">{t("nav.orders")}</Link>
        <Link to="/favorites" className="profile-nav__link">{t("nav.favorites")}</Link>
      </div>

      <div className="profile-grid">
        <form onSubmit={handleUpdateProfile} className="profile-card">
          <h3 className="profile-card__title"><User size={18} /> {t("profile.edit_profile")}</h3>
          <div className="profile-field">
            <label className="profile-field__label">{t("auth.username")}</label>
            <input type="text" className="profile-field__input" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div className="profile-field">
            <label className="profile-field__label">{t("auth.email")}</label>
            <input type="email" className="profile-field__input" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <button type="submit" className="btn btn--primary btn--sm">{t("common.save")}</button>
        </form>

        <form onSubmit={handleChangePassword} className="profile-card">
          <h3 className="profile-card__title"><Lock size={18} /> {t("profile.change_password")}</h3>
          <div className="profile-field">
            <label className="profile-field__label">{t("auth.password")}</label>
            <input type="password" className="profile-field__input" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          </div>
          <div className="profile-field">
            <label className="profile-field__label">{t("auth.confirm_password")}</label>
            <input type="password" className="profile-field__input" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={6} />
          </div>
          <button type="submit" className="btn btn--primary btn--sm">{t("common.save")}</button>
        </form>
      </div>

      {message && <div className="profile-toast profile-toast--success"><CheckCircle size={14} /> {message}</div>}
      {error && <div className="profile-toast profile-toast--error"><AlertCircle size={14} /> {error}</div>}
    </div>
  );
}
