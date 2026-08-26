import { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ShoppingCart, Menu, X,
  Sun, Moon, Search
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useCart } from "../../contexts/CartContext";
import { useCurrency, CURRENCY_SYMBOLS, type Currency } from "../../contexts/CurrencyContext";
import { useIsMobile } from "../../hooks";
import { useTheme } from "../../hooks/useTheme";
import { Badge } from "../ui/Badge";
import "./Header.css";

export function Header() {
  const { t, i18n } = useTranslation();
  const { user, logout, isAdmin } = useAuth();
  const { itemCount } = useCart();
  const { currency, setCurrency } = useCurrency();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [currencyMenuOpen, setCurrencyMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const { theme, toggle: toggleTheme } = useTheme();
  const [searchValue, setSearchValue] = useState("");
  const userMenuRef = useRef<HTMLDivElement>(null);
  const langMenuRef = useRef<HTMLDivElement>(null);
  const currencyMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
    setUserMenuOpen(false);
    setLangMenuOpen(false);
    setCurrencyMenuOpen(false);
    setSearchOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node))
        setUserMenuOpen(false);
      if (langMenuRef.current && !langMenuRef.current.contains(e.target as Node))
        setLangMenuOpen(false);
      if (currencyMenuRef.current && !currencyMenuRef.current.contains(e.target as Node))
        setCurrencyMenuOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      navigate(`/catalog?q=${encodeURIComponent(searchValue.trim())}`);
      setSearchValue("");
      setSearchOpen(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
    setUserMenuOpen(false);
  };

  const changeLang = (lng: string) => {
    i18n.changeLanguage(lng);
    setLangMenuOpen(false);
  };

  const languages = [
    { code: "uk", label: "UA" },
    { code: "en", label: "EN" },
    { code: "pl", label: "PL" },
  ];

  return (
    <>
      <header className={`header ${scrolled ? "header--scrolled" : ""}`}>
        <div className="header__inner container--wide">
          {/* Logo */}
          <Link to="/" className="header__logo">
            <span className="header__logo-icon">S</span>
            {!isMobile && <span className="header__logo-text">InternetShop</span>}
          </Link>

          {/* Desktop Nav */}
          {!isMobile && (
            <nav className="header__nav">
              <Link to="/catalog" className={`header__nav-link ${location.pathname === "/catalog" ? "header__nav-link--active" : ""}`}>
                {t("nav.catalog")}
              </Link>
              {user && (
                <Link to="/favorites" className={`header__nav-link ${location.pathname === "/favorites" ? "header__nav-link--active" : ""}`}>
                  {t("nav.favorites")}
                </Link>
              )}
            </nav>
          )}

          {/* Search */}
          {!isMobile && (
            <form className="header__search" onSubmit={handleSearch}>
              <div className="header__search-wrap">
                <Search size={16} className="header__search-icon" />
                <input
                  type="text"
                  className="header__search-input"
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  placeholder={t("catalog.search_placeholder")}
                />
              </div>
            </form>
          )}

          {/* Right Actions */}
          <div className="header__actions">
            {/* Mobile Search */}
            {isMobile && (
              <button className="header__icon-btn" onClick={() => setSearchOpen(!searchOpen)}>
                <Search size={18} />
              </button>
            )}

            {/* Language */}
            <div className="header__dropdown-wrap" ref={langMenuRef}>
              <button
                className="header__icon-btn"
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                title={t("common.language")}
              >
                <span className="header__lang-label">{languages.find(l => l.code === i18n.language)?.label || "EN"}</span>
              </button>
              {langMenuOpen && (
                <div className="header__dropdown header__dropdown--right">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      className={`header__dropdown-item ${i18n.language === lang.code ? "header__dropdown-item--active" : ""}`}
                      onClick={() => changeLang(lang.code)}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Currency */}
            <div className="header__dropdown-wrap" ref={currencyMenuRef}>
              <button
                className="header__icon-btn"
                onClick={() => setCurrencyMenuOpen(!currencyMenuOpen)}
                title={t("common.currency")}
              >
                <span className="header__currency-label">{CURRENCY_SYMBOLS[currency]}</span>
              </button>
              {currencyMenuOpen && (
                <div className="header__dropdown header__dropdown--right">
                  {(Object.keys(CURRENCY_SYMBOLS) as Currency[]).map((cur) => (
                    <button
                      key={cur}
                      className={`header__dropdown-item ${currency === cur ? "header__dropdown-item--active" : ""}`}
                      onClick={() => { setCurrency(cur); setCurrencyMenuOpen(false); }}
                    >
                      {CURRENCY_SYMBOLS[cur]} {cur}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Theme */}
            <button
              className="header__icon-btn"
              onClick={toggleTheme}
              title={t("common.theme")}
            >
              {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            </button>

            {/* Cart */}
            {user && (
              <Link to="/cart" className="header__icon-btn header__cart-btn" title={t("nav.cart")}>
                <ShoppingCart size={18} />
                {itemCount > 0 && <span className="header__badge">{itemCount}</span>}
              </Link>
            )}

            {/* User */}
            {user ? (
              <div className="header__dropdown-wrap" ref={userMenuRef}>
                <button
                  className="header__user-btn"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                  <div className="header__avatar">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                </button>
                {userMenuOpen && (
                  <div className="header__dropdown header__dropdown--right">
                    <div className="header__dropdown-header">
                      <div className="header__avatar header__avatar--lg">
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="header__dropdown-name">{user.username}</div>
                        <div className="header__dropdown-email">{user.email}</div>
                      </div>
                    </div>
                    <div className="header__dropdown-divider" />
                    <Link to="/profile" className="header__dropdown-item">
                      {t("nav.profile")}
                    </Link>
                    <Link to="/orders" className="header__dropdown-item">
                      {t("nav.orders")}
                    </Link>
                    <Link to="/favorites" className="header__dropdown-item">
                      {t("nav.favorites")}
                    </Link>
                    {isAdmin && (
                      <Link to="/admin" className="header__dropdown-item">
                        {t("nav.admin")}
                      </Link>
                    )}
                    <div className="header__dropdown-divider" />
                    <button className="header__dropdown-item header__dropdown-item--danger" onClick={handleLogout}>
                      {t("nav.logout")}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="header__auth-btns">
                <Link to="/login" className="btn btn--ghost btn--sm">{t("nav.login")}</Link>
                <Link to="/register" className="btn btn--primary btn--sm">{t("nav.register")}</Link>
              </div>
            )}

            {/* Mobile Hamburger */}
            {isMobile && (
              <button
                className="header__icon-btn"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Search Overlay */}
      {isMobile && searchOpen && (
        <div className="header__search-overlay">
          <form className="header__search-form" onSubmit={handleSearch}>
            <button type="button" className="header__icon-btn" onClick={() => setSearchOpen(false)}>
              <X size={18} />
            </button>
            <input
              autoFocus
              type="text"
              className="header__search-input"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder={t("catalog.search_placeholder")}
            />
            <button type="submit" className="header__icon-btn">
              <Search size={18} />
            </button>
          </form>
        </div>
      )}

      {/* Mobile Menu */}
      {isMobile && mobileMenuOpen && (
        <div className="mobile-menu">
          <div className="mobile-menu__overlay" onClick={() => setMobileMenuOpen(false)} />
          <div className="mobile-menu__panel">
            <nav className="mobile-menu__nav">
              <Link to="/catalog" className="mobile-menu__link">{t("nav.catalog")}</Link>
              {user && (
                <>
                  <Link to="/favorites" className="mobile-menu__link">{t("nav.favorites")}</Link>
                  <Link to="/cart" className="mobile-menu__link">
                    {t("nav.cart")} {itemCount > 0 && <Badge variant="primary">{itemCount}</Badge>}
                  </Link>
                  <Link to="/orders" className="mobile-menu__link">{t("nav.orders")}</Link>
                  <Link to="/profile" className="mobile-menu__link">{t("nav.profile")}</Link>
                  {isAdmin && <Link to="/admin" className="mobile-menu__link">{t("nav.admin")}</Link>}
                </>
              )}
            </nav>

            <div className="mobile-menu__divider" />

            <div className="mobile-menu__section">
              <div className="mobile-menu__section-title">{t("common.language")}</div>
              <div className="header__lang-pills header__lang-pills--mobile">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    className={`header__lang-pill ${i18n.language === lang.code ? "header__lang-pill--active" : ""}`}
                    onClick={() => changeLang(lang.code)}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="mobile-menu__section">
              <div className="mobile-menu__section-title">{t("common.theme")}</div>
              <button className="mobile-menu__link" onClick={toggleTheme}>
                {theme === "light" ? <Moon size={18} /> : <Sun size={18} />} {t("common.theme")}
              </button>
            </div>

            <div className="mobile-menu__divider" />

            <div className="mobile-menu__bottom">
              {user ? (
                <button className="mobile-menu__link mobile-menu__link--danger" onClick={handleLogout}>
                  {t("nav.logout")}
                </button>
              ) : (
                <>
                  <Link to="/login" className="btn btn--primary btn--full">{t("nav.login")}</Link>
                  <Link to="/register" className="btn btn--secondary btn--full">{t("nav.register")}</Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Spacer */}
      <div className="header-spacer" />
    </>
  );
}
