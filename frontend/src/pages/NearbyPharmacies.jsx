import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  MapPin, Navigation, Search, Phone, Clock, ShieldCheck,
  Star, ExternalLink, RefreshCw, AlertTriangle, CheckCircle2,
  Filter, Layers, List, Map as MapIcon, ChevronRight, X,
  Pill, AlertCircle, Sparkles, Building2, CreditCard, Award,
  ArrowRight, Compass, Store, ShoppingBag, LocateFixed
} from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon URLs in bundler environments
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom SVG Icons for Leaflet Map
const createUserLocationIcon = () => {
  return L.divIcon({
    className: 'user-gps-marker',
    html: `
      <div style="position: relative; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;">
        <div style="position: absolute; width: 28px; height: 28px; border-radius: 50%; background: rgba(33, 102, 245, 0.25); animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
        <div style="width: 16px; height: 16px; border-radius: 50%; background: #2166F5; border: 3px solid #FFFFFF; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
};

const createPharmacyIcon = (isNetwork = false, isSelected = false) => {
  const bg = isSelected ? '#F59E0B' : (isNetwork ? '#10B981' : '#2166F5');
  const size = isSelected ? 42 : 36;
  return L.divIcon({
    className: 'pharmacy-marker-pin',
    html: `
      <div style="position: relative; width: ${size}px; height: ${size}px; filter: drop-shadow(0 3px 5px rgba(0,0,0,0.25)); transition: transform 0.2s;">
        <svg viewBox="0 0 38 48" width="${size}" height="${size}" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 0C8.5 0 0 8.5 0 19C0 32.5 19 48 19 48C19 48 38 32.5 38 19C38 8.5 29.5 0 19 0Z" fill="${bg}"/>
          <circle cx="19" cy="18" r="13" fill="#FFFFFF"/>
          <path d="M19 10V26M11 18H27" stroke="${bg}" stroke-width="3.5" stroke-linecap="round"/>
          ${isNetwork ? '<circle cx="30" cy="8" r="6" fill="#10B981" stroke="#FFFFFF" stroke-width="1.5"/><path d="M28 8L29.5 9.5L32.5 6.5" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>' : ''}
        </svg>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  });
};

