import React, { useState, useEffect } from 'react';
import {
  HeartPulse, ShieldAlert, AlertTriangle, CheckCircle, Edit,
  Plus, Trash2, Save, Activity, User, Phone, MapPin, Droplets,
  Calendar, FileText, ChevronRight
} from 'lucide-react';
import { api } from '../services/api';

export default function HealthProfilePage({ onNavigate }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const [profile, setProfile] = useState({
    patient_name: localStorage.getItem('pharmintel_patient_name') || '',
    medical_conditions: ["Type 2 Diabetes", "Heart Disease", "High Blood Pressure"],
    allergies: ["Penicillin"],
    age: 58,
    gender: "Female",
    blood_group: "B+",
    weight_kg: 64,
    height_cm: 162,
    kidney_function: "Normal",
    liver_function: "Normal",
    primary_physician: "Not Assigned",
    emergency_contact: "Not Provided"
  });

  const [newCondition, setNewCondition] = useState('');
  const [newAllergy, setNewAllergy] = useState('');

  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await api.getPatientSafetyProfile();
        if (res && res.health_profile) {
          const loadedName = res.health_profile.patient_name || localStorage.getItem('pharmintel_patient_name') || '';
          setProfile(prev => ({
            ...prev,
            ...res.health_profile,
            patient_name: loadedName
          }));
          if (loadedName) {
            localStorage.setItem('pharmintel_patient_name', loadedName);
          }
        }
      } catch (err) {
        console.warn("Using default profile:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  const handleAddCondition = () => {
    if (newCondition.trim() && !profile.medical_conditions.includes(newCondition.trim())) {
      setProfile({
        ...profile,
        medical_conditions: [...profile.medical_conditions, newCondition.trim()]
      });
      setNewCondition('');
    }
  };

  const handleRemoveCondition = (cond) => {
    setProfile({
      ...profile,
      medical_conditions: profile.medical_conditions.filter(c => c !== cond)
    });
  };

  const handleAddAllergy = () => {
    if (newAllergy.trim() && !profile.allergies.includes(newAllergy.trim())) {
      setProfile({
        ...profile,
        allergies: [...profile.allergies, newAllergy.trim()]
      });
      setNewAllergy('');
    }
  };

  const handleRemoveAllergy = (alg) => {
    setProfile({
      ...profile,
      allergies: profile.allergies.filter(a => a !== alg)
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const cleanName = profile.patient_name ? profile.patient_name.trim() : '';
      if (cleanName) {
        localStorage.setItem('pharmintel_patient_name', cleanName);
        window.dispatchEvent(new Event('patientNameUpdated'));
      }
      await api.savePatientSafetyProfile({
        patient_name: cleanName || null,
        health_profile: {
          patient_name: cleanName || null,
          medical_conditions: profile.medical_conditions,
          allergies: profile.allergies,
          age: profile.age,
          kidney_function: profile.kidney_function,
          liver_function: profile.liver_function
        },
        existing_medicines: []
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      console.error("Save error:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#2166F5] to-[#27C4D8] text-white flex items-center justify-center font-black text-xl shadow-sm uppercase shrink-0">
            {profile.patient_name ? profile.patient_name.trim().slice(0, 2) : <User className="w-8 h-8" />}
          </div>
          <div className="space-y-1.5 flex-1 max-w-md">
            <div className="flex items-center gap-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Patient Name:</label>
              {!profile.patient_name && (
                <span className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full font-medium">
                  Patient name not provided
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Enter Patient Name..."
                value={profile.patient_name}
                onChange={(e) => {
                  const val = e.target.value;
                  setProfile(prev => ({ ...prev, patient_name: val }));
                  localStorage.setItem('pharmintel_patient_name', val);
                  window.dispatchEvent(new Event('patientNameUpdated'));
                }}
                className="w-full text-base font-extrabold text-[#102A56] bg-slate-50 hover:bg-white focus:bg-white border border-slate-200 focus:border-[#2166F5] rounded-xl px-3 py-1.5 transition outline-none"
              />
            </div>
            <p className="text-xs text-slate-500">
              {profile.age} Yrs • {profile.gender} • Blood Group: <span className="font-bold text-[#102A56]">{profile.blood_group}</span> • Clinical Health Profile
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('drug_detection')}
            className="px-4 py-2 rounded-xl text-xs font-bold text-[#2166F5] bg-blue-50 hover:bg-blue-100 transition border border-blue-200/60"
          >
            Check Compatibility →
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-[#2166F5] hover:bg-blue-700 transition shadow-xs flex items-center gap-1.5"
          >
            {saving ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> : <Save className="w-4 h-4" />}
            Save Changes
          </button>
        </div>
      </div>

      {savedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center gap-2 animate-fade-in">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          Health Profile updated successfully in PHARMINTEL Clinical Intelligence records.
        </div>
      )}

      {/* Grid: Conditions & Allergies | Clinical Vitals & Organ Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1: Medical Conditions */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#2166F5] flex items-center justify-center">
                <HeartPulse className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-extrabold text-[#102A56]">Diagnosed Medical Conditions</h2>
            </div>
            <span className="text-[11px] font-bold text-slate-400">
              {profile.medical_conditions.length} Active
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {profile.medical_conditions.map((cond) => (
              <span
                key={cond}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 text-[#2166F5] text-xs font-bold border border-blue-200/70 shadow-2xs"
              >
                {cond}
                <button
                  onClick={() => handleRemoveCondition(cond)}
                  className="hover:text-red-600 ml-1"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="text"
              placeholder="Add condition (e.g. Asthma, Thyroid, Chronic Kidney Disease)..."
              value={newCondition}
              onChange={(e) => setNewCondition(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddCondition()}
              className="flex-1 px-3.5 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5]"
            />
            <button
              onClick={handleAddCondition}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-[#102A56] text-xs font-bold transition flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" /> Add
            </button>
          </div>
        </div>

        {/* Card 2: Documented Allergies */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-extrabold text-[#102A56]">Known Drug & Substance Allergies</h2>
            </div>
            <span className="text-[11px] font-bold text-slate-400">
              {profile.allergies.length} Flagged
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {profile.allergies.map((alg) => (
              <span
                key={alg}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-50 text-rose-700 text-xs font-bold border border-rose-200 shadow-2xs"
              >
                {alg}
                <button
                  onClick={() => handleRemoveAllergy(alg)}
                  className="hover:text-red-800 ml-1"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="text"
              placeholder="Add allergy (e.g. Sulfa, NSAIDs, Aspirin)..."
              value={newAllergy}
              onChange={(e) => setNewAllergy(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddAllergy()}
              className="flex-1 px-3.5 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-400"
            />
            <button
              onClick={handleAddAllergy}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-[#102A56] text-xs font-bold transition flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" /> Add
            </button>
          </div>
        </div>

        {/* Card 3: Organ Function & Safety Parameters */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-extrabold text-[#102A56]">Organ Function & Clearance</h2>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Renal / Kidney Function</label>
              <select
                value={profile.kidney_function}
                onChange={(e) => setProfile({ ...profile, kidney_function: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white font-medium focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5]"
              >
                <option value="Normal">Normal (eGFR &gt; 90 mL/min)</option>
                <option value="Mild Impairment">Mild Impairment (eGFR 60-89)</option>
                <option value="Moderate Impairment">Moderate Impairment (eGFR 30-59)</option>
                <option value="Severe Impairment">Severe Impairment (eGFR &lt; 30)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1.5">Hepatic / Liver Function</label>
              <select
                value={profile.liver_function}
                onChange={(e) => setProfile({ ...profile, liver_function: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white font-medium focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5]"
              >
                <option value="Normal">Normal (Child-Pugh Class A)</option>
                <option value="Moderate Impairment">Moderate (Child-Pugh Class B)</option>
                <option value="Severe Impairment">Severe (Child-Pugh Class C)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Card 4: Clinical Care Team & Emergency Info */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Phone className="w-4 h-4" />
            </div>
            <h2 className="text-sm font-extrabold text-[#102A56]">Care Team & Emergency Contact</h2>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Primary Attending Physician</span>
              <p className="text-xs font-bold text-[#102A56] mt-0.5">{profile.primary_physician}</p>
            </div>
            <div>
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Designated Emergency Contact</span>
              <p className="text-xs font-bold text-[#102A56] mt-0.5">{profile.emergency_contact}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
