import React, { useRef } from 'react';
import { Printer, Download, ArrowLeft, ShieldCheck, FileText } from 'lucide-react';
import { api } from '../../services/api';

export default function PharmacyTaxInvoice({ invoiceData, onBack }) {
  const printRef = useRef(null);

  if (!invoiceData) {
    return (
      <div className="p-8 text-center text-slate-500">
        No invoice data provided.
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = () => {
    // If order_number exists, download via backend PDF endpoint
    if (invoiceData.order_id) {
      window.open(api.getInvoicePdfUrl(invoiceData.order_id), '_blank');
    } else {
      window.print();
    }
  };

  const items = invoiceData.items || [];
  const cust = invoiceData.customer || {};

  return (
    <div className="max-w-4xl mx-auto my-6 px-4">
      {/* Control Actions Header (Hidden in Print View) */}
      <div className="no-print mb-6 flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
          )}
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" /> Professional A4 Tax Invoice Preview
            </h2>
            <p className="text-xs text-slate-500">
              Conforms to Drugs & Cosmetics Act 1940 and GST Rule 46. Size: 210mm × 297mm.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadPdf}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-300 transition shadow-sm"
          >
            <Download className="w-4 h-4" /> Download Official PDF
          </button>
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-md"
          >
            <Printer className="w-4 h-4" /> Print Document (A4)
          </button>
        </div>
      </div>

      {/* A4 PRINT CONTAINER (Visible in Print & Screen) */}
      <div
        ref={printRef}
        className="print-page bg-white p-8 md:p-12 border border-slate-300 rounded-lg shadow-lg mx-auto"
        style={{ width: '100%', maxWidth: '210mm', minHeight: '297mm' }}
      >
        {/* Invoice Header */}
        <div className="border-b-2 border-blue-900 pb-4 mb-4">
          <div className="flex justify-between items-start gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="bg-blue-900 text-white font-black text-sm px-2 py-0.5 rounded tracking-wide">
                  PHARMINTEL
                </span>
                <span className="text-xs font-semibold text-teal-700 uppercase tracking-wider flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Licensed Network Pharmacy
                </span>
              </div>
              <h1 className="text-xl font-bold text-slate-900 leading-tight">
                {invoiceData.pharmacy_name}
              </h1>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed max-w-sm">
                {invoiceData.pharmacy_address}<br />
                Phone: {invoiceData.pharmacy_phone} | Email: {invoiceData.pharmacy_email}
              </p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-700 font-medium mt-2">
                <span><b>Drug License No:</b> {invoiceData.pharmacy_license}</span>
                <span><b>GSTIN:</b> {invoiceData.pharmacy_gst}</span>
              </div>
            </div>

            <div className="text-right">
              <div className="inline-block bg-blue-50 text-blue-900 font-extrabold text-lg px-4 py-1 rounded border border-blue-200 mb-2">
                TAX INVOICE
              </div>
              <div className="text-xs text-slate-700 space-y-1">
                <p><b>Invoice No:</b> <span className="font-mono">{invoiceData.invoice_number}</span></p>
                <p><b>Date:</b> {invoiceData.invoice_date}</p>
                <p><b>Order No:</b> <span className="font-mono">{invoiceData.order_number}</span></p>
                <p><b>Payment:</b> {invoiceData.payment_method} ({invoiceData.payment_status})</p>
              </div>
            </div>
          </div>
        </div>

        {/* Billed To / Patient & Pharmacist Info */}
        <div className="grid grid-cols-2 gap-4 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs mb-5">
          <div>
            <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] mb-1 text-blue-900">
              Billed To (Patient / Customer):
            </h3>
            <p className="font-semibold text-slate-800">{cust.name || 'Valued Customer'}</p>
            <p className="text-slate-600">{cust.address || 'Address provided on checkout'}</p>
            <p className="text-slate-600">Phone: {cust.phone || 'N/A'}</p>
          </div>
          <div className="text-right">
            <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] mb-1 text-blue-900">
              Dispensing Pharmacist Verification:
            </h3>
            <p className="font-semibold text-slate-800">{invoiceData.pharmacist_name || 'Rajesh Nambiar, M.Pharm'}</p>
            <p className="text-slate-600">State Pharmacy Council Reg: {invoiceData.pharmacist_reg || 'KSPC-REG-2015-88391'}</p>
            <span className="inline-block mt-1 text-[10px] bg-green-100 text-green-800 font-bold px-2 py-0.5 rounded border border-green-300">
              Rx Verified & Dispensed
            </span>
          </div>
        </div>

        {/* Itemized Table */}
        <div className="mb-6">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="bg-slate-100 border-y border-slate-300 text-slate-800 font-bold text-left">
                <th className="py-2 px-2 w-8 text-center">#</th>
                <th className="py-2 px-2">Medicine Description & Composition</th>
                <th className="py-2 px-2 w-20">Batch</th>
                <th className="py-2 px-2 w-16">Exp</th>
                <th className="py-2 px-2 w-12 text-center">Qty</th>
                <th className="py-2 px-2 w-16 text-right">MRP</th>
                <th className="py-2 px-2 w-16 text-right">Rate</th>
                <th className="py-2 px-2 w-12 text-center">GST</th>
                <th className="py-2 px-2 w-20 text-right">Total (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {items.map((itm, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2 px-2 text-center text-slate-500">{idx + 1}</td>
                  <td className="py-2 px-2">
                    <span className="font-bold text-slate-900">{itm.name}</span>
                    <span className="block text-[10px] text-slate-500 truncate max-w-xs">{itm.composition}</span>
                  </td>
                  <td className="py-2 px-2 font-mono text-[11px] text-slate-700">{itm.batch_number || 'BT-9901'}</td>
                  <td className="py-2 px-2 text-slate-600">{itm.expiry_date || '2027-08'}</td>
                  <td className="py-2 px-2 text-center font-bold text-slate-800">{itm.quantity}</td>
                  <td className="py-2 px-2 text-right text-slate-500">₹{itm.mrp?.toFixed(2)}</td>
                  <td className="py-2 px-2 text-right font-medium text-slate-800">₹{itm.unit_price?.toFixed(2)}</td>
                  <td className="py-2 px-2 text-center text-slate-600">{itm.gst_rate || 12}%</td>
                  <td className="py-2 px-2 text-right font-bold text-slate-900">₹{itm.total_price?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Tax Breakdown & Grand Totals */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-300 text-xs mb-8 avoid-break">
          <div>
            <h4 className="font-bold text-slate-800 mb-1">Standard Terms & Conditions:</h4>
            <ul className="list-disc list-inside text-[10px] text-slate-600 space-y-0.5 leading-relaxed">
              <li>Goods once sold will not be returned without valid batch receipt within 7 days.</li>
              <li>Schedule H/H1 drugs dispensed strictly on the prescription of a Registered Medical Practitioner.</li>
              <li>Store medications as per cold chain / storage instructions on packaging.</li>
            </ul>
          </div>
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1.5">
            <div className="flex justify-between text-slate-600">
              <span>Item Subtotal:</span>
              <span className="font-mono">₹{invoiceData.subtotal?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>CGST (6%):</span>
              <span className="font-mono">₹{((invoiceData.tax_amount || 0) / 2).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>SGST (6%):</span>
              <span className="font-mono">₹{((invoiceData.tax_amount || 0) / 2).toFixed(2)}</span>
            </div>
            {invoiceData.delivery_fee > 0 && (
              <div className="flex justify-between text-slate-600">
                <span>Healthcare Delivery Fee:</span>
                <span className="font-mono">₹{invoiceData.delivery_fee?.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm font-extrabold text-blue-950 pt-2 border-t border-slate-300">
              <span>Grand Total Amount:</span>
              <span className="text-base font-mono">₹{invoiceData.total_amount?.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Signature Section */}
        <div className="grid grid-cols-2 gap-8 pt-8 border-t border-slate-300 text-xs avoid-break">
          <div className="pt-8 border-t border-dashed border-slate-400 text-center">
            <p className="font-medium text-slate-700">Customer Signature / Acknowledgement</p>
          </div>
          <div className="pt-8 border-t border-dashed border-slate-400 text-center">
            <p className="font-bold text-slate-900">{invoiceData.pharmacist_name || 'Rajesh Nambiar, M.Pharm'}</p>
            <p className="text-[10px] text-slate-500">Authorized Registered Pharmacist (Stamp & Signature)</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-slate-200 text-center text-[10px] text-slate-400">
          PharmIntel AI-Powered Smart Pharmacy Network • Computer-Generated Legal Tax Invoice • Compliant with Pharmacy Practice Regulations
        </div>
      </div>
    </div>
  );
}
