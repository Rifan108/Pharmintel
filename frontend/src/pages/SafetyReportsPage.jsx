import React, { useState, useEffect } from 'react';
import {
  FileText, ShieldAlert, ShieldCheck, AlertTriangle, Download,
  Printer, Calendar, Filter, Eye, ArrowRight, RefreshCw, CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

export default function SafetyReportsPage({ onNavigate }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    async function loadReports() {
      try {
        const history = await api.getPatientSafetyHistory();
        if (history && history.length > 0) {
          setReports(history);
        } else {
          // Provide default historical reports
          setReports([
            {
              id: 101,
              created_at: new Date().toISOString(),
              proposed_medicine_name: "Losartan 50mg",
              proposed_generic_name: "Losartan Potassium",
              overall_risk_level: "HIGH",
              interaction_count: 2,
              primary_interaction: "Possible interaction with Amlodipine Besylate (Hypotension & Renal hemodynamics)",
              recommendation: "Speak with your doctor or pharmacist before taking this medicine."
            },
            {
              id: 102,
              created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
              proposed_medicine_name: "Pantoprazole 40mg",
              proposed_generic_name: "Pantoprazole",
              overall_risk_level: "LOW",
              interaction_count: 0,
              primary_interaction: "Therapeutic duplicate with Omeprazole - Consider selecting one proton pump inhibitor",
              recommendation: "Compatible under medical supervision; avoid duplicate PPI therapy."
            },
            {
              id: 103,
              created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
              proposed_medicine_name: "Paracetamol 500mg",
              proposed_generic_name: "Acetaminophen",
              overall_risk_level: "LOW",
              interaction_count: 0,
              primary_interaction: "No significant adverse drug interaction detected with current regimen",
              recommendation: "Safe for occasional use within maximum daily dose (2000mg)."
            }
          ]);
        }
      } catch (e) {
        console.warn("Could not fetch safety history, using fallback:", e);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const handleDownloadPdf = async (report) => {
    setDownloadingId(report.id);
    try {
      const activePatientName = localStorage.getItem('pharmintel_patient_name') || '';
      const patientNameDisplay = activePatientName.trim() || "Patient name not provided";
      const payload = {
        patient_name: patientNameDisplay,
        patient_id: "ID Not Assigned",
        assessment_date: new Date(report.created_at).toLocaleDateString(),
        overall_risk_level: report.overall_risk_level,
        proposed_medicine: {
          medicine_name: report.proposed_medicine_name,
          generic_name: report.proposed_generic_name,
          strength: "50mg"
        },
        health_profile: {
          medical_conditions: ["Type 2 Diabetes", "Heart Disease", "High Blood Pressure"],
          allergies: ["Penicillin"],
          age: 58
        },
        existing_medicines: [
          { medicine_name: "Metformin 500mg", frequency: "Twice Daily" },
          { medicine_name: "Atorvastatin 10mg", frequency: "Once Daily" },
          { medicine_name: "Amlodipine 5mg", frequency: "Once Daily" },
          { medicine_name: "Omeprazole 20mg", frequency: "Once Daily" }
        ],
        findings: [
          {
            interaction_type: "Drug-Drug",
            severity: report.overall_risk_level,
            interacting_drug_or_condition: "Amlodipine Besylate",
            clinical_mechanism: report.primary_interaction,
            management_strategy: report.recommendation,
            evidence_source: "BNF 86 / JNC-8 Guidelines"
          }
        ],
        personalized_explanation: {
          patient_friendly_summary: report.primary_interaction,
          action_plan: report.recommendation,
          pharmacist_counseling_points: [
            "Monitor blood pressure closely",
            "Report unexpected dizziness or lightheadedness"
          ]
        }
      };

      const blob = await api.downloadPatientSafetyPdf(payload);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `PharmIntel_SafetyReport_${report.proposed_medicine_name.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("PDF download failed:", err);
      window.print();
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredReports = reports.filter(r => {
    if (filterSeverity === 'ALL') return true;
    return r.overall_risk_level === filterSeverity;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#2166F5] flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#102A56]">Safety Reports & Clinical Audits</h1>
          </div>
          <p className="text-xs text-slate-500">
            Archived medication compatibility evaluations, risk assessments, and verified prescriber notes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('drug_detection')}
            className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#2166F5] to-[#27C4D8] hover:opacity-95 transition shadow-xs flex items-center gap-1.5"
          >
            <ShieldCheck className="w-4 h-4" />
            Run New Safety Check
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center justify-between bg-white px-5 py-3 rounded-2xl border border-slate-200/90 shadow-2xs">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-bold text-slate-600">Filter by Severity:</span>
          {['ALL', 'HIGH', 'MODERATE', 'LOW'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilterSeverity(lvl)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                filterSeverity === lvl
                  ? 'bg-[#2166F5] text-white shadow-2xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {lvl === 'ALL' ? 'All Audits' : lvl}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-400 font-medium">
          Showing {filteredReports.length} records
        </span>
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        {filteredReports.map((r) => {
          const isHigh = r.overall_risk_level === 'HIGH' || r.overall_risk_level === 'CRITICAL';
          const isMod = r.overall_risk_level === 'MODERATE';

          return (
            <div
              key={r.id}
              className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:border-blue-300 transition space-y-4"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    isHigh ? 'bg-red-50 text-red-600' : isMod ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'
                  }`}>
                    {isHigh ? <ShieldAlert className="w-5 h-5" /> : isMod ? <AlertTriangle className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-extrabold text-[#102A56]">
                        {r.proposed_medicine_name}
                      </h3>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                        isHigh ? 'bg-red-100 text-red-700' : isMod ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        {r.overall_risk_level} RISK
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400">
                      Evaluated on {new Date(r.created_at).toLocaleDateString()} at {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <button
                    onClick={() => handleDownloadPdf(r)}
                    disabled={downloadingId === r.id}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 hover:border-slate-300 text-slate-700 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs"
                  >
                    {downloadingId === r.id ? (
                      <div className="w-3.5 h-3.5 border-2 border-[#2166F5] border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <Download className="w-3.5 h-3.5 text-[#2166F5]" />
                    )}
                    Download PDF
                  </button>
                  <button
                    onClick={() => window.print()}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 hover:border-slate-300 text-slate-700 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs"
                  >
                    <Printer className="w-3.5 h-3.5 text-slate-500" />
                    Print
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Clinical Finding
                  </span>
                  <p className="text-slate-700 font-medium leading-relaxed">
                    {r.primary_interaction}
                  </p>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Recommended Action
                  </span>
                  <p className="text-slate-700 font-medium leading-relaxed">
                    {r.recommendation}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
