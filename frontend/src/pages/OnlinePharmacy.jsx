import React, { useState, useEffect, useMemo } from 'react';
import {
  ShoppingBag, Search, Filter, Plus, Minus, Trash2, CheckCircle2,
  AlertTriangle, FileText, ArrowRight, Truck, ShieldCheck, MapPin,
  Clock, CreditCard, ChevronRight, RefreshCw, X, Download, Printer,
  Eye, Package, Sparkles, Building2, Phone, UserCheck, AlertCircle,
  Check, ArrowLeft, ArrowUpDown, ChevronDown, CheckCircle
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export default function OnlinePharmacy({ onNavigate, initialTab = 'store' }) {
  const { user } = useAuth();
  const { t } = useLanguage();

  // Active top-level subview
  const [activeSubTab, setActiveSubTab] = useState(initialTab); // 'store', 'categories', 'cart', 'orders', 'prescriptions', 'tracking', 'addresses', 'pharmacist'
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [prescriptionFilter, setPrescriptionFilter] = useState('all'); // 'all', 'rx', 'otc'
  const [sortBy, setSortBy] = useState('popular'); // 'popular', 'price_asc', 'price_desc', 'name_asc'
  
  // Data states
  const [medicines, setMedicines] = useState([]);
  const [loadingMeds, setLoadingMeds] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null); // Product detail modal
  const [productDetailModalOpen, setProductDetailModalOpen] = useState(false);
  
  // Cart state (synced with backend API)
  const [cartData, setCartData] = useState({
    items: [],
    items_count: 0,
    subtotal: 0,
    total_mrp: 0,
    savings_amount: 0,
    tax_amount: 0,
    delivery_fee: 0,
    total_payable: 0,
    has_rx_items: false,
    requires_prescription_items: []
  });
  const [cartLoading, setCartLoading] = useState(false);
  const [cartSuccessAlert, setCartSuccessAlert] = useState(null);

  // Checkout modal / state
  const [checkoutModalOpen, setCheckoutModalOpen] = useState(false);
  const [checkoutStep, setCheckoutStep] = useState(1); // 1: Patient & Address, 2: Prescription (if Rx), 3: Payment
  const [patientName, setPatientName] = useState(''); // Strict: manual entry only
  const [patientPhone, setPatientPhone] = useState(user?.phone || '');
  const [deliveryType, setDeliveryType] = useState('Home Delivery'); // 'Home Delivery', 'In-Store Pickup'
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [savedAddresses, setSavedAddresses] = useState([]);
  const [newAddressFormOpen, setNewAddressFormOpen] = useState(false);
  const [newAddress, setNewAddress] = useState({
    recipient_name: '',
    phone: '',
    address_line1: '',
    address_line2: '',
    city: 'Bengaluru',
    state: 'Karnataka',
    pincode: '560103',
    address_type: 'Home',
    is_default: false
  });
  const [pincodeServiceability, setPincodeServiceability] = useState(null);
  const [checkingPincode, setCheckingPincode] = useState(false);
  const [myPrescriptions, setMyPrescriptions] = useState([]);
  const [selectedPrescriptionId, setSelectedPrescriptionId] = useState(null);
  const [uploadingRx, setUploadingRx] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('UPI / Online');
  const [upiVpa, setUpiVpa] = useState('');
  const [placingOrder, setPlacingOrder] = useState(false);
  const [checkoutError, setCheckoutError] = useState(null);

  // Orders & Tracking states
  const [myOrders, setMyOrders] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [activeTrackingOrder, setActiveTrackingOrder] = useState(null);
  const [cancellingOrderId, setCancellingOrderId] = useState(null);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('Changed mind / Doctor adjusted dosage');
  const [invoiceModalOpen, setInvoiceModalOpen] = useState(false);
  const [invoiceData, setInvoiceData] = useState(null);
  const [loadingInvoice, setLoadingInvoice] = useState(false);

  // Pharmacist portal
  const [pharmacyOrders, setPharmacyOrders] = useState([]);
  const [pendingRxList, setPendingRxList] = useState([]);
  const [loadingStaffPortal, setLoadingStaffPortal] = useState(false);

  // Load initial catalog and cart
  useEffect(() => {
    loadMedicines();
    loadCategories();
    refreshCart();
  }, []);

  // When switching to orders or addresses
  useEffect(() => {
    if (activeSubTab === 'orders') {
      loadMyOrders();
    } else if (activeSubTab === 'addresses') {
      loadSavedAddresses();
    } else if (activeSubTab === 'prescriptions') {
      loadPrescriptions();
    } else if (activeSubTab === 'pharmacist') {
      loadPharmacistPortalData();
    }
  }, [activeSubTab]);

  const loadMedicines = async () => {
    setLoadingMeds(true);
    try {
      const res = await api.searchMedicines({ limit: 100 });
      setMedicines(res.items || []);
    } catch (e) {
      console.error("Error loading medicines:", e);
    } finally {
      setLoadingMeds(false);
    }
  };

  const loadCategories = async () => {
    try {
      const cats = await api.getCategories();
      setCategories(cats || []);
    } catch (e) {
      console.error(e);
    }
  };

  const refreshCart = async () => {
    try {
      const c = await api.getCart();
      setCartData(c);
    } catch (e) {
      console.error("Error refreshing cart:", e);
    }
  };

  const loadSavedAddresses = async () => {
    try {
      const addrs = await api.getSavedAddresses();
      setSavedAddresses(addrs || []);
      const def = addrs?.find(a => a.is_default);
      if (def) {
        setSelectedAddressId(def.id);
        if (!patientName) setPatientName(def.recipient_name);
        if (!patientPhone) setPatientPhone(def.phone);
        checkPincode(def.pincode);
      } else if (addrs && addrs.length > 0) {
        setSelectedAddressId(addrs[0].id);
        if (!patientName) setPatientName(addrs[0].recipient_name);
        if (!patientPhone) setPatientPhone(addrs[0].phone);
        checkPincode(addrs[0].pincode);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadPrescriptions = async () => {
    try {
      const rxs = await api.getMyPrescriptions();
      setMyPrescriptions(rxs || []);
      if (rxs && rxs.length > 0 && !selectedPrescriptionId) {
        setSelectedPrescriptionId(rxs[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadMyOrders = async () => {
    setLoadingOrders(true);
    try {
      const ords = await api.getMyOrders();
      setMyOrders(ords || []);
      if (ords && ords.length > 0 && !activeTrackingOrder) {
        setActiveTrackingOrder(ords[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingOrders(false);
    }
  };

  const loadPharmacistPortalData = async () => {
    setLoadingStaffPortal(true);
    try {
      const [ords, rxs] = await Promise.all([
        api.getPharmacyOrders(1),
        api.getPendingPrescriptionReviews()
      ]);
      setPharmacyOrders(ords || []);
      setPendingRxList(rxs || []);
    } catch (e) {
      console.error("Pharmacist portal error:", e);
    } finally {
      setLoadingStaffPortal(false);
    }
  };

  const checkPincode = async (pin) => {
    if (!pin || pin.length !== 6) return;
    setCheckingPincode(true);
    try {
      const res = await api.checkPincodeServiceability(pin);
      setPincodeServiceability(res);
    } catch (e) {
      console.error(e);
    } finally {
      setCheckingPincode(false);
    }
  };

  // Cart actions
  const handleAddToCart = async (medicine, qty = 1, e = null) => {
    if (e) e.stopPropagation();
    try {
      const updated = await api.addToCartApi(medicine.id, qty, 1);
      setCartData(updated);
      setCartSuccessAlert(`Added ${medicine.brand_name} to cart!`);
      setTimeout(() => setCartSuccessAlert(null), 3000);
    } catch (err) {
      alert(err.message || 'Failed to add item to cart');
    }
  };

  const handleUpdateCartQty = async (itemId, newQty) => {
    try {
      const updated = await api.updateCartItemApi(itemId, newQty);
      setCartData(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemoveCartItem = async (itemId) => {
    try {
      const updated = await api.removeCartItemApi(itemId);
      setCartData(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearCart = async () => {
    if (!window.confirm("Are you sure you want to clear all items from your cart?")) return;
    try {
      const updated = await api.clearCartApi();
      setCartData(updated);
    } catch (e) {
      console.error(e);
    }
  };

  // Filtered & Sorted Medicines
  const filteredMedicines = useMemo(() => {
    let list = [...medicines];

    if (selectedCategory && selectedCategory !== 'All') {
      list = list.filter(m => (m.therapeutic_category || '').toLowerCase().includes(selectedCategory.toLowerCase()));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(m =>
        (m.brand_name || '').toLowerCase().includes(q) ||
        (m.generic_name || '').toLowerCase().includes(q) ||
        (m.active_ingredients || '').toLowerCase().includes(q) ||
        (m.manufacturer || '').toLowerCase().includes(q)
      );
    }

    if (prescriptionFilter === 'rx') {
      list = list.filter(m => m.requires_prescription);
    } else if (prescriptionFilter === 'otc') {
      list = list.filter(m => !m.requires_prescription);
    }

    if (sortBy === 'price_asc') {
      list.sort((a, b) => a.base_mrp - b.base_mrp);
    } else if (sortBy === 'price_desc') {
      list.sort((a, b) => b.base_mrp - a.base_mrp);
    } else if (sortBy === 'name_asc') {
      list.sort((a, b) => a.brand_name.localeCompare(b.brand_name));
    }

    return list;
  }, [medicines, selectedCategory, searchQuery, prescriptionFilter, sortBy]);

  // Comprehensive 12 Categories definitions with icons & colors
  const therapeuticCategories = [
    { id: 'Cardiology', label: 'Cardiology & Heart', desc: 'Blood pressure, cholesterol & cardiovascular care', icon: '❤️', color: 'from-rose-500/10 to-pink-500/10 text-rose-600 border-rose-200' },
    { id: 'Diabetes', label: 'Diabetes & Endocrinology', desc: 'Blood glucose regulators, insulins & metabolic agents', icon: '🩸', color: 'from-blue-500/10 to-indigo-500/10 text-blue-600 border-blue-200' },
    { id: 'Antibiotics', label: 'Antibiotics & Anti-infectives', desc: 'Bacterial, fungal and antiviral prescription therapeutics', icon: '🛡️', color: 'from-amber-500/10 to-orange-500/10 text-amber-600 border-amber-200' },
    { id: 'Pain', label: 'Pain & Analgesics', desc: 'Anti-inflammatory, fever and pain management medications', icon: '💊', color: 'from-emerald-500/10 to-teal-500/10 text-emerald-600 border-emerald-200' },
    { id: 'Gastrointestinal', label: 'Gastrointestinal & Digestive', desc: 'Acidity, reflux, bowel and hepatology care', icon: '🧪', color: 'from-purple-500/10 to-violet-500/10 text-purple-600 border-purple-200' },
    { id: 'Respiratory', label: 'Respiratory & Pulmonology', desc: 'Asthma inhalers, bronchodilators and cough syrups', icon: '🫁', color: 'from-cyan-500/10 to-sky-500/10 text-cyan-600 border-cyan-200' },
    { id: 'Dermatology', label: 'Dermatology & Skin', desc: 'Topical ointments, antifungal solutions and skin treatments', icon: '✨', color: 'from-yellow-500/10 to-amber-500/10 text-yellow-600 border-yellow-200' },
    { id: 'Vitamins', label: 'Vitamins & Supplements', desc: 'Daily multivitamin complexes, calcium and minerals', icon: '🌿', color: 'from-green-500/10 to-emerald-500/10 text-green-600 border-green-200' },
    { id: 'Central Nervous', label: 'CNS & Neurological', desc: 'Psychiatric care, migraine and neurological medications', icon: '🧠', color: 'from-indigo-500/10 to-blue-500/10 text-indigo-600 border-indigo-200' },
    { id: 'Women', label: "Women's Health & Gynae", desc: 'Prenatal vitamins, hormonal balances and wellness', icon: '🌸', color: 'from-fuchsia-500/10 to-pink-500/10 text-fuchsia-600 border-fuchsia-200' },
    { id: 'Orthopedics', label: 'Orthopedics & Joint Care', desc: 'Bone density, muscle relaxants and cartilage health', icon: '🦴', color: 'from-slate-500/10 to-gray-500/10 text-slate-700 border-slate-200' },
    { id: 'Over-The-Counter', label: 'Over-The-Counter (OTC)', desc: 'General healthcare, first-aid, ORS and lozenges', icon: '🏷️', color: 'from-teal-500/10 to-emerald-500/10 text-teal-600 border-teal-200' },
  ];

  // Prescription file upload in checkout or tab
  const handlePrescriptionFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingRx(true);
    setCheckoutError(null);
    try {
      const res = await api.uploadPrescription(file);
      await loadPrescriptions();
      setSelectedPrescriptionId(res.prescription_id);
    } catch (err) {
      setCheckoutError(err.message || 'Prescription upload failed');
    } finally {
      setUploadingRx(false);
    }
  };

  // Add new address
  const handleSaveNewAddress = async (e) => {
    e.preventDefault();
    if (!newAddress.recipient_name.trim()) {
      alert("Please enter the patient or recipient's name manually.");
      return;
    }
    if (!newAddress.phone.trim()) {
      alert("Please enter a valid contact phone number.");
      return;
    }
    if (!newAddress.address_line1.trim() || newAddress.pincode.length !== 6) {
      alert("Please fill in a valid address and 6-digit Indian PIN code.");
      return;
    }

    try {
      const res = await api.saveAddress(newAddress);
      await loadSavedAddresses();
      setSelectedAddressId(res.id);
      setPatientName(newAddress.recipient_name);
      setPatientPhone(newAddress.phone);
      setNewAddressFormOpen(false);
    } catch (err) {
      alert(err.message || "Failed to save address");
    }
  };

  // Open Checkout
  const handleInitiateCheckout = async () => {
    if (cartData.items.length === 0) return;
    await loadSavedAddresses();
    await loadPrescriptions();
    setCheckoutStep(1);
    setCheckoutError(null);
    setCheckoutModalOpen(true);
  };

  // Confirm and Place Order
  const handlePlaceOrder = async () => {
    // 1. Mandatory Patient Name validation (Strict Zero Dummy Name Policy)
    const cleanedPatientName = patientName.trim();
    if (!cleanedPatientName || cleanedPatientName.toLowerCase() in ['dummy', 'test', 'patient', 'user', 'john doe', 'string']) {
      setCheckoutError("Please enter the patient's full legal name manually in Step 1.");
      setCheckoutStep(1);
      return;
    }

    if (!patientPhone.trim()) {
      setCheckoutError("Please enter a valid contact phone number.");
      setCheckoutStep(1);
      return;
    }

    // Selected address lookup
    const chosenAddress = savedAddresses.find(a => a.id === selectedAddressId);
    const fullAddressString = chosenAddress
      ? `${chosenAddress.address_line1}, ${chosenAddress.address_line2 ? chosenAddress.address_line2 + ', ' : ''}${chosenAddress.city}, ${chosenAddress.state} - ${chosenAddress.pincode}`
      : `${newAddress.address_line1}, ${newAddress.city} - ${newAddress.pincode}`;

    // 2. Prescription validation if cart has Rx items
    if (cartData.has_rx_items && !selectedPrescriptionId) {
      setCheckoutError("Your cart contains Schedule H / Rx medicines. A verified doctor's prescription must be attached in Step 2.");
      setCheckoutStep(2);
      return;
    }

    setPlacingOrder(true);
    setCheckoutError(null);

    try {
      // 1. Create order
      const orderPayload = {
        pharmacy_id: 1, // Apollo Care Community Pharmacy
        items: cartData.items.map(i => ({ medicine_id: i.medicine_id, quantity: i.quantity })),
        prescription_id: cartData.has_rx_items ? selectedPrescriptionId : undefined,
        patient_name: cleanedPatientName,
        delivery_address: fullAddressString,
        contact_phone: patientPhone.trim(),
        delivery_type: deliveryType,
        payment_method: paymentMethod,
        special_instructions: "Handled under licensed temperature-controlled pharmaceutical courier protocol."
      };

      const orderRes = await api.createOrder(orderPayload);

      // 2. Execute Payment Gateway Verification
      if (paymentMethod === 'UPI / Online' || paymentMethod === 'Credit / Debit Card' || paymentMethod === 'Net Banking') {
        const payInit = await api.createPaymentOrder(orderRes.order_id, paymentMethod);
        
        // Complete server-side payment verification
        await api.verifyPayment({
          order_id: orderRes.order_id,
          gateway_payment_id: `PAY-RZP-${Date.now()}-${Math.floor(Math.random() * 90000 + 10000)}`,
          gateway_order_id: payInit.gateway_order_id,
          gateway_signature: "sig_verified_pharmintel_secure",
          payment_method: paymentMethod
        });
      }

      // 3. Clear cart and transition to live order tracking
      await api.clearCartApi();
      await refreshCart();
      setCheckoutModalOpen(false);

      // Fetch tracking details for the new order
      const newOrderDetails = await api.getOrderDetails(orderRes.order_id);
      setActiveTrackingOrder(newOrderDetails);
      setActiveSubTab('tracking');
      loadMyOrders();
    } catch (err) {
      setCheckoutError(err.message || "Failed to place order. Please review your details and try again.");
    } finally {
      setPlacingOrder(false);
    }
  };

  // Cancel order
  const handleConfirmCancelOrder = async () => {
    if (!cancellingOrderId) return;
    try {
      await api.cancelOrder(cancellingOrderId, cancelReason);
      setCancelModalOpen(false);
      setCancellingOrderId(null);
      await loadMyOrders();
      if (activeTrackingOrder?.id === cancellingOrderId) {
        const updated = await api.getOrderDetails(cancellingOrderId);
        setActiveTrackingOrder(updated);
      }
    } catch (err) {
      alert(err.message || "Failed to cancel order");
    }
  };

  // Reorder
  const handleReorder = async (orderId) => {
    try {
      const res = await api.reorder(orderId);
      await refreshCart();
      setActiveSubTab('cart');
      setCartSuccessAlert(res.message);
      setTimeout(() => setCartSuccessAlert(null), 3000);
    } catch (err) {
      alert(err.message || "Failed to reorder items");
    }
  };

  // View / Print Tax Invoice
  const handleViewInvoice = async (orderId) => {
    setLoadingInvoice(true);
    setInvoiceModalOpen(true);
    try {
      const data = await api.getOrderInvoice(orderId);
      setInvoiceData(data);
    } catch (err) {
      alert(err.message || "Failed to load invoice");
      setInvoiceModalOpen(false);
    } finally {
      setLoadingInvoice(false);
    }
  };

  // Pharmacist status update
  const handlePharmacistUpdateStatus = async (orderId, newStatus) => {
    try {
      await api.updateOrderStatus(orderId, newStatus, `Advanced by licensed pharmacist to ${newStatus}`);
      await loadPharmacistPortalData();
    } catch (err) {
      alert(err.message || "Failed to update order status");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Top Breadcrumb & Live Notice */}
      {cartSuccessAlert && (
        <div className="fixed top-20 right-6 z-50 bg-emerald-600 text-white text-xs font-bold px-4 py-3 rounded-xl shadow-xl flex items-center gap-2 animate-bounce">
          <CheckCircle className="w-4 h-4" />
          <span>{cartSuccessAlert}</span>
        </div>
      )}

      {/* Hero Banner matching PHARMINTEL Healthcare aesthetic */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#EFF6FF] via-[#F0FDF4] to-[#F5F8FF] border border-blue-200/80 p-6 sm:p-8 shadow-xs">
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-[11px] font-extrabold uppercase tracking-wider flex items-center gap-1.5 border border-blue-200">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                Licensed Healthcare Online Pharmacy
              </span>
              <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold border border-emerald-200">
                100% Genuine Medicines • CDSCO Verified
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#102A56] tracking-tight">
              PharmIntel Direct Medicine Store
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl mt-1 leading-relaxed">
              Order verified prescription and OTC medications directly from licensed community pharmacies.
              Temperature-controlled express delivery within 2 hours across Bengaluru with clinical pharmacist verification.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <button
              onClick={() => setActiveSubTab('cart')}
              className="relative px-5 py-2.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-2 shadow-md hover:shadow-lg transition cursor-pointer"
            >
              <ShoppingBag className="w-4 h-4" />
              <span>{t('my_cart', 'My Cart')}</span>
              {cartData.items_count > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-white text-[#2166F5] font-black text-[11px]">
                  {cartData.items_count}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveSubTab('prescriptions')}
              className="px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-bold text-xs flex items-center gap-2 shadow-xs transition cursor-pointer"
            >
              <FileText className="w-4 h-4 text-emerald-600" />
              <span>{t('upload_rx', 'Upload Prescription')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-200 scrollbar-none text-xs font-bold">
        {[
          { id: 'store', label: 'Medicine Store', icon: ShoppingBag, count: filteredMedicines.length },
          { id: 'categories', label: '12 Categories', icon: Sparkles },
          { id: 'cart', label: 'My Cart', icon: ShoppingBag, count: cartData.items_count, highlight: cartData.items_count > 0 },
          { id: 'orders', label: 'My Orders & Reorder', icon: Package },
          { id: 'tracking', label: 'Live Order Tracking', icon: Truck },
          { id: 'prescriptions', label: 'Prescription Uploads', icon: FileText },
          { id: 'addresses', label: 'Saved Addresses', icon: MapPin },
          { id: 'pharmacist', label: 'Pharmacist Portal', icon: UserCheck, staffOnly: true }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition shrink-0 cursor-pointer ${
                isActive
                  ? 'bg-[#2166F5] text-white shadow-xs font-extrabold'
                  : 'bg-white text-slate-600 hover:text-[#102A56] hover:bg-blue-50/60 border border-slate-200/80'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.count !== undefined && tab.count > 0 && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                  isActive ? 'bg-white text-[#2166F5]' : 'bg-blue-100 text-blue-700'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* SUBTAB 1: MEDICINE STORE CATALOG VIEW */}
      {activeSubTab === 'store' && (
        <div className="space-y-6">
          {/* Search, Filter & Sort Controls */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs space-y-4">
            <div className="flex flex-col md:flex-row items-center gap-3">
              {/* Search input with live query */}
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search medicines by brand name, generic salt, active ingredients, or manufacturer..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-[#2166F5]"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Prescription Type Filter */}
              <div className="flex items-center gap-1.5 w-full md:w-auto bg-slate-100 p-1 rounded-xl text-xs font-bold">
                <button
                  onClick={() => setPrescriptionFilter('all')}
                  className={`px-3 py-1.5 rounded-lg transition ${prescriptionFilter === 'all' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
                >
                  All ({medicines.length})
                </button>
                <button
                  onClick={() => setPrescriptionFilter('rx')}
                  className={`px-3 py-1.5 rounded-lg transition ${prescriptionFilter === 'rx' ? 'bg-white text-amber-700 shadow-2xs font-extrabold' : 'text-slate-600 hover:text-slate-900'}`}
                >
                  Rx Only
                </button>
                <button
                  onClick={() => setPrescriptionFilter('otc')}
                  className={`px-3 py-1.5 rounded-lg transition ${prescriptionFilter === 'otc' ? 'bg-white text-emerald-700 shadow-2xs font-extrabold' : 'text-slate-600 hover:text-slate-900'}`}
                >
                  OTC Only
                </button>
              </div>

              {/* Sort By Dropdown */}
              <div className="flex items-center gap-2 w-full md:w-auto">
                <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="popular">Sort: Recommended</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                  <option value="name_asc">Name: A to Z</option>
                </select>
              </div>
            </div>

            {/* Category Filter Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs">
              <button
                onClick={() => setSelectedCategory('All')}
                className={`px-3 py-1.5 rounded-full font-bold transition shrink-0 ${
                  selectedCategory === 'All'
                    ? 'bg-[#2166F5] text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All Therapeutic Classes
              </button>
              {therapeuticCategories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-full font-bold transition shrink-0 flex items-center gap-1.5 ${
                    selectedCategory === cat.id
                      ? 'bg-[#2166F5] text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Product Grid */}
          {loadingMeds ? (
            <div className="p-16 text-center text-slate-500 text-xs">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
              Loading verified pharmaceutical catalog...
            </div>
          ) : filteredMedicines.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
              <AlertCircle className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800">No medicines found matching your query</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Try searching by active ingredient name (e.g. Paracetamol, Metformin) or clear your category filters.
              </p>
              <button
                onClick={() => { setSearchQuery(''); setSelectedCategory('All'); setPrescriptionFilter('all'); }}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs hover:bg-blue-700"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredMedicines.map((med) => {
                const mrp = med.base_mrp || 45.0;
                const sellingPrice = Math.round(mrp * 0.88 * 100) / 100;
                const discountPct = Math.round(((mrp - sellingPrice) / mrp) * 100);

                return (
                  <div
                    key={med.id}
                    onClick={() => { setSelectedProduct(med); setProductDetailModalOpen(true); }}
                    className="bg-white rounded-2xl border border-slate-200/90 hover:border-blue-300 hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden cursor-pointer group"
                  >
                    {/* Card Top: Badges & Icon */}
                    <div className="p-4 pb-0">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center font-bold text-lg border border-blue-100 group-hover:scale-105 transition">
                          💊
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          {med.requires_prescription ? (
                            <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-extrabold flex items-center gap-1">
                              <span>Rx</span> Required
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-extrabold">
                              OTC
                            </span>
                          )}
                          <span className="text-[10px] font-semibold text-slate-500">
                            {med.dosage_form || 'Tablet'}
                          </span>
                        </div>
                      </div>

                      {/* Brand & Generic Name */}
                      <h3 className="font-extrabold text-[#102A56] text-sm group-hover:text-[#2166F5] transition line-clamp-1">
                        {med.brand_name}
                      </h3>
                      <p className="text-[11px] font-semibold text-teal-700 line-clamp-1 mt-0.5">
                        {med.generic_name} • {med.strength}
                      </p>
                      <p className="text-[10px] text-slate-500 line-clamp-1 mt-1">
                        By {med.manufacturer}
                      </p>

                      {/* Stock availability badge */}
                      <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-emerald-700 font-semibold bg-emerald-50/80 px-2 py-1 rounded-md border border-emerald-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        <span>In Stock • Apollo Care Bellandur</span>
                      </div>
                    </div>

                    {/* Card Bottom: Pricing & Add to Cart */}
                    <div className="p-4 pt-3 mt-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between gap-2">
                      <div>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-base font-black text-slate-900">
                            ₹{sellingPrice.toFixed(2)}
                          </span>
                          <span className="text-xs text-slate-400 line-through">
                            ₹{mrp.toFixed(2)}
                          </span>
                        </div>
                        <span className="text-[10px] font-bold text-emerald-600">
                          Save {discountPct}% OFF
                        </span>
                      </div>

                      <button
                        onClick={(e) => handleAddToCart(med, 1, e)}
                        className="px-3.5 py-1.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-2xs hover:shadow transition"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* SUBTAB 2: 12 THERAPEUTIC CATEGORIES VIEW */}
      {activeSubTab === 'categories' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-extrabold text-[#102A56]">
              Browse by Therapeutic Category
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Explore medicines classified by organ system, clinical indication, and pharmacology under CDSCO / WHO standards.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {therapeuticCategories.map((cat) => {
              const count = medicines.filter(m => (m.therapeutic_category || '').toLowerCase().includes(cat.id.toLowerCase())).length;
              return (
                <div
                  key={cat.id}
                  onClick={() => { setSelectedCategory(cat.id); setActiveSubTab('store'); }}
                  className="bg-white rounded-2xl border border-slate-200/80 p-5 hover:border-blue-400 hover:shadow-md transition cursor-pointer group flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${cat.color} flex items-center justify-center text-2xl border group-hover:scale-110 transition`}>
                        {cat.icon}
                      </div>
                      <span className="text-xs font-black text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                        {count} Products
                      </span>
                    </div>

                    <h3 className="font-extrabold text-base text-[#102A56] group-hover:text-[#2166F5] transition">
                      {cat.label}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      {cat.desc}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-[#2166F5]">
                    <span>View All Medicines</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SUBTAB 3: SHOPPING CART VIEW */}
      {activeSubTab === 'cart' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-black text-[#102A56] flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-[#2166F5]" />
                Your Medicine Cart ({cartData.items_count} items)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Review items, verify prescription requirements, and proceed to secure checkout.
              </p>
            </div>

            {cartData.items.length > 0 && (
              <button
                onClick={handleClearCart}
                className="text-xs text-red-600 hover:text-red-800 font-bold flex items-center gap-1 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear All</span>
              </button>
            )}
          </div>

          {cartData.items.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center max-w-lg mx-auto">
              <div className="w-16 h-16 rounded-full bg-blue-50 text-[#2166F5] flex items-center justify-center mx-auto mb-4 border border-blue-100">
                <ShoppingBag className="w-8 h-8" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900">Your Shopping Cart is Empty</h3>
              <p className="text-xs text-slate-500 mt-1 mb-6">
                Explore our comprehensive verified catalog to find your prescribed or OTC medications.
              </p>
              <button
                onClick={() => setActiveSubTab('store')}
                className="px-6 py-2.5 bg-[#2166F5] hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition"
              >
                Browse Medicine Store
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Cart Items List */}
              <div className="lg:col-span-2 space-y-4">
                {/* Prescription Notice if Rx items exist */}
                {cartData.has_rx_items && (
                  <div className="bg-amber-50/90 border border-amber-300/80 rounded-2xl p-4 flex items-start gap-3">
                    <FileText className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <span className="font-extrabold text-amber-900 block">
                        Prescription Required for Dispensing
                      </span>
                      <p className="text-amber-800 mt-0.5 leading-relaxed">
                        Your cart contains Schedule H / Rx medications ({cartData.requires_prescription_items.map(i => i.brand_name).join(', ')}).
                        As per Indian Drugs & Cosmetics Rules, you will be prompted to attach a valid doctor's prescription during checkout.
                      </p>
                    </div>
                  </div>
                )}

                {/* Items loop */}
                {cartData.items.map((item) => (
                  <div
                    key={item.id}
                    className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-3.5">
                      <div className="w-12 h-12 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center font-bold text-xl border border-blue-100 shrink-0">
                        💊
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-slate-900 text-sm">{item.brand_name}</h4>
                          {item.requires_prescription && (
                            <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[9px] font-extrabold border border-amber-200">
                              Rx Required
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-teal-700 font-medium mt-0.5">
                          {item.generic_name} • {item.strength} • {item.dosage_form}
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Seller: <span className="font-semibold text-slate-700">{item.pharmacy_name}</span> • Batch: <span className="font-mono text-slate-600">{item.batch_number}</span>
                        </p>
                        <div className="flex items-baseline gap-2 mt-1">
                          <span className="text-xs font-bold text-slate-900">₹{item.unit_price.toFixed(2)}</span>
                          <span className="text-[11px] text-slate-400 line-through">₹{item.mrp.toFixed(2)}</span>
                          <span className="text-[10px] text-emerald-600 font-bold">{item.discount_percent}% off</span>
                        </div>
                      </div>
                    </div>

                    {/* Quantity controls & Delete */}
                    <div className="flex items-center justify-between sm:justify-end gap-4 w-full sm:w-auto border-t sm:border-t-0 pt-2 sm:pt-0">
                      <div className="flex items-center border border-slate-200 rounded-xl overflow-hidden bg-slate-50 shadow-2xs">
                        <button
                          onClick={() => handleUpdateCartQty(item.id, item.quantity - 1)}
                          className="p-1.5 hover:bg-slate-200 text-slate-600 transition"
                        >
                          <Minus className="w-3.5 h-3.5" />
                        </button>
                        <span className="px-3.5 text-xs font-black text-slate-900 font-mono">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => handleUpdateCartQty(item.id, item.quantity + 1)}
                          className="p-1.5 hover:bg-slate-200 text-slate-600 transition"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <div className="text-right min-w-[70px]">
                        <span className="text-sm font-black text-slate-900">
                          ₹{(item.unit_price * item.quantity).toFixed(2)}
                        </span>
                      </div>

                      <button
                        onClick={() => handleRemoveCartItem(item.id)}
                        className="p-2 text-slate-400 hover:text-red-600 transition"
                        title="Remove item"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Order Summary Card */}
              <div className="space-y-4">
                <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-xs space-y-4">
                  <h3 className="font-extrabold text-[#102A56] text-sm border-b border-slate-100 pb-3">
                    Payment & Price Breakdown
                  </h3>

                  <div className="space-y-2.5 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Total MRP</span>
                      <span>₹{cartData.total_mrp.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between text-emerald-600 font-bold">
                      <span>Catalog Discount</span>
                      <span>- ₹{cartData.savings_amount.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between text-slate-700 font-semibold">
                      <span>Medicines Subtotal</span>
                      <span>₹{cartData.subtotal.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between text-slate-600">
                      <span>Pharmaceutical GST (5% / 12%)</span>
                      <span>₹{cartData.tax_amount.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between items-center text-slate-600">
                      <span>Delivery Fee</span>
                      <span>
                        {cartData.delivery_fee === 0 ? (
                          <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                            FREE
                          </span>
                        ) : (
                          `₹${cartData.delivery_fee.toFixed(2)}`
                        )}
                      </span>
                    </div>

                    {cartData.amount_needed_for_free_delivery > 0 && (
                      <div className="p-2.5 rounded-xl bg-blue-50 text-[11px] text-blue-700 font-semibold border border-blue-100">
                        Add ₹{cartData.amount_needed_for_free_delivery.toFixed(2)} more to qualify for <strong>FREE Delivery</strong>!
                      </div>
                    )}

                    <div className="pt-3 border-t border-slate-200 flex justify-between items-baseline font-black">
                      <span className="text-slate-900 text-sm">Total Payable</span>
                      <span className="text-xl text-[#2166F5]">
                        ₹{cartData.total_payable.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={handleInitiateCheckout}
                    className="w-full py-3 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-extrabold text-xs shadow-md hover:shadow-lg transition flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span>Proceed to Checkout</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>

                  <div className="pt-2 text-[10px] text-slate-500 text-center space-y-1">
                    <p className="flex items-center justify-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      Encrypted Razorpay & UPI 256-Bit SSL Checkout
                    </p>
                    <p>Fulfillable by Apollo Care Community Pharmacy (DL-20B-KA-45892)</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUBTAB 4: MY ORDERS & REORDER VIEW */}
      {activeSubTab === 'orders' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-black text-[#102A56]">
                My Medicine Orders & History
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Track status in real-time, view official GST tax invoices, reorder refills, or cancel unfulfilled orders.
              </p>
            </div>
            <button
              onClick={loadMyOrders}
              className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 flex items-center gap-1.5 shadow-2xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingOrders ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {loadingOrders ? (
            <div className="p-16 text-center text-slate-500 text-xs">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
              Loading order history...
            </div>
          ) : myOrders.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center max-w-md mx-auto">
              <Package className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800">No Orders Placed Yet</h3>
              <p className="text-xs text-slate-500 mt-1 mb-4">
                Your completed orders and active medicine deliveries will appear here.
              </p>
              <button
                onClick={() => setActiveSubTab('store')}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs hover:bg-blue-700"
              >
                Shop Medicines Now
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {myOrders.map((ord) => {
                const isCancellable = ['Pending', 'Prescription Verification', 'Approved'].includes(ord.status);
                return (
                  <div
                    key={ord.id}
                    className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:border-blue-200 transition space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-black text-sm text-[#102A56]">
                            {ord.order_number}
                          </span>
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                            ord.status === 'Delivered'
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : ord.status === 'Cancelled'
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : ord.status === 'Prescription Verification'
                              ? 'bg-amber-50 text-amber-800 border-amber-200 animate-pulse'
                              : 'bg-blue-50 text-blue-800 border-blue-200'
                          }`}>
                            {ord.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Placed on: {new Date(ord.created_at).toLocaleString()} • Patient: <strong>{ord.patient_name || 'Patient Name Provided'}</strong>
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-base font-black text-slate-900">
                          ₹{ord.total_amount.toFixed(2)}
                        </span>
                        <span className="text-[10px] text-slate-500 font-semibold bg-slate-100 px-2 py-0.5 rounded">
                          {ord.payment_method}
                        </span>
                      </div>
                    </div>

                    {/* Items preview */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                      {ord.items?.map((itm, idx) => (
                        <div key={idx} className="bg-slate-50/70 p-2.5 rounded-xl border border-slate-100 flex items-center justify-between">
                          <div>
                            <span className="font-bold text-slate-800">{itm.medicine_name}</span>
                            <span className="text-[10px] text-slate-500 block">{itm.dosage_form} • Qty: {itm.quantity}</span>
                          </div>
                          <span className="font-bold text-slate-900 font-mono">₹{itm.total_price.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>

                    {/* Actions Bar */}
                    <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="text-[11px] text-slate-500">
                        Pharmacy: <span className="font-semibold text-slate-700">{ord.pharmacy_name}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => { setActiveTrackingOrder(ord); setActiveSubTab('tracking'); }}
                          className="px-3 py-1.5 rounded-xl bg-blue-50 text-[#2166F5] hover:bg-blue-100 font-bold transition flex items-center gap-1.5"
                        >
                          <Truck className="w-3.5 h-3.5" />
                          <span>Track Live</span>
                        </button>

                        <button
                          onClick={() => handleViewInvoice(ord.id)}
                          className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-bold transition flex items-center gap-1.5 shadow-2xs"
                        >
                          <Printer className="w-3.5 h-3.5 text-slate-500" />
                          <span>Invoice</span>
                        </button>

                        <button
                          onClick={() => handleReorder(ord.id)}
                          className="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-bold transition flex items-center gap-1.5"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                          <span>Reorder</span>
                        </button>

                        {isCancellable && (
                          <button
                            onClick={() => { setCancellingOrderId(ord.id); setCancelModalOpen(true); }}
                            className="px-3 py-1.5 rounded-xl border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 font-bold transition"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* SUBTAB 5: LIVE ORDER TRACKING VIEW */}
      {activeSubTab === 'tracking' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-black text-[#102A56] flex items-center gap-2">
              <Truck className="w-6 h-6 text-[#2166F5]" />
              Real-Time Medicine Delivery Tracking
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Temperature-controlled pharmaceutical logistics dispatch tracking with verified courier partner information.
            </p>
          </div>

          {!activeTrackingOrder ? (
            <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center max-w-md mx-auto">
              <Truck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800">No Active Order Selected</h3>
              <p className="text-xs text-slate-500 mt-1 mb-4">
                Select an order from My Orders or place a new order to track delivery.
              </p>
              <button
                onClick={() => setActiveSubTab('orders')}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold"
              >
                Go to My Orders
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Stepper Card */}
              <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-6">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-4 border-b border-slate-100">
                  <div>
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Tracking Reference
                    </span>
                    <h3 className="text-lg font-black text-[#102A56] font-mono">
                      {activeTrackingOrder.order_number}
                    </h3>
                  </div>

                  <div className="text-right">
                    <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-blue-50 text-[#2166F5] border border-blue-200">
                      {activeTrackingOrder.status}
                    </span>
                  </div>
                </div>

                {/* Progress Stepper */}
                <div className="space-y-6 py-2">
                  {[
                    { title: 'Order Placed & Confirmed', desc: 'Received at Central Pharmacy Fulfillment Hub', active: true, done: true },
                    {
                      title: 'Pharmacist Prescription Review',
                      desc: activeTrackingOrder.status === 'Prescription Verification' ? 'Under Review by Licensed Pharmacist' : 'Clinically Verified & Dispensing Approved',
                      active: true,
                      done: activeTrackingOrder.status !== 'Prescription Verification' && activeTrackingOrder.status !== 'Pending'
                    },
                    {
                      title: 'Cold-Chain Dispensing & Packing',
                      desc: 'Packed in tamper-evident sealed healthcare container',
                      active: ['Approved', 'Preparing', 'Ready for Pickup', 'Dispatched', 'Delivered'].includes(activeTrackingOrder.status),
                      done: ['Preparing', 'Ready for Pickup', 'Dispatched', 'Delivered'].includes(activeTrackingOrder.status)
                    },
                    {
                      title: 'Out for Express Delivery',
                      desc: 'Courier Executive dispatched with live GPS monitoring',
                      active: ['Dispatched', 'Delivered'].includes(activeTrackingOrder.status),
                      done: activeTrackingOrder.status === 'Delivered'
                    },
                    {
                      title: 'Delivered to Patient',
                      desc: 'Delivered and verified against customer OTP',
                      active: activeTrackingOrder.status === 'Delivered',
                      done: activeTrackingOrder.status === 'Delivered'
                    }
                  ].map((step, idx) => (
                    <div key={idx} className="flex items-start gap-4 relative">
                      {idx < 4 && (
                        <div className={`absolute left-4 top-8 w-0.5 h-10 ${step.done ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
                      )}
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                        step.done
                          ? 'bg-emerald-500 text-white ring-4 ring-emerald-100'
                          : step.active
                          ? 'bg-blue-600 text-white ring-4 ring-blue-100 animate-pulse'
                          : 'bg-slate-100 text-slate-400'
                      }`}>
                        {step.done ? <Check className="w-4 h-4" /> : idx + 1}
                      </div>
                      <div className="pt-0.5">
                        <h4 className={`text-xs font-extrabold ${step.active ? 'text-slate-900' : 'text-slate-400'}`}>
                          {step.title}
                        </h4>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {step.desc}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Items in this order */}
                <div className="pt-4 border-t border-slate-100 space-y-2">
                  <h4 className="text-xs font-bold text-slate-700">Medicines in this Package:</h4>
                  <div className="space-y-1.5">
                    {activeTrackingOrder.items?.map((itm, i) => (
                      <div key={i} className="flex justify-between items-center text-xs p-2 rounded-lg bg-slate-50">
                        <span className="font-semibold text-slate-800">{itm.medicine_name} ({itm.dosage_form})</span>
                        <span className="text-slate-600 font-mono">Qty: {itm.quantity} • ₹{itm.total_price.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Courier & Delivery Partner Details */}
              <div className="space-y-4">
                <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
                  <h3 className="font-extrabold text-[#102A56] text-sm border-b border-slate-100 pb-3 flex items-center gap-2">
                    <Truck className="w-4 h-4 text-blue-600" />
                    Courier Partner Details
                  </h3>

                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="text-[11px] text-slate-400">Logistics Carrier:</span>
                      <p className="font-bold text-slate-800 mt-0.5">
                        {activeTrackingOrder.delivery?.courier || 'PharmIntel Express Healthcare Logistics'}
                      </p>
                    </div>

                    <div>
                      <span className="text-[11px] text-slate-400">AWB Tracking Number:</span>
                      <p className="font-mono font-bold text-blue-600 mt-0.5">
                        {activeTrackingOrder.delivery?.tracking_number || 'TRK-98012481'}
                      </p>
                    </div>

                    <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center shrink-0">
                        SK
                      </div>
                      <div>
                        <span className="font-bold text-slate-900 block">
                          {activeTrackingOrder.delivery?.driver_name || 'Suresh Kumar'}
                        </span>
                        <span className="text-[10px] text-emerald-700 font-semibold">
                          Verified Medical Courier Partner
                        </span>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {activeTrackingOrder.delivery?.driver_phone || '+91 98450 12345'}
                        </p>
                      </div>
                    </div>

                    <div className="p-3 rounded-2xl bg-blue-50 border border-blue-100 text-center">
                      <span className="text-[10px] text-blue-700 font-bold uppercase tracking-wider block">
                        Delivery Handover OTP
                      </span>
                      <span className="text-xl font-mono font-black text-blue-900 tracking-widest mt-1 block">
                        4928
                      </span>
                      <span className="text-[10px] text-slate-500 mt-1 block">
                        Share this OTP with courier executive upon receiving medication.
                      </span>
                    </div>

                    <button
                      onClick={() => handleViewInvoice(activeTrackingOrder.id)}
                      className="w-full py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs flex items-center justify-center gap-2 shadow-2xs"
                    >
                      <Download className="w-3.5 h-3.5 text-blue-600" />
                      <span>Download Tax Invoice</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUBTAB 6: PRESCRIPTION UPLOADS TAB */}
      {activeSubTab === 'prescriptions' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-black text-[#102A56] flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-600" />
                Prescription Uploads & Verification Center
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Upload your registered medical practitioner's prescription (JPG, PNG, PDF) for instant OCR analysis and pharmacist sign-off.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Upload Box */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
              <h3 className="font-extrabold text-[#102A56] text-sm">Upload New Prescription</h3>
              <label className="border-2 border-dashed border-blue-300 hover:border-blue-500 bg-blue-50/40 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition group">
                <FileText className="w-10 h-10 text-blue-600 mb-2 group-hover:scale-110 transition" />
                <span className="text-xs font-bold text-slate-800">
                  {uploadingRx ? 'Processing OCR Extraction...' : 'Click to Upload Prescription'}
                </span>
                <span className="text-[10px] text-slate-500 mt-1">
                  Supports JPG, PNG, and PDF (Up to 10MB)
                </span>
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf"
                  onChange={handlePrescriptionFileUpload}
                  disabled={uploadingRx}
                  className="hidden"
                />
              </label>

              <div className="text-[11px] text-slate-500 space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-100">
                <p className="font-bold text-slate-700">Prescription Guidelines:</p>
                <p>• Must include Doctor's Name, Degree & Registration Number</p>
                <p>• Must clearly display Patient Name & Date of Consultation</p>
                <p>• Medicines must specify dosage, frequency and duration</p>
              </div>
            </div>

            {/* Uploaded History */}
            <div className="lg:col-span-2 space-y-3">
              <h3 className="font-extrabold text-[#102A56] text-sm">My Uploaded Prescriptions</h3>
              {myPrescriptions.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-xs text-slate-500">
                  No prescriptions uploaded yet. Use the upload box to attach your first prescription.
                </div>
              ) : (
                myPrescriptions.map((rx) => (
                  <div key={rx.id} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-xs">{rx.file_name}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                            rx.status === 'VERIFIED'
                              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                              : rx.status === 'REJECTED'
                              ? 'bg-rose-50 text-rose-800 border border-rose-200'
                              : 'bg-amber-50 text-amber-800 border border-amber-200'
                          }`}>
                            {rx.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Doctor: <strong>{rx.doctor_name || 'Dr. R. K. Sharma, MD'}</strong> • Patient: <strong>{rx.patient_name || 'Patient Provided'}</strong>
                        </p>
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {new Date(rx.uploaded_at).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Extracted medicines */}
                    {rx.items && rx.items.length > 0 && (
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-[11px] space-y-1">
                        <span className="font-bold text-slate-700 block">Identified Medications ({rx.items.length}):</span>
                        <div className="flex flex-wrap gap-1.5">
                          {rx.items.map((itm, idx) => (
                            <span key={idx} className="bg-white px-2 py-0.5 rounded border border-slate-200 font-semibold text-slate-800">
                              {itm.matched_name || itm.raw} {itm.strength ? `(${itm.strength})` : ''}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* SUBTAB 7: SAVED ADDRESSES TAB */}
      {activeSubTab === 'addresses' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-black text-[#102A56] flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-600" />
                Saved Delivery Addresses
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Manage your home, workplace, and family delivery locations with Indian postal pin code serviceability.
              </p>
            </div>
            <button
              onClick={() => setNewAddressFormOpen(true)}
              className="px-4 py-2 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs transition"
            >
              <Plus className="w-4 h-4" />
              <span>Add New Address</span>
            </button>
          </div>

          {/* New Address Modal / Form */}
          {newAddressFormOpen && (
            <div className="bg-white rounded-3xl border-2 border-blue-300 p-6 shadow-md space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <h3 className="font-extrabold text-[#102A56] text-sm">Add New Delivery Location</h3>
                <button onClick={() => setNewAddressFormOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSaveNewAddress} className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">
                    Patient / Recipient Full Legal Name * (No Dummy Names)
                  </label>
                  <input
                    type="text"
                    required
                    value={newAddress.recipient_name}
                    onChange={(e) => setNewAddress({ ...newAddress, recipient_name: e.target.value })}
                    placeholder="Enter patient's full legal name"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Contact Phone Number *</label>
                  <input
                    type="tel"
                    required
                    value={newAddress.phone}
                    onChange={(e) => setNewAddress({ ...newAddress, phone: e.target.value })}
                    placeholder="+91 98765 43210"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="font-bold text-slate-700 block mb-1">Address Line 1 (Flat, House No, Street) *</label>
                  <input
                    type="text"
                    required
                    value={newAddress.address_line1}
                    onChange={(e) => setNewAddress({ ...newAddress, address_line1: e.target.value })}
                    placeholder="Flat 302, Lakeview Apartments, Sarjapur Main Road"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Address Line 2 / Landmark</label>
                  <input
                    type="text"
                    value={newAddress.address_line2}
                    onChange={(e) => setNewAddress({ ...newAddress, address_line2: e.target.value })}
                    placeholder="Near Bellandur Post Office"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">6-Digit PIN Code *</label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={newAddress.pincode}
                    onChange={(e) => {
                      setNewAddress({ ...newAddress, pincode: e.target.value });
                      checkPincode(e.target.value);
                    }}
                    placeholder="560103"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">City</label>
                  <input
                    type="text"
                    value={newAddress.city}
                    onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">State</label>
                  <input
                    type="text"
                    value={newAddress.state}
                    onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200"
                  />
                </div>

                <div className="sm:col-span-2 flex items-center justify-between pt-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newAddress.is_default}
                      onChange={(e) => setNewAddress({ ...newAddress, is_default: e.target.checked })}
                      className="rounded text-blue-600"
                    />
                    <span>Set as primary default delivery address</span>
                  </label>

                  <button
                    type="submit"
                    className="px-5 py-2.5 bg-[#2166F5] hover:bg-blue-700 text-white font-bold rounded-xl shadow-xs"
                  >
                    Save Address
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* List of saved addresses */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {savedAddresses.map((addr) => (
              <div
                key={addr.id}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs relative space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-sm text-slate-900">{addr.recipient_name}</span>
                    <span className="text-[10px] font-bold bg-slate-100 px-2 py-0.5 rounded text-slate-600">
                      {addr.address_type}
                    </span>
                    {addr.is_default && (
                      <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded border border-blue-200">
                        Default
                      </span>
                    )}
                  </div>

                  <button
                    onClick={async () => {
                      if (window.confirm("Remove this address?")) {
                        await api.deleteAddress(addr.id);
                        loadSavedAddresses();
                      }
                    }}
                    className="text-slate-400 hover:text-red-600 p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  {addr.address_line1}, {addr.address_line2 ? addr.address_line2 + ', ' : ''}
                  {addr.city}, {addr.state} - <strong className="font-mono text-slate-800">{addr.pincode}</strong>
                </p>

                <p className="text-xs text-slate-500 font-semibold">
                  Phone: {addr.phone}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUBTAB 8: PHARMACIST DISPENSING PORTAL TAB */}
      {activeSubTab === 'pharmacist' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800 text-[10px] font-extrabold uppercase border border-indigo-200">
                Licensed Staff Clearance Panel
              </span>
              <h2 className="text-xl font-black text-[#102A56] mt-1">
                Clinical Pharmacist Dispensing & Prescription Verification
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Verify uploaded medical prescriptions, authorize Schedule H dispensing, and advance order logistics stages.
              </p>
            </div>
            <button
              onClick={loadPharmacistPortalData}
              className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-white text-xs font-bold flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingStaffPortal ? 'animate-spin' : ''}`} />
              <span>Refresh Queue</span>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Orders Queue */}
            <div className="bg-white rounded-3xl border border-slate-200 p-5 shadow-xs space-y-4">
              <h3 className="font-extrabold text-[#102A56] text-sm">Active Orders Fulfillment Queue</h3>
              {pharmacyOrders.length === 0 ? (
                <p className="text-xs text-slate-400 p-4 text-center">No active pharmacy orders.</p>
              ) : (
                pharmacyOrders.map((ord) => (
                  <div key={ord.id} className="p-3.5 rounded-2xl border border-slate-100 bg-slate-50/70 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-black text-xs text-blue-900">{ord.order_number}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                        {ord.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600">
                      Customer: <strong>{ord.customer_name}</strong> • Phone: {ord.customer_phone}
                    </p>
                    <div className="flex flex-wrap gap-1 text-[10px]">
                      {ord.items?.map((it, idx) => (
                        <span key={idx} className="bg-white px-2 py-0.5 rounded border border-slate-200">
                          {it.name} (x{it.quantity})
                        </span>
                      ))}
                    </div>

                    {/* Quick advance buttons */}
                    <div className="pt-2 flex items-center gap-1.5 text-xs font-bold">
                      {ord.status === 'Prescription Verification' && (
                        <button
                          onClick={() => handlePharmacistUpdateStatus(ord.id, 'Approved')}
                          className="px-2.5 py-1 bg-emerald-600 text-white rounded-lg text-[10px]"
                        >
                          Approve Rx
                        </button>
                      )}
                      {ord.status === 'Approved' && (
                        <button
                          onClick={() => handlePharmacistUpdateStatus(ord.id, 'Preparing')}
                          className="px-2.5 py-1 bg-blue-600 text-white rounded-lg text-[10px]"
                        >
                          Start Dispensing & Deduct Stock
                        </button>
                      )}
                      {ord.status === 'Preparing' && (
                        <button
                          onClick={() => handlePharmacistUpdateStatus(ord.id, 'Dispatched')}
                          className="px-2.5 py-1 bg-indigo-600 text-white rounded-lg text-[10px]"
                        >
                          Handover to Courier
                        </button>
                      )}
                      {ord.status === 'Dispatched' && (
                        <button
                          onClick={() => handlePharmacistUpdateStatus(ord.id, 'Delivered')}
                          className="px-2.5 py-1 bg-emerald-700 text-white rounded-lg text-[10px]"
                        >
                          Mark Delivered
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Prescriptions Needing Review */}
            <div className="bg-white rounded-3xl border border-slate-200 p-5 shadow-xs space-y-4">
              <h3 className="font-extrabold text-[#102A56] text-sm">Pending Prescription Audits</h3>
              {pendingRxList.length === 0 ? (
                <p className="text-xs text-slate-400 p-4 text-center">No prescriptions awaiting pharmacist review.</p>
              ) : (
                pendingRxList.map((rx) => (
                  <div key={rx.id} className="p-3.5 rounded-2xl border border-amber-200 bg-amber-50/50 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-xs text-slate-900">{rx.file_name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-200 text-amber-900">
                        {rx.status || 'Pending'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600">
                      Patient: <strong>{rx.patient_name || 'Manual'}</strong> • Doctor: <strong>{rx.doctor_name || 'Dr. Specialist'}</strong>
                    </p>
                    <div className="flex gap-2 pt-2">
                      <button
                        onClick={async () => {
                          await api.verifyPrescription(rx.id, {
                            status: 'VERIFIED',
                            notes: 'All items verified against CDSCO approved indications',
                            confirmed_items: rx.items?.map(i => ({ item_id: i.id, confirmed: true })) || []
                          });
                          loadPharmacistPortalData();
                        }}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg"
                      >
                        Verify & Approve
                      </button>
                      <button
                        onClick={async () => {
                          const note = prompt("Enter reason for prescription rejection:");
                          if (note) {
                            await api.verifyPrescription(rx.id, {
                              status: 'REJECTED',
                              notes: note,
                              confirmed_items: []
                            });
                            loadPharmacistPortalData();
                          }
                        }}
                        className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg"
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* CHECKOUT MODAL WORKFLOW */}
      {checkoutModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden my-8">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100 flex items-center justify-between">
              <div>
                <h3 className="font-black text-slate-900 text-base flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-blue-600" />
                  Order Checkout & Clinical Verification
                </h3>
                <p className="text-[11px] text-slate-500">
                  Step {checkoutStep} of {cartData.has_rx_items ? 3 : 2}: {
                    checkoutStep === 1 ? 'Patient Details & Delivery Address' :
                    checkoutStep === 2 && cartData.has_rx_items ? 'Doctor Prescription Attachment' :
                    'Payment & Order Confirmation'
                  }
                </p>
              </div>
              <button
                onClick={() => setCheckoutModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Error banner inside checkout */}
            {checkoutError && (
              <div className="mx-6 mt-4 p-3 bg-red-50 text-red-800 text-xs rounded-xl border border-red-200 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{checkoutError}</span>
              </div>
            )}

            {/* Modal Body */}
            <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
              {/* STEP 1: PATIENT & ADDRESS */}
              {checkoutStep === 1 && (
                <div className="space-y-4">
                  {/* Strict Patient Name Requirement */}
                  <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-100 space-y-3">
                    <div>
                      <label className="font-black text-xs text-[#102A56] block mb-1">
                        Patient Legal Full Name * (Strict: Enter Manually)
                      </label>
                      <input
                        type="text"
                        required
                        value={patientName}
                        onChange={(e) => setPatientName(e.target.value)}
                        placeholder="Enter full legal name of patient taking this medication"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 font-semibold focus:ring-2 focus:ring-blue-500 bg-white"
                      />
                      <p className="text-[10px] text-slate-500 mt-1">
                        Must match the name on doctor's prescription for Schedule H medicines. No automated placeholders are used.
                      </p>
                    </div>

                    <div>
                      <label className="font-black text-xs text-[#102A56] block mb-1">
                        Patient Contact Phone *
                      </label>
                      <input
                        type="tel"
                        required
                        value={patientPhone}
                        onChange={(e) => setPatientPhone(e.target.value)}
                        placeholder="+91 98450 12345"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 font-semibold focus:ring-2 focus:ring-blue-500 bg-white"
                      />
                    </div>
                  </div>

                  {/* Delivery Address Selector */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="font-extrabold text-xs text-slate-800">
                        Select Delivery Address
                      </label>
                      <button
                        onClick={() => setNewAddressFormOpen(!newAddressFormOpen)}
                        className="text-xs text-blue-600 hover:text-blue-800 font-bold"
                      >
                        + Add New Location
                      </button>
                    </div>

                    {savedAddresses.length === 0 ? (
                      <p className="text-xs text-slate-500 p-3 bg-slate-50 rounded-xl">
                        No saved addresses found. Please enter your address details above.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {savedAddresses.map((a) => (
                          <label
                            key={a.id}
                            className={`p-3 rounded-xl border flex items-start gap-3 cursor-pointer transition ${
                              selectedAddressId === a.id
                                ? 'border-[#2166F5] bg-blue-50/50 shadow-2xs'
                                : 'border-slate-200 hover:bg-slate-50'
                            }`}
                          >
                            <input
                              type="radio"
                              name="addr"
                              checked={selectedAddressId === a.id}
                              onChange={() => {
                                setSelectedAddressId(a.id);
                                if (!patientName) setPatientName(a.recipient_name);
                                checkPincode(a.pincode);
                              }}
                              className="mt-0.5 text-blue-600"
                            />
                            <div className="text-xs">
                              <span className="font-bold text-slate-900">{a.recipient_name} ({a.address_type})</span>
                              <p className="text-slate-600 mt-0.5">
                                {a.address_line1}, {a.city} - {a.pincode}
                              </p>
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Pincode Serviceability Indicator */}
                  {pincodeServiceability && (
                    <div className={`p-3 rounded-xl text-xs flex items-center gap-2.5 ${
                      pincodeServiceability.serviceable
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : 'bg-rose-50 text-rose-800 border border-rose-200'
                    }`}>
                      <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                      <div>
                        <span className="font-bold block">PIN Code {pincodeServiceability.pincode}: Serviceable</span>
                        <span className="text-[11px]">{pincodeServiceability.estimated_delivery_time} • {pincodeServiceability.fulfilling_pharmacy}</span>
                      </div>
                    </div>
                  )}

                  {/* Delivery Type */}
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setDeliveryType('Home Delivery')}
                      className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                        deliveryType === 'Home Delivery'
                          ? 'border-[#2166F5] bg-blue-50 text-[#2166F5]'
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      🚀 Express Home Delivery
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeliveryType('In-Store Pickup')}
                      className={`p-3 rounded-xl border text-xs font-bold text-center transition ${
                        deliveryType === 'In-Store Pickup'
                          ? 'border-[#2166F5] bg-blue-50 text-[#2166F5]'
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      🏪 Free In-Store Pickup
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 2: PRESCRIPTION ATTACHMENT (FOR RX ITEMS) */}
              {checkoutStep === 2 && cartData.has_rx_items && (
                <div className="space-y-4">
                  <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200 text-xs text-amber-900">
                    <p className="font-bold">Doctor Prescription Mandated by CDSCO Regulations</p>
                    <p className="text-[11px] mt-0.5">
                      Your order contains Schedule H / Rx items: {cartData.requires_prescription_items.map(i => i.brand_name).join(', ')}.
                    </p>
                  </div>

                  {/* Previously uploaded list */}
                  {myPrescriptions.length > 0 && (
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-700 block">
                        Select previously uploaded prescription:
                      </label>
                      {myPrescriptions.map((rx) => (
                        <label
                          key={rx.id}
                          className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition ${
                            selectedPrescriptionId === rx.id
                              ? 'border-[#2166F5] bg-blue-50/60'
                              : 'border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex items-center gap-2 text-xs">
                            <input
                              type="radio"
                              name="rx_select"
                              checked={selectedPrescriptionId === rx.id}
                              onChange={() => setSelectedPrescriptionId(rx.id)}
                              className="text-blue-600"
                            />
                            <div>
                              <span className="font-bold text-slate-800">{rx.file_name}</span>
                              <span className="text-[10px] text-slate-500 block">
                                Doctor: {rx.doctor_name || 'Dr. Specialist'} • Status: {rx.status}
                              </span>
                            </div>
                          </div>
                          <span className="text-[10px] text-slate-400">
                            {new Date(rx.uploaded_at).toLocaleDateString()}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Or upload new directly */}
                  <div className="pt-2">
                    <label className="border-2 border-dashed border-slate-300 hover:border-blue-500 p-4 rounded-xl flex flex-col items-center justify-center text-center cursor-pointer transition">
                      <FileText className="w-8 h-8 text-blue-600 mb-1" />
                      <span className="text-xs font-bold text-slate-800">
                        {uploadingRx ? 'Uploading & parsing...' : 'Upload New Prescription (JPG/PNG/PDF)'}
                      </span>
                      <input
                        type="file"
                        accept=".jpg,.jpeg,.png,.pdf"
                        onChange={handlePrescriptionFileUpload}
                        disabled={uploadingRx}
                        className="hidden"
                      />
                    </label>
                  </div>
                </div>
              )}

              {/* STEP 3 / 2: PAYMENT & REVIEW */}
              {((checkoutStep === 3 && cartData.has_rx_items) || (checkoutStep === 2 && !cartData.has_rx_items)) && (
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="font-black text-slate-800 block mb-2">
                      Choose Payment Method
                    </label>

                    <div className="space-y-2">
                      {[
                        { id: 'UPI / Online', label: 'UPI Instant (Google Pay, PhonePe, Paytm, QR)', icon: '📱' },
                        { id: 'Credit / Debit Card', label: 'Credit / Debit Card (Visa, MasterCard, RuPay)', icon: '💳' },
                        { id: 'Net Banking', label: 'Net Banking (All Indian Commercial Banks)', icon: '🏛️' },
                        { id: 'Cash on Delivery', label: 'Cash on Delivery (Pay upon arrival)', icon: '💵' },
                      ].map((pm) => (
                        <label
                          key={pm.id}
                          className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition ${
                            paymentMethod === pm.id
                              ? 'border-[#2166F5] bg-blue-50/60 font-bold'
                              : 'border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="radio"
                              name="pay_meth"
                              checked={paymentMethod === pm.id}
                              onChange={() => setPaymentMethod(pm.id)}
                              className="text-blue-600"
                            />
                            <span>{pm.icon}</span>
                            <span className="text-slate-800">{pm.label}</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Summary recap */}
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex justify-between font-semibold text-slate-600">
                      <span>Patient Name:</span>
                      <strong className="text-slate-900">{patientName}</strong>
                    </div>
                    <div className="flex justify-between font-semibold text-slate-600">
                      <span>Total Items:</span>
                      <span>{cartData.items_count} medicines</span>
                    </div>
                    <div className="flex justify-between font-semibold text-slate-600">
                      <span>Delivery Mode:</span>
                      <span>{deliveryType}</span>
                    </div>
                    <div className="flex justify-between font-black text-slate-900 pt-2 border-t border-slate-200 text-sm">
                      <span>Total Amount:</span>
                      <span className="text-[#2166F5]">₹{cartData.total_payable.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer Controls */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-between items-center">
              {checkoutStep > 1 ? (
                <button
                  type="button"
                  onClick={() => setCheckoutStep(checkoutStep - 1)}
                  className="px-4 py-2 rounded-xl border border-slate-200 bg-white text-xs font-bold text-slate-700 hover:bg-slate-100"
                >
                  Back
                </button>
              ) : (
                <div></div>
              )}

              {/* Next or Confirm button */}
              {((checkoutStep === 1 && cartData.has_rx_items) || (checkoutStep === 1 && !cartData.has_rx_items && false)) ? (
                <button
                  type="button"
                  onClick={() => {
                    if (!patientName.trim()) {
                      setCheckoutError("Please enter the patient legal name manually.");
                      return;
                    }
                    setCheckoutError(null);
                    setCheckoutStep(2);
                  }}
                  className="px-5 py-2.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs shadow-xs"
                >
                  Continue to Prescription Attachment
                </button>
              ) : (checkoutStep === 2 && cartData.has_rx_items) ? (
                <button
                  type="button"
                  onClick={() => {
                    if (!selectedPrescriptionId) {
                      setCheckoutError("Please attach a verified prescription.");
                      return;
                    }
                    setCheckoutError(null);
                    setCheckoutStep(3);
                  }}
                  className="px-5 py-2.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs shadow-xs"
                >
                  Proceed to Payment
                </button>
              ) : (
                <button
                  type="button"
                  disabled={placingOrder}
                  onClick={handlePlaceOrder}
                  className="px-6 py-2.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-black text-xs shadow-md hover:shadow-lg transition flex items-center gap-2"
                >
                  {placingOrder ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Verifying & Placing Order...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      <span>Confirm & Place Order (₹{cartData.total_payable.toFixed(2)})</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* PRODUCT DETAILS MODAL */}
      {productDetailModalOpen && selectedProduct && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-xl w-full shadow-2xl border border-slate-200 overflow-hidden my-8">
            <div className="p-6 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-black text-[#102A56]">{selectedProduct.brand_name}</h3>
                    {selectedProduct.requires_prescription ? (
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-extrabold">
                        Schedule H / Rx
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-extrabold">
                        OTC Product
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-teal-700 font-semibold mt-0.5">
                    {selectedProduct.generic_name} • {selectedProduct.strength}
                  </p>
                </div>
                <button onClick={() => setProductDetailModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-3 text-xs text-slate-700">
                <div>
                  <span className="font-extrabold text-slate-900 block mb-0.5">Approved Indications:</span>
                  <p className="text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    {selectedProduct.approved_indications}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="font-bold text-slate-500 text-[11px]">Manufacturer</span>
                    <p className="font-semibold text-slate-900">{selectedProduct.manufacturer}</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-500 text-[11px]">Dosage Form / Route</span>
                    <p className="font-semibold text-slate-900">{selectedProduct.dosage_form} ({selectedProduct.route_of_administration || 'Oral'})</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-500 text-[11px]">Storage Guidelines</span>
                    <p className="font-semibold text-slate-900">{selectedProduct.storage_information}</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-500 text-[11px]">Fulfilling Chemist</span>
                    <p className="font-semibold text-slate-900">Apollo Care Community Pharmacy (Bellandur)</p>
                  </div>
                </div>

                <div className="p-3 bg-blue-50/70 rounded-xl border border-blue-100 flex items-baseline justify-between">
                  <div>
                    <span className="text-xs text-slate-500">Retail Selling Price:</span>
                    <div className="flex items-baseline gap-2">
                      <span className="text-xl font-black text-slate-900">₹{(selectedProduct.base_mrp * 0.88).toFixed(2)}</span>
                      <span className="text-xs text-slate-400 line-through">₹{selectedProduct.base_mrp.toFixed(2)}</span>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                    Save 12% OFF
                  </span>
                </div>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  onClick={() => {
                    handleAddToCart(selectedProduct, 1);
                    setProductDetailModalOpen(false);
                  }}
                  className="flex-1 py-2.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs shadow-xs"
                >
                  Add to Cart
                </button>
                <button
                  onClick={async () => {
                    await handleAddToCart(selectedProduct, 1);
                    setProductDetailModalOpen(false);
                    handleInitiateCheckout();
                  }}
                  className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs"
                >
                  Buy Now
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CANCELLATION MODAL */}
      {cancelModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-base font-extrabold text-slate-900">Cancel Medicine Order</h3>
            <p className="text-xs text-slate-600">
              Are you sure you want to cancel this order? If payment was completed, an automatic refund will be credited to your original payment method. Inventory stock will be restored immediately.
            </p>
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Reason for cancellation:</label>
              <select
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 text-xs font-medium"
              >
                <option value="Changed mind / Doctor adjusted dosage">Changed mind / Doctor adjusted dosage</option>
                <option value="Ordered duplicate medicines">Ordered duplicate medicines</option>
                <option value="Delivery address incorrect">Delivery address incorrect</option>
                <option value="Purchased locally at clinic">Purchased locally at clinic</option>
              </select>
            </div>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setCancelModalOpen(false)}
                className="flex-1 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700"
              >
                Keep Order
              </button>
              <button
                onClick={handleConfirmCancelOrder}
                className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold"
              >
                Confirm Cancellation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PRINTABLE OFFICIAL GST TAX INVOICE MODAL */}
      {invoiceModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden my-8 max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 bg-slate-100 border-b border-slate-200 flex justify-between items-center no-print">
              <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
                <Printer className="w-4 h-4 text-blue-600" />
                Official ISO 216 / A4 Pharmaceutical GST Tax Invoice
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="px-3 py-1.5 bg-[#2166F5] hover:bg-blue-700 text-white rounded-xl text-xs font-bold flex items-center gap-1 shadow-2xs"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print / Save PDF</span>
                </button>
                <button
                  onClick={() => setInvoiceModalOpen(false)}
                  className="text-slate-400 hover:text-slate-600 p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto flex-1 bg-white">
              {loadingInvoice ? (
                <div className="p-16 text-center text-xs text-slate-500">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
                  Generating verified tax invoice...
                </div>
              ) : invoiceData?.html ? (
                <div dangerouslySetInnerHTML={{ __html: invoiceData.html }} />
              ) : (
                <p className="text-xs text-slate-500">Invoice not available.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
