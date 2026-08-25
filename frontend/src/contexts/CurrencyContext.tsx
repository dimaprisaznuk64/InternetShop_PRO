import { createContext, useContext } from "react";
import { useLocalStorage } from "../hooks";

export type Currency = "UAH" | "USD" | "EUR";

interface CurrencyContextValue {
  currency: Currency;
  setCurrency: (c: Currency) => void;
  symbol: string;
  rate: number;
}

const SYMBOLS: Record<Currency, string> = {
  UAH: "\u20B4",
  USD: "$",
  EUR: "\u20AC",
};

export const CURRENCY_SYMBOLS = SYMBOLS;

const RATES: Record<Currency, number> = {
  UAH: 1,
  USD: 41.5,
  EUR: 45,
};

const CurrencyContext = createContext<CurrencyContextValue>({
  currency: "UAH",
  setCurrency: () => {},
  symbol: "\u20B4",
  rate: 1,
});

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const [currency, setCurrency] = useLocalStorage<Currency>("currency", "UAH");

  const value: CurrencyContextValue = {
    currency,
    setCurrency,
    symbol: SYMBOLS[currency],
    rate: RATES[currency],
  };

  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  return useContext(CurrencyContext);
}

export function formatPrice(uahPrice: number | string, currency: Currency): string {
  const num = Number(uahPrice);
  const converted = num / RATES[currency];
  return `${converted.toLocaleString("uk-UA", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${SYMBOLS[currency]}`;
}
