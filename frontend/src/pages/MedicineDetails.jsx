import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, Pill, ShieldCheck, AlertTriangle, RefreshCw,
  ShoppingBag, Check, Building2, Bookmark, Info
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function MedicineDetails({ medicineId, onNavigate }) {
  const { addToCart } = useAuth();
  const [medicine, setMedicine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    async function loadDetails() {
      if (!medicineId) return;
      try {
        const data = await api.getMedicineDetails(medicineId);
        setMedicine(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadDetails();
  }, [medicineId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-600" />
        <p className="text-xs">Loading verified pharmacological monograph...</p>
      </div>
    );
  }

  if (!medicine) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center text-slate-500">
        Medicine record not found.
      </div>
    );
  }

  const handleAdd = () => {
    addToCart(medicine, 1, 1);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => onNavigate('search')}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Search
      </button>

      {/* Main Medicine Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-md p-6 sm:p-8 mb-6">
        <div className="flex flex-col sm:flex-row justify-between items-start gap-4 pb-6 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                {medicine.therapeutic_category}
              </span>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded ${
                medicine.requires_prescription
                  ? 'bg-amber-50 text-amber-800 border border-amber-200'
                  : 'bg-green-50 text-green-800 border border-green-200'
              }`}>
                {medicine.prescription_classification}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Code: {medicine.medicine_code}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 leading-tight">
              {medicine.brand_name}
            </h1>
            <p className="text-sm font-bold text-teal-700 mt-1">
              Generic: {medicine.generic_name} ({medicine.strength})
            </p>
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5" /> Manufacturer: <span className="text-slate-700 font-semibold">{medicine.manufacturer}</span>
            </p>
          </div>

          <div className="text-right sm:text-right w-full sm:w-auto bg-slate-50 sm:bg-transparent p-4 sm:p-0 rounded-xl">
            <span className="text-xs text-slate-400 block">Maximum Retail Price (MRP)</span>
            <span className="text-2xl font-black text-slate-900 font-mono">₹{medicine.base_mrp.toFixed(2)}</span>
            <div className="mt-3 flex sm:justify-end gap-2">
              <button
                onClick={() => onNavigate('alternatives', medicine.id)}
                className="px-3 py-2 text-xs font-bold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg border border-teal-200 transition"
              >
                Find Alternatives
              </button>
              <button
                onClick={handleAdd}
                className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow-sm ${
                  added ? 'bg-green-600 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {added ? <Check className="w-4 h-4" /> : <ShoppingBag className="w-4 h-4" />}
                {added ? 'Added to Cart' : 'Add to Cart'}
              </button>
            </div>
          </div>
        </div>

        {/* Detailed Clinical Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 text-xs leading-relaxed">
          {/* Formulation & Ingredients */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-1.5 text-blue-900">
              <Pill className="w-4 h-4 text-blue-600" /> Formulation & Composition
            </h3>
            <p className="text-slate-700 mb-2"><b>Composition:</b> {medicine.composition}</p>
            <p className="text-slate-700 mb-2"><b>Active Ingredients:</b> {medicine.active_ingredients}</p>
            <p className="text-slate-700 mb-2"><b>Dosage Form:</b> {medicine.dosage_form}</p>
            <p className="text-slate-700"><b>Drug Classification:</b> {medicine.drug_classification || 'Standard Small Molecule'}</p>
          </div>

          {/* Approved Indications */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-1.5 text-teal-900">
              <Bookmark className="w-4 h-4 text-teal-600" /> Approved Clinical Indications
            </h3>
            <p className="text-slate-700 leading-relaxed">{medicine.approved_indications}</p>
          </div>

          {/* Contraindications */}
          <div className="bg-red-50/60 p-4 rounded-xl border border-red-200">
            <h3 className="font-bold text-red-900 text-sm mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-red-600" /> Contraindications & Black-Box Warnings
            </h3>
            <p className="text-red-900/90 leading-relaxed">{medicine.contraindications}</p>
          </div>

          {/* Known Adverse Effects */}
          <div className="bg-amber-50/60 p-4 rounded-xl border border-amber-200">
            <h3 className="font-bold text-amber-900 text-sm mb-2 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-amber-600" /> Known Adverse Reactions
            </h3>
            <p className="text-amber-900/90 leading-relaxed">{medicine.known_adverse_effects}</p>
          </div>

          {/* Storage Information */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 md:col-span-2">
            <h3 className="font-bold text-slate-900 text-sm mb-1 text-slate-800">
              Storage Instructions & Cold Chain Requirements
            </h3>
            <p className="text-slate-600">{medicine.storage_information}</p>
          </div>
        </div>

        {/* Provenance & Audit Footer */}
        <div className="mt-8 pt-4 border-t border-slate-200 flex flex-wrap justify-between items-center text-[10px] text-slate-400 gap-2">
          <span>Source: {medicine.source}</span>
          <span>Last Clinical Verification Date: {medicine.last_verified_date}</span>
          <span>DrugBank ID: {medicine.drugbank_id || 'N/A'} | PubChem CID: {medicine.pubchem_cid || 'N/A'}</span>
        </div>
      </div>
    </div>
  );
}
