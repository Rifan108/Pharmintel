import React, { useState } from 'react';
import {
  UploadCloud, FileText, CheckCircle, AlertTriangle, RefreshCw,
  Clock, ShieldCheck, ArrowRight, Eye, Check
} from 'lucide-react';
import { api } from '../services/api';

export default function PrescriptionScanner({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setError(null);
      if (selected.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(selected));
      } else {
        setPreviewUrl(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadPrescription(file);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Prescription upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Title */}
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900">
          Prescription Scanner & Clinical OCR
        </h1>
        <p className="text-xs text-slate-500 mt-1 max-w-3xl">
          Automated OpenCV document preprocessing, text extraction, and dosage instruction parsing.
          Prescription orders require review and signoff by a licensed pharmacist before dispensing.
        </p>
      </div>

      {/* Mandatory Statutory Notice */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl mb-6 text-xs text-amber-900">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">PRESCRIPTION DISPENSING STATUTORY PROTOCOL:</span>
            <span>
              Handwritten prescriptions can be visually ambiguous. Extracted medicines are presented for manual
              verification and require confirmation by an appropriately qualified registered pharmacist prior to fulfillment.
            </span>
          </div>
        </div>
      </div>

      {/* Upload Box */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm mb-8">
        <div className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-8 text-center transition bg-slate-50/50">
          <UploadCloud className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800 mb-1">
            Upload Doctor Prescription (JPG, PNG, or PDF)
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Supports multi-page clinical notes and electronic hospital discharge summaries up to 10MB
          </p>

          <input
            type="file"
            id="rx-upload-input"
            accept=".jpg,.jpeg,.png,.pdf"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="flex justify-center gap-3">
            <label
              htmlFor="rx-upload-input"
              className="px-5 py-2.5 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 cursor-pointer shadow-xs transition"
            >
              Browse Files
            </label>

            {file && (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-md transition flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Processing OCR...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" /> Start OCR Extraction
                  </>
                )}
              </button>
            )}
          </div>

          {file && (
            <p className="text-xs font-mono text-blue-700 mt-3 font-semibold">
              Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-800 text-xs rounded-lg border border-red-200">
            {error}
          </div>
        )}
      </div>

      {/* Extracted Results Section */}
      {result && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4 pb-4 border-b border-slate-200 mb-6">
            <div>
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                OCR Status: {result.verification_status}
              </span>
              <h2 className="text-xl font-black text-slate-900 mt-2">
                Structured Prescription Extraction Preview
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Prescription ID: <span className="font-mono font-bold">RX-{result.prescription_id}</span> •
                Doctor: <span className="text-slate-800 font-semibold">{result.doctor_name || 'Medical Practitioner'}</span> •
                Date: {result.prescription_date || 'N/A'}
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-400 block">Overall Extraction Confidence</span>
              <span className="text-2xl font-black font-mono text-teal-700">
                {(result.overall_confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Side-by-Side: Original Upload & Extracted Table */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Original Preview */}
            <div className="lg:col-span-1 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-blue-600" /> Original Prescription Document
              </h3>
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Prescription preview"
                  className="w-full h-auto max-h-72 object-contain rounded border border-slate-300 bg-white"
                />
              ) : (
                <div className="p-8 text-center text-xs text-slate-400 bg-white rounded border border-slate-200">
                  <FileText className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                  PDF / Electronic Document Uploaded
                </div>
              )}
              <p className="text-[10px] text-slate-400 mt-2">
                Preserved securely with patient privacy encryption.
              </p>
            </div>

            {/* Extracted Structured Posology */}
            <div className="lg:col-span-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3 text-teal-900">
                Detected Medicines ({result.items.length}):
              </h3>

              <div className="space-y-3">
                {result.items.map((itm, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white transition flex flex-col sm:flex-row justify-between items-start gap-2 text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm text-slate-900">
                          {itm.matched_medicine_name || itm.raw_line}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                          {itm.strength}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Instructions: <span className="font-medium text-slate-700">{itm.frequency}</span> • {itm.duration} • {itm.instructions}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-0.5 italic">
                        Raw OCR text: "{itm.raw_line}"
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] text-slate-500 block">Confidence</span>
                      <span className="font-mono font-bold text-teal-700">
                        {(itm.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-200 flex flex-wrap justify-between items-center gap-3">
                <span className="text-xs text-slate-500 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-green-600" /> Submitted to Pharmacist Review Queue
                </span>
                <button
                  onClick={() => onNavigate('search')}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition"
                >
                  Proceed to Medicine Store
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
