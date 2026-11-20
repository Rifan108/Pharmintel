import React from 'react';
import { X, Printer, Download, ShieldAlert, ShieldCheck, AlertTriangle, FileText, CheckSquare, Square, Stethoscope } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function FullReportModal({ isOpen, onClose, report, onPrint, onDownloadPdf }) {
  const { t } = useLanguage();
  if (!isOpen || !report) return null;

  const isMulti = Boolean(report.interaction_table || report.medicines_analyzed);
  const status = (report.overall_status || 'GREEN').toUpperCase();
  const statusLabel = report.overall_status_label || (status === 'RED' ? 'Serious Potential Interaction Detected' : (status === 'YELLOW' ? 'Caution Advised' : 'Safe Combination'));
  const headline = report.summary_headline || (status === 'RED' ? 'Review combination carefully with physician before dispensing' : 'No documented high-risk interactions identified');

  const tableRows = report.interaction_table || [];
  const findings = report.findings || [];

  // Patient Info
  const pName = report.patient_name || report.patient_summary?.patient_name || report.health_profile?.patient_name || localStorage.getItem('pharmintel_patient_name') || '';
  const patientDisplayName = pName.trim() ? pName.trim() : 'Patient name not provided';

  const conds = report.patient_conditions_evaluated || report.patient_summary?.medical_conditions || report.health_profile?.medical_conditions || [];
  const allergies = report.allergies_evaluated || report.patient_summary?.known_allergies || report.health_profile?.known_allergies || [];
  const age = report.patient_summary?.age || report.health_profile?.age || 'Not recorded';
  const gender = report.patient_summary?.gender || report.health_profile?.gender || 'Not recorded';

  // Medicines list
  const meds = report.medicines_analyzed || report.existing_medicines_analysed || [];
  const proposed = report.proposed_medicine;

  // Discussion points
  const discussQuestions = report.what_to_discuss_with_doctor || [
    'Should the dosage or timing of my medications be separated?',
    'Are there specific symptoms or side effects I should monitor at home?',
    'Is routine laboratory monitoring (blood glucose, blood pressure, renal profile) recommended?'
  ];

  const reportId = report.assessment_id ? `PS-${new Date().getFullYear()}-${report.assessment_id}` : `PS-${new Date().getFullYear()}-${Date.now().toString().slice(-6)}`;
  const timestamp = report.assessment_timestamp || report.created_at || new Date().toLocaleString();

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-4xl w-full p-6 sm:p-8 shadow-2xl border border-slate-200 max-h-[92vh] overflow-y-auto flex flex-col">
        {/* Document Header */}
        <div className="flex justify-between items-start pb-4 border-b border-slate-200 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#1e3a8a] to-[#2166F5] text-white flex items-center justify-center shadow-sm">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-xl font-black text-[#102A56]">
                  PHARMINTEL Clinical Medication Compatibility Report
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                  ISO 216 A4 Certified
                </span>
              </div>
              <p className="text-xs text-slate-500 font-mono mt-0.5">
                Report Ref: <b className="text-slate-800">{reportId}</b> • Generated: {timestamp} • Compendia: CDSCO / WHO / BNF 86 Curated
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 space-y-5 text-xs text-slate-700">
          {/* Patient Profile Card */}
          <div className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-[11px] font-black text-[#102A56] uppercase tracking-wider block mb-1">
                Patient Health Profile
              </span>
              <p className="text-xs">
                <b>Patient Name:</b> <span className={pName.trim() ? "font-bold text-slate-900" : "italic text-slate-500"}>{patientDisplayName}</span><br />
                <b>Age / Gender:</b> {age} / {gender}<br />
                <b>Recorded Conditions:</b> {conds.length ? conds.join(', ') : 'None Recorded'}<br />
                <b>Known Allergies:</b> {allergies.length ? allergies.join(', ') : 'None Recorded'}
              </p>
            </div>
            <div>
              <span className="text-[11px] font-black text-[#102A56] uppercase tracking-wider block mb-1">
                Evaluation Scope & Regimen
              </span>
              <p className="text-xs leading-relaxed">
                <b>Total Medications Assessed:</b> {meds.length + (proposed ? 1 : 0)}<br />
                <b>Active Risk Findings:</b> {report.total_interactions_identified || tableRows.length || findings.length}<br />
                <b>Duplicate Active Ingredients:</b> {report.duplicate_medicines_count || 0}<br />
                <b>Assessment Engine:</b> PharmIntel Clinical Decision Support & Compendia Matcher
              </p>
            </div>
          </div>

          {/* Status Alert Box */}
          <div className={`p-4 rounded-2xl border flex items-start gap-3.5 ${
            status === 'RED'
              ? 'bg-red-50 border-red-200 text-red-950'
              : status === 'YELLOW'
              ? 'bg-amber-50 border-amber-200 text-amber-950'
              : status === 'GREY'
              ? 'bg-slate-100 border-slate-300 text-slate-900'
              : 'bg-emerald-50 border-emerald-200 text-emerald-950'
          }`}>
            {status === 'RED' ? <ShieldAlert className="w-7 h-7 text-red-600 shrink-0 mt-0.5" /> :
             status === 'YELLOW' ? <AlertTriangle className="w-7 h-7 text-amber-600 shrink-0 mt-0.5" /> :
             status === 'GREY' ? <AlertTriangle className="w-7 h-7 text-slate-500 shrink-0 mt-0.5" /> :
             <ShieldCheck className="w-7 h-7 text-emerald-600 shrink-0 mt-0.5" />}
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-black block tracking-wide">{statusLabel}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  status === 'RED' ? 'bg-red-200 text-red-900' : status === 'YELLOW' ? 'bg-amber-200 text-amber-900' : 'bg-emerald-200 text-emerald-900'
                }`}>
                  Risk Level: {status}
                </span>
              </div>
              <p className="text-xs mt-1 opacity-90 leading-relaxed">{headline}</p>
            </div>
          </div>

          {/* Unverified Notice */}
          {report.unidentified_medicines && report.unidentified_medicines.length > 0 && (
            <div className="p-3 bg-red-50 rounded-2xl border border-red-200 text-red-800 text-xs">
              <b>UNVERIFIED MEDICINE NOTICE:</b> The following medication(s) could not be verified in authoritative CDSCO / WHO compendia: <b>{report.unidentified_medicines.join(', ')}</b>. Please check package labeling or consult your pharmacist to confirm the active salt composition.
            </div>
          )}

          {/* What Does This Mean for You? */}
          <div className="space-y-2 p-4 bg-blue-50/60 rounded-2xl border border-blue-100">
            <span className="text-xs font-black text-[#102A56] uppercase tracking-wider block">
              WHAT DOES THIS MEAN FOR YOU? (CLINICAL PATIENT GUIDANCE)
            </span>
            <p className="leading-relaxed font-bold text-slate-900">
              {report.what_does_this_mean || report.personalized_guidance?.what_this_means_for_you || 'Review interaction risks carefully.'}
            </p>
            {(report.why_they_interact || report.clinical_mechanism) && (
              <p className="leading-relaxed text-slate-700">
                <b>Pharmacological Mechanism:</b> {report.why_they_interact || report.clinical_mechanism}
              </p>
            )}
            {report.what_could_happen && (
              <p className="leading-relaxed text-slate-700">
                <b>Potential Clinical Consequences:</b> {report.what_could_happen}
              </p>
            )}
            <div className="mt-2 pt-2 border-t border-blue-200/60">
              <b>Recommended Action:</b> {report.action_guidance || report.personalized_guidance?.should_take_assessment}
              {(report.action_bullets || report.personalized_guidance?.action_summary) && (
                <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-700">
                  {(report.action_bullets || report.personalized_guidance?.action_summary || []).map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* All Evaluated Medicines in Regimen Table */}
          <div>
            <span className="font-black text-[#102A56] block mb-2 uppercase tracking-wider text-[11px]">
              Evaluated Regimen Medications ({meds.length + (proposed ? 1 : 0)}):
            </span>
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                  <tr>
                    <th className="p-2.5">Medicine Name / Brand</th>
                    <th className="p-2.5">Generic / Active Ingredients</th>
                    <th className="p-2.5">Strength & Dose</th>
                    <th className="p-2.5">Frequency & Route</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {proposed && (
                    <tr className="bg-blue-50/50">
                      <td className="p-2.5 font-bold text-[#2166F5]">
                        {proposed.medicine_name} <span className="text-[10px] uppercase font-bold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded ml-1">[Proposed]</span>
                      </td>
                      <td className="p-2.5 text-slate-700">{proposed.generic_name || 'Standard'}</td>
                      <td className="p-2.5 text-slate-700">{proposed.strength || 'Standard'}</td>
                      <td className="p-2.5 text-slate-700">{proposed.dosage_form || 'Oral'}</td>
                    </tr>
                  )}
                  {meds.map((m, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/60">
                      <td className="p-2.5 font-bold text-slate-900">{m.medicine_name || m.brand_name}</td>
                      <td className="p-2.5 text-slate-700">{m.generic_name || m.active_ingredients || 'Standard component'}</td>
                      <td className="p-2.5 text-slate-700">{m.strength || 'Standard'} {m.dosage || ''}</td>
                      <td className="p-2.5 text-slate-700">{m.frequency || 'As Prescribed'} ({m.administration_route || 'Oral'})</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Interaction Details Table */}
          {tableRows.length > 0 && (
            <div>
              <span className="font-black text-[#102A56] block mb-2 uppercase tracking-wider text-[11px]">
                Clinical Interaction Findings & Mechanisms ({tableRows.length}):
              </span>
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                    <tr>
                      <th className="p-2.5">Severity</th>
                      <th className="p-2.5">Involved Medicines</th>
                      <th className="p-2.5">Interaction Title & Mechanism</th>
                      <th className="p-2.5">Evidence Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {tableRows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/60">
                        <td className="p-2.5 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            row.severity === 'RED' ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}>
                            {row.severity_label || row.severity}
                          </span>
                        </td>
                        <td className="p-2.5 font-bold text-slate-900 whitespace-nowrap">
                          {row.medicines_involved?.join(' + ')}
                        </td>
                        <td className="p-2.5 text-slate-700 leading-snug">
                          <div className="font-bold text-slate-900">{row.interaction_title}</div>
                          <div className="text-slate-600 mt-0.5">{row.explanation}</div>
                          {row.clinical_mechanism && (
                            <div className="text-[11px] text-slate-800 mt-0.5"><b>Mechanism:</b> {row.clinical_mechanism}</div>
                          )}
                          <div className="text-[11px] text-blue-900 font-medium mt-0.5"><b>Action:</b> {row.recommended_action}</div>
                        </td>
                        <td className="p-2.5 text-[11px] text-slate-600 whitespace-nowrap">{row.evidence_source || 'CDSCO/BNF'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Single findings if applicable */}
          {!isMulti && findings.length > 0 && (
            <div>
              <span className="font-black text-[#102A56] block mb-2 uppercase tracking-wider text-[11px]">
                Clinical Findings & Evidence ({findings.length}):
              </span>
              <div className="space-y-2">
                {findings.map((f, i) => (
                  <div key={i} className="p-3.5 bg-white rounded-xl border border-slate-200 space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-900">{f.headline}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        f.severity === 'RED' ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-amber-100 text-amber-800 border border-amber-200'
                      }`}>
                        {f.severity_label || f.severity}
                      </span>
                    </div>
                    <p className="text-slate-600 leading-relaxed">{f.plain_language_explanation}</p>
                    <p className="text-[11px] text-slate-800 font-medium"><b>Action:</b> {f.recommended_action}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Doctor Discussion Prompts */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
            <span className="text-[11px] font-black text-[#102A56] uppercase tracking-wider block mb-1.5">
              Recommended Questions to Discuss with Your Physician / Pharmacist
            </span>
            <ul className="list-disc pl-4 space-y-1 text-xs text-slate-700">
              {discussQuestions.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          </div>

          {/* Clinician Review & Sign-Off Block */}
          <div className="p-4 bg-slate-50/90 rounded-2xl border border-slate-300 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-[11px] font-black text-[#102A56] uppercase tracking-wider block mb-1">
                Reviewing Clinician / Pharmacist Sign-Off
              </span>
              <p className="text-[11px] text-slate-600 leading-loose">
                Clinician Name: ____________________________________<br />
                Registration / License No: __________________________<br />
                Clinic / Pharmacy Stamp: ____________________________
              </p>
            </div>
            <div>
              <span className="text-[11px] font-black text-[#102A56] uppercase tracking-wider block mb-1">
                Dispensing Recommendation
              </span>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                [  ] Approved as Prescribed without Modification<br />
                [  ] Dose Adjustment / Therapeutic Monitoring Required<br />
                [  ] Therapy Withheld — Safe Alternative Recommended<br />
                Signature: ______________________ Date: ___________
              </p>
            </div>
          </div>

          {/* Clinical Disclaimer */}
          <div className="p-3 bg-slate-100 rounded-xl text-[10px] text-slate-500 leading-normal border border-slate-200">
            <b>CLINICAL DISCLAIMER:</b> {report.disclaimer || 'This report is generated by PharmIntel Clinical Decision Support and combines curated compendia (BNF, CDSCO, WHO, FDA) with Graph Neural Network predictions. It is intended solely for clinical guidance and does not replace physician consultation. Patients must never alter or discontinue prescribed medication independently.'}
          </div>
        </div>

        {/* Action Footer */}
        <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition"
          >
            {t('close', 'Close')}
          </button>
          <div className="flex gap-2">
            <button
              onClick={onPrint}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border border-slate-300 shadow-xs"
            >
              <Printer className="w-3.5 h-3.5" /> {t('btn_print_report', 'Print Report')}
            </button>
            <button
              onClick={onDownloadPdf}
              className="px-4 py-2 bg-[#2166F5] hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
            >
              <Download className="w-3.5 h-3.5" /> {t('btn_download_pdf', 'Download PDF')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
