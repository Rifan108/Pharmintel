import React, { useState, useEffect } from 'react';
import {
  Activity, Cpu, ShieldCheck, RefreshCw, BarChart2, TrendingUp,
  Layers, Database, GitBranch, CheckCircle2, ChevronRight
} from 'lucide-react';
import { api } from '../services/api';

export default function MLModelAnalytics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeGraphTab, setActiveGraphTab] = useState('comparison');
  
  // Interactive Live SMILES Tester
  const [drugASmiles, setDrugASmiles] = useState('CC(=O)CC(C1=CC=CC=C1)C2=C(C3=CC=CC=C3OC2=O)O'); // Warfarin
  const [drugBSmiles, setDrugBSmiles] = useState('CC(=O)OC1=CC=CC=C1C(=O)O'); // Aspirin
  const [predictResult, setPredictResult] = useState(null);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await api.getMLMetrics();
      setMetrics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handlePredict = async () => {
    if (!drugASmiles || !drugBSmiles) return;
    setPredicting(true);
    try {
      const res = await api.predictMLDDI(drugASmiles, drugBSmiles);
      setPredictResult(res);
    } catch (e) {
      alert("Prediction error: " + e.message);
    } finally {
      setPredicting(false);
    }
  };

  const graphTabs = [
    { id: 'comparison', label: 'Model Comparison', graphKey: 'comparison' },
    { id: 'ablation', label: 'Ablation Study', graphKey: 'ablation' },
    { id: 'accuracy', label: 'Accuracy Curves', graphKey: 'accuracy' },
    { id: 'loss', label: 'Loss Curves', graphKey: 'loss' },
    { id: 'confusion_matrix', label: 'Confusion Matrix Heatmap', graphKey: 'confusion_matrix' },
    { id: 'roc', label: 'ROC Curves (OvR)', graphKey: 'roc' },
    { id: 'pr_curve', label: 'PR Curves', graphKey: 'pr_curve' },
    { id: 'class_distribution', label: 'Class Distribution', graphKey: 'class_distribution' },
  ];

  const currentGraph = graphTabs.find((t) => t.id === activeGraphTab);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-300">
              Biomedical AI Research Component
            </span>
            <span className="text-xs font-mono text-slate-400">
              PHARMINTEL-HYBRIDGNN • Heterogeneous Graph Architecture
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 flex items-center gap-2">
            <Cpu className="w-7 h-7 text-purple-600" /> Research Model Analytics & Evaluation
          </h1>
          <p className="text-xs text-slate-500 mt-0.5 max-w-3xl">
            Genuine test-set performance metrics, multi-relational knowledge graph topology,
            systematic ablation experiments, and calibrated symmetric pair predictions.
          </p>
        </div>

        <button
          onClick={loadMetrics}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 rounded-lg border border-slate-300 shadow-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-purple-600" /> Refresh Metrics
        </button>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400 text-xs">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-purple-600" />
          Loading experimental research results and model weights...
        </div>
      ) : metrics ? (
        <div className="space-y-8">
          {/* Top Architecture & Provenance Card */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-slate-800">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-purple-300 block font-semibold">
                  Model Architecture
                </span>
                <span className="text-lg font-black block mt-0.5">{metrics.model_name}</span>
                <span className="text-xs text-slate-400 block mt-1">{metrics.architecture}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-purple-300 block font-semibold">
                  Dataset Benchmark
                </span>
                <span className="text-sm font-bold block mt-0.5">{metrics.dataset_name}</span>
                <span className="text-[11px] text-slate-400 block mt-1">{metrics.dataset_citation}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-purple-300 block font-semibold">
                  Knowledge Graph Topology
                </span>
                <span className="text-sm font-bold block mt-0.5">
                  {metrics.total_nodes} Heterogeneous Nodes
                </span>
                <span className="text-[11px] text-slate-400 block mt-1">
                  {metrics.total_edges} Multi-Relational Edges
                </span>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-purple-300 block font-semibold">
                  Leakage Prevention Protocol
                </span>
                <span className="text-xs font-semibold text-green-400 block mt-0.5">
                  ✓ Reverse-Pair Isolation
                </span>
                <span className="text-xs font-semibold text-green-400 block">
                  ✓ Test-Edge Graph Suppression
                </span>
              </div>
            </div>
          </div>

          {/* Key Metric KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">Accuracy</span>
              <span className="text-xl font-black font-mono text-blue-900 mt-1 block">
                {(metrics.performance_summary.accuracy * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400 block">Test Set Ground Truth</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">Macro F1</span>
              <span className="text-xl font-black font-mono text-teal-700 mt-1 block">
                {metrics.performance_summary.macro_f1.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block">Unweighted Mean</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">Weighted F1</span>
              <span className="text-xl font-black font-mono text-purple-700 mt-1 block">
                {metrics.performance_summary.weighted_f1.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block">Imbalance Adjusted</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">ROC-AUC</span>
              <span className="text-xl font-black font-mono text-amber-600 mt-1 block">
                {metrics.performance_summary.roc_auc.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block">One-vs-Rest Macro</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">Precision</span>
              <span className="text-xl font-black font-mono text-slate-800 mt-1 block">
                {metrics.performance_summary.precision.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block">Macro Positive Rate</span>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">Recall</span>
              <span className="text-xl font-black font-mono text-slate-800 mt-1 block">
                {metrics.performance_summary.recall.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-400 block">Macro Sensitivity</span>
            </div>
          </div>

          {/* Genuine Evaluation Graphs Display Area */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200 mb-6">
              <div>
                <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-blue-600" /> Measured Experimental Evaluation Graphs
                </h3>
                <p className="text-xs text-slate-500">
                  Rendered from genuine test-set predictions and training loss histories. Zero synthetic metrics.
                </p>
              </div>

              {/* Graph Switcher Tabs */}
              <div className="flex flex-wrap gap-1 bg-slate-100 p-1 rounded-xl text-xs">
                {graphTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveGraphTab(tab.id)}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                      activeGraphTab === tab.id
                        ? 'bg-white text-blue-700 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Display Selected Graph Image */}
            <div className="flex justify-center items-center py-4 bg-slate-50/60 rounded-xl border border-slate-100 min-h-[380px]">
              <img
                src={api.getMLGraphUrl(currentGraph?.graphKey || 'comparison')}
                alt={currentGraph?.label}
                className="max-h-[460px] w-auto object-contain rounded-lg shadow-sm bg-white p-2 border border-slate-200"
              />
            </div>
          </div>

          {/* Experimental Comparison & Ablation Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Model Comparison Table */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
              <h3 className="font-extrabold text-sm text-slate-900 mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600" /> Baseline Comparison Benchmark
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                      <th className="py-2.5 px-3">Model Architecture</th>
                      <th className="py-2.5 px-2 text-right">Accuracy</th>
                      <th className="py-2.5 px-2 text-right">Macro F1</th>
                      <th className="py-2.5 px-2 text-right">ROC-AUC</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {Object.entries(metrics.model_comparison || {}).map(([mName, mVals]) => {
                      const isProposed = mName.includes('PHARMINTEL');
                      return (
                        <tr key={mName} className={isProposed ? 'bg-purple-50/70 font-bold text-purple-950' : 'hover:bg-slate-50'}>
                          <td className="py-2 px-3 font-sans">
                            {mName} {isProposed && <span className="text-[10px] bg-purple-200 text-purple-800 px-1.5 py-0.2 rounded font-bold ml-1">Proposed</span>}
                          </td>
                          <td className="py-2 px-2 text-right">{(mVals.accuracy * 100).toFixed(1)}%</td>
                          <td className="py-2 px-2 text-right">{mVals.macro_f1.toFixed(4)}</td>
                          <td className="py-2 px-2 text-right">{mVals.roc_auc.toFixed(4)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Ablation Study Table */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
              <h3 className="font-extrabold text-sm text-slate-900 mb-3 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-teal-600" /> Systematic Ablation Study (Macro-F1)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                      <th className="py-2.5 px-3">Component Variation</th>
                      <th className="py-2.5 px-3 text-right">Macro F1 Score</th>
                      <th className="py-2.5 px-3 text-right">Contribution Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {Object.entries(metrics.ablation_study || {}).map(([vName, score]) => {
                      const isFull = vName.includes('Full');
                      return (
                        <tr key={vName} className={isFull ? 'bg-teal-50/70 font-bold text-teal-950' : 'hover:bg-slate-50'}>
                          <td className="py-2 px-3 font-sans">{vName}</td>
                          <td className="py-2 px-3 text-right">{score.toFixed(4)}</td>
                          <td className="py-2 px-3 text-right text-teal-700 font-semibold font-sans text-[11px]">
                            {isFull ? 'Full Architecture' : 'Ablation Sub-component'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Interactive Live SMILES Symmetric Pair Inference */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="font-extrabold text-base text-slate-900 mb-1 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-purple-600" /> Interactive Drug-Pair Inference Console
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Pass arbitrary canonical SMILES to test the symmetric pair encoder and evaluate calibrated category probabilities.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs mb-4">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Drug A Canonical SMILES:</label>
                <input
                  type="text"
                  value={drugASmiles}
                  onChange={(e) => setDrugASmiles(e.target.value)}
                  className="w-full p-2.5 font-mono text-[11px] bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-purple-600"
                />
              </div>
              <div>
                <label className="font-bold text-slate-700 block mb-1">Drug B Canonical SMILES:</label>
                <input
                  type="text"
                  value={drugBSmiles}
                  onChange={(e) => setDrugBSmiles(e.target.value)}
                  className="w-full p-2.5 font-mono text-[11px] bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-purple-600"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handlePredict}
                disabled={predicting}
                className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-2 shadow-sm"
              >
                {predicting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Cpu className="w-4 h-4" />}
                Execute Symmetric GNN Prediction
              </button>
            </div>

            {predictResult && (
              <div className="mt-5 p-4 rounded-xl bg-purple-50/80 border border-purple-200 text-xs">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-purple-950 text-sm">
                    Predicted Category: <span className="font-extrabold text-purple-800">{predictResult.predicted_category}</span>
                  </span>
                  <span className="font-mono font-bold text-purple-900 bg-purple-200/60 px-2.5 py-0.5 rounded">
                    Confidence: {(predictResult.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-[11px] text-purple-800 mb-2">
                  Topological Fingerprint Overlap: <span className="font-mono font-bold">{predictResult.molecular_structural_similarity}</span> •
                  Model Version: <span className="font-mono">{predictResult.model_version}</span>
                </p>
                <div className="grid grid-cols-4 gap-2 pt-2 border-t border-purple-200 text-[10px] font-mono text-center">
                  {Object.entries(predictResult.probabilities || {}).map(([cat, prob]) => (
                    <div key={cat} className="bg-white/80 p-1.5 rounded">
                      <span className="block text-slate-500 font-sans">{cat}</span>
                      <span className="font-bold text-slate-900">{(prob * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-16 text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
          No metrics available. Please run the training pipeline.
        </div>
      )}
    </div>
  );
}
