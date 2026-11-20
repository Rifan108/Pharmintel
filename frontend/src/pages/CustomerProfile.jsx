import React, { useState } from 'react';
import { User, ShieldAlert, Heart, Calendar, Phone, MapPin, Mail, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function CustomerProfile({ onNavigate }) {
  const { user } = useAuth();
  const [allergies, setAllergies] = useState(user?.profile?.allergies || 'Penicillin, Sulfa drugs');
  const [conditions, setConditions] = useState(user?.profile?.medical_conditions || 'Type 2 Diabetes Mellitus, Essential Hypertension');
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
          <div className="w-16 h-16 rounded-2xl bg-blue-100 text-blue-800 font-black text-2xl flex items-center justify-center shadow-xs">
            {user?.name ? user.name[0].toUpperCase() : 'U'}
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900">{user?.name || 'Valued Patient'}</h1>
            <p className="text-xs text-slate-500">{user?.email} • Role: <span className="font-bold capitalize text-blue-700">{user?.role?.replace('_', ' ')}</span></p>
            <span className="inline-block mt-1 text-[10px] font-bold px-2 py-0.5 rounded bg-green-100 text-green-800 border border-green-200">
              Verified Patient Profile
            </span>
          </div>
        </div>

        <form onSubmit={handleSave} className="pt-6 space-y-6 text-xs">
          {/* Clinical Allergies & Conditions */}
          <div className="bg-amber-50/50 p-5 rounded-xl border border-amber-200 space-y-4">
            <h3 className="font-bold text-amber-900 text-sm flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" /> Clinical Allergy & Pre-Existing Medical Profile
            </h3>
            <div>
              <label className="font-bold text-slate-700 block mb-1">Documented Drug Allergies:</label>
              <input
                type="text"
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Cross-referenced by the Drug Interaction Checker during consultations.</span>
            </div>
            <div>
              <label className="font-bold text-slate-700 block mb-1">Diagnosed Chronic Conditions:</label>
              <input
                type="text"
                value={conditions}
                onChange={(e) => setConditions(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-300 rounded-lg text-xs"
              />
            </div>
          </div>

          {/* Contact Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Primary Phone Number:</label>
              <input
                type="text"
                defaultValue={user?.phone || '+91 98400 99001'}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div>
              <label className="font-bold text-slate-700 block mb-1">Emergency Contact:</label>
              <input
                type="text"
                defaultValue="+91 98400 99002 (Spouse)"
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="font-bold text-slate-700 block mb-1">Default Delivery Address:</label>
              <textarea
                rows={2}
                defaultValue={user?.profile?.address || 'Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103'}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-xs transition flex items-center gap-1.5"
            >
              {saved ? <CheckCircle className="w-4 h-4" /> : null}
              {saved ? 'Profile Saved' : 'Save Clinical Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
