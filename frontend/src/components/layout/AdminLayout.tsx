import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LayoutDashboard, Package, FolderTree, Users, ShoppingCart, Tag, ChevronRight } from "lucide-react";
import "./AdminLayout.css";

const NAV_ITEMS = [
  { to: "/admin", labelKey: "admin.dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/products", labelKey: "admin.products", icon: Package },
  { to: "/admin/categories", labelKey: "admin.categories", icon: FolderTree },
  { to: "/admin/users", labelKey: "admin.users", icon: Users },
  { to: "/admin/orders", labelKey: "admin.orders", icon: ShoppingCart },
  { to: "/admin/promo", labelKey: "admin.promo", icon: Tag },
];

export function AdminLayout() {
  const { t } = useTranslation();

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-sidebar__header">
          <span className="admin-sidebar__logo">A</span>
          <span className="admin-sidebar__title">{t("nav.admin")}</span>
        </div>
        <nav className="admin-sidebar__nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `admin-sidebar__link ${isActive ? "admin-sidebar__link--active" : ""}`
              }
            >
              <item.icon size={18} />
              <span>{t(item.labelKey)}</span>
              <ChevronRight size={14} className="admin-sidebar__arrow" />
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="admin-content">
        <Outlet />
      </div>
    </div>
  );
}
