import React, { useState, useEffect } from 'react';
import {
  Pill, AlertTriangle, Plus, Search, ShieldAlert, CheckCircle,
  Clock, RefreshCw, Archive, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';

export default function PharmacyInventory() {
  const [pharmacyId, setPharmacyId] = useState(1);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [medicines, setMedicines] = useState([]);
  const [selectedMedId, setSelectedMedId] = useState(1);
  const [batchNumber, setBatchNumber] = useState('');
  const [expiryDate, setExpiryDate] = useState('2027-12-31');
  const [quantity, setQuantity] = useState(50);
  const [mrp, setMrp] = useState(50);

  useEffect(() => {
    loadInventory();
    loadMedicines();
  }, [pharmacyId]);

  const loadInventory = async () => {
    setLoading(true);
    try {
      const data = await api.getInventory(pharmacyId);
      setInventory(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadMedicines = async () => {
    try {
      const res = await api.searchMedicines({ limit: 50 });
      setMedicines(res.items || []);
      if (res.items?.length > 0) {
        setSelectedMedId(res.items[0].id);
        setMrp(res.items[0].base_mrp);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddBatch = async (e) => {
    e.preventDefault();
    try {
      await api.addBatch(pharmacyId, selectedMedId, {
        batch_number: batchNumber || `BT-${Date.now().toString().slice(-6)}`,
        expiry_date: expiryDate,
        purchase_price: roundPrice(mrp * 0.72),
        selling_price: mrp,
        mrp: mrp,
        quantity: Number(quantity),
      });
      setShowAddModal(false);
      setBatchNumber('');
      loadInventory();
      alert("Batch successfully added to inventory!");
    } catch (err) {
      alert("Failed to add batch: " + err.message);
    }
  };

  const roundPrice = (val) => Math.round(val * 100) / 100;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Pill className="w-6 h-6 text-blue-600" /> Pharmacy Inventory & Batch Tracker
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit-grade batch management, expiry date surveillance, and automated low-stock warnings.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Add Inward Batch (Stock-In)
        </button>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 text-xs">
          <span className="font-bold text-slate-700">
            Total Inventory Items: {inventory.length}
          </span>
          <button
            onClick={loadInventory}
            className="text-slate-500 hover:text-blue-600 flex items-center gap-1 font-semibold"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Stock
          </button>
        </div>

        {loading ? (
          <div className="text-center py-16 text-slate-400 text-xs">
            Loading pharmacy batches...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100/75 border-b border-slate-200 text-slate-700 font-bold">
                  <th className="py-3 px-4">Medicine Code</th>
                  <th className="py-3 px-4">Brand & Generic Name</th>
                  <th className="py-3 px-4">Form & Strength</th>
                  <th className="py-3 px-4 text-center">Current Stock</th>
                  <th className="py-3 px-4 text-center">Batch Status</th>
                  <th className="py-3 px-4 text-right">Base MRP</th>
                  <th className="py-3 px-4 text-center">Stock Alert</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {inventory.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-4 font-mono text-[11px] font-bold text-slate-600">
                      {item.medicine_code}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-900 block">{item.medicine_name}</span>
                      <span className="text-slate-400 text-[11px]">{item.generic_name}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {item.strength} • {item.dosage_form}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-slate-900">
                      {item.stock_quantity} units
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="text-[10px] text-slate-500 font-mono">
                        {item.batches?.length || 0} Batches Registered
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-slate-800">
                      ₹{item.base_mrp.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.is_low_stock ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                          <AlertTriangle className="w-3 h-3" /> Low Stock
                        </span>
                      ) : item.has_near_expiry_batches ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-800">
                          <Clock className="w-3 h-3" /> Expiring Soon
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-green-100 text-green-800">
                          <CheckCircle className="w-3 h-3" /> Optimal
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Batch Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="font-extrabold text-slate-900 text-base mb-1">
              Add New Medicine Batch (Inward Stock)
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Enter supplier batch number, statutory expiry date, and verified quantity.
            </p>

            <form onSubmit={handleAddBatch} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Select Medicine:</label>
                <select
                  value={selectedMedId}
                  onChange={(e) => {
                    const id = Number(e.target.value);
                    setSelectedMedId(id);
                    const found = medicines.find((m) => m.id === id);
                    if (found) setMrp(found.base_mrp);
                  }}
                  className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg"
                >
                  {medicines.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.brand_name} ({m.generic_name} • {m.strength})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Batch Number:</label>
                <input
                  type="text"
                  placeholder="e.g. BT-2026-9041"
                  value={batchNumber}
                  onChange={(e) => setBatchNumber(e.target.value)}
                  className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Expiry Date:</label>
                  <input
                    type="date"
                    value={expiryDate}
                    onChange={(e) => setExpiryDate(e.target.value)}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Units Quantity:</label>
                  <input
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Selling MRP (₹):</label>
                <input
                  type="number"
                  step="0.01"
                  value={mrp}
                  onChange={(e) => setMrp(Number(e.target.value))}
                  className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg font-mono"
                />
              </div>

              <div className="pt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-sm"
                >
                  Save Batch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
