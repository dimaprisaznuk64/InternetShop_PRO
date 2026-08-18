import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { useCart } from "../../contexts/CartContext";

export function Header() {
  const { user, logout, isAdmin } = useAuth();
  const { itemCount } = useCart();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="header__logo">
          InternetShop
        </Link>

        <nav className="header__nav">
          <Link to="/catalog">Catalog</Link>
          {user && (
            <>
              <Link to="/cart" className="header__cart">
                Cart
                {itemCount > 0 && (
                  <span className="header__cart-badge">{itemCount}</span>
                )}
              </Link>
              <Link to="/orders">Orders</Link>
              <Link to="/favorites">Favorites</Link>
              <Link to="/profile">{user.username}</Link>
              {isAdmin && <Link to="/admin">Admin</Link>}
              <button onClick={handleLogout} className="btn btn--ghost">
                Logout
              </button>
            </>
          )}
          {!user && (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
