import React, { useState, useEffect } from 'react';
import {
  RefreshCw, ArrowLeft, Pill, AlertTriangle, ShieldCheck,
  Check, ShoppingBag, TrendingDown, TrendingUp
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function MedicineAlternatives({ medicineId, onNavigate }) {
  const { addToCart } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [allMedicines, setAllMedicines] = useState([]);
  const [selectedId, setSelectedId] = useState(medicineId || 1);
  const [addedId, setAddedId] = useState(null);

  useEffect(() => {
    async function init() {
      try {
        const medList = await api.searchMedicines({ limit: 50 });
        setAllMedicines(medList.items || []);
      } catch (e) {
        console.error(e);
      }
    }
    init();
  }, []);

  useEffect(() => {
    async function loadAlt() {
      if (!selectedId) return;
      setLoading(true);
      try {
        const res = await api.getAlternatives(selectedId);
        setData(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadAlt();
  }, [selectedId]);

  const handleAdd = (alt) => {
    addToCart(alt, 1, 1);
    setAddedId(alt.id);
    setTimeout(() => setAddedId(null), 1500);
  };

  const target = data?.target_medicine;
  const alternatives = data?.alternatives || [];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <RefreshCw className="w-6 h-6 text-teal-600" /> Medicine Alternatives & Substitution Engine
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Compare exact bioequivalent generics, same-ingredient branded alternatives, and therapeutic class options.
          </p>
        </div>

        {/* Medicine Selector Dropdown */}
        <div className="flex items-center gap-2 text-xs">
          <span className="font-semibold text-slate-600">Select Target Drug:</span>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(Number(e.target.value))}
            className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-bold text-slate-900 focus:outline-none focus:border-teal-500 shadow-xs"
          >
            {allMedicines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.brand_name} ({m.generic_name} • {m.strength})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Clinical Substitution Safety Protocol Banner */}
      <div className="bg-teal-50 border-l-4 border-teal-600 p-4 rounded-r-xl mb-6 text-xs text-teal-950">
        <div className="flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">PHARMACEUTICAL SUBSTITUTION CODE:</span>
            <span>
              Generic equivalents share identical active pharmaceutical ingredients, strength, and dosage form.
              Substitutions are never automated; they must be verified by a registered pharmacist upon customer consent.
            </span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400 text-xs">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-teal-600" />
          Analyzing bioequivalence and therapeutic category index...
        </div>
      ) : target ? (
        <div className="space-y-6">
          {/* Target Reference Card */}
          <div className="bg-white p-6 rounded-2xl border-2 border-blue-900/40 shadow-sm">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-900 uppercase tracking-wider">
              Currently Selected Reference Drug
            </span>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mt-2">
              <div>
                <h2 className="text-xl font-black text-slate-900">{target.brand_name}</h2>
                <p className="text-xs font-semibold text-teal-700 mt-0.5">
                  {target.generic_name} • {target.strength} • {target.dosage_form}
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Manufacturer: {target.manufacturer} • Class: {target.category}
                </p>
              </div>

              <div className="text-right">
                <span className="text-[10px] text-slate-400 block">Reference MRP</span>
                <span className="text-xl font-black font-mono text-slate-900">₹{target.base_mrp.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Alternatives List */}
          <div className="space-y-4">
            <h3 className="font-extrabold text-slate-900 text-sm">
              Available Alternatives & Generic Matches ({alternatives.length}):
            </h3>

            {alternatives.length > 0 ? (
              alternatives.map((alt) => {
                const isCheaper = alt.price_difference < 0;
                return (
                  <div
                    key={alt.id}
                    className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
                  >
                    <div className="max-w-2xl">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          alt.alternative_type === 'EXACT_GENERIC'
                            ? 'bg-green-100 text-green-800 border border-green-300'
                            : alt.alternative_type === 'BRANDED_EQUIVALENT'
                            ? 'bg-blue-100 text-blue-800 border border-blue-300'
                            : 'bg-purple-100 text-purple-800 border border-purple-300'
                        }`}>
                          {alt.alternative_type.replace('_', ' ')}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400">
                          {alt.medicine_code}
                        </span>
                      </div>

                      <h4 className="text-base font-extrabold text-slate-900">{alt.brand_name}</h4>
                      <p className="text-xs font-semibold text-slate-700 mt-0.5">
                        {alt.generic_name} • {alt.strength} • {alt.dosage_form}
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Manufacturer: <span className="font-medium text-slate-700">{alt.manufacturer}</span>
                      </p>
                      <p className="text-[11px] text-slate-600 mt-1.5 leading-relaxed bg-slate-50 p-2 rounded border border-slate-100">
                        {alt.reason}
                      </p>
                    </div>

                    <div className="text-right shrink-0 w-full md:w-auto flex md:flex-col justify-between items-center md:items-end border-t md:border-t-0 pt-3 md:pt-0">
                      <div>
                        <span className="text-[10px] text-slate-400 block">Alternative Price</span>
                        <span className="text-lg font-black font-mono text-slate-900">
                          ₹{alt.base_mrp.toFixed(2)}
                        </span>
                        <span className={`block text-[11px] font-bold flex items-center justify-end gap-1 ${
                          isCheaper ? 'text-green-600' : 'text-slate-500'
                        }`}>
                          {isCheaper ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                          {isCheaper ? `Saves ₹${Math.abs(alt.price_difference).toFixed(2)}` : `+₹${alt.price_difference.toFixed(2)}`}
                        </span>
                      </div>

                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => onNavigate('details', alt.id)}
                          className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg border border-slate-200 font-semibold"
                        >
                          Details
                        </button>
                        <button
                          onClick={() => handleAdd(alt)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-xs ${
                            addedId === alt.id ? 'bg-green-600 text-white' : 'bg-teal-600 hover:bg-teal-700 text-white'
                          }`}
                        >
                          {addedId === alt.id ? <Check className="w-3.5 h-3.5" /> : <ShoppingBag className="w-3.5 h-3.5" />}
                          {addedId === alt.id ? 'Added' : 'Substitute'}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12 text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
                No direct bioequivalent alternatives currently recorded for this specific chemical entity.
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
