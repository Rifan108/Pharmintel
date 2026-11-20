import React, { useState, useEffect, useRef } from 'react';
import {
  QrCode, Camera, Upload, AlertCircle, ShieldCheck,
  AlertTriangle, CheckCircle2, XCircle, Search, RefreshCw,
  Building, Calendar, Pill, ShieldAlert, Award, FileText,
  Copy, ExternalLink, Printer, ArrowRight, ShoppingBag, Eye,
  RotateCcw, Sparkles, SwitchCamera, Baby, Plus, Check
} from 'lucide-react';
import { Html5Qrcode } from 'html5-qrcode';
import { api } from '../services/api';

export default function MedicineQRScanner({ onNavigate }) {
  // Tabs: 'camera' (Scan Using Camera), 'upload' (Upload Medicine Photo), 'manual' (Search Medicine Manually)
  const [activeTab, setActiveTab] = useState('camera');
  const [scanning, setScanning] = useState(false);
  const [manualInput, setManualInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cameraErrorKind, setCameraErrorKind] = useState(null); // 'permission_denied', 'no_camera', 'in_use', 'insecure', 'general'
  const [verificationResult, setVerificationResult] = useState(null);
  const [sampleCodes, setSampleCodes] = useState([]);
  const [facingMode, setFacingMode] = useState('environment'); // 'environment' (back) or 'user' (front)
  const [addedToMyMeds, setAddedToMyMeds] = useState(false);

  // File upload preview state
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const scannerRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadSamples();

    return () => {
      stopCameraScanner();
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, []);

  const loadSamples = async () => {
    try {
      const data = await api.getQRSamples();
      setSampleCodes(data || []);
    } catch (err) {
      console.warn("Could not load QR samples:", err);
    }
  };

  // -------------------------------------------------------------
  // CAMERA SCANNER ENGINE WITH getUserMedia AND CAPTURE PHOTO
  // -------------------------------------------------------------
  const startCameraScanner = async (overrideFacing) => {
    setError(null);
    setCameraErrorKind(null);
    stopCameraScanner();

    // Check secure context
    if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      setCameraErrorKind('insecure');
      setError("Camera access requires a secure connection (HTTPS) or localhost. Please use 'Upload Medicine Photo' or open via localhost.");
      return;
    }

    // Check mediaDevices support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraErrorKind('no_camera');
      setError("Your browser does not support camera capture via getUserMedia. Please use 'Upload Medicine Photo' instead.");
      return;
    }

    const targetFacing = overrideFacing || facingMode;

    try {
      setScanning(true);

      // 1. Native getUserMedia video stream for real-time camera preview
      let stream = null;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: targetFacing },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        });
      } catch (constraintErr) {
        // Fallback to basic video constraints
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute('playsinline', 'true');
        await videoRef.current.play().catch(e => console.warn("Video play error:", e));
      }

      // 2. Also attach Html5Qrcode to reader container for real-time barcode decoding
      try {
        const html5QrCode = new Html5Qrcode("qr-reader-viewport");
        scannerRef.current = html5QrCode;
        await html5QrCode.start(
          { facingMode: targetFacing },
          { fps: 12, qrbox: { width: 250, height: 250 } },
          async (decodedText) => {
            stopCameraScanner();
            await handleVerifyQR(decodedText, 'camera_scan');
          },
          () => {} // Frame callback
        );
      } catch (html5Err) {
        // Native video is still streaming, user can click "Capture Package Photo"
        console.warn("Html5Qrcode background scanner note:", html5Err);
      }

    } catch (err) {
      console.error("Camera start failure:", err);
      stopCameraScanner();

      const name = err.name || '';
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setCameraErrorKind('permission_denied');
        setError("Camera permission was denied in your browser. Please click the lock or camera icon in your browser address bar, set Camera to 'Allow', and click 'Retry Camera'.");
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        setCameraErrorKind('no_camera');
        setError("No camera device was detected on your computer or phone. Please verify your webcam is connected or use 'Upload Medicine Photo'.");
      } else if (name === 'NotReadableError' || name === 'TrackStartError') {
        setCameraErrorKind('in_use');
        setError("The camera is currently locked or in use by another application (e.g. Zoom, Teams, or another browser tab). Please close other camera apps and retry.");
      } else if (name === 'SecurityError') {
        setCameraErrorKind('insecure');
        setError("Camera access was blocked by browser security. Ensure you are accessing via HTTPS or localhost.");
      } else {
        setCameraErrorKind('general');
        setError(`Unable to initialize camera (${err.message || 'Device access failed'}). Please check permissions or upload a package photo.`);
      }
    }
  };

  const stopCameraScanner = () => {
    if (scannerRef.current) {
      try {
        scannerRef.current.stop();
        scannerRef.current.clear();
      } catch (e) {}
      scannerRef.current = null;
    }

    if (streamRef.current) {
      try {
        streamRef.current.getTracks().forEach(track => track.stop());
      } catch (e) {}
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setScanning(false);
  };

  const handleSwitchCamera = () => {
    const nextFacing = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(nextFacing);
    if (scanning) {
      startCameraScanner(nextFacing);
    }
  };

  // -------------------------------------------------------------
  // CAPTURE IMAGE SNAPSHOT FROM CAMERA
  // -------------------------------------------------------------
  const handleCapturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    try {
      setLoading(true);
      setError(null);

      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      stopCameraScanner();

      // Convert to JPEG blob
      canvas.toBlob(async (blob) => {
        if (!blob) {
          setError("Failed to capture image frame from video camera.");
          setLoading(false);
          return;
        }

        const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(file));

        try {
          const res = await api.scanQRImage(file);
          setVerificationResult(res);
        } catch (err) {
          setError(err.message || "Medicine identification is not sufficiently reliable. Please upload a clearer photograph showing the medicine name and ingredients.");
        } finally {
          setLoading(false);
        }
      }, 'image/jpeg', 0.92);

    } catch (e) {
      console.error("Capture photo error:", e);
      setError("Failed to capture photo from camera stream.");
      setLoading(false);
    }
  };

  // -------------------------------------------------------------
  // FILE UPLOAD AND SMART RECOGNITION
  // -------------------------------------------------------------
  const handleFileSelected = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setCameraErrorKind(null);
  };

  const handleClearSelectedFile = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleScanUploadedImage = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.scanQRImage(selectedFile);
      setVerificationResult(res);
    } catch (err) {
      console.error("Image scan failed:", err);
      setError(
        err.message ||
        "Medicine identification is not sufficiently reliable. Please upload a clearer photograph showing the medicine name and ingredients."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyQR = async (rawCode, sourceType = 'camera_scan') => {
    if (!rawCode || !rawCode.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.verifyMedicineQR(rawCode.trim(), sourceType);
      setVerificationResult(res);
    } catch (err) {
      console.error("Verification failed:", err);
      setError(err.message || "Failed to query authoritative verification registry.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------
  // ACTIONS: ASK AI, DETECT MEDICINE, ONLINE PHARMACY, MY MEDICINES
  // -------------------------------------------------------------
  const handleAskAIAboutMedicine = () => {
    if (!verificationResult) return;
    const medName = verificationResult.medicine_name || verificationResult.generic_name;
    const initialQuery = `Can I take ${medName} while pregnant? What are its active ingredients, dosage, and side effects?`;

    try {
      sessionStorage.setItem('pharmintel_assistant_initial_query', initialQuery);
    } catch (e) {}

    if (onNavigate) {
      onNavigate('ai_assistant', initialQuery);
    } else {
      window.location.hash = '#ai_assistant';
    }
  };

  const handleCheckCompatibility = () => {
    if (!verificationResult) return;
    const medName = verificationResult.medicine_name || verificationResult.generic_name;
    try {
      sessionStorage.setItem('pharmintel_detect_initial_med', medName);
    } catch (e) {}

    if (onNavigate) {
      onNavigate('drug_detection', medName);
    } else {
      window.location.hash = '#drug_detection';
    }
  };

  const handleOrderOnline = () => {
    if (!verificationResult) return;
    const medName = verificationResult.medicine_name || verificationResult.generic_name;
    try {
      sessionStorage.setItem('pharmintel_pharmacy_search', medName);
    } catch (e) {}

    if (onNavigate) {
      onNavigate('online_pharmacy', medName);
    } else {
      window.location.hash = '#online_pharmacy';
    }
  };

  const handleAddToMyMedicines = () => {
    if (!verificationResult) return;
    const medName = verificationResult.medicine_name;
    try {
      const existing = JSON.parse(localStorage.getItem('pharmintel_saved_medicines') || '[]');
      if (!existing.some(m => m.name === medName)) {
        existing.push({
          id: `med_${Date.now()}`,
          name: medName,
          generic: verificationResult.generic_name,
          dosage: verificationResult.strength || '1 tablet',
          timing: 'As directed by physician',
          frequency: 'Daily',
          addedAt: new Date().toLocaleDateString()
        });
        localStorage.setItem('pharmintel_saved_medicines', JSON.stringify(existing));
      }
      setAddedToMyMeds(true);
      setTimeout(() => setAddedToMyMeds(false), 3000);
    } catch (e) {
      console.warn('Error saving to my medicines:', e);
    }
  };

  const handleResetScan = () => {
    setVerificationResult(null);
    setError(null);
    setCameraErrorKind(null);
    handleClearSelectedFile();
    setManualInput('');
    stopCameraScanner();
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Hidden canvas for video frame capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200">
              CDSCO Verified Track & Trace
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
              Smart Packaging OCR & Barcodes
            </span>
            <span className="text-xs font-mono text-slate-400">Anti-Counterfeiting Registry</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <QrCode className="w-6 h-6 text-teal-600" /> Medicine Scanner & Packaging Recognition
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Identify genuine medicines by live camera, uploading strip/bottle packaging photos, or 2D QR codes with verified CDSCO clinical data.
          </p>
        </div>

        {verificationResult && (
          <button
            onClick={handleResetScan}
            className="px-3.5 py-1.5 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold transition flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Scan Another Package
          </button>
        )}
      </div>

      {/* Regulatory Compliance Protocol Banner */}
      <div className="p-3.5 mb-6 bg-slate-900 text-white rounded-2xl border border-slate-800 flex items-start gap-3 shadow-xs">
        <Award className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed">
          <span className="font-bold text-teal-300 uppercase tracking-wider block mb-0.5">
            CDSCO Clinical Provenance Verification Directive:
          </span>
          PharmIntel verifies packaging barcodes, OCR medicine labels, and 2D GS1 DataMatrix codes directly against the Central Drugs Standard Control Organisation (CDSCO) Registry and Licensed Pharmacy Ledgers to safeguard against counterfeit medicines.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Scanner & Input Methods */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            {/* Three Clear Navigation Tabs */}
            <div className="flex bg-slate-100 p-1 rounded-xl mb-4 text-xs font-semibold">
              <button
                onClick={() => {
                  stopCameraScanner();
                  setActiveTab('camera');
                }}
                className={`flex-1 py-2 rounded-lg transition flex items-center justify-center gap-1.5 ${
                  activeTab === 'camera'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Camera className="w-3.5 h-3.5" /> Scan Using Camera
              </button>
              <button
                onClick={() => {
                  stopCameraScanner();
                  setActiveTab('upload');
                }}
                className={`flex-1 py-2 rounded-lg transition flex items-center justify-center gap-1.5 ${
                  activeTab === 'upload'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Upload className="w-3.5 h-3.5" /> Upload Medicine Photo
              </button>
              <button
                onClick={() => {
                  stopCameraScanner();
                  setActiveTab('manual');
                }}
                className={`flex-1 py-2 rounded-lg transition flex items-center justify-center gap-1.5 ${
                  activeTab === 'manual'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Search className="w-3.5 h-3.5" /> Search Manually
              </button>
            </div>

            {/* TAB 1: SCAN USING CAMERA */}
            {activeTab === 'camera' && (
              <div className="space-y-3">
                {/* Live Camera Viewport */}
                <div className="relative w-full bg-slate-950 rounded-xl overflow-hidden min-h-[280px] border border-slate-800 flex items-center justify-center">
                  {/* Background QR decoder target container */}
                  <div
                    id="qr-reader-viewport"
                    className={`w-full h-full absolute inset-0 ${scanning ? 'block opacity-0 pointer-events-none' : 'hidden'}`}
                  />

                  {/* Native HTML5 Video Element for live camera feed */}
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`w-full h-[280px] object-cover ${scanning ? 'block' : 'hidden'}`}
                  />

                  {/* Camera Idle Placeholder */}
                  {!scanning && (
                    <div className="p-6 text-center text-slate-400 flex flex-col items-center justify-center">
                      <Camera className="w-12 h-12 mx-auto mb-3 text-teal-400/80" />
                      <h3 className="text-sm font-bold text-slate-200">Camera Live Preview</h3>
                      <p className="text-xs text-slate-400 mt-1 max-w-xs">
                        Point camera at a medicine strip, box, bottle, or barcode to scan.
                      </p>
                      <button
                        onClick={() => startCameraScanner()}
                        className="mt-4 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-2"
                      >
                        <Camera className="w-4 h-4" /> Start Camera
                      </button>
                    </div>
                  )}

                  {/* Scanning targeting overlay */}
                  {scanning && (
                    <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-between p-4">
                      <div className="bg-black/60 backdrop-blur-xs text-[10px] text-teal-300 px-3 py-1 rounded-full font-mono">
                        {facingMode === 'environment' ? 'Rear Camera (Package Scanning)' : 'Front Camera'}
                      </div>
                      <div className="w-48 h-48 border-2 border-teal-400/80 rounded-2xl relative shadow-lg">
                        <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-teal-300"></div>
                        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-teal-300"></div>
                        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-teal-300"></div>
                        <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-teal-300"></div>
                      </div>
                      <div className="text-[11px] text-white/90 bg-black/60 backdrop-blur-xs px-3 py-1 rounded-full">
                        Center medicine name or barcode inside box
                      </div>
                    </div>
                  )}
                </div>

                {/* Camera Control Bar when Active */}
                {scanning && (
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={handleCapturePhoto}
                      disabled={loading}
                      className="flex-1 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center justify-center gap-1.5"
                    >
                      <Camera className="w-4 h-4" /> Capture Package Photo
                    </button>
                    <button
                      onClick={handleSwitchCamera}
                      title="Switch front/rear camera"
                      className="px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
                    >
                      <SwitchCamera className="w-4 h-4" />
                    </button>
                    <button
                      onClick={stopCameraScanner}
                      className="px-3.5 py-2.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5"
                    >
                      <XCircle className="w-4 h-4" /> Stop
                    </button>
                  </div>
                )}

                {/* Specific Camera Error Guidance Banners */}
                {cameraErrorKind && (
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-2">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div className="leading-relaxed">
                        <strong className="block mb-0.5">
                          {cameraErrorKind === 'permission_denied' && 'Camera Permission Denied'}
                          {cameraErrorKind === 'no_camera' && 'No Camera Detected'}
                          {cameraErrorKind === 'in_use' && 'Camera Currently in Use'}
                          {cameraErrorKind === 'insecure' && 'Insecure Connection'}
                          {cameraErrorKind === 'general' && 'Camera Initialization Issue'}
                        </strong>
                        {error}
                      </div>
                    </div>
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => startCameraScanner()}
                        className="px-3 py-1.5 bg-amber-700 hover:bg-amber-800 text-white text-xs font-bold rounded-lg transition flex items-center gap-1"
                      >
                        <RefreshCw className="w-3 h-3" /> Retry Camera
                      </button>
                      <button
                        onClick={() => setActiveTab('upload')}
                        className="px-3 py-1.5 bg-white border border-amber-300 text-amber-800 text-xs font-bold rounded-lg hover:bg-amber-100/50 transition flex items-center gap-1"
                      >
                        <Upload className="w-3 h-3" /> Upload Photo Instead
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: UPLOAD MEDICINE PHOTO */}
            {activeTab === 'upload' && (
              <div className="space-y-4">
                {!selectedFile ? (
                  <label className="border-2 border-dashed border-slate-300 hover:border-teal-500 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-teal-50/30 transition text-center min-h-[220px]">
                    <Upload className="w-10 h-10 text-teal-600 mb-2" />
                    <span className="text-xs font-bold text-slate-800">
                      Upload Medicine Packaging Photo
                    </span>
                    <span className="text-[11px] text-slate-500 mt-1 max-w-xs">
                      Supports photographs of strips, boxes, bottles, syrup labels, prescriptions, or barcodes (JPG, PNG, WEBP).
                    </span>
                    <span className="mt-3 px-3.5 py-1.5 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50">
                      Browse Image File
                    </span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileSelected}
                      className="hidden"
                    />
                  </label>
                ) : (
                  <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50 space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                      <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                        <FileText className="w-4 h-4 text-teal-600" /> Package Image Preview
                      </span>
                      <button
                        onClick={handleClearSelectedFile}
                        className="text-xs text-red-600 hover:text-red-700 font-semibold"
                      >
                        Remove
                      </button>
                    </div>

                    {previewUrl && (
                      <div className="max-h-[200px] overflow-hidden rounded-xl border border-slate-200 bg-white flex items-center justify-center p-2">
                        <img
                          src={previewUrl}
                          alt="Package Preview"
                          className="max-h-[180px] w-auto object-contain"
                        />
                      </div>
                    )}

                    <div className="text-[11px] text-slate-500 flex justify-between">
                      <span className="truncate max-w-[200px]">{selectedFile.name}</span>
                      <span>{(selectedFile.size / 1024).toFixed(1)} KB</span>
                    </div>

                    <button
                      onClick={handleScanUploadedImage}
                      disabled={loading}
                      className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center justify-center gap-2 disabled:bg-slate-300 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Analyzing Medicine Packaging (OCR & Barcode)...
                        </>
                      ) : (
                        <>
                          <QrCode className="w-4 h-4" /> Analyze Medicine Photo
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: SEARCH MEDICINE MANUALLY */}
            {activeTab === 'manual' && (
              <div className="space-y-3">
                <p className="text-xs text-slate-600 leading-relaxed">
                  Enter medicine brand name, active generic name, batch number, or GS1 string:
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="e.g. Dolo 650, Augmentin, BT-1101-1, or Metformin"
                    value={manualInput}
                    onChange={(e) => setManualInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleVerifyQR(manualInput, 'manual_entry')}
                    className="flex-1 bg-slate-50 px-3 py-2 text-xs border border-slate-300 rounded-xl focus:outline-none focus:border-teal-600"
                  />
                  <button
                    onClick={() => handleVerifyQR(manualInput, 'manual_entry')}
                    disabled={!manualInput.trim() || loading}
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-xs disabled:bg-slate-200 disabled:text-slate-400"
                  >
                    Search
                  </button>
                </div>
              </div>
            )}

            {/* General Error Banner (Non-camera) */}
            {error && !cameraErrorKind && (
              <div className="mt-4 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}
          </div>

          {/* Sample Test Packages */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" /> One-Click Test Packages:
            </h2>
            <div className="space-y-2">
              {sampleCodes.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleVerifyQR(s.raw_payload, 'sample_click')}
                  className="w-full text-left p-2.5 rounded-xl border border-slate-100 hover:border-teal-300 hover:bg-teal-50/40 transition group"
                >
                  <div className="flex justify-between items-center mb-0.5">
                    <span className="text-xs font-bold text-slate-800 group-hover:text-teal-900">
                      {s.label}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      s.category === 'AUTHENTIC'
                        ? 'bg-emerald-100 text-emerald-800'
                        : s.category === 'RECALLED'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {s.category}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-snug line-clamp-1">
                    {s.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Verification Result */}
        <div className="lg:col-span-7">
          {loading ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs flex flex-col items-center justify-center min-h-[350px]">
              <RefreshCw className="w-10 h-10 text-teal-600 animate-spin mb-3" />
              <h3 className="text-sm font-bold text-slate-800">Verifying Authoritative Provenance</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Cross-referencing packaging OCR, active pharmaceutical ingredients, and CDSCO national registries...
              </p>
            </div>
          ) : verificationResult ? (
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
              {/* Authenticity Status Header */}
              <div className={`p-5 text-white ${
                verificationResult.is_verified_authentic
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-700'
                  : verificationResult.is_recalled
                  ? 'bg-gradient-to-r from-red-600 to-rose-700'
                  : 'bg-gradient-to-r from-amber-600 to-orange-700'
              }`}>
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[11px] font-mono tracking-wider uppercase opacity-90 block mb-1">
                      CDSCO Regulatory Status
                    </span>
                    <h2 className="text-lg font-black flex items-center gap-2">
                      {verificationResult.authenticity_badge}
                    </h2>
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-white/20 backdrop-blur-xs">
                    {verificationResult.verification_timestamp}
                  </span>
                </div>
                <p className="text-xs mt-2.5 opacity-95 leading-relaxed bg-black/10 p-3 rounded-xl border border-white/10">
                  {verificationResult.authenticity_statement}
                </p>
              </div>

              {/* Action Buttons Bar */}
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap gap-2.5 items-center justify-between">
                <span className="text-xs font-bold text-slate-700">Actions for this medicine:</span>
                <div className="flex gap-2 flex-wrap">
                  {/* Ask AI */}
                  <button
                    onClick={handleAskAIAboutMedicine}
                    className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-purple-200" /> Ask AI About This Medicine
                  </button>

                  {/* Detect Medicine */}
                  <button
                    onClick={handleCheckCompatibility}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" /> Check Compatibility in Detect Medicine
                  </button>

                  {/* Order Online */}
                  <button
                    onClick={handleOrderOnline}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5"
                  >
                    <ShoppingBag className="w-3.5 h-3.5" /> Order from Online Pharmacy
                  </button>

                  {/* Add to My Medicines */}
                  <button
                    onClick={handleAddToMyMedicines}
                    className={`px-3 py-1.5 text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5 ${
                      addedToMyMeds
                        ? 'bg-teal-700 text-white'
                        : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {addedToMyMeds ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-teal-200" /> Added to My Medicines!
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" /> Add to My Medicines
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-5">
                {/* 1. Core Medicine Identity */}
                <div className="border-b pb-4">
                  <span className="text-[10px] font-mono text-teal-700 font-bold uppercase tracking-wider block mb-1">
                    Verified Product Identity:
                  </span>
                  <h3 className="text-xl font-black text-slate-900">
                    {verificationResult.medicine_name}
                  </h3>
                  <div className="text-xs text-slate-600 mt-1 flex flex-wrap gap-x-4 gap-y-1">
                    <span><strong>Generic:</strong> {verificationResult.generic_name}</span>
                    <span><strong>Category:</strong> {verificationResult.therapeutic_category}</span>
                    <span><strong>Form:</strong> {verificationResult.dosage_form} ({verificationResult.strength})</span>
                    <span><strong>Class:</strong> {verificationResult.prescription_classification}</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1.5 flex items-center gap-1">
                    <Building className="w-3.5 h-3.5 text-slate-400" />
                    <span>Manufacturer: <strong>{verificationResult.manufacturer}</strong></span>
                  </div>
                </div>

                {/* 2. Batch & Expiry Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                      Batch Identifier:
                    </span>
                    <div className="text-base font-black font-mono text-slate-900">
                      {verificationResult.batch_number}
                    </div>
                    <span className="text-[10px] text-slate-400 block mt-1">
                      Track & Trace ID: {verificationResult.packaging_metadata.serial_number || 'N/A'}
                    </span>
                  </div>

                  <div className={`p-4 rounded-xl border ${
                    verificationResult.is_expired
                      ? 'bg-red-50 border-red-200 text-red-900'
                      : 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  }`}>
                    <span className="text-[10px] font-bold uppercase tracking-wider block mb-1">
                      Expiry Date:
                    </span>
                    <div className="text-base font-black font-mono">
                      {verificationResult.expiry_date}
                    </div>
                    <span className="text-[10px] block mt-1 font-semibold">
                      {verificationResult.is_expired ? '⚠️ EXPIRED - DO NOT DISPENSE' : '✓ Verified Valid Shelf Life'}
                    </span>
                  </div>
                </div>

                {/* 3. Pregnancy & Lactation Safety Guidance Card */}
                <div className="p-4 bg-purple-50/70 border border-purple-200 rounded-xl">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-purple-900 mb-1">
                    <Baby className="w-4 h-4 text-purple-600" /> Pregnancy & Lactation Safety Note:
                  </div>
                  <p className="text-xs text-purple-800 leading-relaxed">
                    Suitability during pregnancy or breastfeeding depends on gestational age, underlying maternal liver/kidney health, and concurrent medicines. Lowest effective dose for shortest duration; never exceed maximum daily limits. Always confirm with your obstetrician.
                  </p>
                </div>

                {/* 4. Clinical Details */}
                <div className="space-y-3 pt-1">
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Composition:
                    </h4>
                    <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      {verificationResult.composition}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      Approved Clinical Indications:
                    </h4>
                    <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      {verificationResult.safety_information.approved_indications}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                        Common Adverse Effects:
                      </h4>
                      <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {verificationResult.safety_information.known_adverse_effects}
                      </p>
                    </div>

                    <div>
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                        Storage & Handling:
                      </h4>
                      <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {verificationResult.safety_information.storage_information}
                      </p>
                    </div>
                  </div>
                </div>

                {/* 5. Authoritative Source Reference */}
                <div className="pt-3 border-t text-[11px] text-slate-500 flex flex-wrap justify-between items-center gap-2">
                  <span>Registry: <strong>{verificationResult.authoritative_source_name}</strong></span>
                  <span>MRP: <strong>₹{verificationResult.packaging_metadata.mrp?.toFixed(2) || 'N/A'}</strong></span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs flex flex-col items-center justify-center min-h-[350px]">
              <div className="w-16 h-16 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 mb-4">
                <QrCode className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-slate-800">No Medicine Scanned Yet</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Select <strong>Scan Using Camera</strong> to capture live packaging, <strong>Upload Medicine Photo</strong> to upload a strip or box picture, or choose a test sample on the left.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
