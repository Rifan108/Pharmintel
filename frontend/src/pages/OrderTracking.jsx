import React, { useState, useEffect } from 'react';
import {
  Truck, CheckCircle, Clock, AlertTriangle, FileText,
  Printer, Download, ArrowLeft, RefreshCw, MapPin, Phone
} from 'lucide-react';
import { api } from '../services/api';
import PharmacyTaxInvoice from '../components/print/PharmacyTaxInvoice';

export default function OrderTracking({ orderId, onNavigate }) {
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewInvoice, setViewInvoice] = useState(false);
  const [invoicePrintData, setInvoicePrintData] = useState(null);

  useEffect(() => {
    async function loadOrders() {
      try {
        const myOrders = await api.getMyOrders();
        setOrders(myOrders);
        if (orderId) {
          const found = myOrders.find((o) => o.id === orderId);
          setSelectedOrder(found || myOrders[0]);
        } else if (myOrders.length > 0) {
          setSelectedOrder(myOrders[0]);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadOrders();
  }, [orderId]);

  const handleOpenInvoice = async (ord) => {
    try {
      const data = await api.getInvoicePrintData(ord.id);
      data.order_id = ord.id;
      setInvoicePrintData(data);
      setViewInvoice(true);
    } catch (e) {
      alert("Could not load invoice data: " + e.message);
    }
  };

  if (viewInvoice && invoicePrintData) {
    return (
      <PharmacyTaxInvoice
        invoiceData={invoicePrintData}
        onBack={() => setViewInvoice(false)}
      />
    );
  }

  const stages = [
    { label: 'Order Placed', status: 'Pending' },
    { label: 'Rx Verification', status: 'Prescription Verification' },
    { label: 'Pharmacist Approved', status: 'Approved' },
    { label: 'Dispensing & Packing', status: 'Preparing' },
    { label: 'Out for Delivery', status: 'Dispatched' },
    { label: 'Delivered', status: 'Delivered' },
  ];

  const getStageIndex = (currentStatus) => {
    const map = {
      'Pending': 0,
      'Prescription Verification': 1,
      'Approved': 2,
      'Preparing': 3,
      'Ready for Pickup': 3,
      'Dispatched': 4,
      'Delivered': 5,
    };
    return map[currentStatus] !== undefined ? map[currentStatus] : 0;
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Truck className="w-6 h-6 text-blue-600" /> Medicine Delivery Tracking
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time pharmacy fulfillment lifecycle and healthcare courier dispatch coordination.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400 text-xs">
          Loading order tracking status...
        </div>
      ) : selectedOrder ? (
        <div className="space-y-6">
          {/* Main Tracking Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4 pb-6 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-800 font-mono">
                  Order Ref: {selectedOrder.order_number}
                </span>
                <h2 className="text-xl font-bold text-slate-900 mt-2">
                  Fulfilling Pharmacy: {selectedOrder.pharmacy_name}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Placed on {new Date(selectedOrder.created_at).toLocaleDateString()} • {selectedOrder.delivery_type}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => handleOpenInvoice(selectedOrder)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-lg border border-slate-300 transition flex items-center gap-1.5"
                >
                  <Printer className="w-3.5 h-3.5" /> View A4 Tax Invoice
                </button>
                <a
                  href={api.getInvoicePdfUrl(selectedOrder.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" /> Download PDF
                </a>
              </div>
            </div>

            {/* Lifecycle Stepper */}
            <div className="py-8">
              <div className="relative flex justify-between">
                {/* Connecting Line */}
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-slate-200 -translate-y-1/2 z-0"></div>
                <div
                  className="absolute top-1/2 left-0 h-1 bg-teal-600 -translate-y-1/2 z-0 transition-all duration-500"
                  style={{ width: `${(getStageIndex(selectedOrder.status) / (stages.length - 1)) * 100}%` }}
                ></div>

                {stages.map((stg, i) => {
                  const currentIdx = getStageIndex(selectedOrder.status);
                  const isDone = i <= currentIdx;
                  const isCurrent = i === currentIdx;

                  return (
                    <div key={i} className="relative z-10 flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition shadow-xs ${
                        isDone
                          ? 'bg-teal-600 text-white'
                          : 'bg-white text-slate-400 border-2 border-slate-300'
                      } ${isCurrent ? 'ring-4 ring-teal-100' : ''}`}>
                        {isDone ? <CheckCircle className="w-4 h-4" /> : i + 1}
                      </div>
                      <span className={`text-[11px] font-semibold mt-2 text-center max-w-[80px] ${
                        isCurrent ? 'text-teal-900 font-bold' : isDone ? 'text-slate-800' : 'text-slate-400'
                      }`}>
                        {stg.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Delivery Courier Details */}
            {selectedOrder.delivery && (
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Logistics Partner</span>
                  <span className="font-bold text-slate-900">{selectedOrder.delivery.courier}</span>
                  <p className="text-[11px] font-mono text-blue-700 mt-0.5">AWB: {selectedOrder.delivery.tracking_number}</p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Assigned Delivery Partner</span>
                  <span className="font-bold text-slate-900">{selectedOrder.delivery.driver_name}</span>
                  <p className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                    <Phone className="w-3 h-3" /> {selectedOrder.delivery.driver_phone}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Current Delivery Status</span>
                  <span className="inline-block px-2.5 py-0.5 bg-green-100 text-green-800 font-bold rounded mt-0.5">
                    {selectedOrder.delivery.current_status}
                  </span>
                  <p className="text-[10px] text-slate-500 mt-1">Est. Time: {selectedOrder.delivery.estimated_time}</p>
                </div>
              </div>
            )}
          </div>

          {/* Itemized Order Details */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm mb-4">Dispensed Prescription Items</h3>
            <div className="divide-y divide-slate-100 text-xs">
              {selectedOrder.items.map((itm) => (
                <div key={itm.id} className="py-2.5 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-900">{itm.medicine_name}</span>
                    <span className="text-slate-500 ml-2">({itm.strength} • {itm.dosage_form})</span>
                    <span className="text-slate-400 ml-2">× {itm.quantity}</span>
                  </div>
                  <span className="font-mono font-bold text-slate-900">
                    ₹{itm.total_price.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
            <div className="pt-3 border-t border-slate-200 flex justify-between font-extrabold text-sm text-slate-900 mt-2">
              <span>Total Paid:</span>
              <span className="font-mono text-blue-900">₹{selectedOrder.total_amount.toFixed(2)}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-16 text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
          No orders found for this account.
        </div>
      )}
    </div>
  );
}