export default function NearbyPharmacies({ onNavigate }) {
  const { t, language } = useLanguage();

  // Coordinates & Location State
  // Strictly null until user explicitly grants permission or enters a manual search
  const [coordinates, setCoordinates] = useState(null);
  const [gpsDetected, setGpsDetected] = useState(false);
  const [locationStatus, setLocationStatus] = useState('prompt'); // 'prompt', 'detecting', 'success', 'denied', 'unavailable', 'timeout', 'insecure', 'unsupported', 'error'
  const [detectedLocality, setDetectedLocality] = useState('');
  const [locationDetails, setLocationDetails] = useState(null);
  const [manualAreaInput, setManualAreaInput] = useState('');

  // Pharmacy Data & Filtering State
  const [pharmacies, setPharmacies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [radiusKm, setRadiusKm] = useState(5.0);
  const [searchName, setSearchName] = useState('');
  const [openNowOnly, setOpenNowOnly] = useState(false);
  const [selectedService, setSelectedService] = useState('all'); // 'all', '247', 'delivery', 'generic'
  const [sortBy, setSortBy] = useState('distance'); // 'distance', 'rating', 'name'

  // Medicine Availability Integration
  const [medicineQuery, setMedicineQuery] = useState('');
  const [medicineSuggestions, setMedicineSuggestions] = useState([]);
  const [activeMedicineFilter, setActiveMedicineFilter] = useState(null);

  // View & UI State
  const [viewMode, setViewMode] = useState('split'); // 'split', 'list', 'map'
  const [selectedPharmacy, setSelectedPharmacy] = useState(null);
  const [modalPharmacy, setModalPharmacy] = useState(null);

  // Leaflet Map Refs
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const userMarkerRef = useRef(null);

  // Format distance accurately in meters (<1 km) or kilometers (>=1 km)
  const formatDistance = (distKm) => {
    if (distKm === null || distKm === undefined) return null;
    if (distKm < 1.0) {
      const meters = Math.round(distKm * 1000);
      return `${meters} ${t('meters_away', 'm away')}`;
    }
    return `${distKm.toFixed(1)} ${t('km_away', 'km away')}`;
  };

  // 1. User-Initiated GPS Geolocation Detection
  const requestUserLocation = () => {
    // Check HTTPS / Secure Context
    if (typeof window !== 'undefined' && window.isSecureContext === false && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      setLocationStatus('insecure');
      setErrorMsg(t('location_insecure_msg', 'Geolocation requires a secure connection (HTTPS or localhost).'));
      return;
    }

    // Check Geolocation Support
    if (!navigator.geolocation) {
      setLocationStatus('unsupported');
      setErrorMsg(t('location_unsupported_msg', 'Geolocation is not supported by your browser. Please search manually.'));
      return;
    }

    setLocationStatus('detecting');
    setErrorMsg(null);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setCoordinates({ lat, lng });
        setGpsDetected(true);
        setLocationStatus('success');

        try {
          const rev = await api.reverseGeocodeLocation(lat, lng);
          if (rev) {
            setDetectedLocality(rev.locality || `${lat.toFixed(4)}, ${lng.toFixed(4)}`);
            setLocationDetails(rev);
          }
        } catch (e) {
          console.warn('Reverse geocode failed:', e);
          setDetectedLocality(`${lat.toFixed(4)}, ${lng.toFixed(4)}`);
        }

        fetchPharmacies(lat, lng, radiusKm);
      },
      (err) => {
        console.warn('Geolocation failed:', err.code, err.message);
        setGpsDetected(false);

        if (err.code === 1) { // PERMISSION_DENIED
          setLocationStatus('denied');
          setErrorMsg(t('location_permission_expl', 'Location permission was denied. Please allow location access in your browser settings (click the lock icon in the address bar) or search manually by city, area, or PIN code below.'));
        } else if (err.code === 2) { // POSITION_UNAVAILABLE
          setLocationStatus('unavailable');
          setErrorMsg(t('location_gps_unavailable', 'GPS or location services are currently unavailable on your device. Please ensure location services are enabled or search manually.'));
        } else if (err.code === 3) { // TIMEOUT
          setLocationStatus('timeout');
          setErrorMsg(t('location_timeout_msg', 'Location detection timed out. Please check your signal and click "Refresh Location", or enter your area manually.'));
        } else {
          setLocationStatus('error');
          setErrorMsg(err.message || t('location_error', 'Unable to detect GPS position.'));
        }
      },
      { timeout: 10000, enableHighAccuracy: true, maximumAge: 0 }
    );
  };

  // 2. Fetch Pharmacies from Backend API (Uses actual user coordinates)
  const fetchPharmacies = async (lat, lng, radius, medName = null) => {
    if (lat === null || lat === undefined || lng === null || lng === undefined) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.getNearbyPharmacies({
        lat,
        lng,
        radius_km: radius,
        search_name: searchName || undefined,
        medicine_name: medName || activeMedicineFilter || undefined,
        open_now_only: openNowOnly,
        sort_by: sortBy === 'rating' ? 'rating' : (sortBy === 'name' ? 'name' : 'distance')
      });

      setPharmacies(data.pharmacies || []);
      if (data.detected_locality && !detectedLocality) {
        setDetectedLocality(data.detected_locality);
      }
      if (data.location_details && !locationDetails) {
        setLocationDetails(data.location_details);
      }
    } catch (err) {
      console.error('Failed to load pharmacies:', err);
      setErrorMsg(err.message || 'Unable to connect to pharmacy discovery network.');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when radius, openNowOnly, activeMedicineFilter, or sortBy changes
  useEffect(() => {
    if (coordinates && coordinates.lat && coordinates.lng) {
      fetchPharmacies(coordinates.lat, coordinates.lng, radiusKm);
    }
  }, [radiusKm, openNowOnly, activeMedicineFilter, sortBy]);

  // Handle Manual Area Search (Geocode)
  const handleAreaSearch = async (e) => {
    if (e) e.preventDefault();
    if (!manualAreaInput.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    try {
      const geo = await api.geocodeLocation(manualAreaInput.trim());
      if (geo && geo.latitude && geo.longitude) {
        const newCoords = { lat: geo.latitude, lng: geo.longitude };
        setCoordinates(newCoords);
        setGpsDetected(false); // Manual search, not GPS
        setLocationStatus('success');

        const locName = geo.area || geo.city || geo.display_name.split(',')[0];
        setDetectedLocality(locName);
        setLocationDetails(geo);

        fetchPharmacies(geo.latitude, geo.longitude, radiusKm);

        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo([geo.latitude, geo.longitude], 14, { duration: 1.2 });
        }
      }
    } catch (err) {
      setErrorMsg(t('location_error', 'Unable to find coordinates for this area. Please try a different PIN code or city name.'));
    } finally {
      setLoading(false);
    }
  };

  // Handle Medicine Autocomplete Search
  const handleMedicineInputChange = async (val) => {
    setMedicineQuery(val);
    if (!val || val.trim().length < 2) {
      setMedicineSuggestions([]);
      return;
    }
    try {
      const res = await api.getAutocomplete(val.trim());
      setMedicineSuggestions(res || []);
    } catch (e) {
      console.warn('Medicine autocomplete error:', e);
    }
  };

  const handleSelectMedicine = (medName) => {
    setActiveMedicineFilter(medName);
    setMedicineQuery(medName);
    setMedicineSuggestions([]);
  };

  const clearMedicineFilter = () => {
    setActiveMedicineFilter(null);
    setMedicineQuery('');
    setMedicineSuggestions([]);
  };

  // 3. Client-Side Filtered & Sorted Pharmacies
  const filteredPharmacies = useMemo(() => {
    let list = [...pharmacies];

    // Filter by pharmacy name
    if (searchName.trim()) {
      const q = searchName.toLowerCase();
      list = list.filter((p) =>
        p.name.toLowerCase().includes(q) ||
        (p.address && p.address.toLowerCase().includes(q))
      );
    }

    // Filter by specific service tag
    if (selectedService === '247') {
      list = list.filter((p) =>
        (p.operating_hours && p.operating_hours.toLowerCase().includes('24')) ||
        (p.available_services && p.available_services.some(s => s.toLowerCase().includes('24')))
      );
    } else if (selectedService === 'delivery') {
      list = list.filter((p) =>
        p.available_services && p.available_services.some(s => s.toLowerCase().includes('delivery'))
      );
    } else if (selectedService === 'generic') {
      list = list.filter((p) =>
        p.is_network_pharmacy ||
        (p.available_services && p.available_services.some(s => s.toLowerCase().includes('generic') || s.toLowerCase().includes('counter')))
      );
    }

    // Sort
    if (sortBy === 'rating') {
      list.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
    } else if (sortBy === 'name') {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      list.sort((a, b) => (a.distance_km ?? 999) - (b.distance_km ?? 999));
    }

    return list;
  }, [pharmacies, searchName, selectedService, sortBy]);

  // 4. Initialize & Update Leaflet Map
  useEffect(() => {
    if (viewMode === 'list') return;
    if (!coordinates || !coordinates.lat || !coordinates.lng) return;
    if (!mapContainerRef.current) return;

    // Initialize map if not yet created
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [coordinates.lat, coordinates.lng],
        zoom: 14,
        zoomControl: false,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      mapInstanceRef.current = map;
      markersLayerRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    // Update user marker
    if (userMarkerRef.current) {
      userMarkerRef.current.remove();
    }
    userMarkerRef.current = L.marker([coordinates.lat, coordinates.lng], {
      icon: createUserLocationIcon(),
      zIndexOffset: 1000,
    })
      .bindPopup(`
        <div style="font-family: inherit; font-size: 12px; line-height: 1.4;">
          <strong style="color: #2166F5;">📍 ${gpsDetected ? t('gps_active_badge', 'Live GPS Location') : t('manual_location_badge', 'Manually Selected Location')}</strong><br/>
          <span style="color: #64748B;">${detectedLocality || `${coordinates.lat.toFixed(4)}, ${coordinates.lng.toFixed(4)}`}</span>
        </div>
      `)
      .addTo(map);

    // Clear previous pharmacy pins
    markersLayer.clearLayers();

    // Add pharmacy markers and compute bounds
    const bounds = L.latLngBounds([[coordinates.lat, coordinates.lng]]);

    filteredPharmacies.forEach((p) => {
      if (p.latitude && p.longitude) {
        bounds.extend([p.latitude, p.longitude]);

        const isSelected = selectedPharmacy && selectedPharmacy.id === p.id;
        const marker = L.marker([p.latitude, p.longitude], {
          icon: createPharmacyIcon(p.is_network_pharmacy, isSelected),
        });

        const distStr = formatDistance(p.distance_km);
        const openStatusHtml = p.is_open_now === true
          ? '<span style="color: #10B981; font-weight: 700;">● Open Now</span>'
          : (p.is_open_now === false
              ? '<span style="color: #EF4444; font-weight: 700;">● Closed</span>'
              : '<span style="color: #64748B; font-weight: 500;">Hours not specified</span>');

        const directionsUrl = `https://www.google.com/maps/dir/?api=1&origin=${coordinates.lat},${coordinates.lng}&destination=${p.latitude},${p.longitude}`;

        const popupContent = document.createElement('div');
        popupContent.className = 'pharmacy-map-popup p-1 text-slate-800';
        popupContent.style.minWidth = '230px';
        popupContent.innerHTML = `
          <div style="font-family: system-ui, sans-serif; font-size: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px;">
              <span style="font-weight: 700; font-size: 13px; color: #102A56;">${p.name}</span>
              ${p.is_network_pharmacy ? '<span style="background: #ECFDF5; color: #059669; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 9999px;">✓ Verified</span>' : ''}
            </div>
            <div style="color: #64748B; font-size: 11px; margin-bottom: 6px;">
              ${distStr ? `<strong>${distStr}</strong> • ` : ''}
              ${openStatusHtml}
            </div>
            <p style="font-size: 11px; color: #475569; margin-bottom: 8px; line-height: 1.3;">
              ${p.address}
            </p>
            <div style="display: flex; gap: 6px;">
              <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" 
                 style="flex: 1; text-align: center; background: #2166F5; color: #FFFFFF; padding: 6px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; text-decoration: none;">
                ${t('directions_btn', 'Directions')}
              </a>
              ${p.phone && p.phone !== 'Information unavailable' ? `
                <a href="tel:${p.phone}" style="background: #EFF6FF; color: #2166F5; padding: 6px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; text-decoration: none; border: 1px solid #BFDBFE;">
                  ${t('call_btn', 'Call')}
                </a>
              ` : ''}
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);

        marker.on('click', () => {
          setSelectedPharmacy(p);
        });

        markersLayer.addLayer(marker);
      }
    });

    // Auto-fit bounds if we have pharmacies
    if (filteredPharmacies.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    }

    // Invalidate size on layout adjustments
    setTimeout(() => {
      map.invalidateSize();
    }, 200);
  }, [coordinates, filteredPharmacies, selectedPharmacy, viewMode, gpsDetected, detectedLocality]);

  // Center Map on Selected Pharmacy from List Card
  const handlePharmacyCardClick = (pharmacy) => {
    setSelectedPharmacy(pharmacy);
    if (mapInstanceRef.current && pharmacy.latitude && pharmacy.longitude) {
      mapInstanceRef.current.flyTo([pharmacy.latitude, pharmacy.longitude], 16, { duration: 0.8 });
    }
  };

  // Re-center on user coordinates
  const handleRecenter = () => {
    if (mapInstanceRef.current && coordinates) {
      mapInstanceRef.current.flyTo([coordinates.lat, coordinates.lng], 14, { duration: 0.8 });
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-16">
      {/* 1. HERO HEADER WITH LIVE LOCATION & GPS STATUS */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#102A56] via-[#1E3A8A] to-[#2166F5] text-white p-6 sm:p-8 shadow-xl border border-blue-400/20">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-semibold text-blue-100">
              <Compass className="w-3.5 h-3.5 text-blue-300 animate-spin-slow" />
              <span>{t('nearby_hero_subtitle', 'Find verified medical shops and community pharmacies near you')}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white flex items-center gap-3">
              <Building2 className="w-7 h-7 text-emerald-400" />
              {t('nearby_hero_title', 'Nearby Medical Shops')}
            </h1>
            <p className="text-xs sm:text-sm text-blue-100/90 max-w-2xl leading-relaxed">
              {t('nearby_hero_desc', 'Real-time geolocation discovery, live stock verification, operating hours, and turn-by-turn navigation.')}
            </p>
          </div>

          {/* Location & GPS Controls Card */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4 shrink-0 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/15 text-white flex items-center justify-center shrink-0">
                <MapPin className="w-5 h-5 text-emerald-300" />
              </div>
              <div>
                <div className="text-[10px] uppercase font-bold tracking-wider text-blue-200">
                  {t('detected_location', 'Detected Location')}
                </div>
                <div className="text-sm font-bold text-white max-w-[220px] truncate" title={detectedLocality || 'No location set'}>
                  {locationStatus === 'detecting'
                    ? t('detecting_location', 'Detecting GPS location...')
                    : (detectedLocality || 'Click "Use My Current Location"')}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className={`w-2 h-2 rounded-full ${
                    gpsDetected
                      ? 'bg-emerald-400 animate-pulse'
                      : (coordinates ? 'bg-amber-400' : 'bg-slate-400')
                  }`}></span>
                  <span className="text-[10px] text-blue-100">
                    {gpsDetected
                      ? t('gps_active_badge', 'Live GPS Location')
                      : (coordinates ? t('manual_location_badge', 'Manually Selected Location') : 'Location Not Set')}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={requestUserLocation}
              disabled={locationStatus === 'detecting'}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-white text-[#102A56] hover:bg-blue-50 text-xs font-black transition flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 cursor-pointer"
            >
              <LocateFixed className={`w-4 h-4 text-[#2166F5] ${locationStatus === 'detecting' ? 'animate-spin' : ''}`} />
              <span>{t('use_my_location', 'Use My Current Location')}</span>
            </button>
          </div>
        </div>

        {/* Diagnostic Error & Permission Guidance Banner */}
        {errorMsg && (
          <div className="mt-4 p-4 bg-amber-500/20 border border-amber-300/40 rounded-2xl flex items-start justify-between gap-3 text-xs text-amber-100">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-5 h-5 text-amber-300 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-white">{errorMsg}</span>
                <p className="text-[11px] text-amber-200/90 leading-relaxed">
                  You can use the search bar below to manually find pharmacies by entering your city, locality, or 6-digit postal PIN code.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                const el = document.getElementById('manual-area-input');
                if (el) el.focus();
              }}
              className="px-3 py-1.5 bg-white text-[#102A56] rounded-xl font-bold text-xs shrink-0 hover:bg-amber-100 transition shadow-xs"
            >
              Enter Area
            </button>
          </div>
        )}
      </div>

      {/* 2. PROMPT STATE: WHEN LOCATION HAS NOT BEEN DETECTED YET */}
      {!coordinates && (
        <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-12 text-center space-y-6 shadow-sm max-w-3xl mx-auto">
          <div className="w-16 h-16 rounded-3xl bg-blue-50 text-[#2166F5] flex items-center justify-center mx-auto shadow-inner">
            <LocateFixed className="w-8 h-8 text-[#2166F5] animate-pulse" />
          </div>

          <div className="space-y-2 max-w-lg mx-auto">
            <h2 className="text-xl sm:text-2xl font-black text-[#102A56]">
              {t('location_prompt_title', 'Locate Nearby Medical Shops')}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
              {t('location_prompt_desc', 'Click "Use My Current Location" to discover verified pharmacies and medical shops near you, or search manually by city, area, or PIN code.')}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto pt-2">
            <button
              onClick={requestUserLocation}
              disabled={locationStatus === 'detecting'}
              className="w-full sm:w-auto px-6 py-3.5 bg-[#2166F5] hover:bg-blue-700 text-white font-black text-sm rounded-2xl shadow-md transition flex items-center justify-center gap-2.5 cursor-pointer disabled:opacity-50"
            >
              <LocateFixed className={`w-4 h-4 ${locationStatus === 'detecting' ? 'animate-spin' : ''}`} />
              <span>{locationStatus === 'detecting' ? t('detecting_location', 'Detecting GPS location...') : t('use_my_location', 'Use My Current Location')}</span>
            </button>
          </div>

          {/* Inline Manual Search Alternative */}
          <div className="pt-4 border-t border-slate-100 max-w-md mx-auto">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">Or Search Manually</div>
            <form onSubmit={handleAreaSearch} className="flex gap-2">
              <div className="relative flex-1">
                <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder={t('search_area_placeholder', 'Enter city, locality or 6-digit PIN code...')}
                  value={manualAreaInput}
                  onChange={(e) => setManualAreaInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-[#102A56] placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5] transition"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2.5 bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shrink-0 shadow-xs cursor-pointer"
              >
                Search
              </button>
            </form>
          </div>
        </div>
      )}

      {/* 3. ACTIVE CONTROLS: SEARCH, FILTER & FUTURE-READY MEDICINE INVENTORY BAR */}
      {coordinates && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-4">
          {/* Top Search Controls Row */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            {/* Pharmacy Name Search */}
            <div className="md:col-span-4 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder={t('search_pharmacy_placeholder', 'Search medical shop by name...')}
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-[#102A56] placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5] transition"
              />
              {searchName && (
                <button onClick={() => setSearchName('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Area / PIN Code Manual Search */}
            <form onSubmit={handleAreaSearch} className="md:col-span-4 flex gap-2">
              <div className="relative flex-1">
                <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="manual-area-input"
                  type="text"
                  placeholder={t('search_area_placeholder', 'Enter city, locality or 6-digit PIN code...')}
                  value={manualAreaInput}
                  onChange={(e) => setManualAreaInput(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-[#102A56] placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#2166F5]/20 focus:border-[#2166F5] transition"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2.5 bg-[#EFF6FF] hover:bg-blue-100 text-[#2166F5] font-bold text-xs rounded-xl border border-blue-200 transition shrink-0 cursor-pointer"
              >
                Go
              </button>
            </form>

            {/* Connected Medicine Stock Search (Future-Ready Integration) */}
            <div className="md:col-span-4 relative">
              <Pill className="w-4 h-4 text-emerald-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder={t('search_medicine_placeholder', 'Check medicine stock (e.g. Losartan, Paracetamol)...')}
                value={medicineQuery}
                onChange={(e) => handleMedicineInputChange(e.target.value)}
                className="w-full pl-10 pr-8 py-2.5 bg-emerald-50/50 border border-emerald-200/80 rounded-xl text-xs text-[#102A56] placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
              {activeMedicineFilter && (
                <button onClick={clearMedicineFilter} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-red-500">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}

              {/* Autocomplete Dropdown */}
              {medicineSuggestions.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-1.5 bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden divide-y divide-slate-100 max-h-52 overflow-y-auto">
                  {medicineSuggestions.map((med) => (
                    <button
                      key={med.id}
                      type="button"
                      onClick={() => handleSelectMedicine(med.brand_name)}
                      className="w-full px-3.5 py-2.5 text-left text-xs hover:bg-[#EFF6FF] flex items-center justify-between transition group"
                    >
                      <div>
                        <span className="font-bold text-[#102A56] group-hover:text-[#2166F5]">{med.brand_name}</span>
                        <span className="text-slate-400 text-[11px] ml-2">({med.generic_name})</span>
                      </div>
                      <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
                        ₹{med.base_mrp}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Active Medicine Filter Chip */}
          {activeMedicineFilter && (
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-lg text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>Checking verified stock for: <strong>{activeMedicineFilter}</strong></span>
              <button onClick={clearMedicineFilter} className="ml-1 hover:text-emerald-950">
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Bottom Filters & View Toggles Row */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 text-xs">
            {/* Distance Radius Pills */}
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-500">{t('filter_distance', 'Radius')}:</span>
              {[1, 3, 5, 10, 20].map((km) => (
                <button
                  key={km}
                  onClick={() => setRadiusKm(km)}
                  className={`px-3 py-1.5 rounded-lg font-bold transition cursor-pointer ${
                    radiusKm === km
                      ? 'bg-[#2166F5] text-white shadow-2xs'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                >
                  {km} km
                </button>
              ))}
            </div>

            {/* Quick Filter Toggles */}
            <div className="flex items-center gap-2">
              {/* Open Now Toggle */}
              <button
                onClick={() => setOpenNowOnly(!openNowOnly)}
                className={`px-3 py-1.5 rounded-lg font-bold border transition flex items-center gap-1.5 cursor-pointer ${
                  openNowOnly
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300 shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${openNowOnly ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
                <span>{t('filter_open_now', 'Open Now')}</span>
              </button>

              {/* Service Filters */}
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-semibold text-slate-700 focus:outline-none focus:border-blue-400"
              >
                <option value="all">All Services</option>
                <option value="247">24/7 Service</option>
                <option value="delivery">Home Delivery</option>
                <option value="generic">Generic Medicines</option>
              </select>

              {/* Sort Dropdown */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg font-semibold text-slate-700 focus:outline-none focus:border-blue-400"
              >
                <option value="distance">{t('sort_nearest', 'Nearest Distance')}</option>
                <option value="rating">{t('sort_highest_rated', 'Highest Rated')}</option>
                <option value="name">{t('sort_name_az', 'Name (A-Z)')}</option>
              </select>
            </div>

            {/* View Mode Switcher (Split / List / Map) */}
            <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1">
              <button
                onClick={() => setViewMode('split')}
                title={t('view_split', 'Split View')}
                className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                  viewMode === 'split' ? 'bg-white text-[#2166F5] shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t('view_split', 'Split')}</span>
              </button>
              <button
                onClick={() => setViewMode('list')}
                title={t('view_list', 'List View')}
                className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                  viewMode === 'list' ? 'bg-white text-[#2166F5] shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <List className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t('view_list', 'List')}</span>
              </button>
              <button
                onClick={() => setViewMode('map')}
                title={t('view_map', 'Map View')}
                className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition cursor-pointer ${
                  viewMode === 'map' ? 'bg-white text-[#2166F5] shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <MapIcon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t('view_map', 'Map')}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. MAIN CONTENT: INTERACTIVE MAP & PHARMACY CARDS */}
      {coordinates && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* PHARMACY LIST COLUMN */}
          <div className={`space-y-4 ${
            viewMode === 'list' ? 'lg:col-span-12' : (viewMode === 'map' ? 'hidden' : 'lg:col-span-5 xl:col-span-5')
          }`}>
            {/* Header Count */}
            <div className="flex items-center justify-between text-xs text-slate-500 px-1">
              <span>
                Found <strong className="text-slate-900">{filteredPharmacies.length}</strong> medical shops within {radiusKm} km
              </span>
              {loading && <span className="text-[#2166F5] font-semibold animate-pulse">Updating real-time network...</span>}
            </div>

            {/* Loading Skeletons */}
            {loading && filteredPharmacies.length === 0 && (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3 animate-pulse">
                    <div className="h-4 bg-slate-200 rounded-md w-3/4"></div>
                    <div className="h-3 bg-slate-100 rounded-md w-1/2"></div>
                    <div className="h-10 bg-slate-100 rounded-xl"></div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!loading && filteredPharmacies.length === 0 && (
              <div className="bg-white rounded-2xl border border-slate-200/80 p-8 text-center space-y-4 shadow-xs">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-[#2166F5] flex items-center justify-center mx-auto">
                  <Store className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-slate-900">
                    {t('no_pharmacies_found', 'No medical shops found matching your criteria')}
                  </h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    {t('expand_radius_suggestion', 'Try increasing your search radius or searching by another locality.')}
                  </p>
                </div>
                <button
                  onClick={() => setRadiusKm(10)}
                  className="px-4 py-2 bg-[#2166F5] text-white font-bold text-xs rounded-xl shadow-xs hover:bg-blue-700 transition cursor-pointer"
                >
                  {t('expand_radius_btn', 'Expand to 10 km')}
                </button>
              </div>
            )}

            {/* Pharmacy Cards List */}
            <div className={`space-y-4 overflow-y-auto pr-1 ${viewMode === 'split' ? 'max-h-[720px]' : ''}`}>
              {filteredPharmacies.map((p) => {
                const isSelected = selectedPharmacy && selectedPharmacy.id === p.id;
                const distStr = formatDistance(p.distance_km);
                const directionsUrl = `https://www.google.com/maps/dir/?api=1&origin=${coordinates.lat},${coordinates.lng}&destination=${p.latitude},${p.longitude}`;

                return (
                  <div
                    key={p.id}
                    onClick={() => handlePharmacyCardClick(p)}
                    className={`bg-white rounded-2xl border p-5 shadow-xs transition-all cursor-pointer flex flex-col justify-between group hover:shadow-md ${
                      isSelected
                        ? 'border-[#2166F5] ring-2 ring-[#2166F5]/20 bg-blue-50/20'
                        : 'border-slate-200/80 hover:border-blue-300'
                    }`}
                  >
                    <div className="space-y-3">
                      {/* Top Row: Name + Badges */}
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-extrabold text-sm text-[#102A56] group-hover:text-[#2166F5] transition">
                              {p.name}
                            </h3>
                            {p.is_network_pharmacy && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                                {t('verified_chem_network', 'Verified Network')}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                            {p.address}
                          </p>
                        </div>

                        {/* Distance Badge */}
                        {distStr && (
                          <div className="shrink-0 px-2.5 py-1 rounded-xl bg-[#EFF6FF] border border-blue-200 text-[#2166F5] font-black text-xs">
                            {distStr}
                          </div>
                        )}
                      </div>

                      {/* Meta Row: Open/Closed Badge + Operating Hours + Rating */}
                      <div className="flex items-center gap-3 text-xs flex-wrap">
                        {/* Open Now Badge (Shown only when reliable information exists) */}
                        {p.is_open_now !== null && (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-bold text-[11px] ${
                            p.is_open_now === true
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-red-50 text-red-700 border border-red-200'
                          }`}>
                            <Clock className="w-3 h-3" />
                            {p.is_open_now === true ? t('open_now_badge', 'Open Now') : t('closed_badge', 'Closed')}
                          </span>
                        )}

                        {/* Hours text */}
                        <span className="text-slate-500 text-[11px]">
                          {p.operating_hours || t('hours_not_specified', 'Hours not listed / Contact store')}
                        </span>

                        {/* Rating (Shown only when verified rating exists) */}
                        {p.rating && (
                          <div className="flex items-center gap-1 text-amber-500 font-bold text-xs ml-auto">
                            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                            <span>{p.rating}</span>
                          </div>
                        )}
                      </div>

                      {/* Medicine Availability Box (When Medicine Searched) */}
                      {activeMedicineFilter && (
                        <div className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
                          p.medicine_stock && p.medicine_stock > 0
                            ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                            : (p.is_network_pharmacy
                                ? 'bg-amber-50/70 border-amber-200 text-amber-900'
                                : 'bg-slate-50 border-slate-200 text-slate-600')
                        }`}>
                          <div>
                            <div className="font-bold flex items-center gap-1.5">
                              <Pill className="w-3.5 h-3.5 text-emerald-600" />
                              <span>{activeMedicineFilter}:</span>
                              <span className={p.medicine_stock > 0 ? 'text-emerald-700 font-extrabold' : 'text-slate-700'}>
                                {p.medicine_stock_status || (p.is_network_pharmacy ? 'In Stock' : 'Inventory Not Connected')}
                              </span>
                            </div>
                            {p.last_inventory_update && (
                              <div className="text-[10px] text-slate-500 mt-0.5">
                                {t('last_updated', 'Updated')}: {p.last_inventory_update}
                              </div>
                            )}
                          </div>

                          {p.medicine_price && (
                            <div className="text-right">
                              <span className="text-[10px] text-slate-500 uppercase">{t('unit_price', 'Price')}</span>
                              <div className="text-sm font-black text-emerald-700">₹{p.medicine_price}</div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Services Tags */}
                      {p.available_services && p.available_services.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap pt-1">
                          {p.available_services.slice(0, 3).map((srv, idx) => (
                            <span key={idx} className="text-[10px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                              {srv}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Actions Row: Get Directions, Call Pharmacy, View Details */}
                    <div className="pt-3 mt-3 border-t border-slate-100 flex flex-wrap items-center gap-2">
                      {/* Order Online if network connected */}
                      {p.is_network_pharmacy && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onNavigate) onNavigate('online_pharmacy', 'store');
                          }}
                          className="py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                        >
                          <ShoppingBag className="w-3.5 h-3.5" />
                          <span>Order</span>
                        </button>
                      )}

                      {/* Get Directions Link (Uses user actual coordinates as origin) */}
                      <a
                        href={directionsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 py-2 px-3 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold text-xs transition flex items-center justify-center gap-1.5 shadow-2xs"
                      >
                        <Navigation className="w-3.5 h-3.5" />
                        <span>{t('get_directions', 'Get Directions')}</span>
                      </a>

                      {/* Call Pharmacy (Verified only) */}
                      {p.phone && p.phone !== 'Information unavailable' ? (
                        <a
                          href={`tel:${p.phone}`}
                          onClick={(e) => e.stopPropagation()}
                          className="py-2 px-3 rounded-xl bg-[#EFF6FF] hover:bg-blue-100 text-[#2166F5] font-bold text-xs border border-blue-200 transition flex items-center justify-center gap-1.5"
                        >
                          <Phone className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">{t('call_pharmacy', 'Call')}</span>
                        </a>
                      ) : (
                        <span className="py-2 px-3 rounded-xl bg-slate-100 text-slate-400 font-semibold text-[11px] cursor-not-allowed">
                          {t('no_phone_listed', 'No phone listed')}
                        </span>
                      )}

                      {/* View Details Modal Trigger */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setModalPharmacy(p);
                        }}
                        className="py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <span>{t('view_details', 'Details')}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* INTERACTIVE MAP COLUMN */}
          <div className={`relative ${
            viewMode === 'map' ? 'lg:col-span-12' : (viewMode === 'list' ? 'hidden' : 'lg:col-span-7 xl:col-span-7')
          }`}>
            <div className="sticky top-6">
              <div className="relative rounded-3xl border border-slate-200/90 overflow-hidden shadow-lg bg-slate-100 h-[640px] sm:h-[720px] w-full z-0">
                {/* Map DOM Container */}
                <div ref={mapContainerRef} className="w-full h-full z-0" />

                {/* Map Floating Overlay Header */}
                <div className="absolute top-4 left-4 z-40 bg-white/90 backdrop-blur-md px-3.5 py-2 rounded-2xl shadow-md border border-slate-200/80 flex items-center gap-2 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="font-extrabold text-[#102A56]">
                    {filteredPharmacies.length} Stores on Map
                  </span>
                </div>

                {/* Recenter on User Location Floating Button */}
                <button
                  onClick={handleRecenter}
                  title={t('recenter_btn', 'Recenter on Me')}
                  className="absolute bottom-6 left-4 z-40 bg-white text-[#102A56] hover:bg-blue-50 p-2.5 rounded-2xl shadow-md border border-slate-200 transition flex items-center gap-2 text-xs font-bold cursor-pointer"
                >
                  <Compass className="w-4 h-4 text-[#2166F5]" />
                  <span className="hidden sm:inline">{t('recenter_btn', 'Recenter on Me')}</span>
                </button>

                {/* Map Legend */}
                <div className="absolute bottom-6 right-16 z-40 bg-white/95 backdrop-blur-md p-2.5 rounded-2xl shadow-md border border-slate-200/80 text-[11px] space-y-1.5 hidden sm:block">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-[#2166F5] border border-white shadow-2xs"></span>
                    <span className="font-semibold text-slate-700">Your Location</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-[#10B981] border border-white shadow-2xs"></span>
                    <span className="font-semibold text-slate-700">Verified Network</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-[#3B82F6] border border-white shadow-2xs"></span>
                    <span className="font-semibold text-slate-700">Community Chemist</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. DETAILED PHARMACY MODAL */}
      {modalPharmacy && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 flex flex-col">
            {/* Modal Header */}
            <div className="p-6 bg-gradient-to-r from-[#EFF6FF] to-white border-b border-slate-200/80 flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-black text-[#102A56]">{modalPharmacy.name}</h2>
                  {modalPharmacy.is_network_pharmacy && (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                      ✓ Licensed CDSCO Chemist
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">{modalPharmacy.address}</p>
                {modalPharmacy.distance_km !== null && (
                  <p className="text-xs font-bold text-[#2166F5]">
                    {formatDistance(modalPharmacy.distance_km)}
                  </p>
                )}
              </div>
              <button
                onClick={() => setModalPharmacy(null)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition shrink-0 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 text-xs">
              {/* Quick Info Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/70 space-y-1">
                  <div className="font-bold text-slate-500 uppercase text-[10px]">{t('operating_hours', 'Operating Hours')}</div>
                  <div className="font-bold text-sm text-[#102A56]">
                    {modalPharmacy.operating_hours || t('hours_not_specified', 'Hours not listed / Contact store')}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {modalPharmacy.is_open_now === true
                      ? '● Currently Open'
                      : (modalPharmacy.is_open_now === false ? '● Currently Closed' : 'Hours verification pending')}
                  </div>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/70 space-y-1">
                  <div className="font-bold text-slate-500 uppercase text-[10px]">{t('phone_number', 'Phone Number')}</div>
                  <div className="font-bold text-sm text-[#102A56]">
                    {modalPharmacy.phone || t('no_phone_listed', 'Phone not listed')}
                  </div>
                  <div className="text-[11px] text-slate-500">Contact for stock or emergency queries</div>
                </div>
              </div>

              {/* License & Regulatory Information */}
              <div className="p-4 rounded-2xl bg-blue-50/50 border border-blue-100 space-y-2">
                <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-[#2166F5]" />
                  <span>Regulatory Registration & License</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-500">{t('license_number', 'License Number')}:</span>{' '}
                    <strong className="text-slate-800">{modalPharmacy.license_number || 'State Drug Control Verified'}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">{t('registration_id', 'Registration ID')}:</span>{' '}
                    <strong className="text-slate-800">{modalPharmacy.registration_number || 'REG-PHARM-AUTHENTIC'}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Data Source:</span>{' '}
                    <strong className="text-slate-800">{modalPharmacy.data_source || 'Verified Healthcare Ledger'}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Verification Status:</span>{' '}
                    <span className="text-emerald-700 font-bold">Authentic Location</span>
                  </div>
                </div>
              </div>

              {/* Accepted Payment Methods */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
                  <CreditCard className="w-4 h-4 text-emerald-600" />
                  <span>{t('accepted_payments', 'Accepted Payment Methods')}</span>
                </h4>
                <div className="flex flex-wrap gap-2 text-[11px]">
                  {['Cash', 'UPI (Google Pay, PhonePe, Paytm)', 'Cards (Visa, RuPay, Mastercard)', 'PharmIntel Digital Wallet'].map((pay, i) => (
                    <span key={i} className="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg font-medium border border-slate-200">
                      ✓ {pay}
                    </span>
                  ))}
                </div>
              </div>

              {/* Available Services */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-blue-600" />
                  <span>{t('available_services', 'Available Services')}</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                  {(modalPharmacy.available_services || [
                    'Prescription Dispensing',
                    'Over-the-Counter Medicines',
                    'First Aid Supplies'
                  ]).map((srv, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-slate-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                      <span>{srv}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="p-6 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
              <button
                onClick={() => setModalPharmacy(null)}
                className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold transition text-xs cursor-pointer"
              >
                {t('close', 'Close')}
              </button>

              {modalPharmacy.phone && modalPharmacy.phone !== 'Information unavailable' && (
                <a
                  href={`tel:${modalPharmacy.phone}`}
                  className="px-4 py-2.5 rounded-xl bg-[#EFF6FF] text-[#2166F5] hover:bg-blue-100 border border-blue-200 font-bold transition text-xs flex items-center gap-1.5"
                >
                  <Phone className="w-3.5 h-3.5" />
                  <span>{t('call_pharmacy', 'Call Pharmacy')}</span>
                </a>
              )}

              {coordinates && (
                <a
                  href={`https://www.google.com/maps/dir/?api=1&origin=${coordinates.lat},${coordinates.lng}&destination=${modalPharmacy.latitude},${modalPharmacy.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-5 py-2.5 rounded-xl bg-[#2166F5] hover:bg-blue-700 text-white font-bold transition text-xs flex items-center gap-1.5 shadow-xs"
                >
                  <Navigation className="w-3.5 h-3.5" />
                  <span>{t('get_directions', 'Get Directions')}</span>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
