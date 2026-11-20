import React, { useState, useEffect } from 'react';
import {
  CreditCard, Truck, FileText, CheckCircle, AlertTriangle,
  ArrowLeft, ShieldCheck, RefreshCw, Upload
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Checkout({ onNavigate }) {
  const { cart, clearCart, user } = useAuth();
  const [pharmacies, setPharmacies] = useState([]);
  const [selectedPharmacyId, setSelectedPharmacyId] = useState(1);
  const [deliveryType, setDeliveryType] = useState('Home Delivery');
  const [paymentMethod, setPaymentMethod] = useState('UPI / Online');
  const [address, setAddress] = useState(user?.profile?.address || 'Flat 402, Green Glen Layout, Bellandur, Bengaluru');
  const [phone, setPhone] = useState(user?.phone || '+91 98400 99001');
  const [specialNotes, setSpecialNotes] = useState('');
  
  // Prescriptions
  const [myPrescriptions, setMyPrescriptions] = useState([]);
  const [selectedRxId, setSelectedRxId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const hasRxItems = cart.some((itm) => itm.requires_prescription);

  useEffect(() => {
    async function loadData() {
      try {
        const pharms = await api.getPharmacies();
        setPharmacies(pharms);
        if (pharms.length > 0) setSelectedPharmacyId(pharms[0].id);

        const rxs = await api.getMyPrescriptions();
        setMyPrescriptions(rxs);
        if (rxs.length > 0) setSelectedRxId(rxs[0].id);
      } catch (e) {
        console.error(e);
      }
    }
    loadData();
  }, []);

  const subtotal = cart.reduce((sum, itm) => sum + itm.base_mrp * itm.quantity, 0);
  const tax = subtotal * 0.12;
  const deliveryFee = deliveryType === 'Home Delivery' ? (subtotal > 500 ? 0 : 40) : 0;
  const total = subtotal + tax + deliveryFee;

  const handlePlaceOrder = async () => {
    if (cart.length === 0) return;
    if (hasRxItems && !selectedRxId) {
      setError("A verified prescription must be attached for Schedule H / Rx medications.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const orderData = {
        pharmacy_id: selectedPharmacyId,
        items: cart.map((i) => ({ medicine_id: i.id, quantity: i.quantity })),
        prescription_id: hasRxItems ? selectedRxId : undefined,
        delivery_address: address,
        contact_phone: phone,
        delivery_type: deliveryType,
        payment_method: paymentMethod,
        special_instructions: specialNotes || undefined,
      };

      const res = await api.createOrder(orderData);
      clearCart();
      onNavigate('tracking', res.order_id);
    } catch (e) {
      setError(e.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button
        onClick={() => onNavigate('cart')}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Cart
      </button>

      <h1 className="text-2xl font-black text-slate-900 mb-6">
        Secure Order Checkout & Verification
      </h1>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-800 text-xs rounded-xl border border-red-200 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Checkout Form */}
        <div className="md:col-span-2 space-y-6">
          {/* Pharmacy Selection */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm mb-3">1. Select Fulfilling Pharmacy</h3>
            <select
              value={selectedPharmacyId}
              onChange={(e) => setSelectedPharmacyId(Number(e.target.value))}
              className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:border-blue-500"
            >
              {pharmacies.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.address} ({p.distance_km || '1.2'} km)
                </option>
              ))}
            </select>
          </div>

          {/* Prescription Attachment (Mandatory for Rx items) */}
          <div className={`p-5 rounded-xl border shadow-xs ${
            hasRxItems ? 'bg-amber-50/50 border-amber-300' : 'bg-white border-slate-200'
          }`}>
            <h3 className="font-bold text-slate-900 text-sm mb-1 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" /> 2. Attach Doctor's Prescription
              </span>
              {hasRxItems && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-800">
                  MANDATORY FOR RX
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              Schedule H medicines strictly require verification by the dispensing pharmacist.
            </p>

            {myPrescriptions.length > 0 ? (
              <div className="space-y-2">
                {myPrescriptions.map((rx) => (
                  <label
                    key={rx.id}
                    className={`flex items-center justify-between p-3 rounded-lg border text-xs cursor-pointer transition ${
                      selectedRxId === rx.id
                        ? 'bg-blue-50 border-blue-500 text-blue-900 font-bold'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="rx_select"
                        checked={selectedRxId === rx.id}
                        onChange={() => setSelectedRxId(rx.id)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <div>
                        <span className="block font-semibold">RX-{rx.id}: {rx.file_name}</span>
                        <span className="text-[10px] opacity-75">
                          {rx.doctor_name || 'Dr. K. S. Sharma'} • Status: {rx.status}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {(rx.confidence * 100).toFixed(0)}% OCR
                    </span>
                  </label>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 bg-white rounded-lg border border-dashed border-slate-300 text-xs">
                <p className="text-slate-500 mb-2">No prescriptions uploaded to your profile yet.</p>
                <button
                  onClick={() => onNavigate('scanner')}
                  className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700 transition"
                >
                  Upload Prescription Now
                </button>
              </div>
            )}
          </div>

          {/* Delivery Details */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
            <h3 className="font-bold text-slate-900 text-sm">3. Delivery & Contact Details</h3>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Delivery Address:</label>
              <textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                rows={2}
                className="w-full p-2.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Contact Phone Number:</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full p-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Payment Method */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm mb-3">4. Payment Method</h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <label
                className={`p-3 rounded-lg border cursor-pointer font-bold flex items-center gap-2 transition ${
                  paymentMethod === 'UPI / Online'
                    ? 'bg-blue-50 border-blue-500 text-blue-900'
                    : 'bg-slate-50 border-slate-200 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="pay_method"
                  checked={paymentMethod === 'UPI / Online'}
                  onChange={() => setPaymentMethod('UPI / Online')}
                  className="w-4 h-4 text-blue-600"
                />
                UPI / Net Banking / Card
              </label>

              <label
                className={`p-3 rounded-lg border cursor-pointer font-bold flex items-center gap-2 transition ${
                  paymentMethod === 'Cash on Delivery'
                    ? 'bg-blue-50 border-blue-500 text-blue-900'
                    : 'bg-slate-50 border-slate-200 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="pay_method"
                  checked={paymentMethod === 'Cash on Delivery'}
                  onChange={() => setPaymentMethod('Cash on Delivery')}
                  className="w-4 h-4 text-blue-600"
                />
                Cash on Delivery (COD)
              </label>
            </div>
          </div>
        </div>

        {/* Order Summary Column */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm h-fit">
          <h3 className="font-bold text-slate-900 text-sm mb-4 pb-2 border-b border-slate-100">
            Payment Summary
          </h3>
          <div className="space-y-2 text-xs text-slate-600 mb-4">
            <div className="flex justify-between">
              <span>Items Total:</span>
              <span className="font-mono text-slate-900">₹{subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>GST (12%):</span>
              <span className="font-mono text-slate-900">₹{tax.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Delivery Fee:</span>
              <span className="font-mono text-slate-900">
                {deliveryFee === 0 ? <span className="text-green-600 font-bold">FREE</span> : `₹${deliveryFee.toFixed(2)}`}
              </span>
            </div>
            <div className="flex justify-between text-base font-extrabold text-blue-950 pt-3 border-t border-slate-200">
              <span>Total Payable:</span>
              <span className="font-mono">₹{total.toFixed(2)}</span>
            </div>
          </div>

          <button
            onClick={handlePlaceOrder}
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-md"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Verifying Order...
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" /> Place Verified Order
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
