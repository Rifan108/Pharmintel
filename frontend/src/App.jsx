import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import TopNavbar from './components/TopNavbar';
import Sidebar from './components/Sidebar';
import LivePharmacistModal from './components/LivePharmacistModal';
import { MessageSquare, Heart } from 'lucide-react';

// Core Pages matching reference navigation
import DrugInteractionChecker from './pages/DrugInteractionChecker';
import CustomerDashboard from './pages/CustomerDashboard';
import HealthProfilePage from './pages/HealthProfilePage';
import MyMedicinesPage from './pages/MyMedicinesPage';
import SafetyReportsPage from './pages/SafetyReportsPage';
import HealthInsightsPage from './pages/HealthInsightsPage';
import AIHealthAssistant from './pages/AIHealthAssistant';
import MedicineQRScanner from './pages/MedicineQRScanner';
import SettingsPage from './pages/SettingsPage';
import HelpSupportPage from './pages/HelpSupportPage';

// Additional Enterprise Platform Pages
import MedicineSearch from './pages/MedicineSearch';
import MedicineDetails from './pages/MedicineDetails';
import PrescriptionScanner from './pages/PrescriptionScanner';
import MedicineAlternatives from './pages/MedicineAlternatives';
import HealthcareProducts from './pages/HealthcareProducts';
import PharmacyFinder from './pages/PharmacyFinder';
import NearbyPharmacies from './pages/NearbyPharmacies';
import ShoppingCart from './pages/ShoppingCart';
import Checkout from './pages/Checkout';
import OrderTracking from './pages/OrderTracking';
import PharmacistDashboard from './pages/PharmacistDashboard';
import PharmacyInventory from './pages/PharmacyInventory';
import PharmacyOrderManagement from './pages/PharmacyOrderManagement';
import AdminDashboard from './pages/AdminDashboard';
import MLModelAnalytics from './pages/MLModelAnalytics';
import LoginPage from './pages/LoginPage';
import OnlinePharmacy from './pages/OnlinePharmacy';

