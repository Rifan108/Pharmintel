import React, { useState, useEffect } from 'react';
import {
  Stethoscope, CheckCircle, XCircle, FileText, AlertTriangle,
  Clock, ShieldCheck, RefreshCw, Eye, User, Pill
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function PharmacistDashboard({ onNavigate }) {
  const { user } = useAuth();
  const [pendingRxs, setPendingRxs] = useState([]);
  const [selectedRx, setSelectedRx] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadPendingReviews();
  }, []);

  const loadPendingReviews = async () => {
    setLoading(true);
    try {
      const data = await api.getPendingPrescriptionReviews();
      setPendingRxs(data);
      if (data.length > 0) {
        setSelectedRx(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (status) => {
    if (!selectedRx) return;
    setActionLoading(true);
    try {
      const confirmedItems = (selectedRx.items || []).map((itm) => ({
        item_id: itm.id,
        matched_medicine_id: itm.matched_medicine_id,
        confirmed: true,
      }));

      await api.verifyPrescription(selectedRx.id, {
        status: status, // VERIFIED or REJECTED
        notes: notes || `Pharmacist verified on ${new Date().toLocaleDateString()}`,
        confirmed_items: confirmedItems,
      });

      alert(`Prescription RX-${selectedRx.id} successfully marked as ${status}`);
      setNotes('');
      loadPendingReviews();
    } catch (e) {
      alert("Verification error: " + e.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-300">
              Pharmacist Clinical Verification Desk
            </span>
            <span className="text-xs font-mono text-slate-400">
              Drugs & Cosmetics Act Compliance
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-teal-700" /> Pharmacist Audit & Review Queue
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Verify uploaded doctor prescriptions before authorizing Schedule H / Rx medicine dispensing.
          </p>
        </div>

        <button
          onClick={loadPendingReviews}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 rounded-lg border border-slate-300 shadow-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-blue-600" /> Refresh Queue
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400 text-xs">
          Loading verification queue...
        </div>
      ) : pendingRxs.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pending List Column */}
          <div className="lg:col-span-1 space-y-3">
            <h3 className="font-bold text-slate-800 text-xs uppercase tracking-wider mb-2">
              Pending Prescriptions ({pendingRxs.length})
            </h3>
            {pendingRxs.map((rx) => (
              <button
                key={rx.id}
                onClick={() => setSelectedRx(rx)}
                className={`w-full text-left p-4 rounded-xl border transition shadow-xs ${
                  selectedRx?.id === rx.id
                    ? 'bg-blue-50/80 border-blue-500 ring-2 ring-blue-100'
                    : 'bg-white border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex justify-between items-start mb-1 text-xs">
                  <span className="font-bold text-slate-900 font-mono">RX-{rx.id}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                    {(rx.confidence * 100).toFixed(0)}% OCR
                  </span>
                </div>
                <p className="text-xs font-semibold text-slate-800">{rx.customer_name}</p>
                <p className="text-[11px] text-slate-500 truncate">Dr. {rx.doctor_name || 'Practitioner'}</p>
                <p className="text-[10px] text-slate-400 mt-1">
                  Uploaded: {new Date(rx.uploaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </button>
            ))}
          </div>

          {/* Verification Workspace Details */}
          {selectedRx && (
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
              <div className="flex justify-between items-start pb-4 border-b border-slate-100">
                <div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-900 font-mono">
                    Prescription Ref: RX-{selectedRx.id}
                  </span>
                  <h2 className="text-lg font-bold text-slate-900 mt-1">
                    Patient: {selectedRx.customer_name}
                  </h2>
                  <p className="text-xs text-slate-500">
                    Prescribing Doctor: <span className="font-semibold text-slate-700">{selectedRx.doctor_name || 'Medical Practitioner'}</span>
                  </p>
                </div>

                <div className="text-right text-xs">
                  <span className="text-slate-400 block text-[10px]">OCR Confidence</span>
                  <span className="text-xl font-black font-mono text-teal-700">
                    {(selectedRx.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Raw Extracted Text */}
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
                <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px] block mb-1">
                  Extracted Raw Prescription Text:
                </span>
                <p className="text-slate-600 font-mono whitespace-pre-line text-[11px] max-h-32 overflow-y-auto">
                  {selectedRx.raw_text}
                </p>
              </div>

              {/* Posology / Medicine Items Confirmation */}
              <div>
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-2">
                  Medicines to be Dispensed ({selectedRx.items?.length || 0}):
                </h4>
                <div className="space-y-2">
                  {(selectedRx.items || []).map((itm) => (
                    <div
                      key={itm.id}
                      className="p-3 rounded-lg border border-slate-200 bg-white flex justify-between items-center text-xs"
                    >
                      <div>
                        <span className="font-bold text-slate-900">{itm.medicine_name_raw}</span>
                        <span className="text-slate-500 ml-2">({itm.strength} • {itm.frequency} • {itm.duration})</span>
                        <span className="text-slate-400 block text-[10px] mt-0.5">{itm.instructions}</span>
                      </div>
                      <span className="text-[10px] font-mono bg-green-50 text-green-700 px-2 py-0.5 rounded font-bold border border-green-200">
                        {(itm.confidence_score * 100).toFixed(0)}% Match
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pharmacist Notes Input */}
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Pharmacist Clinical Review Notes:
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter audit notes (e.g. verified with clinic, dosage instructions confirmed with patient)..."
                  rows={2}
                  className="w-full p-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button
                  onClick={() => handleVerify('REJECTED')}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg text-xs font-bold border border-red-200 transition flex items-center gap-1.5"
                >
                  <XCircle className="w-4 h-4" /> Reject Prescription
                </button>
                <button
                  onClick={() => handleVerify('VERIFIED')}
                  disabled={actionLoading}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-bold shadow-md transition flex items-center gap-1.5"
                >
                  <CheckCircle className="w-4 h-4" /> Approve & Sign Off (Authorize Dispensing)
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-16 text-slate-400 text-xs bg-white rounded-2xl border border-slate-200">
          <ShieldCheck className="w-12 h-12 text-teal-600 mx-auto mb-2 opacity-60" />
          <h3 className="font-bold text-slate-800 text-sm">All Prescriptions Reviewed!</h3>
          <p className="text-slate-400 mt-0.5">The pharmacist review queue is completely clear.</p>
        </div>
      )}
    </div>
  );
}
