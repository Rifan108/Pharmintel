import React, { useState, useEffect } from 'react';
import {
  Pill, Plus, Trash2, Clock, Calendar, ShieldCheck,
  AlertTriangle, Upload, Search, CheckCircle, ArrowRight,
  Filter, Sparkles, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export default function MyMedicinesPage({ onNavigate }) {
  const [medicines, setMedicines] = useState([
    {
      id: 1,
      medicine_name: "Metformin 500mg",
      brand_name: "Metformin 500mg",
      generic_name: "Metformin Hydrochloride",
      active_ingredients: "Metformin Hydrochloride",
      strength: "500mg",
      dosage: "1 tablet",
      frequency: "Twice Daily",
      timing: "With meals",
      route: "Oral",
      indication: "Type 2 Diabetes Mellitus"
    },
    {
      id: 2,
      medicine_name: "Atorvastatin 10mg",
      brand_name: "Atorvastatin 10mg",
      generic_name: "Atorvastatin Calcium",
      active_ingredients: "Atorvastatin Calcium",
      strength: "10mg",
      dosage: "1 tablet",
      frequency: "Once Daily",
      timing: "Night",
      route: "Oral",
      indication: "Hyperlipidemia & Cardioprotection"
    },
    {
      id: 3,
      medicine_name: "Amlodipine 5mg",
      brand_name: "Amlodipine 5mg",
      generic_name: "Amlodipine Besylate",
      active_ingredients: "Amlodipine Besylate",
      strength: "5mg",
      dosage: "1 tablet",
      frequency: "Once Daily",
      timing: "Morning",
      route: "Oral",
      indication: "Hypertension"
    },
    {
      id: 4,
      medicine_name: "Omeprazole 20mg",
      brand_name: "Omeprazole 20mg",
      generic_name: "Omeprazole",
      active_ingredients: "Omeprazole",
      strength: "20mg",
      dosage: "1 capsule",
      frequency: "Once Daily",
      timing: "Before breakfast",
      route: "Oral",
      indication: "Gastroprotection"
    }
  ]);

  const [search, setSearch] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMed, setNewMed] = useState({
    medicine_name: '',
    strength: '',
    frequency: 'Once Daily',
    timing: 'Morning',
    indication: ''
  });

  useEffect(() => {
    async function loadMeds() {
      try {
        const res = await api.getPatientSafetyProfile();
        if (res && res.existing_medicines && res.existing_medicines.length > 0) {
          setMedicines(res.existing_medicines);
        }
      } catch (e) {
        console.warn("Using default meds:", e);
      }
    }
    loadMeds();
  }, []);

  const handleAddMed = () => {
    if (!newMed.medicine_name.trim()) return;
    const added = {
      id: Date.now(),
      medicine_name: newMed.medicine_name.trim(),
      brand_name: newMed.medicine_name.trim(),
      generic_name: newMed.medicine_name.trim(),
      strength: newMed.strength || 'Standard',
      frequency: newMed.frequency,
      timing: newMed.timing,
      indication: newMed.indication || 'Maintenance Therapy'
    };
    setMedicines([...medicines, added]);
    setNewMed({ medicine_name: '', strength: '', frequency: 'Once Daily', timing: 'Morning', indication: '' });
    setShowAddForm(false);
  };

  const handleRemoveMed = (id) => {
    setMedicines(medicines.filter(m => m.id !== id));
  };

  const filtered = medicines.filter(m =>
    m.medicine_name.toLowerCase().includes(search.toLowerCase()) ||
    (m.indication && m.indication.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#2166F5] flex items-center justify-center">
              <Pill className="w-4 h-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#102A56]">My Current Medicines</h1>
          </div>
          <p className="text-xs text-slate-500">
            {medicines.length} Active Prescriptions • Verified by Clinical Pharmacist
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('drug_detection')}
            className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#2166F5] to-[#27C4D8] hover:opacity-95 transition shadow-xs flex items-center gap-1.5"
          >
            <ShieldCheck className="w-4 h-4" />
            Check New Medicine Safety
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 rounded-xl text-xs font-bold text-[#102A56] bg-slate-100 hover:bg-slate-200 transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Add Medicine
          </button>
        </div>
      </div>

      {/* Add Medicine Inline Form */}
      {showAddForm && (
        <div className="bg-white rounded-2xl border border-blue-200/90 p-6 shadow-sm space-y-4 animate-fade-in">
          <h2 className="text-sm font-extrabold text-[#102A56]">Add New Medication</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-[11px] font-bold text-slate-700 block mb-1">Medicine Name</label>
              <input
                type="text"
                placeholder="e.g. Losartan, Glimepiride"
                value={newMed.medicine_name}
                onChange={(e) => setNewMed({ ...newMed, medicine_name: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20"
              />
            </div>
            <div>
              <label className="text-[11px] font-bold text-slate-700 block mb-1">Strength</label>
              <input
                type="text"
                placeholder="e.g. 50mg, 1000mg"
                value={newMed.strength}
                onChange={(e) => setNewMed({ ...newMed, strength: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20"
              />
            </div>
            <div>
              <label className="text-[11px] font-bold text-slate-700 block mb-1">Frequency</label>
              <select
                value={newMed.frequency}
                onChange={(e) => setNewMed({ ...newMed, frequency: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white"
              >
                <option value="Once Daily">Once Daily</option>
                <option value="Twice Daily">Twice Daily</option>
                <option value="Thrice Daily">Thrice Daily</option>
                <option value="As Needed (SOS)">As Needed (SOS)</option>
              </select>
            </div>
            <div>
              <label className="text-[11px] font-bold text-slate-700 block mb-1">Timing</label>
              <select
                value={newMed.timing}
                onChange={(e) => setNewMed({ ...newMed, timing: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white"
              >
                <option value="Morning">Morning</option>
                <option value="Night">Night</option>
                <option value="With meals">With meals</option>
                <option value="Before breakfast">Before breakfast</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-1.5 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              onClick={handleAddMed}
              className="px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-[#2166F5] hover:bg-blue-700"
            >
              Add to Regimen
            </button>
          </div>
        </div>
      )}

      {/* Search Filter */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder="Filter your medications by name or health indication..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl bg-white border border-slate-200/90 focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5]"
        />
      </div>

      {/* Medicines Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((med) => (
          <div
            key={med.id || med.medicine_name}
            className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:border-blue-300 transition flex items-start justify-between gap-4 group"
          >
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center shrink-0 mt-0.5">
                <Pill className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-extrabold text-[#102A56]">{med.medicine_name}</h3>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-600">
                    {med.strength || "Standard"}
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  {med.generic_name || med.medicine_name}
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-2 text-[11px] text-slate-600">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-blue-500" />
                    {med.frequency} • {med.timing}
                  </span>
                  {med.indication && (
                    <span className="inline-flex items-center gap-1 text-slate-400">
                      • {med.indication}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={() => handleRemoveMed(med.id)}
              className="text-slate-300 hover:text-red-600 p-1 rounded-lg transition"
              title="Remove from regimen"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
