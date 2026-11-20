import React, { useState, useEffect } from 'react';
import {
  Store, MapPin, Phone, Clock, ShieldCheck, Navigation,
  Search, Star, CheckCircle2, Pill
} from 'lucide-react';
import { api } from '../services/api';

export default function PharmacyFinder({ onNavigate }) {
  const [pharmacies, setPharmacies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState({ lat: 12.9279, lng: 77.6771 }); // Default: Bellandur, Bengaluru
  const [cityFilter, setCityFilter] = useState('');

  useEffect(() => {
    loadPharmacies();
  }, [cityFilter]);

  const loadPharmacies = async () => {
    setLoading(true);
    try {
      const data = await api.getPharmacies({
        lat: userLocation.lat,
        lng: userLocation.lng,
        city: cityFilter || undefined,
      });
      setPharmacies(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleUseMyLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          loadPharmacies();
        },
        (err) => {
          console.warn("Geolocation denied or error:", err);
          // Keep current benchmark coordinates
        }
      );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Store className="w-6 h-6 text-blue-600" /> Licensed Pharmacy Network
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Discover verified community chemists with real-time inventory verification and distance calculation.
          </p>
        </div>

        <button
          onClick={handleUseMyLocation}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 shadow-xs transition"
        >
          <Navigation className="w-3.5 h-3.5 text-blue-600" /> Use My Exact Geolocation
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs mb-8 flex flex-wrap gap-4 items-center justify-between text-xs">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <MapPin className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Filter by city (e.g., Bengaluru)..."
            value={cityFilter}
            onChange={(e) => setCityFilter(e.target.value)}
            className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="text-slate-500 font-medium">
          Showing <span className="font-bold text-slate-900">{pharmacies.length}</span> verified licensed stores
        </div>
      </div>

      {/* Pharmacy Cards Grid */}
      {loading ? (
        <div className="text-center py-16 text-slate-400 text-xs">
          Loading verified pharmacy registry...
        </div>
      ) : pharmacies.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pharmacies.map((pharm) => (
            <div
              key={pharm.id}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:border-blue-400 hover:shadow-md transition flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-1.5 text-green-700 font-bold text-xs bg-green-50 px-2.5 py-0.5 rounded border border-green-200">
                    <ShieldCheck className="w-3.5 h-3.5" /> Licensed & Verified
                  </div>
                  <div className="flex items-center gap-1 text-xs font-bold text-slate-700 font-mono">
                    <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" /> {pharm.rating}
                  </div>
                </div>

                <h3 className="text-lg font-bold text-slate-900 leading-tight mb-1">
                  {pharm.name}
                </h3>
                <p className="text-xs text-slate-500 flex items-start gap-1.5 leading-relaxed mb-3">
                  <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-400 mt-0.5" />
                  {pharm.address}, {pharm.city} - {pharm.postal_code}
                </p>

                <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <p className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span><b>Hours:</b> {pharm.operating_hours}</span>
                  </p>
                  <p className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span><b>Contact:</b> {pharm.phone}</span>
                  </p>
                  <p className="text-[11px] text-slate-400">
                    DL No: <span className="font-mono text-slate-600">{pharm.license_number}</span>
                  </p>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Distance from you</span>
                  <span className="text-sm font-black font-mono text-blue-700">
                    {pharm.distance_km !== null ? `${pharm.distance_km} km away` : 'Within City'}
                  </span>
                </div>

                <button
                  onClick={() => onNavigate('search')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                >
                  Order Medicines
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-slate-400 text-xs bg-white rounded-xl border border-slate-200">
          No registered pharmacies found matching the criteria.
        </div>
      )}
    </div>
  );
}
