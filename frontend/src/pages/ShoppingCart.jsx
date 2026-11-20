import React from 'react';
import {
  ShoppingBag, Trash2, Plus, Minus, ArrowRight, ShieldAlert,
  FileText, ArrowLeft, CheckCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ShoppingCart({ onNavigate }) {
  const { cart, updateQuantity, removeFromCart, clearCart } = useAuth();

  const subtotal = cart.reduce((sum, itm) => sum + itm.base_mrp * itm.quantity, 0);
  const tax = subtotal * 0.12;
  const deliveryFee = subtotal > 500 ? 0 : 40;
  const total = subtotal + tax + (subtotal > 0 ? deliveryFee : 0);

  const hasRxItems = cart.some((itm) => itm.requires_prescription);

  if (cart.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Your Shopping Cart is Empty</h2>
        <p className="text-xs text-slate-500 mb-6">
          Browse our centralized medicine database to select verified medications.
        </p>
        <button
          onClick={() => onNavigate('search')}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition"
        >
          Explore Medicines
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
          <ShoppingBag className="w-6 h-6 text-blue-600" /> Medicine Cart ({cart.length} items)
        </h1>
        <button
          onClick={clearCart}
          className="text-xs text-red-600 hover:text-red-800 font-semibold"
        >
          Clear Cart
        </button>
      </div>

      {hasRxItems && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl mb-6 text-xs text-amber-900 flex items-start gap-2">
          <FileText className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Prescription Required for Dispensing:</span>
            <span>
              Your cart contains Schedule H / Rx medications. You will be prompted to attach a verified
              doctor's prescription at checkout.
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items List */}
        <div className="lg:col-span-2 space-y-4">
          {cart.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold text-slate-900">{item.brand_name}</span>
                  {item.requires_prescription && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                      Rx Required
                    </span>
                  )}
                </div>
                <p className="text-xs text-teal-700 font-medium">
                  {item.generic_name} • {item.strength} • {item.dosage_form}
                </p>
                <p className="text-xs font-mono font-bold text-slate-900 mt-1">
                  ₹{item.base_mrp.toFixed(2)} each
                </p>
              </div>

              <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
                {/* Quantity Controls */}
                <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-slate-50">
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    className="p-1.5 hover:bg-slate-200 text-slate-600 transition"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="px-3 text-xs font-bold font-mono text-slate-900">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    className="p-1.5 hover:bg-slate-200 text-slate-600 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>

                <span className="font-mono font-bold text-sm text-slate-900 min-w-16 text-right">
                  ₹{(item.base_mrp * item.quantity).toFixed(2)}
                </span>

                <button
                  onClick={() => removeFromCart(item.id)}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary & Proceed */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm h-fit">
          <h3 className="font-bold text-slate-900 text-sm mb-4 pb-2 border-b border-slate-100">
            Order Price Breakdown
          </h3>

          <div className="space-y-2.5 text-xs text-slate-600 mb-4">
            <div className="flex justify-between">
              <span>Item Subtotal:</span>
              <span className="font-mono text-slate-900">₹{subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Pharma GST (12%):</span>
              <span className="font-mono text-slate-900">₹{tax.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Healthcare Delivery:</span>
              <span className="font-mono text-slate-900">
                {deliveryFee === 0 ? <span className="text-green-600 font-bold">FREE</span> : `₹${deliveryFee.toFixed(2)}`}
              </span>
            </div>
            <div className="flex justify-between text-base font-extrabold text-slate-900 pt-3 border-t border-slate-200">
              <span>Total Payable:</span>
              <span className="font-mono text-blue-900">₹{total.toFixed(2)}</span>
            </div>
          </div>

          <button
            onClick={() => onNavigate('checkout')}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-md"
          >
            Proceed to Checkout <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
