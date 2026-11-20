import React, { useState, useEffect } from 'react';
import { Search, Filter, Pill, ShieldAlert, ShoppingBag, Eye, RefreshCw, Check } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function MedicineSearch({ onNavigate }) {
  const { addToCart } = useAuth();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [dosageForm, setDosageForm] = useState('');
  const [categories, setCategories] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [addedId, setAddedId] = useState(null);

  useEffect(() => {
    loadCategories();
    performSearch();
  }, [category, dosageForm]);

  const loadCategories = async () => {
    try {
      const cats = await api.getCategories();
      setCategories(cats);
    } catch (e) {
      console.error(e);
    }
  };

  const performSearch = async () => {
    setLoading(true);
    try {
      const res = await api.searchMedicines({
        q: query,
        category: category || undefined,
        dosage_form: dosageForm || undefined,
        limit: 50,
      });
      setMedicines(res.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = (med) => {
    addToCart(med, 1, 1);
    setAddedId(med.id);
    setTimeout(() => setAddedId(null), 1500);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-black text-slate-900">Centralized Medicine Database</h1>
        <p className="text-xs text-slate-500 mt-1">
          Search verified pharmaceutical monographs, approved indications, active ingredients, and comparative pricing.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs mb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Text Search */}
          <div className="md:col-span-2 relative flex items-center">
            <Search className="w-4 h-4 text-slate-400 absolute left-3" />
            <input
              type="text"
              placeholder="Search by brand, generic, active ingredient..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && performSearch()}
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:bg-white focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          {/* Category Dropdown */}
          <div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full py-2 px-3 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="">All Therapeutic Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Dosage Form Dropdown */}
          <div className="flex gap-2">
            <select
              value={dosageForm}
              onChange={(e) => setDosageForm(e.target.value)}
              className="w-full py-2 px-3 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="">All Dosage Forms</option>
              <option value="Tablet">Tablet</option>
              <option value="Capsule">Capsule</option>
              <option value="Syrup">Syrup</option>
              <option value="Injection">Injection</option>
            </select>
            <button
              onClick={performSearch}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-xs"
            >
              <Search className="w-3.5 h-3.5" /> Filter
            </button>
          </div>
        </div>
      </div>

      {/* Results Grid */}
      {loading ? (
        <div className="text-center py-16 text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-500" />
          <p className="text-xs">Searching verified pharmacology compendia...</p>
        </div>
      ) : medicines.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {medicines.map((med) => (
            <div
              key={med.id}
              className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 shadow-xs hover:shadow-md transition p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    {med.therapeutic_category}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    med.requires_prescription
                      ? 'bg-amber-50 text-amber-800 border border-amber-200'
                      : 'bg-green-50 text-green-800 border border-green-200'
                  }`}>
                    {med.prescription_classification}
                  </span>
                </div>

                <h3 className="font-extrabold text-base text-slate-900 leading-tight">
                  {med.brand_name}
                </h3>
                <p className="text-xs font-semibold text-teal-800 mt-0.5">
                  {med.generic_name} • {med.strength}
                </p>
                <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                  {med.composition}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Manufacturer: <span className="text-slate-600 font-medium">{med.manufacturer}</span>
                </p>
              </div>

              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Maximum Retail Price</span>
                  <span className="text-lg font-black text-slate-900 font-mono">₹{med.base_mrp.toFixed(2)}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => onNavigate('alternatives', med.id)}
                    className="p-2 text-slate-500 hover:text-teal-700 hover:bg-teal-50 rounded-lg border border-slate-200 transition"
                    title="Find Generic / Branded Alternatives"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onNavigate('details', med.id)}
                    className="p-2 text-slate-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg border border-slate-200 transition"
                    title="View Full Monograph Details"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleAddToCart(med)}
                    className={`px-3 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                      addedId === med.id
                        ? 'bg-green-600 text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white shadow-xs'
                    }`}
                  >
                    {addedId === med.id ? (
                      <>
                        <Check className="w-3.5 h-3.5" /> Added
                      </>
                    ) : (
                      <>
                        <ShoppingBag className="w-3.5 h-3.5" /> Add
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
          <Pill className="w-10 h-10 mx-auto mb-2 opacity-30 text-slate-600" />
          No medicines matching your criteria were found.
        </div>
      )}
    </div>
  );
}
