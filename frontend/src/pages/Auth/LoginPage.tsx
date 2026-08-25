import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, LogIn, AlertCircle } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { getApiErrorMessage } from "../../api/client";
import "./Auth.css";

export function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: string })?.from || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, "Invalid email or password"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page container">
      <div className="auth-card">
        <div className="auth-card__icon"><LogIn size={24} /></div>
        <h1 className="auth-card__title">{t("auth.login_title")}</h1>
        <p className="auth-card__subtitle">{t("auth.login_subtitle")}</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label className="auth-field__label">{t("auth.email")}</label>
            <input
              type="email"
              className="auth-field__input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="auth-field">
            <label className="auth-field__label">{t("auth.password")}</label>
            <div className="auth-field__password">
              <input
                type={showPassword ? "text" : "password"}
                className="auth-field__input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
              <button type="button" className="auth-field__toggle" onClick={() => setShowPassword(!showPassword)} tabIndex={-1}>
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="auth-error"><AlertCircle size={14} /> {error}</div>
          )}

          <button type="submit" className="btn btn--primary btn--full btn--lg" disabled={loading}>
            {loading ? t("common.loading") : t("auth.login")}
          </button>
        </form>

        <p className="auth-card__footer">
          {t("auth.no_account")} <Link to="/register">{t("nav.register")}</Link>
        </p>
      </div>
    </div>
  );
}
