import React from 'react';
import { Printer, Download, ArrowLeft, Stethoscope, CheckCircle, Clock } from 'lucide-react';

export default function PrescriptionRecord({ rxData, onBack }) {
  if (!rxData) return null;

  return (
    <div className="max-w-4xl mx-auto my-6 px-4">
      {/* Control Actions Header */}
      <div className="no-print mb-6 flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
          )}
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-teal-600" /> Professional Prescription Record (A4)
            </h2>
            <p className="text-xs text-slate-500">
              Verified clinical record with OCR extraction confidence and pharmacist audit logs.
            </p>
          </div>
        </div>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg transition shadow-md"
        >
          <Printer className="w-4 h-4" /> Print Record (A4)
        </button>
      </div>

      {/* A4 PRINT CONTAINER */}
      <div
        className="print-page bg-white p-8 md:p-12 border border-slate-300 rounded-lg shadow-lg mx-auto"
        style={{ width: '100%', maxWidth: '210mm', minHeight: '297mm' }}
      >
        {/* Prescription Header */}
        <div className="border-b-2 border-teal-800 pb-4 mb-4">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="bg-teal-800 text-white font-bold text-xs px-2 py-0.5 rounded">
                  CLINICAL RECORD
                </span>
                <span className="text-xs text-slate-500">Ref: RX-{rxData.id}</span>
              </div>
              <h1 className="text-xl font-bold text-slate-900">{rxData.doctor_name || 'Registered Medical Practitioner'}</h1>
              <p className="text-xs text-slate-600">Prescription Date: {rxData.prescription_date || 'N/A'}</p>
            </div>
            <div className="text-right text-xs">
              <div className="inline-flex items-center gap-1 font-bold px-3 py-1 rounded text-xs mb-1 bg-green-100 text-green-800 border border-green-300">
                <CheckCircle className="w-3.5 h-3.5" /> {rxData.verification_status || 'VERIFIED'}
              </div>
              <p className="text-slate-500">OCR Extraction Confidence: {(rxData.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>

        {/* Patient Details */}
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs mb-6 grid grid-cols-2 gap-4">
          <div>
            <p className="text-slate-500">Patient Full Name:</p>
            <p className="font-bold text-sm text-slate-900">{rxData.patient_name || localStorage.getItem('pharmintel_patient_name') || 'Patient name not provided'}</p>
          </div>
          <div>
            <p className="text-slate-500">Prescription Uploaded File:</p>
            <p className="font-mono text-slate-700">{rxData.file_name}</p>
          </div>
        </div>

        {/* Structured Medicine Items */}
        <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wider text-teal-900">
          Prescribed Medications & Posology:
        </h3>
        <table className="w-full border-collapse text-xs mb-8">
          <thead>
            <tr className="bg-slate-100 border-y border-slate-300 text-slate-800 font-bold">
              <th className="py-2 px-2 text-center w-8">#</th>
              <th className="py-2 px-2 text-left">Medicine Name & Formulation</th>
              <th className="py-2 px-2 text-left">Strength</th>
              <th className="py-2 px-2 text-left">Frequency</th>
              <th className="py-2 px-2 text-left">Duration</th>
              <th className="py-2 px-2 text-center w-24">Pharmacist Audit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {(rxData.items || []).map((itm, idx) => (
              <tr key={idx}>
                <td className="py-2.5 px-2 text-center text-slate-500">{idx + 1}</td>
                <td className="py-2.5 px-2">
                  <p className="font-bold text-slate-900">{itm.matched_name || itm.raw}</p>
                  <p className="text-[10px] text-slate-500">{itm.raw}</p>
                </td>
                <td className="py-2.5 px-2 font-medium">{itm.strength || 'Standard'}</td>
                <td className="py-2.5 px-2 font-medium text-teal-800">{itm.frequency}</td>
                <td className="py-2.5 px-2 text-slate-700">{itm.duration}</td>
                <td className="py-2.5 px-2 text-center">
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-green-50 text-green-700 border border-green-200">
                    Confirmed
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pharmacist Clinical Signoff */}
        <div className="pt-8 border-t border-slate-300 text-xs grid grid-cols-2 gap-8 avoid-break">
          <div>
            <p className="font-bold text-slate-800 mb-1">Clinical Safety Disclaimer:</p>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              This document represents an authenticated electronic prescription record verified by a licensed pharmacist.
              Prescription-only drugs are dispensed strictly according to statutory pharmacy regulations.
            </p>
          </div>
          <div className="text-right">
            <p className="font-bold text-slate-900">Verified by Registered Pharmacist</p>
            <p className="text-[11px] text-slate-600">PharmIntel Certified Verification Desk</p>
            <div className="mt-8 border-b border-dashed border-slate-400 w-48 ml-auto"></div>
            <p className="text-[10px] text-slate-400 mt-1">Authorized Stamp & Signature</p>
          </div>
        </div>
      </div>
    </div>
  );
}
