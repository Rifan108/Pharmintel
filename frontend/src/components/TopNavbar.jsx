import React, { useState, useEffect, useRef } from 'react';
import {
  Search, Bell, User, ChevronDown, LogOut, CheckCircle,
  AlertTriangle, ShieldAlert, Sparkles, X, HeartPulse, Stethoscope,
  Globe
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';

export default function TopNavbar({ onNavigate }) {
  const { user, logout } = useAuth();
  const { language, setLanguage, supportedLanguages, currentLanguageMeta, t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const langRef = useRef(null);
  const [notifications] = useState([
    {
      id: 1,
      title: "Medication Reminder",
      message: "Time to take Metformin 500mg with dinner.",
      time: "10m ago",
      type: "reminder",
      unread: true
    },
    {
      id: 2,
      title: "Interaction Safety Alert",
      message: "Potential interaction flagged between Losartan & Amlodipine.",
      time: "1h ago",
      type: "alert",
      unread: true
    }
  ]);

  const searchRef = useRef(null);
  const notifRef = useRef(null);
  const profileRef = useRef(null);

  // Global search autocomplete
  useEffect(() => {
    const handleSearch = async () => {
      if (searchQuery.trim().length > 1) {
        try {
          const res = await api.getAutocomplete(searchQuery.trim());
          setSuggestions(res.slice(0, 5));
        } catch {
          setSuggestions([]);
        }
      } else {
        setSuggestions([]);
      }
    };
    const timer = setTimeout(handleSearch, 200);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setSuggestions([]);
      }
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setShowProfileMenu(false);
      }
      if (langRef.current && !langRef.current.contains(event.target)) {
        setShowLangMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Keyboard shortcut listener (⌘K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const inputEl = document.getElementById('global-search-input');
        if (inputEl) inputEl.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSelectMed = (med) => {
    setSearchQuery('');
    setSuggestions([]);
    if (onNavigate) {
      onNavigate('drug_detection');
    }
  };

  const [patientName, setPatientName] = useState(() => localStorage.getItem('pharmintel_patient_name') || '');

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

  const displayName = patientName || user?.name || "Patient name not provided";
  const displayId = user?.id ? `PI-${String(user.id).padStart(4, '0')}` : "ID Not Assigned";

  return (
    <header className="no-print sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between gap-4 shadow-xs">
      {/* LEFT: PHARMINTEL BRAND & LOGO */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={() => onNavigate && onNavigate('home')}
          className="flex items-center gap-2.5 text-left group"
        >
          {/* Medical Cross Icon (Cyan & Blue gradient) */}
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#2166F5] to-[#27C4D8] flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition">
            <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
              <path d="M10.5 4.5a1.5 1.5 0 0 1 3 0v4.5h4.5a1.5 1.5 0 0 1 0 3H13.5v4.5a1.5 1.5 0 0 1-3 0V12H6a1.5 1.5 0 0 1 0-3h4.5V4.5z" />
            </svg>
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-[#102A56] block leading-none">
              PHARM<span className="text-[#2166F5]">INTEL</span>
            </span>
            <span className="text-[10px] font-semibold text-slate-500 tracking-wider block mt-0.5">
              Smart Medicine. Safer You.
            </span>
          </div>
        </button>
      </div>

      {/* CENTRE: GLOBAL SEARCH BAR */}
      <div ref={searchRef} className="hidden md:flex flex-1 max-w-xl relative">
        <div className="w-full relative flex items-center bg-[#F5F8FF] hover:bg-[#EFF6FF] focus-within:bg-white border border-slate-200 focus-within:border-[#2166F5] rounded-xl px-3 py-2 transition shadow-inner">
          <Search className="w-4 h-4 text-slate-400 mr-2 shrink-0" />
          <input
            id="global-search-input"
            type="text"
            placeholder="Search medicines, conditions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-transparent text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="p-1 text-slate-400 hover:text-slate-600 mr-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <kbd className="hidden lg:inline-flex items-center gap-0.5 px-2 py-0.5 text-[10px] font-mono font-bold text-slate-400 bg-white border border-slate-200 rounded shadow-2xs">
            ⌘ K
          </kbd>
        </div>

        {/* Global Autocomplete Dropdown */}
        {suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 overflow-hidden divide-y divide-slate-100">
            <div className="px-3 py-2 bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Medicines Found in CDSCO Registry
            </div>
            {suggestions.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSelectMed(s)}
                className="w-full text-left px-4 py-2.5 hover:bg-blue-50/70 text-xs flex justify-between items-center transition"
              >
                <div>
                  <span className="font-bold text-slate-900">{s.brand_name}</span>
                  <span className="text-slate-500 ml-2">({s.generic_name} • {s.strength})</span>
                </div>
                <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold">
                  Test Compatibility
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT: LANGUAGE SELECTOR, NOTIFICATIONS & USER PROFILE */}
      <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
        {/* Language Selector Dropdown */}
        <div ref={langRef} className="relative">
          <button
            onClick={() => setShowLangMenu(!showLangMenu)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-blue-50 hover:text-[#2166F5] border border-slate-200/80 transition text-xs font-bold text-slate-700 shadow-2xs"
            title="Change Platform Language"
          >
            <Globe className="w-4 h-4 text-[#2166F5]" />
            <span className="hidden sm:inline font-semibold">{currentLanguageMeta.nativeName}</span>
            <span className="sm:hidden font-semibold">{currentLanguageMeta.code.toUpperCase()}</span>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${showLangMenu ? 'rotate-180' : ''}`} />
          </button>

          {showLangMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 overflow-hidden divide-y divide-slate-100 animate-fade-in">
              <div className="px-3.5 py-2.5 bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
                <span>Select Language</span>
                <span className="text-[#2166F5] font-mono">7 Supported</span>
              </div>
              <div className="py-1">
                {supportedLanguages.map((lang) => {
                  const isSelected = language === lang.code;
                  return (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setLanguage(lang.code);
                        setShowLangMenu(false);
                      }}
                      className={`w-full px-4 py-2.5 text-left text-xs flex items-center justify-between transition ${
                        isSelected
                          ? 'bg-[#EFF6FF] text-[#2166F5] font-bold'
                          : 'text-slate-700 hover:bg-slate-50 font-medium'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-sm">{lang.flag}</span>
                        <div>
                          <span className="block font-bold leading-tight">{lang.nativeName}</span>
                          <span className="text-[10px] text-slate-400 block">{lang.name}</span>
                        </div>
                      </div>
                      {isSelected && (
                        <CheckCircle className="w-4 h-4 text-[#2166F5]" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Notifications Icon with Badge */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200/80 flex items-center justify-center text-slate-600 transition relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-600 ring-2 ring-white"></span>
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 overflow-hidden">
              <div className="p-3 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                <span className="text-xs font-bold text-slate-900">Notifications</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">2 New</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto text-xs">
                {notifications.map((n) => (
                  <div key={n.id} className="p-3 hover:bg-slate-50 transition flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-blue-50 text-[#2166F5] flex items-center justify-center shrink-0 mt-0.5">
                      {n.type === 'alert' ? <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> : <Sparkles className="w-3.5 h-3.5" />}
                    </div>
                    <div className="flex-1">
                      <span className="font-bold text-slate-900 block leading-tight">{n.title}</span>
                      <p className="text-[11px] text-slate-600 mt-0.5 leading-snug">{n.message}</p>
                      <span className="text-[9px] text-slate-400 block mt-1">{n.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill */}
        <div ref={profileRef} className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2.5 p-1.5 pl-2 hover:bg-slate-100 rounded-xl transition text-left"
          >
            {/* Avatar image */}
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-amber-200 to-blue-200 border border-slate-200 flex items-center justify-center overflow-hidden shrink-0 shadow-xs">
              <img
                src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=120&h=120&q=80"
                alt="Profile"
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
              <User className="w-5 h-5 text-slate-600" />
            </div>

            <div className="hidden sm:block">
              <span className="text-xs font-bold text-[#102A56] block leading-none">
                {displayName}
              </span>
              <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
                {displayId}
              </span>
            </div>

            <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 p-2 text-xs">
              <div className="px-3 py-2 border-b border-slate-100 mb-1">
                <span className="font-bold text-slate-900 block">{displayName}</span>
                <span className="text-[10px] text-slate-400 font-mono">{user?.email || 'No email registered'}</span>
              </div>
              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  onNavigate && onNavigate('health_profile');
                }}
                className="w-full text-left px-3 py-2 hover:bg-blue-50 text-slate-700 rounded-lg transition"
              >
                My Health Profile
              </button>
              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  onNavigate && onNavigate('settings');
                }}
                className="w-full text-left px-3 py-2 hover:bg-blue-50 text-slate-700 rounded-lg transition"
              >
                Settings & Preferences
              </button>
              <div className="border-t border-slate-100 my-1"></div>
              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  logout();
                  onNavigate && onNavigate('home');
                }}
                className="w-full text-left px-3 py-2 hover:bg-red-50 text-red-600 rounded-lg font-semibold transition flex items-center gap-1.5"
              >
                <LogOut className="w-3.5 h-3.5" /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
