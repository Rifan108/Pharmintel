import React, { useState } from 'react';
import { X, Check, Save, Activity, AlertCircle, User } from 'lucide-react';

const CONDITIONS_LIST = [
  "Type 2 Diabetes",
  "Heart Disease",
  "High Blood Pressure",
  "Kidney Disease",
  "Liver Disease",
  "Thyroid Disorders",
  "Asthma",
  "Glaucoma",
  "Gout"
];

const ALLERGIES_LIST = [
  "Penicillin",
  "Sulfa Drugs (Sulfonamides)",
  "Aspirin / NSAIDs",
  "ACE Inhibitors",
  "Macrolide Antibiotics"
];

export default function EditProfileModal({ isOpen, onClose, currentProfile, onSave }) {
  if (!isOpen) return null;

  const [patientName, setPatientName] = useState(currentProfile?.patient_name || localStorage.getItem('pharmintel_patient_name') || '');
  const [conditions, setConditions] = useState(currentProfile?.medical_conditions || ["Type 2 Diabetes", "Heart Disease", "High Blood Pressure"]);
  const [allergies, setAllergies] = useState(currentProfile?.allergies || ["Penicillin"]);
  const [customCond, setCustomCond] = useState('');
  const [customAlg, setCustomAlg] = useState('');
  const [age, setAge] = useState(currentProfile?.age || 58);
  const [kidney, setKidney] = useState(currentProfile?.kidney_function || "Normal");
  const [liver, setLiver] = useState(currentProfile?.liver_function || "Normal");

  const toggleCondition = (c) => {
    setConditions(prev => prev.includes(c) ? prev.filter(item => item !== c) : [...prev, c]);
  };

  const addCustomCond = () => {
    if (customCond.trim() && !conditions.includes(customCond.trim())) {
      setConditions(prev => [...prev, customCond.trim()]);
      setCustomCond('');
    }
  };

  const toggleAllergy = (a) => {
    setAllergies(prev => prev.includes(a) ? prev.filter(item => item !== a) : [...prev, a]);
  };

  const addCustomAlg = () => {
    if (customAlg.trim() && !allergies.includes(customAlg.trim())) {
      setAllergies(prev => [...prev, customAlg.trim()]);
      setCustomAlg('');
    }
  };

  const handleSave = () => {
    if (patientName.trim()) {
      localStorage.setItem('pharmintel_patient_name', patientName.trim());
      window.dispatchEvent(new Event('patientNameUpdated'));
    }
    onSave({
      patient_name: patientName.trim() || undefined,
      medical_conditions: conditions,
      allergies: allergies,
      age: age ? parseInt(age, 10) : null,
      kidney_function: kidney,
      liver_function: liver
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center pb-4 border-b border-slate-100 mb-5">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-black text-[#102A56]">Edit Your Health Profile</h2>
              <p className="text-[11px] text-slate-500">Update diagnosed conditions and verified drug allergies</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-5 text-xs">
          {/* Patient Name */}
          <div>
            <label className="font-bold text-slate-800 block mb-1.5">Patient Name (Required):</label>
            <input
              type="text"
              placeholder="Enter Patient Name..."
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5] text-xs font-bold text-[#102A56]"
            />
            {!patientName && (
              <span className="text-[10px] text-amber-600 block mt-1">Patient name not provided</span>
            )}
          </div>
          {/* Medical Conditions */}
          <div>
            <label className="font-bold text-slate-800 block mb-2">Medical Conditions (Select all diagnosed):</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {CONDITIONS_LIST.map((c) => {
                const active = conditions.includes(c);
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() => toggleCondition(c)}
                    className={`px-3 py-1.5 rounded-xl border transition flex items-center gap-1.5 ${
                      active
                        ? 'bg-[#EFF6FF] border-[#2166F5] text-[#2166F5] font-bold shadow-2xs'
                        : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <span>{c}</span>
                    {active && <Check className="w-3.5 h-3.5" />}
                  </button>
                );
              })}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add other medical condition..."
                value={customCond}
                onChange={(e) => setCustomCond(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustomCond()}
                className="flex-1 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:border-[#2166F5]"
              />
              <button
                type="button"
                onClick={addCustomCond}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-700 font-bold border border-slate-200"
              >
                + Add
              </button>
            </div>
          </div>

          {/* Known Allergies */}
          <div>
            <label className="font-bold text-slate-800 block mb-2">Known Drug Allergies:</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {ALLERGIES_LIST.map((a) => {
                const active = allergies.includes(a);
                return (
                  <button
                    key={a}
                    type="button"
                    onClick={() => toggleAllergy(a)}
                    className={`px-3 py-1.5 rounded-xl border transition flex items-center gap-1.5 ${
                      active
                        ? 'bg-red-50 border-red-300 text-red-700 font-bold shadow-2xs'
                        : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    <span>{a}</span>
                    {active && <Check className="w-3.5 h-3.5 text-red-600" />}
                  </button>
                );
              })}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add other drug allergy..."
                value={customAlg}
                onChange={(e) => setCustomAlg(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustomAlg()}
                className="flex-1 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:border-red-500"
              />
              <button
                type="button"
                onClick={addCustomAlg}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-700 font-bold border border-slate-200"
              >
                + Add
              </button>
            </div>
          </div>

          {/* Age & Organ Status */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Age (Years):</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="w-full bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:border-[#2166F5]"
              />
            </div>
            <div>
              <label className="font-bold text-slate-700 block mb-1">Kidney Status:</label>
              <select
                value={kidney}
                onChange={(e) => setKidney(e.target.value)}
                className="w-full bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:border-[#2166F5]"
              >
                <option value="Normal">Normal</option>
                <option value="Mild Impairment">Mild (60-89)</option>
                <option value="Moderate Impairment">Moderate (30-59)</option>
                <option value="Severe Impairment">Severe (&lt; 30)</option>
              </select>
            </div>
            <div>
              <label className="font-bold text-slate-700 block mb-1">Liver Status:</label>
              <select
                value={liver}
                onChange={(e) => setLiver(e.target.value)}
                className="w-full bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:border-[#2166F5]"
              >
                <option value="Normal">Normal</option>
                <option value="Mild Impairment">Mild</option>
                <option value="Moderate Impairment">Moderate</option>
                <option value="Severe Impairment">Severe</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-6 mt-6 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-[#2166F5] hover:bg-blue-700 text-white transition flex items-center gap-1.5 shadow-md shadow-blue-500/20"
          >
            <Save className="w-3.5 h-3.5" /> Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
