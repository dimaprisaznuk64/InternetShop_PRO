import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Search, ArrowRight, Moon, Sun, Globe, ShoppingCart } from "lucide-react";
import { productsApi } from "../../api";
import { useCurrency, CURRENCY_SYMBOLS, type Currency } from "../../contexts/CurrencyContext";
import { useTheme } from "../../hooks/useTheme";
import type { Product } from "../../types";
import "./CommandPalette.css";

interface PaletteItem {
  id: string;
  label: string;
  sublabel?: string;
  icon?: React.ReactNode;
  action: () => void;
  keywords?: string[];
  isProduct: boolean;
  product?: Product;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: Props) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { setCurrency } = useCurrency();
  const { theme, toggle: toggleTheme } = useTheme();
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const languages = [
    { code: "uk", label: "UA" },
    { code: "en", label: "EN" },
    { code: "pl", label: "PL" },
  ];

  const actions: PaletteItem[] = [
    {
      id: "catalog",
      label: t("nav.catalog"),
      icon: <ArrowRight size={16} />,
      action: () => { navigate("/catalog"); onClose(); },
      keywords: ["catalog", "products", "товари"],
      isProduct: false,
    },
    {
      id: "cart",
      label: t("nav.cart"),
      icon: <ShoppingCart size={16} />,
      action: () => { navigate("/cart"); onClose(); },
      keywords: ["cart", "кошик"],
      isProduct: false,
    },
    {
      id: "theme",
      label: `${t("common.theme")} (${theme === "light" ? t("common.dark") : t("common.light")})`,
      icon: theme === "light" ? <Moon size={16} /> : <Sun size={16} />,
      action: () => { toggleTheme(); onClose(); },
      keywords: ["theme", "dark", "light", "тема"],
      isProduct: false,
    },
    ...languages.map((l) => ({
      id: `lang-${l.code}`,
      label: `${t("common.language")}: ${l.label}`,
      icon: <Globe size={16} />,
      action: () => { i18n.changeLanguage(l.code); onClose(); },
      keywords: ["language", "мова", "lang", l.code],
      isProduct: false as const,
    })),
    ...(Object.keys(CURRENCY_SYMBOLS) as Currency[]).map((cur) => ({
      id: `cur-${cur}`,
      label: `${t("common.currency")}: ${CURRENCY_SYMBOLS[cur]} ${cur}`,
      icon: <span style={{ fontFamily: "var(--font-family-mono)", fontSize: "0.875rem" }}>{CURRENCY_SYMBOLS[cur]}</span>,
      action: () => { setCurrency(cur); onClose(); },
      keywords: ["currency", "валюта", cur.toLowerCase()],
      isProduct: false as const,
    })),
  ];

  const allItems: PaletteItem[] = [
    ...products.map((p) => ({
      id: `product-${p.id}`,
      label: p.name,
      sublabel: p.brand || undefined,
      action: () => { navigate(`/catalog/${p.id}`); onClose(); },
      isProduct: true,
      product: p,
    })),
    ...actions.map((a) => ({
      id: a.id,
      label: a.label,
      icon: a.icon,
      action: a.action,
      keywords: a.keywords,
      isProduct: false,
    })),
  ];

  const filteredItems = query.trim()
    ? allItems.filter((item) => {
        const q = query.toLowerCase();
        if (item.isProduct && item.product) {
          const p = item.product;
          return (
            p.name.toLowerCase().includes(q) ||
            (p.brand && p.brand.toLowerCase().includes(q)) ||
            p.sku.toLowerCase().includes(q)
          );
        }
        return (
          item.label.toLowerCase().includes(q) ||
          (item.keywords && item.keywords.some((k) => k.includes(q)))
        );
      })
    : actions;

  const displayItems = filteredItems;

  // Debounced product search
  useEffect(() => {
    if (!open) {
      setQuery("");
      setProducts([]);
      setActiveIdx(0);
      return;
    }
    // Focus input on open
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (!query.trim() || query.trim().length < 2) {
      setProducts([]);
      setActiveIdx(0);
      return;
    }
    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await productsApi.list({ q: query.trim(), limit: 5 });
        setProducts(data.products);
      } catch {
        setProducts([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  useEffect(() => {
    setActiveIdx(0);
  }, [displayItems.length, query]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIdx((i) => (i + 1) % displayItems.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIdx((i) => (i - 1 + displayItems.length) % displayItems.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        displayItems[activeIdx]?.action();
      } else if (e.key === "Escape") {
        onClose();
      }
    },
    [displayItems, activeIdx, onClose]
  );

  if (!open) return null;

  return (
    <div className="cp-overlay" onClick={onClose}>
      <div className="cp" onClick={(e) => e.stopPropagation()}>
        <div className="cp__input-wrap">
          <Search size={18} className="cp__search-icon" />
          <input
            ref={inputRef}
            className="cp__input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("command_palette.search") || "Search products, actions..."}
            autoComplete="off"
          />
          {searching && <span className="cp__spinner" />}
          <kbd className="cp__kbd">ESC</kbd>
        </div>

        <div className="cp__list">
          {displayItems.length === 0 && (
            <div className="cp__empty">{t("command_palette.no_results") || "No results"}</div>
          )}
          {displayItems.map((item, i) => (
            <button
              key={item.id}
              className={`cp__item ${i === activeIdx ? "cp__item--active" : ""}`}
              onMouseEnter={() => setActiveIdx(i)}
              onClick={item.action}
            >
              <span className="cp__item-label">{item.label}</span>
              {item.sublabel && <span className="cp__item-sub">{item.sublabel}</span>}
              {item.icon && <span className="cp__item-icon">{item.icon}</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/** Global hook: listens for Ctrl+K / Cmd+K */
export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return { open, setOpen };
}
