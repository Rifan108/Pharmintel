import React, { useState } from 'react';
import { HeartPulse, Lock, Mail, User, ShieldCheck, ArrowRight, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage({ onNavigate }) {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('customer');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (isRegister) {
        await register({
          email,
          password,
          full_name: fullName,
          role,
        });
      } else {
        await login(email, password);
      }
      onNavigate('dashboard');
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const fillQuickRole = (roleType) => {
    if (roleType === 'customer') {
      setEmail('patient@example.com');
      setPassword('Customer@Pass2026');
    } else if (roleType === 'pharmacist') {
      setEmail('pharmacist@apolloclinic.com');
      setPassword('Pharmacist@Apollo2026');
    } else if (roleType === 'pharm_admin') {
      setEmail('manager@medpluscare.com');
      setPassword('Manager@MedPlus2026');
    } else if (roleType === 'platform_admin') {
      setEmail('admin@pharmintel.com');
      setPassword('Admin@PharmIntel2026');
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 px-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl p-8">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-700 to-teal-500 text-white flex items-center justify-center mx-auto mb-3 shadow-md">
            <HeartPulse className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-black text-slate-900">
            {isRegister ? 'Create PharmIntel Account' : 'Welcome to PharmIntel'}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            AI-Powered Smart Pharmacy Network for Drug Safety
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-800 text-xs rounded-lg border border-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {isRegister && (
            <div>
              <label className="font-bold text-slate-700 block mb-1">Full Legal Name:</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
          )}

          <div>
            <label className="font-bold text-slate-700 block mb-1">Email Address:</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
            />
          </div>

          <div>
            <label className="font-bold text-slate-700 block mb-1">Password:</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
            />
          </div>

          {isRegister && (
            <div>
              <label className="font-bold text-slate-700 block mb-1">Account Role:</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-semibold"
              >
                <option value="customer">Customer / Patient</option>
                <option value="pharmacist">Licensed Pharmacist</option>
                <option value="pharmacy_admin">Pharmacy Administrator</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs shadow-md transition flex items-center justify-center gap-1.5"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
            {isRegister ? 'Register Account' : 'Sign In'}
          </button>
        </form>

        <div className="mt-4 text-center text-xs">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-blue-600 hover:text-blue-800 font-semibold"
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>

        {/* Quick Role Fill Buttons */}
        <div className="mt-6 pt-5 border-t border-slate-200">
          <p className="text-[11px] font-bold text-slate-700 mb-2 text-center uppercase tracking-wider">
            One-Click Verified Demo Credentials:
          </p>
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <button
              type="button"
              onClick={() => fillQuickRole('customer')}
              className="p-2 bg-slate-100 hover:bg-slate-200 rounded text-slate-800 font-semibold text-center border border-slate-300"
            >
              Patient / Customer
            </button>
            <button
              type="button"
              onClick={() => fillQuickRole('pharmacist')}
              className="p-2 bg-teal-50 hover:bg-teal-100 rounded text-teal-800 font-semibold text-center border border-teal-300"
            >
              Licensed Pharmacist
            </button>
            <button
              type="button"
              onClick={() => fillQuickRole('pharm_admin')}
              className="p-2 bg-purple-50 hover:bg-purple-100 rounded text-purple-800 font-semibold text-center border border-purple-300"
            >
              Pharmacy Admin
            </button>
            <button
              type="button"
              onClick={() => fillQuickRole('platform_admin')}
              className="p-2 bg-blue-50 hover:bg-blue-100 rounded text-blue-800 font-semibold text-center border border-blue-300"
            >
              Platform Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
