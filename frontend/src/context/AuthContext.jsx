import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('pharmintel_token'));
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState(() => {
    try {
      const saved = localStorage.getItem('pharmintel_cart');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('pharmintel_cart', JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const userData = await api.getMe();
          setUser(userData);
        } catch (e) {
          console.error("Token verification failed:", e);
          localStorage.removeItem('pharmintel_token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    }
    loadUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await api.login(email, password);
    localStorage.setItem('pharmintel_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res;
  };

  const register = async (data) => {
    const res = await api.register(data);
    localStorage.setItem('pharmintel_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res;
  };

  const logout = () => {
    localStorage.removeItem('pharmintel_token');
    setToken(null);
    setUser(null);
  };

  // Cart operations
  const addToCart = (medicine, quantity = 1, pharmacyId = 1) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.id === medicine.id);
      if (existing) {
        return prev.map((item) =>
          item.id === medicine.id ? { ...item, quantity: item.quantity + quantity } : item
        );
      }
      return [
        ...prev,
        {
          id: medicine.id,
          brand_name: medicine.brand_name,
          generic_name: medicine.generic_name,
          strength: medicine.strength,
          dosage_form: medicine.dosage_form,
          base_mrp: medicine.base_mrp,
          requires_prescription: medicine.requires_prescription,
          pharmacy_id: pharmacyId,
          quantity: quantity,
        },
      ];
    });
  };

  const removeFromCart = (medicineId) => {
    setCart((prev) => prev.filter((item) => item.id !== medicineId));
  };

  const updateQuantity = (medicineId, qty) => {
    if (qty <= 0) {
      removeFromCart(medicineId);
    } else {
      setCart((prev) =>
        prev.map((item) => (item.id === medicineId ? { ...item, quantity: qty } : item))
      );
    }
  };

  const clearCart = () => setCart([]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        cart,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
