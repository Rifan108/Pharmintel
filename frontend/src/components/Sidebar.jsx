import React from 'react';
import {
  Home, ShieldAlert, HeartPulse, Pill, FileText,
  TrendingUp, Sparkles, Settings, HelpCircle,
  QrCode, ShieldCheck, ArrowRight, MessageSquare,
  ChevronRight, Stethoscope, MapPin, ShoppingBag
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function Sidebar({ activeTab, onNavigate, onOpenLiveChat }) {
  const { t } = useLanguage();

  const navItems = [
    { id: 'home', labelKey: 'nav_home', defaultLabel: 'Home', icon: Home },
    { id: 'drug_detection', labelKey: 'nav_drug_detection', defaultLabel: 'Drug Detection', icon: ShieldAlert, highlight: true },
    { id: 'online_pharmacy', labelKey: 'nav_online_pharmacy', defaultLabel: 'Online Pharmacy', icon: ShoppingBag },
    { id: 'nearby_pharmacies', labelKey: 'nav_nearby_pharmacies', defaultLabel: 'Nearby Medical Shops', icon: MapPin },
    { id: 'health_profile', labelKey: 'nav_health_profile', defaultLabel: 'My Health Profile', icon: HeartPulse },
    { id: 'my_medicines', labelKey: 'nav_my_medicines', defaultLabel: 'My Medicines', icon: Pill },
    { id: 'safety_reports', labelKey: 'nav_safety_reports', defaultLabel: 'Safety Reports', icon: FileText },
    { id: 'health_insights', labelKey: 'nav_health_insights', defaultLabel: 'Health Insights', icon: TrendingUp },
    { id: 'ai_assistant', labelKey: 'nav_ai_assistant', defaultLabel: 'AI Assistant', icon: Sparkles },
    { id: 'medicine_qr', labelKey: 'nav_medicine_qr', defaultLabel: 'Medicine QR', icon: QrCode },
    { id: 'settings', labelKey: 'nav_settings', defaultLabel: 'Settings', icon: Settings },
    { id: 'help_support', labelKey: 'nav_help_support', defaultLabel: 'Help & Support', icon: HelpCircle },
  ];

  return (
    <aside className="no-print w-64 bg-white border-r border-slate-200/80 shrink-0 min-h-[calc(100vh-4.5rem)] p-4 flex flex-col justify-between select-none">
      {/* Navigation Links */}
      <div className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          const label = t(item.labelKey, item.defaultLabel);
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition group ${
                isActive
                  ? 'bg-[#EFF6FF] text-[#2166F5] font-bold shadow-2xs border border-blue-200/60'
                  : 'text-slate-600 hover:text-[#102A56] hover:bg-[#F5F8FF]'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition ${
                    isActive ? 'text-[#2166F5]' : 'text-slate-400 group-hover:text-[#2166F5]'
                  }`}
                />
                <span>{label}</span>
              </div>
              {isActive && (
                <div className="w-1.5 h-4 bg-[#2166F5] rounded-full"></div>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Cards: Promo Card + Live Support */}
      <div className="pt-4 space-y-3">
        {/* Promotional Card: "Your Health. Our Priority." */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#EFF6FF] via-[#F0FDF4] to-[#F5F8FF] border border-blue-100/80 p-4 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-[#10B981]/15 text-[#10B981] flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <span className="text-xs font-extrabold text-[#102A56] leading-tight">
              {t('your_health_priority', 'Your Health. Our Priority.')}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 leading-snug mb-3">
            {t('trusted_millions', 'Trusted by millions for safer medication.')}
          </p>
          <button
            onClick={() => onNavigate('help_support')}
            className="w-full py-1.5 px-3 rounded-lg bg-[#2166F5] hover:bg-blue-700 text-white text-[11px] font-bold transition flex items-center justify-center gap-1 shadow-xs"
          >
            {t('learn_more', 'Learn More')} <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Live Support block */}
        <div
          onClick={onOpenLiveChat}
          className="p-3 bg-[#F8FAFC] hover:bg-[#F1F5F9] rounded-2xl border border-slate-200/80 transition cursor-pointer flex items-center gap-3 group"
        >
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-slate-200 overflow-hidden border border-slate-300">
              <img
                src="https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=120&h=120&q=80"
                alt="Pharmacist"
                className="w-full h-full object-cover"
              />
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1">
              <span className="text-xs font-bold text-slate-900 block leading-tight">
                {t('live_support', 'Live Support')}
              </span>
            </div>
            <span className="text-[10px] text-slate-500 block truncate group-hover:text-[#2166F5] transition">
              {t('chat_with_pharmacist', 'Chat with our pharmacist')}
            </span>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition" />
        </div>
      </div>
    </aside>
  );
}
