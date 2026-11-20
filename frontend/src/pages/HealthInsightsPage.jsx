import React, { useState } from 'react';
import {
  TrendingUp, Activity, ShieldCheck, Heart, AlertTriangle,
  Calendar, Award, CheckCircle2, ArrowUpRight, BarChart3
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';

export default function HealthInsightsPage({ onNavigate }) {
  const [timeRange, setTimeRange] = useState('30d');

  // Adherence trend data
  const adherenceData = [
    { date: 'Day 1', adherence: 100, target: 95 },
    { date: 'Day 5', adherence: 100, target: 95 },
    { date: 'Day 10', adherence: 85, target: 95 },
    { date: 'Day 15', adherence: 100, target: 95 },
    { date: 'Day 20', adherence: 92, target: 95 },
    { date: 'Day 25', adherence: 100, target: 95 },
    { date: 'Day 30', adherence: 98, target: 95 }
  ];

  // Risk breakdown data
  const riskData = [
    { name: 'Safe / Compatible', value: 78, color: '#10B981' },
    { name: 'Monitor (Mild)', value: 14, color: '#27C4D8' },
    { name: 'Moderate Precaution', value: 6, color: '#F59E0B' },
    { name: 'Contraindicated (High)', value: 2, color: '#DC2626' }
  ];

  // Daily Schedule & Vitals correlation
  const vitalsCorrelation = [
    { slot: 'Morning (08:00)', systolicBP: 124, diastolicBP: 80, medsTaken: 2 },
    { slot: 'Afternoon (13:00)', systolicBP: 122, diastolicBP: 78, medsTaken: 1 },
    { slot: 'Evening (19:00)', systolicBP: 126, diastolicBP: 82, medsTaken: 1 },
    { slot: 'Night (22:00)', systolicBP: 118, diastolicBP: 76, medsTaken: 1 }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#2166F5] flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#102A56]">Health Insights & Adherence Analytics</h1>
          </div>
          <p className="text-xs text-slate-500">
            Real-time biometric telemetry, medication compliance patterns, and drug safety risk indices.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl">
          {['7d', '30d', '90d'].map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                timeRange === r
                  ? 'bg-white text-[#2166F5] shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Last {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Cards Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Regimen Adherence</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-[#102A56]">96.4%</span>
            <span className="text-[11px] font-bold text-emerald-600 flex items-center">
              +2.1% <ArrowUpRight className="w-3 h-3" />
            </span>
          </div>
          <p className="text-[11px] text-slate-400">Target: 95% minimum</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Safety Index</span>
            <div className="w-7 h-7 rounded-lg bg-blue-50 text-[#2166F5] flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-[#102A56]">98 / 100</span>
            <span className="text-[11px] font-bold text-blue-600">Optimal</span>
          </div>
          <p className="text-[11px] text-slate-400">Zero unmanaged severe DDIs</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Active Prescriptions</span>
            <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-[#102A56]">4 Meds</span>
            <span className="text-[11px] font-bold text-slate-500">Stable</span>
          </div>
          <p className="text-[11px] text-slate-400">Metformin, Atorvastatin, etc.</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500">Adverse Events Flagged</span>
            <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <Heart className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-emerald-600">0</span>
            <span className="text-[11px] font-bold text-emerald-600">Clear</span>
          </div>
          <p className="text-[11px] text-slate-400">30-day monitoring window</p>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: 30-Day Medication Adherence (2 Columns) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h2 className="text-sm font-extrabold text-[#102A56]">Medication Adherence Compliance Trend</h2>
              <p className="text-[11px] text-slate-400">Daily dose consumption tracking vs clinical target</p>
            </div>
            <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              96.4% Avg
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={adherenceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="adherenceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2166F5" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2166F5" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis domain={[70, 105]} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#102A56', color: '#fff', borderRadius: '12px', fontSize: '11px', border: 'none' }}
                />
                <Area type="monotone" dataKey="adherence" stroke="#2166F5" strokeWidth={2.5} fillOpacity={1} fill="url(#adherenceGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Regimen Safety Distribution (1 Column) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h2 className="text-sm font-extrabold text-[#102A56]">Safety Risk Distribution</h2>
            <p className="text-[11px] text-slate-400">Evaluated queries across patient regimen</p>
          </div>

          <div className="h-52 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#102A56', color: '#fff', borderRadius: '12px', fontSize: '11px', border: 'none' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 pt-2">
            {riskData.map((d) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }}></span>
                  <span className="text-slate-600 font-medium">{d.name}</span>
                </div>
                <span className="font-extrabold text-[#102A56]">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
