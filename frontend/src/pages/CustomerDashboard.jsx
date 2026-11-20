import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, Activity, Search, FileText, Sparkles, Store,
  Pill, ArrowRight, CheckCircle, Clock, AlertTriangle, TrendingUp,
  QrCode, HeartPulse, ShieldCheck, User
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function CustomerDashboard({ onNavigate }) {
  const { user } = useAuth();
  const [patientName, setPatientName] = useState(() => localStorage.getItem('pharmintel_patient_name') || '');
  const [analytics, setAnalytics] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [quickSearch, setQuickSearch] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const handleStorage = () => {
      setPatientName(localStorage.getItem('pharmintel_patient_name') || '');
    };
    window.addEventListener('storage', handleStorage);
    window.addEventListener('patientNameUpdated', handleStorage);
    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('patientNameUpdated', handleStorage);
    };
  }, []);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.getAnalyticsDashboard();
        setAnalytics(data);
      } catch (e) {
        console.error(e);
      }
      try {
        const orders = await api.getMyOrders();
        setRecentOrders(orders.slice(0, 3));
      } catch (e) {
        // User may not be logged in
      }
    }
    loadData();
  }, []);

  const handleSearchChange = async (val) => {
    setQuickSearch(val);
    if (val.trim().length > 1) {
      try {
        const res = await api.getAutocomplete(val);
        setSuggestions(res.slice(0, 5));
      } catch {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Welcome & Safety Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#102A56] via-[#1A3D7C] to-[#2166F5] text-white p-6 sm:p-8 shadow-sm">
        {/* Decorative background glow */}
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-[#27C4D8]/20 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md text-cyan-200 text-xs font-bold px-3 py-1 rounded-full border border-white/20 mb-3 shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></span>
            Dual-Layer Safety Active: Curated Rules + PHARMINTEL-HYBRIDGNN
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            Welcome to PharmIntel{patientName ? `, ${patientName}` : ''}
          </h1>

          <div className="flex items-center gap-2 mb-4 bg-white/15 backdrop-blur-md rounded-xl p-2 max-w-md border border-white/20">
            <User className="w-4 h-4 text-cyan-200 shrink-0" />
            <input
              type="text"
              placeholder="Enter Patient Name..."
              value={patientName}
              onChange={(e) => {
                const val = e.target.value;
                setPatientName(val);
                localStorage.setItem('pharmintel_patient_name', val);
                window.dispatchEvent(new Event('patientNameUpdated'));
              }}
              className="bg-transparent text-xs text-white placeholder-blue-200 focus:outline-none w-full"
            />
            {patientName ? (
              <span className="text-[10px] bg-emerald-500/30 text-emerald-200 border border-emerald-400/30 px-2 py-0.5 rounded-md font-bold whitespace-nowrap">
                Active Patient
              </span>
            ) : (
              <span className="text-[10px] text-amber-200 font-medium whitespace-nowrap">
                Patient name not provided
              </span>
            )}
          </div>
          <p className="text-blue-100 text-xs sm:text-sm leading-relaxed mb-6">
            Intelligent medication safety intelligence, patient-specific drug-drug interaction detection,
            multilingual AI health consultation, and verified prescription delivery.
          </p>

          {/* Quick Search Bar */}
          <div className="relative">
            <div className="relative flex items-center bg-white rounded-xl shadow-lg p-1.5 border border-white/30 text-slate-800">
              <Search className="w-5 h-5 text-slate-400 ml-3" />
              <input
                type="text"
                placeholder="Search medicines by Brand, Generic Name, or Therapeutic Category..."
                value={quickSearch}
                onChange={(e) => handleSearchChange(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && onNavigate('drug_detection')}
                className="w-full bg-transparent px-3 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
              />
              <button
                onClick={() => onNavigate('drug_detection')}
                className="bg-[#2166F5] hover:bg-blue-700 text-white px-5 py-2 rounded-lg text-xs font-bold transition shadow-xs"
              >
                Search
              </button>
            </div>

            {/* Quick Suggestions Dropdown */}
            {suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-2xl border border-slate-200 z-50 overflow-hidden divide-y divide-slate-100 text-slate-800">
                {suggestions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => onNavigate('drug_detection')}
                    className="w-full text-left px-4 py-3 hover:bg-blue-50/60 flex items-center justify-between text-xs transition"
                  >
                    <div>
                      <span className="font-bold text-slate-900 text-xs sm:text-sm">{s.brand_name}</span>
                      <span className="text-slate-500 ml-2">({s.generic_name} • {s.strength})</span>
                    </div>
                    <span className="font-mono font-bold text-[#2166F5]">₹{s.base_mrp.toFixed(2)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Primary Action Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          onClick={() => onNavigate('drug_detection')}
          className="bg-white p-5 rounded-2xl border border-slate-200/90 hover:border-[#2166F5] hover:shadow-md transition text-left group shadow-xs"
        >
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center mb-3 group-hover:bg-[#2166F5] group-hover:text-white transition">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <h3 className="font-extrabold text-[#102A56] text-sm mb-1 flex items-center justify-between">
            Drug Detection
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition" />
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Multi-drug safety analysis, whole-regimen compatibility & allergy contraindications.
          </p>
        </button>

        <button
          onClick={() => onNavigate('medicine_qr')}
          className="bg-white p-5 rounded-2xl border border-slate-200/90 hover:border-emerald-500 hover:shadow-md transition text-left group shadow-xs"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:bg-emerald-600 group-hover:text-white transition">
            <QrCode className="w-5 h-5" />
          </div>
          <h3 className="font-extrabold text-[#102A56] text-sm mb-1 flex items-center justify-between">
            Medicine QR Info
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition" />
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Scan packaging for CDSCO-verified batch, expiry, composition & authenticity data.
          </p>
        </button>

        <button
          onClick={() => onNavigate('ai_assistant')}
          className="bg-white p-5 rounded-2xl border border-slate-200/90 hover:border-purple-500 hover:shadow-md transition text-left group shadow-xs"
        >
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-3 group-hover:bg-purple-600 group-hover:text-white transition">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="font-extrabold text-[#102A56] text-sm mb-1 flex items-center justify-between">
            AI Voice Assistant
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition" />
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Voice & text consultation in Kannada, Hindi, Malayalam, Tamil, Telugu, Marathi & English.
          </p>
        </button>

        <button
          onClick={() => onNavigate('health_insights')}
          className="bg-white p-5 rounded-2xl border border-slate-200/90 hover:border-cyan-500 hover:shadow-md transition text-left group shadow-xs"
        >
          <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center mb-3 group-hover:bg-cyan-600 group-hover:text-white transition">
            <TrendingUp className="w-4 h-4" />
          </div>
          <h3 className="font-extrabold text-[#102A56] text-sm mb-1 flex items-center justify-between">
            Health Insights
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition" />
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            30-day compliance tracking, risk distributions, and biometric telemetry.
          </p>
        </button>
      </div>

      {/* Network Health Stats & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network Metrics */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs lg:col-span-1 space-y-4">
          <h3 className="text-sm font-extrabold text-[#102A56] flex items-center gap-2 pb-2 border-b border-slate-100">
            <ShieldCheck className="w-4 h-4 text-[#2166F5]" /> Clinical Intelligence Architecture
          </h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Verified Medicine Compendia</span>
              <span className="font-bold text-[#102A56] font-mono">{analytics?.overview?.verified_medicines || 21} Monographed</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Deterministic Rules (Layer 1)</span>
              <span className="font-bold text-emerald-700 font-mono">11 Curated</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Network Licensed Pharmacies</span>
              <span className="font-bold text-[#102A56] font-mono">{analytics?.overview?.active_pharmacies || 3} Active</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-100">
              <span className="text-slate-500 font-medium">Research Model Version</span>
              <span className="font-bold text-purple-700 font-mono">HYBRIDGNN v1.0.0-PROD</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-slate-500 font-medium">Printing Engine Standard</span>
              <span className="font-bold text-[#2166F5] font-mono">ISO 216 A4 (ReportLab)</span>
            </div>
          </div>
        </div>

        {/* Current Regimen Summary */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-slate-100">
            <h3 className="text-sm font-extrabold text-[#102A56] flex items-center gap-2">
              <Pill className="w-4 h-4 text-[#2166F5]" /> Active Medication Regimen {patientName ? `(${patientName})` : '(Patient name not provided)'}
            </h3>
            <button
              onClick={() => onNavigate('my_medicines')}
              className="text-xs font-bold text-[#2166F5] hover:text-blue-700 flex items-center gap-1"
            >
              Manage Regimen <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-extrabold text-[#102A56] block">Metformin 500mg</span>
              <span className="text-[11px] text-slate-500">Twice Daily • With meals (Diabetes)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-extrabold text-[#102A56] block">Atorvastatin 10mg</span>
              <span className="text-[11px] text-slate-500">Once Daily • Night (Cardioprotection)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-extrabold text-[#102A56] block">Amlodipine 5mg</span>
              <span className="text-[11px] text-slate-500">Once Daily • Morning (Hypertension)</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-extrabold text-[#102A56] block">Omeprazole 20mg</span>
              <span className="text-[11px] text-slate-500">Once Daily • Before breakfast</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
