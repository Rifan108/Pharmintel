import React from 'react';
import {
  ShieldAlert, Activity, Search, Sparkles, ShoppingBag,
  FileText, Store, Pill, User, LogOut, HeartPulse, Stethoscope, QrCode
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, logout, cart } = useAuth();
  const totalCartCount = cart.reduce((sum, itm) => sum + itm.quantity, 0);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'] },
    { id: 'search', label: 'Medicine Search', icon: Search, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'] },
    { id: 'interactions', label: 'Interaction Checker', icon: ShieldAlert, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'], highlight: true },
    { id: 'qr_scanner', label: 'Medicine QR', icon: QrCode, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'], highlight: true },
    { id: 'scanner', label: 'Prescription OCR', icon: FileText, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'] },
    { id: 'assistant', label: 'AI Health Assistant', icon: Sparkles, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'] },
    { id: 'pharmacies', label: 'Pharmacies', icon: Store, roles: ['customer', 'pharmacist', 'pharmacy_admin', 'platform_admin'] },
    { id: 'ml_analytics', label: 'ML Analytics', icon: HeartPulse, roles: ['pharmacist', 'pharmacy_admin', 'platform_admin', 'customer'] },
    // Pharmacist & Admin specific tabs
    { id: 'pharmacist_dash', label: 'Pharmacist Desk', icon: Stethoscope, roles: ['pharmacist', 'pharmacy_admin', 'platform_admin'] },
    { id: 'inventory', label: 'Inventory', icon: Pill, roles: ['pharmacist', 'pharmacy_admin', 'platform_admin'] },
  ];

  const visibleItems = navItems.filter(
    (item) => !item.roles || item.roles.includes(user?.role || 'customer')
  );

  return (
    <nav className="no-print bg-white border-b border-slate-200 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('dashboard')}
              className="flex items-center gap-2.5 text-left group"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-teal-500 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition">
                <HeartPulse className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xl font-black tracking-tight text-slate-900 block leading-none">
                  Pharm<span className="text-blue-600">Intel</span>
                </span>
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest block mt-0.5">
                  AI Smart Pharmacy Network
                </span>
              </div>
            </button>
          </div>

          {/* Navigation Links */}
          <div className="hidden lg:flex items-center space-x-1">
            {visibleItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 shadow-xs border border-blue-200/60'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  } ${item.highlight ? 'text-teal-700 font-bold' : ''}`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  {item.label}
                  {item.id === 'interactions' && (
                    <span className="ml-1 px-1.5 py-0.2 bg-teal-100 text-teal-800 text-[9px] rounded-full font-bold">
                      GNN
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Right Action Icons (Cart, User, Logout) */}
          <div className="flex items-center gap-3">
            {/* Shopping Cart Button */}
            <button
              onClick={() => setActiveTab('cart')}
              className="relative p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition"
              title="Shopping Cart"
            >
              <ShoppingBag className="w-5 h-5" />
              {totalCartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center shadow-xs">
                  {totalCartCount}
                </span>
              )}
            </button>

            {/* User Profile Pill */}
            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                <button
                  onClick={() => setActiveTab('profile')}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition text-left"
                >
                  <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-800 font-bold text-xs flex items-center justify-center">
                    {user.name ? user.name[0].toUpperCase() : 'U'}
                  </div>
                  <div className="hidden sm:block">
                    <span className="block text-xs font-bold text-slate-800 leading-tight">
                      {user.name || user.email}
                    </span>
                    <span className="block text-[10px] font-medium text-teal-700 capitalize">
                      {user.role?.replace('_', ' ')}
                    </span>
                  </div>
                </button>
                <button
                  onClick={logout}
                  className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setActiveTab('login')}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
