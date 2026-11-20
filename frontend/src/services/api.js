const API_BASE = '/api';

function getAuthHeader() {
  const token = localStorage.getItem('pharmintel_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export const api = {
  // Authentication
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  async register(data) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Unauthorized');
    return res.json();
  },

  // Medicines
  async searchMedicines(params = {}) {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.category) query.append('category', params.category);
    if (params.dosage_form) query.append('dosage_form', params.dosage_form);
    if (params.requires_prescription !== undefined) query.append('requires_prescription', params.requires_prescription);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);

    const res = await fetch(`${API_BASE}/medicines?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch medicines');
    return res.json();
  },

  async getAutocomplete(prefix) {
    const res = await fetch(`${API_BASE}/medicines/autocomplete?prefix=${encodeURIComponent(prefix)}`);
    if (!res.ok) return [];
    return res.json();
  },

  async getMedicineDetails(id) {
    const res = await fetch(`${API_BASE}/medicines/${id}`);
    if (!res.ok) throw new Error('Medicine not found');
    return res.json();
  },

  async getCategories() {
    const res = await fetch(`${API_BASE}/medicines/categories`);
    if (!res.ok) return [];
    return res.json();
  },

  // Medicine Intelligence & Discovery
  async searchMedicineIntelligence(q, limit = 15, offset = 0) {
    const res = await fetch(`${API_BASE}/medicine-intelligence/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Failed to query medicine intelligence');
    return res.json();
  },

  async resolveMedicineIntelligence(name, sessionId = null) {
    let url = `${API_BASE}/medicine-intelligence/resolve?name=${encodeURIComponent(name)}`;
    if (sessionId) url += `&session_id=${encodeURIComponent(sessionId)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to resolve medicine');
    return res.json();
  },

  async discoverExternalMedicine(query, sessionId = null) {
    const res = await fetch(`${API_BASE}/medicine-intelligence/discover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId }),
    });
    if (!res.ok) throw new Error('Failed to discover medicine');
    return res.json();
  },

  async getDiagnosticCodes() {
    const res = await fetch(`${API_BASE}/medicine-intelligence/diagnostic-codes`);
    if (!res.ok) throw new Error('Failed to fetch diagnostic codes');
    return res.json();
  },

  async getMedicineAdminMetrics() {
    const res = await fetch(`${API_BASE}/medicine-intelligence/admin/metrics`);
    if (!res.ok) throw new Error('Failed to fetch admin metrics');
    return res.json();
  },

  async getMedicineAdminList(params = {}) {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.category) query.append('category', params.category);
    if (params.verification_status) query.append('verification_status', params.verification_status);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const res = await fetch(`${API_BASE}/medicine-intelligence/admin/medicines?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch admin medicines');
    return res.json();
  },

  // Drug Interactions
  async checkInteractions(medicineIds, enableMl = true) {
    const res = await fetch(`${API_BASE}/interactions/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medicine_ids: medicineIds, enable_ml_prediction: enableMl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to check interactions');
    }
    return res.json();
  },

  // Patient-Specific Regimen Safety Intelligence
  async checkRegimenCompatibility(payload) {
    const res = await fetch(`${API_BASE}/interactions/patient-safety/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to analyze regimen compatibility');
    }
    return res.json();
  },

  // Multiple Medicine Compatibility Engine
  async checkMultipleMedicinesCompatibility(payload) {
    const res = await fetch(`${API_BASE}/interactions/multi-check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to analyze multiple medicine compatibility');
    }
    return res.json();
  },

  async getPatientSafetyProfile() {
    const res = await fetch(`${API_BASE}/interactions/patient-safety/profile`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return { health_profile: { medical_conditions: [], allergies: [] }, existing_medicines: [] };
    return res.json();
  },

  async savePatientSafetyProfile(healthProfile, existingMedicines) {
    const res = await fetch(`${API_BASE}/interactions/patient-safety/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ health_profile: healthProfile, existing_medicines: existingMedicines }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to save patient safety profile');
    }
    return res.json();
  },

  async getAssessmentHistory() {
    const res = await fetch(`${API_BASE}/interactions/patient-safety/history`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  async downloadPatientSafetyPdf(reportData) {
    const res = await fetch(`${API_BASE}/interactions/patient-safety/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reportData),
    });
    if (!res.ok) throw new Error('Failed to download safety report PDF');
    return res.blob();
  },

  // Alternatives
  async getAlternatives(medicineId) {
    const res = await fetch(`${API_BASE}/alternatives/${medicineId}`);
    if (!res.ok) throw new Error('Failed to load alternatives');
    return res.json();
  },

  // Pharmacies
  async getPharmacies(params = {}) {
    const query = new URLSearchParams();
    if (params.lat !== undefined && params.lng !== undefined) {
      query.append('lat', params.lat);
      query.append('lng', params.lng);
    }
    if (params.medicine_id) query.append('medicine_id', params.medicine_id);
    if (params.city) query.append('city', params.city);

    const res = await fetch(`${API_BASE}/pharmacies?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch pharmacies');
    return res.json();
  },

  async getNearbyPharmacies(params = {}) {
    const query = new URLSearchParams();
    if (params.lat !== undefined && params.lat !== null) query.append('lat', params.lat);
    if (params.lng !== undefined && params.lng !== null) query.append('lng', params.lng);
    if (params.radius_km) query.append('radius_km', params.radius_km);
    if (params.search_name) query.append('search_name', params.search_name);
    if (params.city) query.append('city', params.city);
    if (params.postal_code) query.append('postal_code', params.postal_code);
    if (params.medicine_id) query.append('medicine_id', params.medicine_id);
    if (params.medicine_name) query.append('medicine_name', params.medicine_name);
    if (params.open_now_only) query.append('open_now_only', 'true');
    if (params.sort_by) query.append('sort_by', params.sort_by);

    const res = await fetch(`${API_BASE}/pharmacies/nearby?${query.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch nearby medical shops');
    }
    return res.json();
  },

  async geocodeLocation(q) {
    const res = await fetch(`${API_BASE}/pharmacies/geocode?q=${encodeURIComponent(q)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to geocode location');
    }
    return res.json();
  },

  async reverseGeocodeLocation(lat, lng) {
    const res = await fetch(`${API_BASE}/pharmacies/reverse-geocode?lat=${lat}&lng=${lng}`);
    if (!res.ok) return { locality: 'Detected Location', latitude: lat, longitude: lng };
    return res.json();
  },

  // Inventory Management
  async getInventory(pharmacyId) {
    const res = await fetch(`${API_BASE}/inventory/${pharmacyId}`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Failed to fetch inventory');
    return res.json();
  },

  async addBatch(pharmacyId, medicineId, batchData) {
    const res = await fetch(`${API_BASE}/inventory/${pharmacyId}/medicines/${medicineId}/batches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(batchData),
    });
    if (!res.ok) throw new Error('Failed to add batch');
    return res.json();
  },

  async adjustStock(pharmacyId, medicineId, adjustmentData) {
    const res = await fetch(`${API_BASE}/inventory/${pharmacyId}/medicines/${medicineId}/adjust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(adjustmentData),
    });
    if (!res.ok) throw new Error('Failed to adjust stock');
    return res.json();
  },

  async getAuditLogs(pharmacyId) {
    const res = await fetch(`${API_BASE}/inventory/${pharmacyId}/audit-logs`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  // Prescriptions & OCR
  async uploadPrescription(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/prescriptions/upload`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async getMyPrescriptions() {
    const res = await fetch(`${API_BASE}/prescriptions/my-prescriptions`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  async getPendingPrescriptionReviews() {
    const res = await fetch(`${API_BASE}/prescriptions/pending-reviews`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  async verifyPrescription(prescriptionId, verificationData) {
    const res = await fetch(`${API_BASE}/prescriptions/${prescriptionId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(verificationData),
    });
    if (!res.ok) throw new Error('Verification failed');
    return res.json();
  },

  // Orders
  async createOrder(orderData) {
    const res = await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(orderData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to place order');
    }
    return res.json();
  },

  async getOrderDetails(orderId) {
    const res = await fetch(`${API_BASE}/orders/${orderId}`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Order not found');
    return res.json();
  },

  async cancelOrder(orderId, reason = null) {
    const url = reason ? `${API_BASE}/orders/${orderId}/cancel?reason=${encodeURIComponent(reason)}` : `${API_BASE}/orders/${orderId}/cancel`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to cancel order');
    }
    return res.json();
  },

  async reorder(orderId) {
    const res = await fetch(`${API_BASE}/orders/${orderId}/reorder`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to reorder items');
    }
    return res.json();
  },

  async getOrderInvoice(orderId) {
    const res = await fetch(`${API_BASE}/orders/${orderId}/invoice`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Failed to load invoice');
    return res.json();
  },

  // Online Pharmacy Cart (Persistent Backend Cart)
  async getCart(pincode = null) {
    const url = pincode ? `${API_BASE}/cart?destination_pincode=${encodeURIComponent(pincode)}` : `${API_BASE}/cart`;
    const res = await fetch(url, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return { items: [], items_count: 0, subtotal: 0, total_payable: 0 };
    return res.json();
  },

  async addToCartApi(medicineId, quantity = 1, pharmacyId = 1) {
    const res = await fetch(`${API_BASE}/cart/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ medicine_id: medicineId, quantity, pharmacy_id: pharmacyId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add item to cart');
    }
    return res.json();
  },

  async updateCartItemApi(cartItemId, quantity) {
    const res = await fetch(`${API_BASE}/cart/items/${cartItemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ quantity }),
    });
    if (!res.ok) throw new Error('Failed to update cart quantity');
    return res.json();
  },

  async removeCartItemApi(cartItemId) {
    const res = await fetch(`${API_BASE}/cart/items/${cartItemId}`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Failed to remove cart item');
    return res.json();
  },

  async clearCartApi() {
    const res = await fetch(`${API_BASE}/cart`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Failed to clear cart');
    return res.json();
  },

  // Saved Addresses & Serviceability
  async getSavedAddresses() {
    const res = await fetch(`${API_BASE}/addresses`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  async saveAddress(addressData) {
    const res = await fetch(`${API_BASE}/addresses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(addressData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to save address');
    }
    return res.json();
  },

  async deleteAddress(addressId) {
    const res = await fetch(`${API_BASE}/addresses/${addressId}`, {
      method: 'DELETE',
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Failed to delete address');
    return res.json();
  },

  async checkPincodeServiceability(pincode) {
    const res = await fetch(`${API_BASE}/addresses/serviceability?pincode=${encodeURIComponent(pincode)}`);
    if (!res.ok) return { serviceable: false, reason: 'Failed to verify postal serviceability' };
    return res.json();
  },

  // Online Payment Gateway (Razorpay/UPI Sandbox)
  async createPaymentOrder(orderId, paymentMethod = 'UPI / Online') {
    const res = await fetch(`${API_BASE}/payments/create-order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ order_id: orderId, payment_method: paymentMethod }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to initialize payment gateway');
    }
    return res.json();
  },

  async verifyPayment(payload) {
    const res = await fetch(`${API_BASE}/payments/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Payment verification failed');
    }
    return res.json();
  },

  async getMyOrders() {
    const res = await fetch(`${API_BASE}/orders/my-orders`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  async getPharmacyOrders(pharmacyId, statusFilter) {
    const query = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : '';
    const res = await fetch(`${API_BASE}/orders/pharmacy/${pharmacyId}${query}`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) return [];
    return res.json();
  },

  async updateOrderStatus(orderId, status, notes) {
    const res = await fetch(`${API_BASE}/orders/${orderId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ status, notes }),
    });
    if (!res.ok) throw new Error('Failed to update status');
    return res.json();
  },

  async getOrderTracking(orderId) {
    const res = await fetch(`${API_BASE}/orders/${orderId}/tracking`, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error('Failed to load tracking');
    return res.json();
  },

  // AI Health Assistant (Zero Gemini Flash, Provider-Independent)
  async chatWithAssistant(sessionId, message, language = 'en', mode = 'ai_assistant', patientName = null) {
    const res = await fetch(`${API_BASE}/assistant/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        language,
        mode,
        patient_name: patientName
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Assistant query failed');
    }
    return res.json();
  },

  async clearAssistantSession(sessionId) {
    const res = await fetch(`${API_BASE}/assistant/clear-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ session_id: sessionId })
    });
    return res.json();
  },

  async escalateToPharmacist(sessionId, patientName, notes) {
    const res = await fetch(`${API_BASE}/assistant/escalate-pharmacist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({
        session_id: sessionId,
        patient_name: patientName,
        notes
      })
    });
    return res.json();
  },

  // Medicine QR Information System
  async verifyMedicineQR(rawQrContent, sourceType = 'camera_scan') {
    const res = await fetch(`${API_BASE}/qr/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ raw_qr_content: rawQrContent, source_type: sourceType }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'QR verification failed');
    }
    return res.json();
  },

  async scanQRImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/qr/scan-image`, {
      method: 'POST',
      headers: { ...getAuthHeader() },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to decode medicine packaging photo');
    }
    return res.json();
  },

  async getQRSamples() {
    const res = await fetch(`${API_BASE}/qr/samples`);
    if (!res.ok) throw new Error('Failed to load QR sample codes');
    return res.json();
  },

  async getBatchQR(batchId) {
    const res = await fetch(`${API_BASE}/qr/generate-batch/${batchId}`);
    if (!res.ok) throw new Error('Failed to generate batch QR');
    return res.json();
  },

  // ML Research & Metrics
  async getMLMetrics() {
    const res = await fetch(`${API_BASE}/ml/metrics`);
    if (!res.ok) throw new Error('Failed to fetch ML metrics');
    return res.json();
  },

  getMLGraphUrl(graphName) {
    return `${API_BASE}/ml/graphs/${graphName}`;
  },

  async predictMLDDI(drugASmiles, drugBSmiles) {
    const res = await fetch(`${API_BASE}/ml/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ drug_a_smiles: drugASmiles, drug_b_smiles: drugBSmiles }),
    });
    if (!res.ok) throw new Error('ML Prediction failed');
    return res.json();
  },

  // Printing
  async getInvoicePrintData(orderId) {
    const res = await fetch(`${API_BASE}/printing/invoice/${orderId}/data`);
    if (!res.ok) throw new Error('Failed to fetch invoice print data');
    return res.json();
  },

  getInvoicePdfUrl(orderId) {
    return `${API_BASE}/printing/invoice/${orderId}/pdf`;
  },

  // Platform Analytics
  async getAnalyticsDashboard() {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  }
};
