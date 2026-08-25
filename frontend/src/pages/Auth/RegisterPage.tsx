import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, UserPlus, AlertCircle } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { getApiErrorMessage } from "../../api/client";
import "./Auth.css";

export function RegisterPage() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) { setError("Passwords do not match"); return; }
    if (password.length < 6) { setError("Password must be at least 6 characters"); return; }
    setLoading(true);
    try {
      await register(email, username, password);
      navigate("/");
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Registration failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__icon"><UserPlus size={24} /></div>
        <h1 className="auth-card__title">{t("auth.register_title")}</h1>
        <p className="auth-card__subtitle">{t("auth.register_subtitle")}</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label className="auth-field__label">{t("auth.email")}</label>
            <input type="email" className="auth-field__input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" />
          </div>
          <div className="auth-field">
            <label className="auth-field__label">{t("auth.username")}</label>
            <input type="text" className="auth-field__input" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" required autoComplete="username" />
          </div>
          <div className="auth-field">
            <label className="auth-field__label">{t("auth.password")}</label>
            <div className="auth-field__password">
              <input type={showPassword ? "text" : "password"} className="auth-field__input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required minLength={6} autoComplete="new-password" />
              <button type="button" className="auth-field__toggle" onClick={() => setShowPassword(!showPassword)} tabIndex={-1}>
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
          <div className="auth-field">
            <label className="auth-field__label">{t("auth.confirm_password")}</label>
            <input type={showPassword ? "text" : "password"} className="auth-field__input" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" required autoComplete="new-password" />
          </div>

          {error && <div className="auth-error"><AlertCircle size={14} /> {error}</div>}

          <button type="submit" className="btn btn--primary btn--full btn--lg" disabled={loading}>
            {loading ? t("common.loading") : t("auth.register")}
          </button>
        </form>

        <p className="auth-card__footer">
          {t("auth.has_account")} <Link to="/login">{t("nav.login")}</Link>
        </p>
      </div>
    </div>
  );
}
