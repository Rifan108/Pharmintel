import React, { useState } from 'react';
import {
  HelpCircle, Phone, MessageSquare, ShieldAlert, ChevronDown,
  ExternalLink, Clock, AlertTriangle, Stethoscope, HeartPulse
} from 'lucide-react';

export default function HelpSupportPage({ onOpenLiveChat }) {
  const [openFaq, setOpenFaq] = useState(0);

  const faqs = [
    {
      q: "How does PharmIntel analyze medicine compatibility?",
      a: "PharmIntel employs a dual-layer clinical evaluation architecture. First, it executes deterministic multi-dimensional screening against curated, authoritative clinical rules (BNF 86, Lexicomp, JNC-8, KDIGO). Second, it utilizes the PHARMINTEL-HYBRIDGNN (Hybrid Graph Neural Network) to cross-reference drug-drug interactions, drug-disease contraindications, drug-allergy warnings, and cumulative regimen risks (such as additive bleeding or the 'Triple Whammy' effect)."
    },
    {
      q: "What should I do if a 'High Risk' interaction is detected?",
      a: "If a High Risk alert is triggered, do NOT begin taking the new medicine without consulting your prescribing physician or a licensed clinical pharmacist. The alert explains specific clinical mechanisms (e.g., severe hypotension, acute kidney injury risk) and provides actionable guidance to share with your doctor."
    },
    {
      q: "How accurate is the Prescription OCR feature?",
      a: "Our Tesseract and regex-driven OCR pipeline identifies brand names, dosage formulations, and frequencies with high accuracy. However, for patient safety, all extracted medications require patient verification and pharmacist review before entering your active regimen."
    },
    {
      q: "Can I print or download official safety reports for my doctor?",
      a: "Yes! Every compatibility assessment can be downloaded as an ISO 216 standard A4 clinical PDF or printed directly from your browser with structured tables, severity badges, and pharmacotherapy notes."
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-[#102A56]">Clinical Help & Emergency Support</h1>
            <p className="text-xs text-slate-500">24/7 pharmacist assistance, medical hotlines and clinical FAQs.</p>
          </div>
        </div>

        <button
          onClick={onOpenLiveChat}
          className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#2166F5] to-[#27C4D8] hover:opacity-95 transition shadow-xs flex items-center gap-2"
        >
          <MessageSquare className="w-4 h-4" /> Chat With Pharmacist
        </button>
      </div>

      {/* Emergency Hotlines Banner */}
      <div className="bg-gradient-to-r from-red-600 to-rose-700 text-white rounded-2xl p-6 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-red-200" />
          <h2 className="text-sm font-extrabold tracking-tight uppercase">Emergency Medical Hotlines (India)</h2>
        </div>
        <p className="text-xs text-red-100">
          If you or someone around you is experiencing severe symptoms, acute allergic reaction (anaphylaxis), or suspected overdose, call emergency services immediately.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="bg-white/10 backdrop-blur-sm p-3 rounded-xl border border-white/20">
            <span className="text-[10px] font-bold text-red-200 block uppercase">National Emergency</span>
            <span className="text-lg font-black tracking-wide">112</span>
          </div>
          <div className="bg-white/10 backdrop-blur-sm p-3 rounded-xl border border-white/20">
            <span className="text-[10px] font-bold text-red-200 block uppercase">Medical Ambulance</span>
            <span className="text-lg font-black tracking-wide">108</span>
          </div>
          <div className="bg-white/10 backdrop-blur-sm p-3 rounded-xl border border-white/20">
            <span className="text-[10px] font-bold text-red-200 block uppercase">Poison Center (AIIMS)</span>
            <span className="text-sm font-black tracking-wide">1800-116-117</span>
          </div>
        </div>
      </div>

      {/* FAQs */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-extrabold text-[#102A56] pb-2 border-b border-slate-100">
          Frequently Asked Clinical Questions
        </h2>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div
                key={idx}
                className="border border-slate-200 rounded-xl overflow-hidden transition"
              >
                <button
                  onClick={() => setOpenFaq(isOpen ? -1 : idx)}
                  className="w-full p-4 text-left flex items-center justify-between text-xs font-bold text-[#102A56] hover:bg-slate-50 transition"
                >
                  <span>{faq.q}</span>
                  <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </button>
                {isOpen && (
                  <div className="px-4 pb-4 text-xs text-slate-600 leading-relaxed border-t border-slate-100 pt-3 bg-[#F8FAFC]">
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
