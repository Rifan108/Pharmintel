import React from 'react';
import { Heart, Activity, ShieldCheck, ShoppingBag, Pill, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function HealthcareProducts({ onNavigate }) {
  const { addToCart } = useAuth();

  const products = [
    {
      id: 101,
      name: "Accu-Chek Active Blood Glucose Monitoring Kit",
      category: "Diabetes Care & Diagnostics",
      description: "ISO 15197:2013 compliant glucometer with 10 test strips and sterile lancets.",
      base_mrp: 999.00,
      requires_prescription: false,
      rating: 4.8
    },
    {
      id: 102,
      name: "Omron HEM-7120 Digital Automatic Blood Pressure Monitor",
      category: "Cardiovascular Devices",
      description: "Clinically validated oscillometric blood pressure monitor with hypertension indicator.",
      base_mrp: 1850.00,
      requires_prescription: false,
      rating: 4.9
    },
    {
      id: 103,
      name: "Becozym C Forte Multivitamin with Vitamin B-Complex & Vitamin C",
      category: "Vitamins & Nutritional Supplements",
      description: "Therapeutic dietary supplement for nutritional deficiency and immune support.",
      base_mrp: 65.00,
      requires_prescription: false,
      rating: 4.7
    },
    {
      id: 104,
      name: "Dettol Antiseptic Disinfectant Liquid 550ml",
      category: "First Aid & Antiseptics",
      description: "Chloroxylenol formulation for wound cleansing, surface disinfection, and hygiene.",
      base_mrp: 215.00,
      requires_prescription: false,
      rating: 4.9
    },
    {
      id: 105,
      name: "Volini Joint Pain Relief Gel 75g",
      category: "Pain Relief & Orthopedics",
      description: "Topical formulation containing Diclofenac Diethylamine, Methyl Salicylate, and Menthol.",
      base_mrp: 235.00,
      requires_prescription: false,
      rating: 4.6
    },
    {
      id: 106,
      name: "Dr. Morepen Pulse Oximeter PO-09",
      category: "Respiratory & Diagnostic Devices",
      description: "Non-invasive optical pulse oximeter for pulse rate and arterial oxygen saturation (%SpO2).",
      base_mrp: 750.00,
      requires_prescription: false,
      rating: 4.7
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
          <Heart className="w-6 h-6 text-red-600" /> Healthcare Products & Medical Devices
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Certified diagnostic equipment, nutritional supplements, first-aid, and OTC health essentials.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((p) => (
          <div
            key={p.id}
            className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition flex flex-col justify-between"
          >
            <div>
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200 inline-block mb-2">
                {p.category}
              </span>
              <h3 className="font-extrabold text-base text-slate-900 leading-tight mb-1">
                {p.name}
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                {p.description}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 block">Retail Price</span>
                <span className="text-lg font-black font-mono text-slate-900">
                  ₹{p.base_mrp.toFixed(2)}
                </span>
              </div>

              <button
                onClick={() => {
                  addToCart({
                    id: p.id + 1000,
                    brand_name: p.name,
                    generic_name: p.category,
                    strength: "1 Unit",
                    dosage_form: "Device/OTC",
                    base_mrp: p.base_mrp,
                    requires_prescription: false
                  }, 1, 1);
                  alert(`Added ${p.name} to cart`);
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-xs"
              >
                <ShoppingBag className="w-3.5 h-3.5" /> Add to Cart
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
