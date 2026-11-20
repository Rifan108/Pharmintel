import React, { useState } from 'react';
import { X, Pill, Trash2, Plus, Clock, Search } from 'lucide-react';
import { api } from '../services/api';

export default function ViewAllMedicinesModal({ isOpen, onClose, medicines, onAddMedicine, onRemoveMedicine }) {
  if (!isOpen) return null;

  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  const handleSearch = async (val) => {
    setSearch(val);
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

  const handleSelect = (item) => {
    onAddMedicine({
      id: Date.now(),
      medicine_id: item.id,
      medicine_name: item.brand_name,
      brand_name: item.brand_name,
      generic_name: item.generic_name,
      active_ingredients: item.active_ingredients || item.generic_name,
      strength: item.strength,
      dosage: "1 tablet",
      frequency: "Once daily",
      administration_route: "Oral",
      timing: "After meals"
    });
    setSearch('');
    setSuggestions([]);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center pb-3 border-b border-slate-100 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center">
              <Pill className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-black text-[#102A56]">Current Medication Regimen ({medicines.length})</h2>
              <p className="text-[11px] text-slate-500">All active prescription and OTC medications you take regularly</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Add Search */}
        <div className="relative mb-4">
          <div className="flex items-center bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs focus-within:bg-white focus-within:border-[#2166F5]">
            <Search className="w-4 h-4 text-slate-400 mr-2" />
            <input
              type="text"
              placeholder="Search medicine database to add to your regimen..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full bg-transparent focus:outline-none text-xs"
            />
          </div>

          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden divide-y divide-slate-100">
              {suggestions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleSelect(s)}
                  className="w-full text-left px-3.5 py-2 hover:bg-blue-50 text-xs flex justify-between items-center"
                >
                  <div>
                    <span className="font-bold text-slate-900">{s.brand_name}</span>
                    <span className="text-slate-500 ml-2">({s.generic_name} • {s.strength})</span>
                  </div>
                  <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-bold">
                    + Add
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Medicines List Table */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 border border-slate-200 rounded-2xl">
          {medicines.map((m) => (
            <div key={m.id} className="p-3.5 flex items-center justify-between hover:bg-slate-50/70 transition">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#EFF6FF] text-[#2166F5] flex items-center justify-center shrink-0">
                  <Pill className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-900 block leading-tight">{m.medicine_name || m.brand_name}</span>
                  <span className="text-[11px] text-slate-500">{m.generic_name} • {m.strength || 'Standard'}</span>
                  <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                    <Clock className="w-3 h-3" />
                    <span>{m.dosage} • {m.frequency} ({m.timing || 'Daily'})</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onRemoveMedicine(m.id)}
                className="p-1.5 text-slate-400 hover:text-red-600 transition rounded-lg hover:bg-red-50"
                title="Remove"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 mt-3 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-[#2166F5] text-white hover:bg-blue-700 transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
