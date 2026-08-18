import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div className="home">
      <section className="hero">
        <h1>Welcome to InternetShop</h1>
        <p>Find the best products at great prices</p>
        <Link to="/catalog" className="btn btn--primary">
          Browse Catalog
        </Link>
      </section>
    </div>
  );
}
