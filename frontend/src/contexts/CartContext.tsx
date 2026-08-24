import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { cartApi } from "../api";
import { useAuth } from "./AuthContext";
import type { Cart } from "../types";

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  itemCount: number;
  addItem: (productId: string, quantity: number, variantId?: string) => Promise<void>;
  updateItem: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clear: () => Promise<void>;
  refresh: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!user) {
      setCart(null);
      return;
    }
    try {
      setLoading(true);
      const data = await cartApi.get();
      setCart(data);
    } catch {
      setCart(null);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const itemCount =
    cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0;

  const addItem = async (
    productId: string,
    quantity: number,
    variantId?: string
  ) => {
    const data = await cartApi.addItem({
      product_id: productId,
      quantity,
      variant_id: variantId ?? null,
    });
    setCart(data);
  };

  const updateItem = async (itemId: string, quantity: number) => {
    const data = await cartApi.updateItem(itemId, { quantity });
    setCart(data);
  };

  const removeItem = async (itemId: string) => {
    await cartApi.removeItem(itemId);
    await fetchCart();
  };

  const clear = async () => {
    await cartApi.clear();
    setCart(null);
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        itemCount,
        addItem,
        updateItem,
        removeItem,
        clear,
        refresh: fetchCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) throw new Error("useCart must be used within CartProvider");
  return context;
}