function MainAppShell() {
  // Default to 'drug_detection' matching the uploaded reference image
  const [activeTab, setActiveTab] = useState('drug_detection');
  const [selectedEntityId, setSelectedEntityId] = useState(null);
  const [isLiveChatOpen, setIsLiveChatOpen] = useState(false);

  const handleNavigate = (tab, entityId = null) => {
    setActiveTab(tab);
    if (entityId !== null) {
      setSelectedEntityId(entityId);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#F5F8FF] text-[#102A56] flex flex-col font-sans antialiased selection:bg-[#2166F5]/20 selection:text-[#2166F5]">
      {/* Top Navbar Header */}
      <TopNavbar onNavigate={handleNavigate} />

      {/* Main Layout Container: Sidebar + Content Area */}
      <div className="flex-1 flex flex-row w-full max-w-[1920px] mx-auto overflow-hidden">
        {/* Left Vertical Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onNavigate={handleNavigate}
          onOpenLiveChat={() => setIsLiveChatOpen(true)}
        />

        {/* Dynamic Content Pane */}
        <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {/* Reference Image Screens */}
          {activeTab === 'drug_detection' && (
            <DrugInteractionChecker onNavigate={handleNavigate} />
          )}
          {activeTab === 'online_pharmacy' && (
            <OnlinePharmacy onNavigate={handleNavigate} initialTab={selectedEntityId || 'store'} />
          )}
          {activeTab === 'nearby_pharmacies' && (
            <NearbyPharmacies onNavigate={handleNavigate} />
          )}
          {activeTab === 'home' && (
            <CustomerDashboard onNavigate={handleNavigate} />
          )}
          {activeTab === 'health_profile' && (
            <HealthProfilePage onNavigate={handleNavigate} />
          )}
          {activeTab === 'my_medicines' && (
            <MyMedicinesPage onNavigate={handleNavigate} />
          )}
          {activeTab === 'safety_reports' && (
            <SafetyReportsPage onNavigate={handleNavigate} />
          )}
          {activeTab === 'health_insights' && (
            <HealthInsightsPage onNavigate={handleNavigate} />
          )}
          {activeTab === 'ai_assistant' && (
            <AIHealthAssistant />
          )}
          {activeTab === 'medicine_qr' && (
            <MedicineQRScanner onNavigate={handleNavigate} />
          )}
          {activeTab === 'settings' && (
            <SettingsPage />
          )}
          {activeTab === 'help_support' && (
            <HelpSupportPage onOpenLiveChat={() => setIsLiveChatOpen(true)} />
          )}

          {/* Legacy / Direct-link views */}
          {activeTab === 'interactions' && (
            <DrugInteractionChecker onNavigate={handleNavigate} />
          )}
          {activeTab === 'dashboard' && (
            <CustomerDashboard onNavigate={handleNavigate} />
          )}
          {activeTab === 'profile' && (
            <HealthProfilePage onNavigate={handleNavigate} />
          )}
          {activeTab === 'search' && (
            <MedicineSearch onNavigate={handleNavigate} />
          )}
          {activeTab === 'details' && (
            <MedicineDetails medicineId={selectedEntityId} onNavigate={handleNavigate} />
          )}
          {activeTab === 'qr_scanner' && (
            <MedicineQRScanner onNavigate={handleNavigate} />
          )}
          {activeTab === 'scanner' && (
            <PrescriptionScanner onNavigate={handleNavigate} />
          )}
          {activeTab === 'assistant' && (
            <AIHealthAssistant />
          )}
          {activeTab === 'alternatives' && (
            <MedicineAlternatives medicineId={selectedEntityId} onNavigate={handleNavigate} />
          )}
          {activeTab === 'products' && (
            <OnlinePharmacy onNavigate={handleNavigate} initialTab="store" />
          )}
          {activeTab === 'pharmacies' && (
            <NearbyPharmacies onNavigate={handleNavigate} />
          )}
          {activeTab === 'cart' && (
            <OnlinePharmacy onNavigate={handleNavigate} initialTab="cart" />
          )}
          {activeTab === 'checkout' && (
            <OnlinePharmacy onNavigate={handleNavigate} initialTab="cart" />
          )}
          {activeTab === 'tracking' && (
            <OnlinePharmacy onNavigate={handleNavigate} initialTab="tracking" />
          )}
          {activeTab === 'orders' && (
            <OnlinePharmacy onNavigate={handleNavigate} initialTab="orders" />
          )}
          {activeTab === 'pharmacist_dash' && (
            <PharmacistDashboard onNavigate={handleNavigate} />
          )}
          {activeTab === 'inventory' && (
            <PharmacyInventory />
          )}
          {activeTab === 'pharmacy_orders' && (
            <PharmacyOrderManagement />
          )}
          {activeTab === 'admin' && (
            <AdminDashboard onNavigate={handleNavigate} />
          )}
          {activeTab === 'ml_analytics' && (
            <MLModelAnalytics />
          )}
          {activeTab === 'login' && (
            <LoginPage onNavigate={handleNavigate} />
          )}

          {/* Bottom Footer Bar matching reference image */}
          <footer className="no-print mt-12 pt-6 border-t border-slate-200/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
            <p className="font-medium text-slate-500">
              PHARMINTEL &copy; 2025. All rights reserved.
            </p>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-600">
                Powered by Advanced Clinical Intelligence
              </span>
              <span className="text-[#2166F5]">💙</span>
            </div>
          </footer>
        </main>
      </div>

      {/* Floating Pharmacist Chat Trigger in bottom-right matching reference icon */}
      <button
        onClick={() => setIsLiveChatOpen(true)}
        className="no-print fixed bottom-6 right-6 w-13 h-13 rounded-full bg-gradient-to-tr from-[#2166F5] to-[#27C4D8] text-white shadow-xl hover:shadow-2xl hover:scale-105 transition flex items-center justify-center z-40 group"
        title="Chat with our licensed pharmacist"
      >
        <MessageSquare className="w-6 h-6" />
        <span className="sr-only">Live Support</span>
      </button>

      {/* Live Clinical Pharmacist Consultation Modal */}
      <LivePharmacistModal
        isOpen={isLiveChatOpen}
        onClose={() => setIsLiveChatOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <MainAppShell />
      </AuthProvider>
    </LanguageProvider>
  );
}
