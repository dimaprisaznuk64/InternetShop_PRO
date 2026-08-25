import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Mail, Phone, MapPin } from "lucide-react";
import "./Footer.css";

export function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="container--wide footer__inner">
        <div className="footer__grid">
          <div className="footer__brand">
            <Link to="/" className="footer__logo">
              <span className="footer__logo-icon">S</span>
              InternetShop
            </Link>
            <p className="footer__desc">{t("footer.description")}</p>
          </div>

          <div className="footer__col">
            <h4 className="footer__heading">{t("nav.catalog")}</h4>
            <Link to="/catalog" className="footer__link">{t("nav.catalog")}</Link>
            <Link to="/catalog?sort=newest" className="footer__link">{t("footer.new_arrivals")}</Link>
            <Link to="/catalog?sort=popular" className="footer__link">{t("footer.popular")}</Link>
          </div>

          <div className="footer__col">
            <h4 className="footer__heading">{t("footer.support")}</h4>
            <a href="mailto:support@internetshop.com" className="footer__link">
              <Mail size={14} /> support@internetshop.com
            </a>
            <a href="tel:+380991234567" className="footer__link">
              <Phone size={14} /> +380 99 123 45 67
            </a>
            <span className="footer__link">
              <MapSize14 /> {t("footer.shipping")}
            </span>
          </div>
        </div>

        <div className="footer__bottom">
          <p className="footer__copy">&copy; {year} InternetShop PRO. {t("footer.rights")}</p>
        </div>
      </div>
    </footer>
  );
}

function MapSize14() {
  return <MapPin size={14} />;
}
