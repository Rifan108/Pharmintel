import React from 'react';
import { ShieldCheck, PhoneCall, AlertTriangle, HeartPulse } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="no-print bg-slate-900 text-slate-400 text-xs border-t border-slate-800 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 text-white font-bold text-base mb-3">
              <HeartPulse className="w-5 h-5 text-teal-400" /> PharmIntel Technology
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              AI-Powered Smart Pharmacy Network combining authoritative pharmacology databases,
              multi-relational Graph Neural Networks (PHARMINTEL-HYBRIDGNN), and provider-independent clinical reasoning.
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3 uppercase tracking-wider text-[11px]">Emergency Contacts</h4>
            <ul className="space-y-1.5 text-slate-400">
              <li className="flex items-center gap-2 text-red-400 font-bold">
                <AlertTriangle className="w-4 h-4" /> National Emergency: 112
              </li>
              <li className="flex items-center gap-2 text-amber-400 font-bold">
                <PhoneCall className="w-4 h-4" /> Ambulance Services: 108
              </li>
              <li>Poison Control Center: 1800-116-117</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3 uppercase tracking-wider text-[11px]">Clinical Safety Protocols</h4>
            <ul className="space-y-1 text-[11px]">
              <li>• Two-Tier Safety: Verified Rules + HybridGNN</li>
              <li>• Zero-Gemini-Flash Architecture</li>
              <li>• Mandatory Pharmacist Verification for Schedule H</li>
              <li>• Reverse-Pair Leakage Isolated Graph Evaluation</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3 uppercase tracking-wider text-[11px]">Statutory Compliance</h4>
            <p className="text-[11px] leading-relaxed">
              Compliant with the Drugs & Cosmetics Act 1940, Pharmacy Act 1948, and Pharmacy Practice Regulations.
              All invoices generated conform to GST Rule 46 (ISO A4 standard).
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px]">
          <p>© 2026 PharmIntel Technology Network. Built for research & enterprise healthcare.</p>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1 text-teal-400">
              <ShieldCheck className="w-3.5 h-3.5" /> HIPAA & Medical Ethics Guardrails Active
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
