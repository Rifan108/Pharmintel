import React, { useState, useEffect } from 'react';
import {
  Package, Printer, CheckCircle, Clock, Truck, RefreshCw,
  Eye, FileText, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import PharmacyTaxInvoice from '../components/print/PharmacyTaxInvoice';

export default function PharmacyOrderManagement() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  useEffect(() => {
    loadOrders();
  }, [statusFilter]);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await api.getPharmacyOrders(1, statusFilter || undefined);
      setOrders(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (orderId, newStatus) => {
    try {
      await api.updateOrderStatus(orderId, newStatus);
      loadOrders();
    } catch (e) {
      alert("Status update failed: " + e.message);
    }
  };

  const handleViewInvoice = async (orderId) => {
    try {
      const data = await api.getInvoicePrintData(orderId);
      data.order_id = orderId;
      setSelectedInvoice(data);
    } catch (e) {
      alert("Failed to load invoice: " + e.message);
    }
  };

  if (selectedInvoice) {
    return (
      <PharmacyTaxInvoice
        invoiceData={selectedInvoice}
        onBack={() => setSelectedInvoice(null)}
      />
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Package className="w-6 h-6 text-blue-600" /> Pharmacy Order Fulfillment & Dispensing
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Process verified orders, deduct batch inventory with audit logs, and print statutory A4 tax invoices.
          </p>
        </div>

        <div className="flex gap-2 text-xs">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="p-2 bg-white border border-slate-300 rounded-lg font-semibold text-slate-700"
          >
            <option value="">All Order Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Prescription Verification">Prescription Verification</option>
            <option value="Approved">Approved</option>
            <option value="Preparing">Preparing / Dispensing</option>
            <option value="Dispatched">Dispatched</option>
            <option value="Delivered">Delivered</option>
          </select>

          <button
            onClick={loadOrders}
            className="p-2 bg-white hover:bg-slate-50 text-slate-700 rounded-lg border border-slate-300"
          >
            <RefreshCw className="w-4 h-4 text-blue-600" />
          </button>
        </div>
      </div>

      {/* Orders List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="text-center py-16 text-slate-400 text-xs">
            Loading pharmacy orders...
          </div>
        ) : orders.length > 0 ? (
          <div className="divide-y divide-slate-100 text-xs">
            {orders.map((ord) => (
              <div key={ord.id} className="p-5 hover:bg-slate-50/60 transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-bold text-slate-900 text-sm">{ord.order_number}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      ord.status === 'Delivered' ? 'bg-green-100 text-green-800' :
                      ord.status === 'Prescription Verification' ? 'bg-amber-100 text-amber-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {ord.status}
                    </span>
                    {ord.prescription_id && (
                      <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono">
                        Rx Attached (RX-{ord.prescription_id})
                      </span>
                    )}
                  </div>
                  <p className="text-slate-700 font-semibold">{ord.customer_name} • Phone: {ord.customer_phone}</p>
                  <p className="text-slate-500 text-[11px] truncate max-w-md">{ord.delivery_address}</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {ord.items_count} items • Total: <span className="font-bold text-slate-900 font-mono">₹{ord.total_amount.toFixed(2)}</span> ({ord.payment_method})
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
                  <button
                    onClick={() => handleViewInvoice(ord.id)}
                    className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg font-bold border border-slate-300 transition flex items-center gap-1.5"
                  >
                    <Printer className="w-3.5 h-3.5" /> A4 Tax Invoice
                  </button>

                  {ord.status === 'Approved' && (
                    <button
                      onClick={() => handleUpdateStatus(ord.id, 'Preparing')}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-xs transition"
                    >
                      Deduct Stock & Pack
                    </button>
                  )}

                  {ord.status === 'Preparing' && (
                    <button
                      onClick={() => handleUpdateStatus(ord.id, 'Dispatched')}
                      className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-bold shadow-xs transition"
                    >
                      Dispatch to Courier
                    </button>
                  )}

                  {ord.status === 'Dispatched' && (
                    <button
                      onClick={() => handleUpdateStatus(ord.id, 'Delivered')}
                      className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold shadow-xs transition"
                    >
                      Confirm Delivered
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-slate-400 text-xs">
            No orders found matching the filter.
          </div>
        )}
      </div>
    </div>
  );
}
