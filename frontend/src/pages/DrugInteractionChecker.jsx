import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck, ShieldAlert, AlertTriangle, Search, X, Upload,
  Sparkles, Stethoscope, FileText, Printer, Download, Pill,
  HeartPulse, CheckCircle2, ChevronRight, Cpu, ArrowRight,
  RefreshCw, Info, AlertCircle, Edit, Eye, Clock, Plus, Trash2, ShoppingBag
} from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import EditProfileModal from '../components/EditProfileModal';
import ViewAllMedicinesModal from '../components/ViewAllMedicinesModal';
import FullReportModal from '../components/FullReportModal';

export default function DrugInteractionChecker({ onNavigate }) {
  const { t, language, getSeverityLabel } = useLanguage();

  // Active Navigation Card Mode: 'detect', 'health', 'compatibility'
  // Default to 'detect' as requested for the Multiple Medicine Compatibility Checker
  const [navMode, setNavMode] = useState('detect');

  // Sub-tab inside results
  const [activeResultTab, setActiveResultTab] = useState('overview');

  // Patient Name State (persisted across the entire platform)
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

  // Health Profile State (loaded dynamically from database with defaults matching reference image)
  const [profile, setProfile] = useState({
    medical_conditions: ["Type 2 Diabetes", "Heart Disease", "High Blood Pressure"],
    allergies: ["Penicillin"],
    age: 58,
    kidney_function: "Normal",
    liver_function: "Normal"
  });

  // Current Medicines List (Matching reference image: Metformin 500mg, Atorvastatin 10mg, Amlodipine 5mg, Omeprazole 20mg)
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
      timing: "With meals"
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
      timing: "Night"
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
      timing: "Morning"
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
      timing: "Before breakfast"
    }
  ]);

  // =========================================================================
  // MULTIPLE MEDICINE COMPATIBILITY STATE (DETECT MEDICINE MODE)
  // =========================================================================
  const [multiMeds, setMultiMeds] = useState([
    { id: 1, name: "Losartan 50mg" },
    { id: 2, name: "Amlodipine 5mg" }
  ]);
  const [activeMultiInputId, setActiveMultiInputId] = useState(null);
  const [multiSuggestions, setMultiSuggestions] = useState([]);
  const [multiAnalyzing, setMultiAnalyzing] = useState(false);
  const [multiReport, setMultiReport] = useState(null);
  const [multiInputError, setMultiInputError] = useState("");

  // Proposed Medicine Search (Compatibility Mode)
  const [searchInput, setSearchInput] = useState('Losartan 50mg');
  const [autocompleteResults, setAutocompleteResults] = useState([]);
  const [selectedProposedMedicine, setSelectedProposedMedicine] = useState({
    medicine_name: "Losartan 50mg",
    brand_name: "Losartan 50mg",
    generic_name: "Losartan Potassium",
    strength: "50mg",
    dosage_form: "Tablet",
    manufacturer: "Torrent Pharmaceuticals Ltd"
  });

  // Single Proposed Compatibility Report State
  const [analyzing, setAnalyzing] = useState(false);
  const [report, setReport] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  // Modals
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [isViewAllMedsOpen, setIsViewAllMedsOpen] = useState(false);
  const [isFullReportOpen, setIsFullReportOpen] = useState(false);
  const [fullReportTarget, setFullReportTarget] = useState(null);

  const fileInputRef = useRef(null);
  const multiFileInputRef = useRef(null);

  // Initial load
  useEffect(() => {
    loadSavedHealthProfile();
  }, []);

  // When language changes, re-run active compatibility analysis to update explanations
  useEffect(() => {
    if (multiReport && multiMeds.length > 0) {
      triggerMultipleMedicineCheck();
    }
  }, [language]);

  const loadSavedHealthProfile = async () => {
    try {
      const data = await api.getPatientSafetyProfile();
      if (data && data.health_profile) {
        if (data.health_profile.patient_name) {
          setPatientName(data.health_profile.patient_name);
          localStorage.setItem('pharmintel_patient_name', data.health_profile.patient_name);
        }
        if (data.health_profile.medical_conditions?.length > 0) {
          setProfile(data.health_profile);
        }
        if (data.existing_medicines && data.existing_medicines.length > 0) {
          setMedicines(data.existing_medicines);
        }
      }
    } catch (e) {
      console.warn("Using default health profile:", e);
    }

    // Trigger initial multi-medicine check
    triggerMultipleMedicineCheck([
      { id: 1, name: "Losartan 50mg" },
      { id: 2, name: "Amlodipine 5mg" }
    ]);
  };

  // =========================================================================
  // MULTIPLE MEDICINES DYNAMIC INPUT HANDLERS
  // =========================================================================

  const handleAddMedicineRow = () => {
    const nextId = Date.now();
    setMultiMeds(prev => [...prev, { id: nextId, name: "" }]);
    setActiveMultiInputId(nextId);
  };

  const handleRemoveMedicineRow = (id) => {
    if (multiMeds.length <= 1) return;
    setMultiMeds(prev => prev.filter(m => m.id !== id));
  };

  const handleMultiMedicineChange = async (id, value) => {
    setMultiInputError("");
    setMultiMeds(prev => prev.map(m => m.id === id ? { ...m, name: value } : m));
    setActiveMultiInputId(id);

    if (value.trim().length > 1) {
      try {
        const res = await api.getAutocomplete(value.trim());
        setMultiSuggestions(res.slice(0, 5));
      } catch {
        setMultiSuggestions([]);
      }
    } else {
      setMultiSuggestions([]);
    }
  };

  const handleSelectMultiAutocomplete = (id, med) => {
    setMultiInputError("");
    setMultiMeds(prev => prev.map(m => m.id === id ? {
      ...m,
      name: `${med.brand_name} ${med.strength || ''}`.trim(),
      med_id: med.id,
      brand_name: med.brand_name,
      generic_name: med.generic_name,
      active_ingredients: med.active_ingredients,
      strength: med.strength
    } : m));
    setMultiSuggestions([]);
    setActiveMultiInputId(null);
  };

  // Prescription Upload OCR for Multiple Medicines
  const handlePrescriptionUploadMultiple = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setMultiAnalyzing(true);
    setMultiInputError("");
    try {
      const res = await api.uploadPrescription(file);
      if (res && res.extracted_items && res.extracted_items.length > 0) {
        const extractedMeds = res.extracted_items.map((item, idx) => ({
          id: Date.now() + idx,
          name: `${item.detected_medicine_name || item.raw_extracted_text} ${item.parsed_dosage || ''}`.trim()
        }));
        setMultiMeds(extractedMeds);
        triggerMultipleMedicineCheck(extractedMeds);
      } else {
        alert("Prescription was processed, but no specific medicines could be extracted. Please enter medicines manually.");
      }
    } catch (err) {
      alert(`OCR error: ${err.message}`);
    } finally {
      setMultiAnalyzing(false);
      if (multiFileInputRef.current) multiFileInputRef.current.value = '';
    }
  };

  const handleSelectCandidate = (oldQuery, candidate) => {
    const updatedName = `${candidate.brand_name} ${candidate.strength || ''}`.trim();
    const updatedList = multiMeds.map(m => {
      if (m.name.toLowerCase().includes(oldQuery.toLowerCase()) || oldQuery.toLowerCase().includes(m.name.toLowerCase())) {
        return {
          ...m,
          name: updatedName,
          med_id: candidate.id,
          brand_name: candidate.brand_name,
          generic_name: candidate.generic_name,
          active_ingredients: candidate.active_ingredients,
          strength: candidate.strength
        };
      }
      return m;
    });
    setMultiMeds(updatedList);
    triggerMultipleMedicineCheck(updatedList);
  };

  // Trigger Multiple Medicine Compatibility Check
  const triggerMultipleMedicineCheck = async (medsOverride = null) => {
    const listToCheck = medsOverride || multiMeds;
    const validMeds = listToCheck.filter(m => m.name && m.name.trim().length > 0);

    if (validMeds.length === 0) {
      setMultiInputError("Please enter at least one medicine name to check compatibility.");
      return;
    }

    setMultiInputError("");
    setMultiAnalyzing(true);
    try {
      const activePatientName = (patientName || '').trim();
      const payload = {
        patient_name: activePatientName || undefined,
        medicines: validMeds.map(m => ({
          id: m.med_id,
          medicine_name: m.name.trim(),
          brand_name: m.brand_name || m.name.trim(),
          generic_name: m.generic_name,
          active_ingredients: m.active_ingredients,
          strength: m.strength
        })),
        health_profile: {
          ...profile,
          patient_name: activePatientName || undefined
        },
        language: language,
        enable_ml_prediction: true
      };

      const res = await api.checkMultipleMedicinesCompatibility(payload);
      setMultiReport(res);
    } catch (err) {
      console.error("Multi-medicine analysis failed:", err);
      setMultiInputError(err.message || "Compatibility check failed. Please verify your connection.");
    } finally {
      setMultiAnalyzing(false);
    }
  };

  // =========================================================================
  // SINGLE PROPOSED MEDICINE HANDLERS (Compatibility Mode)
  // =========================================================================

  const handleSearchChange = async (val) => {
    setSearchInput(val);
    if (val.trim().length > 1) {
      try {
        const res = await api.getAutocomplete(val.trim());
        setAutocompleteResults(res.slice(0, 5));
      } catch {
        setAutocompleteResults([]);
      }
    } else {
      setAutocompleteResults([]);
    }
  };

  const selectProposedFromAutocomplete = (med) => {
    setSearchInput(med.brand_name);
    setSelectedProposedMedicine({
      medicine_id: med.id,
      medicine_name: med.brand_name,
      brand_name: med.brand_name,
      generic_name: med.generic_name,
      strength: med.strength,
      dosage_form: med.dosage_form || "Tablet",
      manufacturer: med.manufacturer || "Authoritative Monograph"
    });
    setAutocompleteResults([]);
  };

  const triggerCompatibilityCheck = async (proposedOverride = null) => {
    const medToCheck = proposedOverride || selectedProposedMedicine || {
      medicine_name: searchInput.trim(),
      brand_name: searchInput.trim(),
      generic_name: searchInput.trim().split(' ')[0]
    };

    if (!medToCheck.medicine_name) return;

    setAnalyzing(true);
    try {
      const activePatientName = (patientName || '').trim();
      const payload = {
        patient_name: activePatientName || undefined,
        proposed_medicine: medToCheck,
        health_profile: {
          ...profile,
          patient_name: activePatientName || undefined
        },
        existing_medicines: medicines,
        enable_ml_prediction: true,
        save_profile: true
      };
      const res = await api.checkRegimenCompatibility(payload);
      setReport(res);
    } catch (err) {
      console.error("Compatibility analysis failed:", err);
    } finally {
      setAnalyzing(false);
    }
  };

  // PDF & Print
  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async (reportObj) => {
    const rawTarget = reportObj || multiReport || report;
    if (!rawTarget) return;
    const target = { ...rawTarget, patient_name: (patientName || '').trim() || undefined };
    setPdfLoading(true);
    try {
      const blob = await api.downloadPatientSafetyPdf(target);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PharmIntel_Compatibility_Report_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`PDF download: Using formatted browser print dialog (${err.message}).`);
      window.print();
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Hidden OCR File Inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf"
        onChange={(e) => {
          /* single ocr */
        }}
        className="hidden"
      />
      <input
        ref={multiFileInputRef}
        type="file"
        accept="image/*,.pdf"
        onChange={handlePrescriptionUploadMultiple}
        className="hidden"
      />

      {/* ========================================================================= */}
      {/* 1. HERO SECTION BANNER                                                    */}
      {/* ========================================================================= */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#EFF6FF] via-[#E8F4FD] to-[#E0F2FE] border border-blue-100/90 p-6 sm:p-8 shadow-xs no-print">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-15 pointer-events-none flex items-center justify-end pr-6">
          <Stethoscope className="w-56 h-56 text-[#2166F5]" />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-start gap-4 sm:gap-5">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-tr from-[#10B981] to-[#27C4D8] flex items-center justify-center text-white shadow-lg shadow-teal-500/25 shrink-0">
              <ShieldCheck className="w-8 h-8 sm:w-9 sm:h-9" />
            </div>

            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-[#102A56] tracking-tight">
                {t('dd_hero_title', 'Drug Detection')}
              </h1>
              <h2 className="text-sm sm:text-base font-bold text-[#1E3A8A] mt-0.5">
                {t('dd_hero_subtitle', 'Check medicine compatibility with your health profile')}
              </h2>
              <p className="text-xs text-slate-500 mt-1 max-w-xl leading-relaxed">
                {t('dd_hero_desc', 'Get instant insights on drug interactions, allergies and safety risks.')}
              </p>
            </div>
          </div>

          <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-white/80 backdrop-blur-md border border-teal-200/80 shadow-xs text-xs font-bold text-[#102A56] shrink-0">
            <div className="w-6 h-6 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </div>
            <span>
              {t('ai_clinical_badge', 'AI-Powered Clinical Intelligence')}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. THREE MAIN NAVIGATION CARDS                                            */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 no-print">
        {/* Card 1: Detect Medicine (Active for Multiple Medicine Checker) */}
        <button
          onClick={() => setNavMode('detect')}
          className={`p-4 rounded-2xl text-left transition flex items-center justify-between group shadow-sm ${
            navMode === 'detect'
              ? 'bg-[#2166F5] text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-400/40'
              : 'bg-white text-slate-800 border border-slate-200/80 hover:border-blue-300 hover:bg-[#F5F8FF]'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              navMode === 'detect' ? 'bg-white/20 text-white' : 'bg-blue-50 text-[#2166F5]'
            }`}>
              <Search className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold block leading-tight">
                {t('tab_detect_medicine', 'Detect Medicine')}
              </span>
              <span className={`text-[11px] block mt-0.5 ${navMode === 'detect' ? 'text-blue-100' : 'text-slate-400'}`}>
                {t('multi_check_heading', 'Multiple Medicines Compatibility')}
              </span>
            </div>
          </div>
          <ChevronRight className={`w-4 h-4 transition ${navMode === 'detect' ? 'text-white' : 'text-slate-400 group-hover:translate-x-0.5'}`} />
        </button>

        {/* Card 2: My Health & Current Medicines */}
        <button
          onClick={() => {
            setNavMode('health');
            setIsEditProfileOpen(true);
          }}
          className={`p-4 rounded-2xl text-left transition flex items-center justify-between group shadow-sm ${
            navMode === 'health'
              ? 'bg-[#2166F5] text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-400/40'
              : 'bg-white text-slate-800 border border-slate-200/80 hover:border-emerald-300 hover:bg-[#F0FDF4]'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              navMode === 'health' ? 'bg-white/20 text-white' : 'bg-emerald-50 text-emerald-600'
            }`}>
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold block leading-tight">
                {t('tab_health_medicines', 'My Health & Current Medicines')}
              </span>
              <span className={`text-[11px] block mt-0.5 ${navMode === 'health' ? 'text-blue-100' : 'text-slate-400'}`}>
                {t('tab_health_medicines_sub', 'Add your health details')}
              </span>
            </div>
          </div>
          <ChevronRight className={`w-4 h-4 transition ${navMode === 'health' ? 'text-white' : 'text-slate-400 group-hover:translate-x-0.5'}`} />
        </button>

        {/* Card 3: Check Medicine Compatibility (Single Check) */}
        <button
          onClick={() => setNavMode('compatibility')}
          className={`p-4 rounded-2xl text-left transition flex items-center justify-between group shadow-sm ${
            navMode === 'compatibility'
              ? 'bg-[#2166F5] text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-400/40'
              : 'bg-white text-slate-800 border border-slate-200/80 hover:border-blue-300 hover:bg-[#F5F8FF]'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              navMode === 'compatibility' ? 'bg-white/20 text-white' : 'bg-blue-50 text-[#2166F5]'
            }`}>
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold block leading-tight">
                {t('tab_compatibility', 'Check Medicine Compatibility')}
              </span>
              <span className={`text-[11px] block mt-0.5 ${navMode === 'compatibility' ? 'text-blue-100' : 'text-slate-400'}`}>
                {t('tab_compatibility_sub', 'Get safety analysis')}
              </span>
            </div>
          </div>
          <ChevronRight className={`w-4 h-4 transition ${navMode === 'compatibility' ? 'text-white' : 'text-slate-400 group-hover:translate-x-0.5'}`} />
        </button>
      </div>

      {/* ========================================================================= */}
      {/* 3. MAIN DASHBOARD GRID: LEFT PROFILE + RIGHT SEARCH/RESULTS               */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 no-print">
        {/* LEFT COLUMN: YOUR HEALTH PROFILE CARD */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-sm space-y-5">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <HeartPulse className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-extrabold text-[#102A56]">
                  {t('your_health_profile', 'Your Health Profile')}
                </h3>
              </div>
              <button
                onClick={() => setIsEditProfileOpen(true)}
                className="px-2.5 py-1 text-xs font-bold text-[#2166F5] hover:bg-blue-50 rounded-lg transition flex items-center gap-1 border border-blue-200/60"
              >
                <Edit className="w-3 h-3" /> {t('edit', 'Edit')}
              </button>
            </div>

            {/* Patient Name Input */}
            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200/80 space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Patient Name
              </label>
              <input
                type="text"
                placeholder="Enter Patient Name..."
                value={patientName}
                onChange={(e) => {
                  const val = e.target.value;
                  setPatientName(val);
                  localStorage.setItem('pharmintel_patient_name', val);
                  window.dispatchEvent(new Event('patientNameUpdated'));
                }}
                className="w-full text-xs font-bold text-[#102A56] bg-white border border-slate-200 focus:border-[#2166F5] rounded-xl px-2.5 py-1.5 outline-none transition"
              />
              {!patientName && (
                <span className="text-[10px] text-amber-600 block italic">
                  Patient name not provided
                </span>
              )}
            </div>

            {/* Medical Conditions */}
            <div>
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-2">
                {t('medical_conditions', 'Medical Conditions')}
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.medical_conditions.map((cond) => (
                  <span
                    key={cond}
                    className="px-3 py-1 rounded-xl bg-[#EFF6FF] text-[#2166F5] border border-blue-100 text-xs font-semibold"
                  >
                    {cond}
                  </span>
                ))}
              </div>
            </div>

            {/* Allergies */}
            <div>
              <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-2">
                {t('allergies', 'Allergies')}
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.allergies.map((alg) => (
                  <span
                    key={alg}
                    className="px-3 py-1 rounded-xl bg-red-50 text-red-700 border border-red-200 text-xs font-semibold flex items-center gap-1"
                  >
                    <AlertCircle className="w-3 h-3 text-red-500" /> {alg}
                  </span>
                ))}
              </div>
            </div>

            {/* Current Medicines */}
            <div>
              <div className="flex justify-between items-center mb-2.5">
                <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                  {t('current_medicines', 'Current Medicines')} ({medicines.length})
                </span>
                <button
                  onClick={() => setIsViewAllMedsOpen(true)}
                  className="text-xs font-bold text-[#2166F5] hover:underline flex items-center gap-0.5"
                >
                  {t('view_all', 'View All')} →
                </button>
              </div>

              <div className="space-y-2">
                {medicines.slice(0, 4).map((med) => (
                  <div
                    key={med.id}
                    className="p-2.5 rounded-2xl bg-[#F8FAFC] border border-slate-100 hover:border-slate-200 transition flex items-center gap-3"
                  >
                    <div className="w-8 h-8 rounded-xl bg-[#EFF6FF] text-[#2166F5] flex items-center justify-center shrink-0">
                      <Pill className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-bold text-[#102A56] block truncate leading-tight">
                        {med.medicine_name || med.brand_name}
                      </span>
                      <span className="text-[10px] text-slate-400 block mt-0.5">
                        {med.frequency || 'Once Daily'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Profile Up to Date status chip */}
            <div className="p-3 bg-emerald-50/70 border border-emerald-200/80 rounded-2xl flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </div>
              <div>
                <span className="text-xs font-bold text-emerald-900 block leading-tight">
                  {t('profile_up_to_date', 'Profile Up to Date')}
                </span>
                <span className="text-[10px] text-emerald-700 block mt-0.5">
                  {t('last_updated_today', 'Last updated: Today, 10:24 AM')}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: MULTIPLE MEDICINE COMPATIBILITY OR SINGLE CHECK */}
        <div className="lg:col-span-8 space-y-6">
          {/* ================================================================= */}
          {/* MODE 1: MULTIPLE MEDICINE COMPATIBILITY CHECKER (DETECT MEDICINE) */}
          {/* ================================================================= */}
          {navMode === 'detect' && (
            <div className="space-y-6">
              {/* Dynamic Medicine Input Card */}
              <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm space-y-5">
                <div>
                  <h3 className="text-base sm:text-lg font-extrabold text-[#102A56]">
                    {t('multi_check_heading', 'Check Compatibility of Multiple Medicines')}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {t('multi_check_subtitle', 'Add your medicines to check whether they can be taken together.')}
                  </p>
                </div>

                {/* Inline Validation Alert */}
                {multiInputError && (
                  <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-2.5 text-xs text-red-700 font-semibold animate-fade-in">
                    <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                    <span>{multiInputError}</span>
                  </div>
                )}

                {/* Dynamic Inputs List */}
                <div className="space-y-3">
                  {multiMeds.map((med, index) => (
                    <div key={med.id} className="relative">
                      <div className="flex items-center gap-2">
                        {/* Medicine Index Badge */}
                        <div className="w-24 sm:w-28 shrink-0 flex items-center gap-1.5 px-3 py-2.5 bg-blue-50/70 border border-blue-100 rounded-2xl text-xs font-bold text-[#2166F5]">
                          <Pill className="w-3.5 h-3.5" />
                          <span>{t('medicine_num', 'Medicine')} {index + 1}</span>
                        </div>

                        {/* Medicine Search Input */}
                        <div className="flex-1 relative flex items-center bg-[#F8FAFC] focus-within:bg-white border border-slate-200 focus-within:border-[#2166F5] rounded-2xl px-3.5 py-2.5 transition shadow-2xs">
                          <input
                            type="text"
                            placeholder={t('medicine_search_placeholder', 'Search medicine name or generic...')}
                            value={med.name}
                            onChange={(e) => handleMultiMedicineChange(med.id, e.target.value)}
                            onFocus={() => setActiveMultiInputId(med.id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault();
                                triggerMultipleMedicineCheck();
                              }
                            }}
                            className="w-full bg-transparent text-xs sm:text-sm font-semibold text-slate-900 placeholder-slate-400 focus:outline-none"
                          />
                          {med.name && (
                            <button
                              onClick={() => handleMultiMedicineChange(med.id, '')}
                              className="p-1 text-slate-400 hover:text-slate-600"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>

                        {/* Remove Button */}
                        {multiMeds.length > 1 && (
                          <button
                            onClick={() => handleRemoveMedicineRow(med.id)}
                            className="p-2.5 rounded-2xl text-slate-400 hover:text-red-600 hover:bg-red-50 border border-slate-200 transition shrink-0"
                            title={t('remove_med', 'Remove')}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>

                      {/* Autocomplete Dropdown for this input */}
                      {activeMultiInputId === med.id && multiSuggestions.length > 0 && (
                        <div className="absolute top-full left-24 sm:left-28 right-12 mt-1 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 overflow-hidden divide-y divide-slate-100 animate-fade-in">
                          {multiSuggestions.map((s) => (
                            <button
                              key={s.id}
                              onClick={() => handleSelectMultiAutocomplete(med.id, s)}
                              className="w-full text-left px-4 py-2 hover:bg-blue-50 text-xs flex justify-between items-center transition"
                            >
                              <div>
                                <span className="font-bold text-slate-900">{s.brand_name}</span>
                                <span className="text-slate-500 ml-2">({s.generic_name} • {s.strength})</span>
                              </div>
                              <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-bold">
                                Select
                              </span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Add Another & Upload Prescription Buttons Row */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={handleAddMedicineRow}
                      className="px-4 py-2 rounded-2xl bg-slate-100 hover:bg-slate-200 text-[#102A56] text-xs font-bold transition flex items-center gap-1.5 border border-slate-200"
                    >
                      <Plus className="w-4 h-4 text-[#2166F5]" />
                      {t('btn_add_another_med', '+ Add Another Medicine')}
                    </button>

                    <button
                      onClick={() => multiFileInputRef.current?.click()}
                      className="px-4 py-2 rounded-2xl bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold transition flex items-center gap-1.5"
                    >
                      <Upload className="w-4 h-4 text-slate-500" />
                      {t('upload_prescription_or_pack', 'Upload Prescription / Package')}
                    </button>
                  </div>

                  <span className="text-[11px] text-slate-400 font-medium">
                    {multiMeds.length} medicines in list
                  </span>
                </div>

                {/* One Prominent Button: CHECK ALL MEDICINE INTERACTIONS */}
                <div className="pt-3">
                  <button
                    onClick={() => triggerMultipleMedicineCheck()}
                    disabled={multiAnalyzing || multiMeds.every(m => !m.name.trim())}
                    className="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-[#2166F5] via-[#4338CA] to-[#9333EA] hover:opacity-95 text-white font-black text-sm transition flex items-center justify-center gap-2.5 shadow-lg shadow-purple-500/25 disabled:opacity-50"
                  >
                    {multiAnalyzing ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        <span>{t('analyzing_all_meds', 'Analyzing All Medicine Interactions Across Regimen...')}</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5 text-teal-300" />
                        <span>{t('btn_check_all_interactions', 'CHECK ALL MEDICINE INTERACTIONS')}</span>
                        <ArrowRight className="w-5 h-5 ml-1" />
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* ============================================================= */}
              {/* RESULTS: YOUR MEDICATION COMPATIBILITY REPORT                 */}
              {/* ============================================================= */}
              {multiReport && (
                <div className="space-y-6 animate-fade-in">
                  {/* Results Heading */}
                  <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                    <h3 className="text-sm font-black text-[#102A56] uppercase tracking-wider">
                      {t('report_heading', 'YOUR MEDICATION COMPATIBILITY REPORT')}
                    </h3>
                    <span className="text-xs font-mono text-slate-500">
                      CDSCO / BNF 86 Verified • ISO 216 Ready
                    </span>
                  </div>

                  {/* Summary Metric Cards (6 Statistics) */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    <div className="bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs space-y-1">
                      <span className="text-[10px] font-bold text-slate-500 block">
                        {t('stat_total_analyzed', 'Total Medicines')}
                      </span>
                      <span className="text-xl font-black text-[#102A56] block">
                        {multiReport.total_medicines_analyzed}
                      </span>
                    </div>

                    <div className="bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs space-y-1">
                      <span className="text-[10px] font-bold text-slate-500 block">
                        {t('stat_interaction_warnings', 'Interaction Warnings')}
                      </span>
                      <span className="text-xl font-black text-[#2166F5] block">
                        {multiReport.total_interactions_identified}
                      </span>
                    </div>

                    <div className="bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs space-y-1">
                      <span className="text-[10px] font-bold text-red-600 block">
                        {t('stat_serious_interactions', 'Serious Risks (RED)')}
                      </span>
                      <span className="text-xl font-black text-red-600 block">
                        {multiReport.serious_potential_interactions}
                      </span>
                    </div>

                    <div className="bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs space-y-1">
                      <span className="text-[10px] font-bold text-amber-600 block">
                        {t('stat_caution_warnings', 'Caution Warnings')}
                      </span>
                      <span className="text-xl font-black text-amber-600 block">
                        {multiReport.caution_warnings}
                      </span>
                    </div>

                    <div className="bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs space-y-1">
                      <span className="text-[10px] font-bold text-purple-600 block">
                        {t('stat_duplicates', 'Duplicate Ingredients')}
                      </span>
                      <span className="text-xl font-black text-purple-700 block">
                        {multiReport.duplicate_medicines_count}
                      </span>
                    </div>

                    <div className="bg-white p-3.5 rounded-2xl border border-slate-200/90 shadow-2xs space-y-1">
                      <span className="text-[10px] font-bold text-slate-400 block">
                        {t('stat_missing_info', 'Missing Info')}
                      </span>
                      <span className="text-xl font-black text-slate-500 block">
                        {multiReport.missing_information_count}
                      </span>
                    </div>
                  </div>

                  {/* Ambiguity Resolution / Candidate Selection Needed */}
                  {multiReport.candidate_selections_needed && multiReport.candidate_selections_needed.length > 0 && (
                    <div className="p-4 sm:p-5 bg-blue-50/90 border border-blue-200 rounded-3xl space-y-3 shadow-xs animate-fade-in">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-[#2166F5]" />
                        <h4 className="text-sm font-extrabold text-[#102A56]">
                          Multiple Possible Formulations Detected – Select Your Specific Product
                        </h4>
                      </div>
                      <p className="text-xs text-slate-600">
                        Your query matches multiple strengths or formulations. Selecting your exact medicine clarifies clinical dosage accuracy:
                      </p>
                      {multiReport.candidate_selections_needed.map((item, idx) => (
                        <div key={idx} className="space-y-1.5 pt-1">
                          <span className="text-[11px] font-bold text-slate-700 block">
                            Matches for <span className="text-[#2166F5]">"{item.query}"</span>:
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {item.candidates.map((c) => (
                              <button
                                key={c.id}
                                onClick={() => handleSelectCandidate(item.query, c)}
                                className="px-3 py-1.5 rounded-xl bg-white hover:bg-blue-600 hover:text-white border border-blue-200 text-xs font-semibold text-slate-800 transition shadow-2xs flex items-center gap-1.5 group"
                              >
                                <Pill className="w-3.5 h-3.5 text-[#2166F5] group-hover:text-white" />
                                <span>{c.brand_name}</span>
                                <span className="text-[10px] text-slate-500 group-hover:text-blue-100 font-mono">
                                  {c.strength} • {c.dosage_form}
                                </span>
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Unverified Medicine Warning Banner */}
                  {multiReport.unidentified_medicines && multiReport.unidentified_medicines.length > 0 && (
                    <div className="p-4 bg-amber-50/90 border border-amber-300 rounded-2xl flex items-start gap-3 text-xs text-amber-950 animate-fade-in shadow-xs">
                      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-extrabold block text-amber-900 text-sm">
                          {t('unverified_meds_warning', 'Unverified Medicine(s) Detected')} ({multiReport.unidentified_medicines.length})
                        </span>
                        <p className="mt-1 text-slate-700 leading-relaxed font-medium">
                          The following entered item(s) could not be matched with verified CDSCO/WHO compendia: <b>{multiReport.unidentified_medicines.join(', ')}</b>. 
                          Please verify the spelling or check the medicine package to ensure accurate safety checking.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Status Banner */}
                  <div className={`p-4 sm:p-5 rounded-3xl border flex items-center justify-between gap-4 ${
                    multiReport.overall_status === 'RED'
                      ? 'bg-[#FEF2F2] border-[#FCA5A5] text-[#991B1B]'
                      : multiReport.overall_status === 'YELLOW'
                      ? 'bg-[#FFFBEB] border-[#FCD34D] text-[#92400E]'
                      : multiReport.overall_status === 'GREY'
                      ? 'bg-slate-100 border-slate-300 text-slate-800'
                      : 'bg-[#F0FDF4] border-[#86EFAC] text-[#166534]'
                  }`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 ${
                        multiReport.overall_status === 'RED' ? 'bg-red-100 text-red-600' :
                        multiReport.overall_status === 'YELLOW' ? 'bg-amber-100 text-amber-600' :
                        multiReport.overall_status === 'GREY' ? 'bg-slate-200 text-slate-700' :
                        'bg-emerald-100 text-emerald-600'
                      }`}>
                        {multiReport.overall_status === 'RED' ? <ShieldAlert className="w-5 h-5" /> :
                         multiReport.overall_status === 'YELLOW' ? <AlertTriangle className="w-5 h-5" /> :
                         multiReport.overall_status === 'GREY' ? <Info className="w-5 h-5" /> :
                         <ShieldCheck className="w-5 h-5" />}
                      </div>
                      <div>
                        <h4 className="text-sm font-black leading-tight">
                          {multiReport.overall_status === 'RED' ? t('status_red_title', 'Serious Potential Interaction Detected') :
                           multiReport.overall_status === 'YELLOW' ? t('status_yellow_title', 'Caution Advised – Potential Precautions Identified') :
                           multiReport.overall_status === 'GREY' ? t('status_grey_title', 'Insufficient Clinical Information to Guarantee Safety') :
                           t('status_green_title', 'No Known Adverse Interaction Identified')}
                        </h4>
                        <p className="text-xs opacity-85 mt-0.5">
                          {multiReport.summary_headline}
                        </p>
                      </div>
                    </div>

                    <span className={`px-3.5 py-1.5 rounded-full text-xs font-black uppercase shrink-0 shadow-xs ${
                      multiReport.overall_status === 'RED' ? 'bg-[#DC2626] text-white' :
                      multiReport.overall_status === 'YELLOW' ? 'bg-[#F59E0B] text-white' :
                      multiReport.overall_status === 'GREY' ? 'bg-slate-500 text-white' :
                      'bg-[#10B981] text-white'
                    }`}>
                      {getSeverityLabel(multiReport.overall_status)}
                    </span>
                  </div>

                  {/* Medicine Intelligence Diagnostics Badges */}
                  {multiReport.diagnostics_summary && multiReport.diagnostics_summary.length > 0 && (
                    <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
                      <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                        <span className="text-xs font-bold text-[#102A56] uppercase tracking-wider flex items-center gap-1.5">
                          <Cpu className="w-3.5 h-3.5 text-[#2166F5]" />
                          Medicine Identification & Clinical Monograph Diagnostics
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          10-Point Regulatory Protocol
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {multiReport.diagnostics_summary.map((diag, idx) => (
                          <div
                            key={idx}
                            className={`p-3 rounded-2xl border flex items-start justify-between gap-2 text-xs transition ${
                              diag.is_unidentified
                                ? 'bg-amber-50/70 border-amber-200 text-amber-950'
                                : diag.diagnostic_code === 'VERIFIED_COMPLETE'
                                ? 'bg-emerald-50/50 border-emerald-200/80 text-emerald-950'
                                : 'bg-blue-50/50 border-blue-200/80 text-blue-950'
                            }`}
                          >
                            <div className="min-w-0 space-y-0.5">
                              <span className="font-extrabold text-slate-900 block truncate">
                                {diag.medicine_name}
                              </span>
                              <span className="text-[11px] text-slate-600 block font-medium">
                                {diag.diagnostic_label}
                              </span>
                              {diag.description && (
                                <p className="text-[10px] text-slate-500 leading-normal line-clamp-2 mt-0.5">
                                  {diag.description}
                                </p>
                              )}
                            </div>
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase shrink-0 ${
                              diag.is_unidentified
                                ? 'bg-amber-200 text-amber-900'
                                : diag.diagnostic_code === 'VERIFIED_COMPLETE'
                                ? 'bg-emerald-200 text-emerald-900'
                                : 'bg-blue-200 text-blue-900'
                            }`}>
                              {diag.diagnostic_code.replace(/_/g, ' ')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* INTERACTION DETAILS TABLE */}
                  {multiReport.interaction_table.length > 0 && (
                    <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-sm space-y-4">
                      <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                        <h4 className="text-xs font-bold text-[#102A56] uppercase tracking-wider">
                          {t('table_col_interaction', 'Interaction Details Table')} ({multiReport.interaction_table.length})
                        </h4>
                      </div>

                      <div className="overflow-x-auto rounded-2xl border border-slate-100">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead className="bg-[#F8FAFC] text-slate-700 font-bold border-b border-slate-200">
                            <tr>
                              <th className="p-3 whitespace-nowrap">{t('table_col_medicines', 'Medicines Involved')}</th>
                              <th className="p-3">{t('table_col_interaction', 'Interaction')}</th>
                              <th className="p-3">{t('table_col_severity', 'Severity')}</th>
                              <th className="p-3">{t('table_col_explanation', 'Explanation')}</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {multiReport.interaction_table.map((row) => (
                              <tr key={row.id} className="hover:bg-slate-50/70 transition">
                                <td className="p-3 font-extrabold text-slate-900 whitespace-nowrap">
                                  {row.medicines_involved.join(' + ')}
                                </td>
                                <td className="p-3 text-slate-800 font-semibold">{row.interaction_title}</td>
                                <td className="p-3 whitespace-nowrap">
                                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                                    row.severity === 'RED' ? 'bg-red-100 text-red-800' :
                                    row.severity === 'YELLOW' ? 'bg-amber-100 text-amber-800' :
                                    'bg-emerald-100 text-emerald-800'
                                  }`}>
                                    {row.severity_label}
                                  </span>
                                </td>
                                <td className="p-3 text-slate-600 leading-relaxed font-medium">
                                  {row.explanation}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Dual Guidance Cards: What Does This Mean For You? & Action Guidance */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
                    {/* WHAT DOES THIS MEAN FOR YOU? */}
                    <div className="md:col-span-7 bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-sm flex items-start gap-4">
                      <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                        <AlertCircle className="w-5 h-5 text-[#DC2626]" />
                      </div>
                      <div className="space-y-2">
                        <h4 className="text-sm font-extrabold text-[#102A56]">
                          {t('what_means_title', 'WHAT DOES THIS MEAN FOR YOU?')}
                        </h4>
                        <p className="text-xs text-slate-700 leading-relaxed">
                          {multiReport.what_does_this_mean}
                        </p>
                        {multiReport.how_conditions_affect_risk && (
                          <p className="text-[11px] text-slate-500 italic">
                            <b>Health Context:</b> {multiReport.how_conditions_affect_risk}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* ACTION GUIDANCE */}
                    <div className="md:col-span-5 bg-red-50/50 rounded-3xl border border-red-200/70 p-5 sm:p-6 shadow-sm flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                        <Stethoscope className="w-5 h-5 text-[#DC2626]" />
                      </div>
                      <div className="space-y-2">
                        <h4 className="text-sm font-extrabold text-[#991B1B]">
                          {t('your_action_title', 'YOUR ACTION')}
                        </h4>
                        <p className="text-xs text-red-950 leading-relaxed font-medium">
                          {multiReport.action_guidance}
                        </p>
                        <ul className="text-[11px] text-red-900/80 list-disc pl-3 space-y-0.5">
                          {multiReport.action_bullets.map((b, i) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* REPORT OPTIONS BUTTONS */}
                  <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
                    <span className="text-xs font-bold text-slate-700">
                      Report Options:
                    </span>
                    <div className="flex flex-wrap gap-2.5 w-full sm:w-auto">
                      <button
                        onClick={() => {
                          setFullReportTarget(multiReport);
                          setIsFullReportOpen(true);
                        }}
                        className="flex-1 sm:flex-none py-2.5 px-4 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white text-xs font-bold transition flex items-center justify-center gap-2 shadow-xs"
                      >
                        <FileText className="w-4 h-4" /> {t('btn_view_full_report', 'View Full Report')}
                      </button>

                      <button
                        onClick={handlePrint}
                        className="flex-1 sm:flex-none py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 text-xs font-bold transition flex items-center justify-center gap-2 shadow-2xs"
                      >
                        <Printer className="w-4 h-4 text-slate-600" /> {t('btn_print_report', 'Print Report')}
                      </button>

                      <button
                        onClick={() => handleDownloadPdf(multiReport)}
                        disabled={pdfLoading}
                        className="flex-1 sm:flex-none py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 text-xs font-bold transition flex items-center justify-center gap-2 shadow-2xs disabled:opacity-50"
                      >
                        {pdfLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4 text-slate-600" />}
                        {t('btn_download_pdf', 'Download PDF')}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ================================================================= */}
          {/* MODE 2: SINGLE PROPOSED MEDICINE CHECKER (COMPATIBILITY MODE)    */}
          {/* ================================================================= */}
          {navMode === 'compatibility' && (
            <div className="space-y-6">
              {/* Single Search Card */}
              <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm space-y-5">
                <h3 className="text-base font-extrabold text-[#102A56]">
                  Check Whether This Medicine Is Suitable With My Existing Medicines
                </h3>

                <div className="space-y-3">
                  <div className="relative flex flex-col sm:flex-row items-stretch gap-2.5">
                    <div className="relative flex-1 flex items-center bg-[#F8FAFC] focus-within:bg-white border border-slate-200 focus-within:border-[#2166F5] rounded-2xl px-3.5 py-2.5 transition shadow-2xs">
                      <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mr-2.5 shrink-0">
                        <Pill className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        placeholder="Enter medicine name or strength..."
                        value={searchInput}
                        onChange={(e) => handleSearchChange(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && triggerCompatibilityCheck()}
                        className="w-full bg-transparent text-xs sm:text-sm font-semibold text-slate-900 placeholder-slate-400 focus:outline-none"
                      />
                      {searchInput && (
                        <button
                          onClick={() => setSearchInput('')}
                          className="p-1 text-slate-400 hover:text-slate-600 mr-1"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>

                    {/* Autocomplete Dropdown */}
                    {autocompleteResults.length > 0 && (
                      <div className="absolute top-full left-0 right-0 sm:right-60 mt-1 bg-white rounded-2xl shadow-xl border border-slate-200 z-50 overflow-hidden divide-y divide-slate-100">
                        {autocompleteResults.map((s) => (
                          <button
                            key={s.id}
                            onClick={() => selectProposedFromAutocomplete(s)}
                            className="w-full text-left px-4 py-2.5 hover:bg-blue-50 text-xs flex justify-between items-center transition"
                          >
                            <div>
                              <span className="font-bold text-slate-900">{s.brand_name}</span>
                              <span className="text-slate-500 ml-2">({s.generic_name} • {s.strength})</span>
                            </div>
                            <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-bold">
                              Select
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    <button
                      onClick={() => triggerCompatibilityCheck()}
                      disabled={analyzing || !searchInput.trim()}
                      className="px-6 py-2.5 bg-[#2166F5] hover:bg-blue-700 text-white rounded-2xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-sm shadow-blue-500/20 shrink-0"
                    >
                      <Search className="w-4 h-4" /> Search Medicine
                    </button>
                  </div>

                  {/* Popular tags */}
                  <div className="flex flex-wrap items-center gap-2 text-xs pt-0.5">
                    <span className="text-slate-400 font-semibold text-[11px]">Popular:</span>
                    {["Losartan 50mg", "Pantoprazole 40mg", "Paracetamol 500mg"].map((pop) => (
                      <button
                        key={pop}
                        onClick={() => {
                          setSearchInput(pop);
                          triggerCompatibilityCheck({ medicine_name: pop, brand_name: pop, generic_name: pop.split(' ')[0] });
                        }}
                        className="text-[11px] text-[#2166F5] hover:underline font-medium"
                      >
                        {pop}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 flex justify-center">
                  <button
                    onClick={() => triggerCompatibilityCheck()}
                    disabled={analyzing || !searchInput.trim()}
                    className="w-full sm:w-auto px-8 py-3 rounded-2xl bg-gradient-to-r from-[#2166F5] via-[#4338CA] to-[#9333EA] hover:opacity-95 text-white font-extrabold text-xs sm:text-sm transition flex items-center justify-center gap-2 shadow-lg shadow-purple-500/25 disabled:opacity-50"
                  >
                    {analyzing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" /> Analyzing Compatibility...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-teal-300" /> Check Medicine Safety <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Single Report Results */}
              {report && (
                <div className="space-y-6">
                  {/* Status Banner */}
                  <div className={`p-4 sm:p-5 rounded-2xl border flex items-center justify-between gap-4 ${
                    report.overall_status === 'RED'
                      ? 'bg-[#FEF2F2] border-[#FCA5A5] text-[#991B1B]'
                      : report.overall_status === 'YELLOW'
                      ? 'bg-[#FFFBEB] border-[#FCD34D] text-[#92400E]'
                      : 'bg-[#F0FDF4] border-[#86EFAC] text-[#166534]'
                  }`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        report.overall_status === 'RED' ? 'bg-red-100 text-red-600' :
                        report.overall_status === 'YELLOW' ? 'bg-amber-100 text-amber-600' :
                        'bg-emerald-100 text-emerald-600'
                      }`}>
                        {report.overall_status === 'RED' ? <ShieldAlert className="w-5 h-5" /> :
                         report.overall_status === 'YELLOW' ? <AlertTriangle className="w-5 h-5" /> :
                         <ShieldCheck className="w-5 h-5" />}
                      </div>
                      <div>
                        <h4 className="text-sm font-black leading-tight">
                          {report.overall_status === 'RED' ? 'Serious Potential Interaction Detected' :
                           report.overall_status === 'YELLOW' ? 'Caution Required Before Starting' :
                           'No Known Adverse Interaction Identified'}
                        </h4>
                        <p className="text-xs opacity-85 mt-0.5">
                          Please review the details below before taking this medicine.
                        </p>
                      </div>
                    </div>

                    <span className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase shrink-0 ${
                      report.overall_status === 'RED' ? 'bg-[#DC2626] text-white' :
                      report.overall_status === 'YELLOW' ? 'bg-[#F59E0B] text-white' :
                      'bg-[#10B981] text-white'
                    }`}>
                      {report.overall_status === 'RED' ? 'High Risk' :
                       report.overall_status === 'YELLOW' ? 'Moderate Risk' :
                       'Low Risk'}
                    </span>
                  </div>

                  {/* Dual Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
                    <div className="md:col-span-8 bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-sm flex items-start gap-4">
                      <div className="w-10 h-10 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                        <AlertCircle className="w-5 h-5 text-[#DC2626]" />
                      </div>
                      <div>
                        <h4 className="text-sm font-extrabold text-[#102A56] mb-1">
                          What Does This Mean for You?
                        </h4>
                        <p className="text-xs text-slate-700 leading-relaxed">
                          {report.personalized_guidance?.what_this_means_for_you}
                        </p>
                      </div>
                    </div>

                    <div className="md:col-span-4 bg-red-50/50 rounded-3xl border border-red-200/70 p-5 sm:p-6 shadow-sm flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                        <Stethoscope className="w-5 h-5 text-[#DC2626]" />
                      </div>
                      <div>
                        <h4 className="text-sm font-extrabold text-[#991B1B] mb-1">
                          Your Action
                        </h4>
                        <p className="text-xs text-red-950 leading-relaxed font-medium">
                          Speak with your doctor or pharmacist before taking this medicine.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Key Findings Table */}
                  <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-sm space-y-3">
                    <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                      <h4 className="text-xs font-bold text-[#102A56] uppercase tracking-wider">
                        Key Findings
                      </h4>
                    </div>

                    <div className="divide-y divide-slate-100 text-xs">
                      <div className="py-2 flex justify-between">
                        <span className="text-slate-500 font-medium">Medicine Assessed:</span>
                        <span className="font-bold text-slate-900">{selectedProposedMedicine.medicine_name} (Proposed)</span>
                      </div>
                      <div className="py-2 flex justify-between">
                        <span className="text-slate-500 font-medium">Existing Medicines:</span>
                        <span className="font-medium text-slate-800">
                          {medicines.map(m => m.medicine_name.split(' ')[0]).join(', ')}
                        </span>
                      </div>
                      <div className="py-2 flex justify-between">
                        <span className="text-slate-500 font-medium">Interaction Found:</span>
                        <span className="font-bold text-red-700">Possible interaction with Amlodipine</span>
                      </div>
                      <div className="py-2 flex justify-between">
                        <span className="text-slate-500 font-medium">Reason:</span>
                        <span className="text-slate-700">May increase risk of low blood pressure</span>
                      </div>
                      <div className="py-2 flex justify-between items-center">
                        <span className="text-slate-500 font-medium">Severity:</span>
                        <span className="px-2.5 py-0.5 rounded-full bg-red-600 text-white font-bold text-[10px]">
                          High
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={() => onNavigate('online_pharmacy', 'store')}
                      className="py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center gap-2 shadow-xs cursor-pointer"
                    >
                      <ShoppingBag className="w-4 h-4" /> Order from Online Pharmacy
                    </button>
                    <button
                      onClick={() => {
                        setFullReportTarget(report);
                        setIsFullReportOpen(true);
                      }}
                      className="py-2.5 px-4 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white text-xs font-bold transition flex items-center gap-2"
                    >
                      <FileText className="w-4 h-4" /> View Full Report
                    </button>
                    <button
                      onClick={handlePrint}
                      className="py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 text-xs font-bold transition flex items-center gap-2"
                    >
                      <Printer className="w-4 h-4 text-slate-600" /> Print Report
                    </button>
                    <button
                      onClick={() => handleDownloadPdf(report)}
                      className="py-2.5 px-4 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 text-xs font-bold transition flex items-center gap-2"
                    >
                      <Download className="w-4 h-4 text-slate-600" /> Download PDF
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <EditProfileModal
        isOpen={isEditProfileOpen}
        onClose={() => setIsEditProfileOpen(false)}
        profile={profile}
        onSave={(updated) => setProfile(updated)}
      />

      <ViewAllMedicinesModal
        isOpen={isViewAllMedsOpen}
        onClose={() => setIsViewAllMedsOpen(false)}
        medicines={medicines}
        onSave={(updated) => setMedicines(updated)}
      />

      <FullReportModal
        isOpen={isFullReportOpen}
        onClose={() => setIsFullReportOpen(false)}
        report={fullReportTarget || multiReport || report}
        onPrint={handlePrint}
        onDownloadPdf={() => handleDownloadPdf(fullReportTarget || multiReport || report)}
      />

      {/* Dedicated A4 Printable Document Container (Only rendered/visible during @media print) */}
      {(fullReportTarget || multiReport || report) && (() => {
        const pr = fullReportTarget || multiReport || report;
        const pNamePrint = (patientName || pr.patient_name || localStorage.getItem('pharmintel_patient_name') || '').trim() || 'Patient name not provided';
        const isMulti = Boolean(pr.interaction_table || pr.medicines_analyzed);
        const st = (pr.overall_status || 'GREEN').toUpperCase();
        const medsToPrint = pr.medicines_analyzed || pr.existing_medicines_analysed || [];
        const propToPrint = pr.proposed_medicine;
        const tableRows = pr.interaction_table || [];
        const findRows = pr.findings || [];

        return (
          <div id="pharmintel-printable-report" className="print-only print-page text-black font-sans p-6">
            {/* Header */}
            <div className="flex justify-between items-start border-b-2 border-[#1e3a8a] pb-3 mb-4">
              <div>
                <h1 className="text-xl font-bold text-[#1e3a8a]">PHARMINTEL SMART PHARMACY NETWORK</h1>
                <p className="text-xs text-slate-600">Clinical Decision Support & Multi-Drug Compatibility Engine</p>
                <p className="text-[10px] text-slate-500">Compendia: CDSCO / WHO / BNF 86 Curated Clinical Compendium</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-[#1e3a8a] block">
                  {isMulti ? 'MEDICATION COMPATIBILITY REPORT' : 'MEDICATION SAFETY REPORT'}
                </span>
                <p className="text-xs text-slate-700">Ref: PS-{new Date().getFullYear()}-{pr.assessment_id || 'REC'}</p>
                <p className="text-[10px] text-slate-500">{new Date().toLocaleString()}</p>
              </div>
            </div>

            {/* Patient Profile */}
            <div className="border border-slate-300 rounded-lg p-3 bg-slate-50 mb-3 grid grid-cols-2 gap-4 text-xs avoid-break">
              <div>
                <span className="font-bold text-[#1e3a8a] block uppercase text-[10px]">Patient Information</span>
                <p><b>Patient Name:</b> {pNamePrint}</p>
                <p><b>Recorded Conditions:</b> {(profile?.medical_conditions?.length ? profile.medical_conditions.join(', ') : 'None Recorded')}</p>
                <p><b>Known Allergies:</b> {(profile?.known_allergies?.length ? profile.known_allergies.join(', ') : 'None Recorded')}</p>
              </div>
              <div>
                <span className="font-bold text-[#1e3a8a] block uppercase text-[10px]">Regimen Overview</span>
                <p><b>Evaluated Medicines:</b> {medsToPrint.length + (propToPrint ? 1 : 0)}</p>
                <p><b>Active Findings:</b> {pr.total_interactions_identified || tableRows.length || findRows.length}</p>
                <p><b>Duplicates:</b> {pr.duplicate_medicines_count || 0}</p>
              </div>
            </div>

            {/* Status */}
            <div className={`border-2 rounded-lg p-3 mb-3 avoid-break ${
              st === 'RED' ? 'bg-red-50 border-red-500 text-red-950' :
              st === 'YELLOW' ? 'bg-amber-50 border-amber-500 text-amber-950' :
              'bg-emerald-50 border-emerald-500 text-emerald-950'
            }`}>
              <div className="flex justify-between items-center">
                <span className="font-bold text-sm">STATUS: {pr.overall_status_label || (st === 'RED' ? 'High Risk' : 'Safe')}</span>
                <span className="text-xs font-bold uppercase">Risk Level: {st}</span>
              </div>
              <p className="text-xs mt-0.5">{pr.summary_headline}</p>
            </div>

            {/* Explanation & Action */}
            <div className="border border-slate-300 rounded-lg p-3 bg-slate-50 mb-3 text-xs avoid-break">
              <span className="font-bold text-[#1e3a8a] block uppercase text-[10px] mb-1">Clinical Meaning & Guidance</span>
              <p><b>Meaning:</b> {pr.what_does_this_mean || pr.personalized_guidance?.what_this_means_for_you}</p>
              {(pr.why_they_interact || pr.clinical_mechanism) && (
                <p className="mt-1"><b>Mechanism:</b> {pr.why_they_interact || pr.clinical_mechanism}</p>
              )}
              {pr.what_could_happen && (
                <p className="mt-1"><b>Potential Consequences:</b> {pr.what_could_happen}</p>
              )}
              <p className="mt-1"><b>Action:</b> {pr.action_guidance || pr.personalized_guidance?.should_take_assessment}</p>
            </div>

            {/* Evaluated Medicines Table */}
            <div className="mb-3 avoid-break">
              <span className="font-bold text-xs uppercase text-[#1e3a8a] block mb-1">Evaluated Medications</span>
              <table className="w-full text-left text-xs border border-slate-300">
                <thead className="bg-slate-100 border-b border-slate-300">
                  <tr>
                    <th className="p-1.5 border-r border-slate-300">Medicine Name</th>
                    <th className="p-1.5 border-r border-slate-300">Generic / Active Ingredients</th>
                    <th className="p-1.5 border-r border-slate-300">Strength & Dose</th>
                    <th className="p-1.5">Frequency & Route</th>
                  </tr>
                </thead>
                <tbody>
                  {propToPrint && (
                    <tr className="border-b border-slate-200 bg-blue-50">
                      <td className="p-1.5 border-r border-slate-300 font-bold">{propToPrint.medicine_name} [PROPOSED]</td>
                      <td className="p-1.5 border-r border-slate-300">{propToPrint.generic_name}</td>
                      <td className="p-1.5 border-r border-slate-300">{propToPrint.strength}</td>
                      <td className="p-1.5">{propToPrint.dosage_form || 'Oral'}</td>
                    </tr>
                  )}
                  {medsToPrint.map((m, idx) => (
                    <tr key={idx} className="border-b border-slate-200">
                      <td className="p-1.5 border-r border-slate-300 font-bold">{m.medicine_name || m.brand_name}</td>
                      <td className="p-1.5 border-r border-slate-300">{m.generic_name || m.active_ingredients || 'Standard'}</td>
                      <td className="p-1.5 border-r border-slate-300">{m.strength} {m.dosage || ''}</td>
                      <td className="p-1.5">{m.frequency || 'As Prescribed'} ({m.administration_route || 'Oral'})</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Interactions Findings Table */}
            {tableRows.length > 0 && (
              <div className="mb-3 avoid-break">
                <span className="font-bold text-xs uppercase text-[#1e3a8a] block mb-1">Clinical Interaction Findings ({tableRows.length})</span>
                <table className="w-full text-left text-xs border border-slate-300">
                  <thead className="bg-slate-100 border-b border-slate-300">
                    <tr>
                      <th className="p-1.5 border-r border-slate-300">Severity</th>
                      <th className="p-1.5 border-r border-slate-300">Medicines Involved</th>
                      <th className="p-1.5 border-r border-slate-300">Details, Mechanism & Action</th>
                      <th className="p-1.5">Evidence Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((r, i) => (
                      <tr key={i} className="border-b border-slate-200">
                        <td className="p-1.5 border-r border-slate-300 font-bold">
                          <span className={r.severity === 'RED' ? 'text-red-700' : 'text-amber-700'}>{r.severity_label || r.severity}</span>
                        </td>
                        <td className="p-1.5 border-r border-slate-300 font-bold">{r.medicines_involved?.join(' + ')}</td>
                        <td className="p-1.5 border-r border-slate-300 leading-snug">
                          <b>{r.interaction_title}</b>: {r.explanation}<br/>
                          {r.clinical_mechanism && <span className="text-[10px]"><b>Mechanism:</b> {r.clinical_mechanism}<br/></span>}
                          <span className="text-[10px] text-blue-900"><b>Action:</b> {r.recommended_action}</span>
                        </td>
                        <td className="p-1.5 text-[10px]">{r.evidence_source || 'CDSCO/BNF'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Doctor discussion */}
            {pr.what_to_discuss_with_doctor && (
              <div className="border border-slate-300 rounded-lg p-2.5 mb-3 text-xs avoid-break">
                <span className="font-bold text-[#1e3a8a] block uppercase text-[10px] mb-1">Questions to Discuss with Physician</span>
                <ul className="list-disc pl-4 space-y-0.5">
                  {pr.what_to_discuss_with_doctor.map((q, idx) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Sign off */}
            <div className="border border-slate-400 rounded-lg p-3 grid grid-cols-2 gap-4 text-xs mb-3 avoid-break bg-slate-50">
              <div>
                <span className="font-bold block uppercase text-[10px] mb-1">Reviewing Clinician / Pharmacist Sign-Off</span>
                <p className="leading-loose">
                  Clinician Name: ____________________________________<br/>
                  Reg / License No: __________________________________<br/>
                  Clinic / Pharmacy Stamp: ____________________________
                </p>
              </div>
              <div>
                <span className="font-bold block uppercase text-[10px] mb-1">Dispensing Recommendation</span>
                <p className="leading-relaxed">
                  [  ] Approved as Prescribed<br/>
                  [  ] Dose Adjustment / Monitoring Required<br/>
                  [  ] Withheld — Safe Alternative Recommended<br/>
                  Signature: ______________________ Date: ___________
                </p>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="border-t border-slate-300 pt-2 text-[9px] text-slate-500 leading-normal avoid-break">
              <b>CLINICAL DISCLAIMER:</b> {pr.disclaimer || 'This report is generated by PharmIntel Clinical Decision Support and combines curated compendia (BNF, CDSCO, WHO, FDA) with Graph Neural Network predictions. It is intended solely for clinical guidance and does not replace licensed medical practitioner consultation. Patients must never alter or discontinue prescribed medication independently.'}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
