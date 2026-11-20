import React, { useState } from 'react';
import {
  Settings, Bell, Globe, Shield, Lock, Eye,
  CheckCircle, Smartphone, Mail, AlertCircle, Save
} from 'lucide-react';

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [notifications, setNotifications] = useState({
    ddiAlerts: true,
    medReminders: true,
    smsAlerts: true,
    emailReports: false
  });

  const [language, setLanguage] = useState('en');
  const [twoFactor, setTwoFactor] = useState(true);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-[#102A56]">Account & Safety Settings</h1>
            <p className="text-xs text-slate-500">Configure alert thresholds, notifications, language and clinical privacy.</p>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-[#2166F5] hover:bg-blue-700 transition shadow-xs flex items-center gap-1.5"
        >
          <Save className="w-4 h-4" /> Save Preferences
        </button>
      </div>

      {saved && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center gap-2 animate-fade-in">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          Settings updated successfully.
        </div>
      )}

      {/* Safety Alerts */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Bell className="w-4 h-4 text-[#2166F5]" />
          <h2 className="text-sm font-extrabold text-[#102A56]">Drug Safety Alerts & Notifications</h2>
        </div>

        <div className="space-y-3">
          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 cursor-pointer">
            <div>
              <span className="text-xs font-bold text-[#102A56] block">High-Risk Interaction Push Alerts</span>
              <span className="text-[11px] text-slate-500">Instant notification when a contraindicated medicine is proposed.</span>
            </div>
            <input
              type="checkbox"
              checked={notifications.ddiAlerts}
              onChange={(e) => setNotifications({ ...notifications, ddiAlerts: e.target.checked })}
              className="w-4 h-4 text-[#2166F5] rounded"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 cursor-pointer">
            <div>
              <span className="text-xs font-bold text-[#102A56] block">Daily Medication Reminders</span>
              <span className="text-[11px] text-slate-500">Scheduled reminders for morning, afternoon and bedtime doses.</span>
            </div>
            <input
              type="checkbox"
              checked={notifications.medReminders}
              onChange={(e) => setNotifications({ ...notifications, medReminders: e.target.checked })}
              className="w-4 h-4 text-[#2166F5] rounded"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 cursor-pointer">
            <div>
              <span className="text-xs font-bold text-[#102A56] block">SMS Urgent Notifications</span>
              <span className="text-[11px] text-slate-500">Send critical alerts to verified phone (+91 98400 99001).</span>
            </div>
            <input
              type="checkbox"
              checked={notifications.smsAlerts}
              onChange={(e) => setNotifications({ ...notifications, smsAlerts: e.target.checked })}
              className="w-4 h-4 text-[#2166F5] rounded"
            />
          </label>
        </div>
      </div>

      {/* Language Preferences */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Globe className="w-4 h-4 text-[#2166F5]" />
          <h2 className="text-sm font-extrabold text-[#102A56]">Language & Regional Localization</h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { code: 'en', name: 'English' },
            { code: 'kn', name: 'ಕನ್ನಡ (Kannada)' },
            { code: 'hi', name: 'हिन्दी (Hindi)' },
            { code: 'ml', name: 'മലയാളം (Malayalam)' },
            { code: 'ta', name: 'தமிழ் (Tamil)' },
            { code: 'te', name: 'తెలుగు (Telugu)' },
            { code: 'mr', name: 'मराठी (Marathi)' }
          ].map((lang) => (
            <button
              key={lang.code}
              onClick={() => setLanguage(lang.code)}
              className={`p-3 rounded-xl border text-xs font-bold text-left transition ${
                language === lang.code
                  ? 'border-[#2166F5] bg-blue-50 text-[#2166F5]'
                  : 'border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              {lang.name}
            </button>
          ))}
        </div>
      </div>

      {/* Security & 2FA */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Shield className="w-4 h-4 text-[#2166F5]" />
          <h2 className="text-sm font-extrabold text-[#102A56]">Security & Clinical Privacy Compliance</h2>
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
          <div>
            <span className="text-xs font-bold text-[#102A56] block">Two-Factor Authentication (2FA)</span>
            <span className="text-[11px] text-slate-500">Protect prescription uploads and safety reports with OTP.</span>
          </div>
          <button
            onClick={() => setTwoFactor(!twoFactor)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              twoFactor ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'
            }`}
          >
            {twoFactor ? 'Enabled' : 'Disabled'}
          </button>
        </div>
      </div>
    </div>
  );
}
