import React, { useState, useEffect, useRef } from 'react';
import {
  X, Send, Stethoscope, ShieldCheck, User, Mic, MicOff,
  Volume2, VolumeX, AlertTriangle, ArrowRight, RefreshCw,
  PhoneCall, CheckCircle2, Globe, Clock, ShieldAlert,
  Play, Square, MessageSquare, Headphones, RotateCcw,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

const SUPPORTED_LANGS = [
  { code: 'en', name: 'English', native: 'English', speech: 'en-IN' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', speech: 'kn-IN' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', speech: 'hi-IN' },
  { code: 'ml', name: 'Malayalam', native: 'മലയാളം', speech: 'ml-IN' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்', speech: 'ta-IN' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', speech: 'te-IN' },
  { code: 'mr', name: 'Marathi', native: 'मराठी', speech: 'mr-IN' },
];

export default function LivePharmacistModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const { language: initialLang } = useLanguage();
  const [activeTab, setActiveTab] = useState('voice'); // 'voice' | 'text'
  const [selectedLang, setSelectedLang] = useState(initialLang || 'en');
  const [patientName, setPatientName] = useState(() => localStorage.getItem('pharmintel_patient_name') || '');
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState('');
  const [sessionId] = useState(() => `live_supp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);

  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'pharmacist',
      name: 'PharmIntel AI Live Support Assistant',
      time: 'Just now',
      text: "Hello! I am the PharmIntel AI Live Support Assistant. I provide 24/7 evidence-based guidance on medications, drug interactions, and general health. How can I assist you today?"
    }
  ]);
  const [msgInput, setMsgInput] = useState('');
  const [latestUserTranscript, setLatestUserTranscript] = useState('');
  const [latestAiResponse, setLatestAiResponse] = useState(
    "Hello! I am the PharmIntel AI Live Support Assistant. I provide 24/7 evidence-based guidance on medications, drug interactions, and general health. How can I assist you today?"
  );

  // Assistant State: 'idle' | 'listening' | 'processing' | 'speaking'
  const [assistantState, setAssistantState] = useState('idle');
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [speakerEnabled, setSpeakerEnabled] = useState(true);

  const recognitionRef = useRef(null);
  const isConversationActiveRef = useRef(false);
  const isMutedRef = useRef(false);
  const speakerEnabledRef = useRef(true);
  const messagesEndRef = useRef(null);

  // Sync refs with state
  useEffect(() => {
    isConversationActiveRef.current = isConversationActive;
  }, [isConversationActive]);

  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  useEffect(() => {
    speakerEnabledRef.current = speakerEnabled;
  }, [speakerEnabled]);

  // Escalation Drawer State
  const [isEscalateModalOpen, setIsEscalateModalOpen] = useState(false);
  const [escalating, setEscalating] = useState(false);
  const [escalationResult, setEscalationResult] = useState(null);
  const [escalateNotes, setEscalateNotes] = useState('');

  // Auto-scroll chat in text mode
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, assistantState]);

  // Sync patient name with storage events
  useEffect(() => {
    const handleStorage = () => {
      setPatientName(localStorage.getItem('pharmintel_patient_name') || '');
    };
    window.addEventListener('storage', handleStorage);
    window.addEventListener('patientNameUpdated', handleStorage);
    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('patientNameUpdated', handleStorage);
    };
  }, []);

  // Web Speech API Initialization
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      const langMeta = SUPPORTED_LANGS.find(l => l.code === selectedLang) || SUPPORTED_LANGS[0];
      recognition.lang = langMeta.speech;

      recognition.onstart = () => {
        if (!isMutedRef.current) {
          setAssistantState('listening');
        }
      };

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        if (interim) {
          setLatestUserTranscript(interim);
        }
        if (final) {
          setLatestUserTranscript(final);
          handleVoiceInputReceived(final);
        }
      };

      recognition.onerror = (e) => {
        console.warn('Speech recognition error:', e.error);
        if (assistantState === 'listening') {
          setAssistantState('idle');
        }
        // If conversation active and not aborted, restart listening after pause
        if (isConversationActiveRef.current && e.error !== 'aborted') {
          setTimeout(() => {
            if (isConversationActiveRef.current && !isMutedRef.current) {
              startListeningSafe();
            }
          }, 1000);
        }
      };

      recognition.onend = () => {
        if (assistantState === 'listening') {
          setAssistantState('idle');
        }
        // Auto-restart if conversation is active and we are not speaking or processing
        if (isConversationActiveRef.current && assistantState === 'idle' && !isMutedRef.current) {
          setTimeout(() => {
            if (isConversationActiveRef.current && !isMutedRef.current) {
              startListeningSafe();
            }
          }, 600);
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }
      window.speechSynthesis?.cancel();
    };
  }, [selectedLang]);

  const startListeningSafe = () => {
    if (!recognitionRef.current) return;
    try {
      window.speechSynthesis?.cancel();
      const langMeta = SUPPORTED_LANGS.find(l => l.code === selectedLang) || SUPPORTED_LANGS[0];
      recognitionRef.current.lang = langMeta.speech;
      recognitionRef.current.start();
    } catch (err) {
      // recognition may already be started
    }
  };

  const stopListeningSafe = () => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch (err) {}
  };

  // Text-to-Speech (TTS)
  const speakText = (text, onCompleteCallback) => {
    if (!('speechSynthesis' in window)) {
      if (onCompleteCallback) onCompleteCallback();
      return;
    }

    window.speechSynthesis.cancel();

    if (!speakerEnabledRef.current) {
      setAssistantState('idle');
      if (onCompleteCallback) onCompleteCallback();
      return;
    }

    const cleanText = text.replace(/[*#_`]/g, '').slice(0, 400);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    const langMeta = SUPPORTED_LANGS.find(l => l.code === selectedLang) || SUPPORTED_LANGS[0];
    utterance.lang = langMeta.speech;
    utterance.rate = 1.0;

    utterance.onstart = () => {
      setAssistantState('speaking');
    };

    utterance.onend = () => {
      setAssistantState('idle');
      if (onCompleteCallback) {
        onCompleteCallback();
      }
    };

    utterance.onerror = () => {
      setAssistantState('idle');
      if (onCompleteCallback) {
        onCompleteCallback();
      }
    };

    window.speechSynthesis.speak(utterance);
  };

  const pauseSpeaking = () => {
    if (window.speechSynthesis?.speaking && !window.speechSynthesis?.paused) {
      window.speechSynthesis.pause();
      setAssistantState('paused');
    }
  };

  const resumeSpeaking = () => {
    if (window.speechSynthesis?.paused) {
      window.speechSynthesis.resume();
      setAssistantState('speaking');
    }
  };

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setAssistantState('idle');
  };

  // Conversation control
  const handleStartConversation = () => {
    window.speechSynthesis?.cancel();
    setIsConversationActive(true);
    setIsMuted(false);
    startListeningSafe();
  };

  const handleEndConversation = () => {
    setIsConversationActive(false);
    stopListeningSafe();
    stopSpeaking();
    setAssistantState('idle');
  };

  const handleToggleMute = () => {
    if (isMuted) {
      setIsMuted(false);
      if (isConversationActive) {
        startListeningSafe();
      }
    } else {
      setIsMuted(true);
      stopListeningSafe();
      if (assistantState === 'listening') {
        setAssistantState('idle');
      }
    }
  };

  // Core Assistant Processing
  const handleVoiceInputReceived = async (textToSend) => {
    if (!textToSend.trim()) return;

    stopListeningSafe();
    setAssistantState('processing');

    const userText = textToSend.trim();
    const currentName = patientName.trim() ? patientName.trim() : 'Patient';

    setChatMessages(prev => [
      ...prev,
      {
        sender: 'patient',
        name: currentName,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: userText
      }
    ]);

    try {
      const data = await api.chatWithAssistant(
        sessionId,
        userText,
        selectedLang,
        'live_support',
        patientName.trim() || undefined
      );

      const replyText = data.response || "I have analyzed your clinical query. Please ensure all medications and dosages are reviewed with your physician.";
      setLatestAiResponse(replyText);

      setChatMessages(prev => [
        ...prev,
        {
          sender: 'pharmacist',
          name: 'PharmIntel AI Live Support Assistant',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: replyText,
          isEmergency: data.is_emergency
        }
      ]);

      speakText(replyText);
    } catch (err) {
      const errorMsg = `Connection issue: ${err.message || 'Please retry your clinical query.'}`;
      setLatestAiResponse(errorMsg);
      setAssistantState('idle');
      setChatMessages(prev => [
        ...prev,
        {
          sender: 'pharmacist',
          name: 'PharmIntel System',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: errorMsg
        }
      ]);
      if (isConversationActiveRef.current && !isMutedRef.current) {
        setTimeout(startListeningSafe, 1500);
      }
    }
  };

  // Text message send
  const handleSendText = async (e) => {
    e.preventDefault();
    if (!msgInput.trim() || assistantState === 'processing') return;

    const userText = msgInput.trim();
    setMsgInput('');
    setLatestUserTranscript(userText);
    await handleVoiceInputReceived(userText);
  };

  const handleClearHistory = async () => {
    stopSpeaking();
    stopListeningSafe();
    setIsConversationActive(false);
    setAssistantState('idle');
    try {
      await api.clearAssistantSession(sessionId);
    } catch (e) {
      console.warn("Session clear error:", e);
    }
    const welcome = "Conversation reset. How can I assist you with your medications today?";
    setLatestAiResponse(welcome);
    setLatestUserTranscript('');
    setChatMessages([
      {
        sender: 'pharmacist',
        name: 'PharmIntel AI Live Support Assistant',
        time: 'Just now',
        text: welcome
      }
    ]);
  };

  const handleEscalateSubmit = async () => {
    setEscalating(true);
    try {
      const res = await api.escalateToPharmacist(sessionId, patientName || "Patient name not provided", escalateNotes);
      setEscalationResult(res);
      setChatMessages(prev => [
        ...prev,
        {
          sender: 'pharmacist',
          name: 'Clinical Dispatch Hub',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `🚨 Pharmacist Escalation Ticket #${res.ticket_id} generated.\nAssigned Clinician: ${res.assigned_pharmacist} (${res.license_no}). Direct Line: ${res.contact_phone}. Our team is reviewing your profile.`
        }
      ]);
    } catch (e) {
      alert(`Escalation failed: ${e.message}`);
    } finally {
      setEscalating(false);
    }
  };

  const handleSavePatientName = () => {
    const trimmed = tempName.trim();
    setPatientName(trimmed);
    localStorage.setItem('pharmintel_patient_name', trimmed);
    window.dispatchEvent(new Event('patientNameUpdated'));
    setIsEditingName(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full h-[680px] shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-fade-in relative">
        {/* Top Header */}
        <div className="p-4 bg-gradient-to-r from-[#102A56] via-[#1A3D7C] to-[#2166F5] text-white flex justify-between items-center shadow-xs">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-11 h-11 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20 text-white shadow-xs">
                <Stethoscope className="w-6 h-6 text-cyan-300" />
              </div>
              <span className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full ring-2 ring-[#102A56] ${
                assistantState === 'listening' ? 'bg-emerald-400 animate-pulse' :
                assistantState === 'processing' ? 'bg-amber-400 animate-spin' :
                assistantState === 'speaking' ? 'bg-cyan-400 animate-bounce' : 'bg-emerald-400'
              }`}></span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-black block leading-tight">PHARMINTEL Multilingual AI Voice Assistant</span>
                <span className="bg-emerald-500/30 text-emerald-300 text-[9px] font-bold px-1.5 py-0.5 rounded border border-emerald-400/30">
                  CLINICAL LIVE
                </span>
              </div>
              <div className="text-[11px] text-blue-100 flex items-center gap-2 mt-0.5">
                <span>PharmIntel AI Live Support</span>
                <span>•</span>
                {isEditingName ? (
                  <div className="inline-flex items-center gap-1 bg-white/20 px-2 py-0.5 rounded-md">
                    <input
                      type="text"
                      value={tempName}
                      onChange={(e) => setTempName(e.target.value)}
                      placeholder="Patient name..."
                      className="bg-transparent text-white font-bold text-[10px] outline-none w-28"
                      autoFocus
                    />
                    <button onClick={handleSavePatientName} className="text-emerald-300 font-bold text-[10px]">Save</button>
                    <button onClick={() => setIsEditingName(false)} className="text-white/70 text-[10px]">✕</button>
                  </div>
                ) : (
                  <button
                    onClick={() => { setTempName(patientName); setIsEditingName(true); }}
                    className="hover:underline flex items-center gap-1 text-white font-bold"
                    title="Click to edit patient name"
                  >
                    Patient: {patientName.trim() ? patientName : <span className="italic opacity-80">Patient name not provided</span>}
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setIsEscalateModalOpen(true)}
              className="px-2.5 py-1 bg-amber-400 hover:bg-amber-300 text-slate-900 text-[10px] font-black rounded-lg transition shadow-xs flex items-center gap-1"
              title="Escalate to Registered Pharmacist"
            >
              <PhoneCall className="w-3 h-3" /> Escalate
            </button>
            <button
              onClick={handleClearHistory}
              className="p-1.5 text-blue-200 hover:text-white rounded-lg transition"
              title="Clear Session"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => {
                handleEndConversation();
                onClose();
              }}
              className="p-1.5 text-white/80 hover:text-white rounded-lg transition ml-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Mode Switcher Tabs & Language Controls */}
        <div className="px-4 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs">
          {/* Tab Switcher */}
          <div className="flex items-center bg-slate-200/80 p-0.5 rounded-xl">
            <button
              onClick={() => setActiveTab('voice')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition ${
                activeTab === 'voice'
                  ? 'bg-white text-[#2166F5] shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Headphones className="w-3.5 h-3.5" /> Live Voice Support
            </button>
            <button
              onClick={() => setActiveTab('text')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition ${
                activeTab === 'text'
                  ? 'bg-white text-[#2166F5] shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" /> Text Support
            </button>
          </div>

          {/* Language Selector & Speaker Toggle */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-[#2166F5]" />
              <select
                value={selectedLang}
                onChange={(e) => {
                  stopSpeaking();
                  stopListeningSafe();
                  setSelectedLang(e.target.value);
                }}
                className="bg-white border border-slate-200 rounded-lg px-2 py-0.5 text-[11px] font-bold text-slate-800 outline-none focus:border-[#2166F5]"
              >
                {SUPPORTED_LANGS.map(l => (
                  <option key={l.code} value={l.code}>{l.native} ({l.name})</option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setSpeakerEnabled(!speakerEnabled)}
              className={`p-1.5 rounded-lg border text-xs font-bold transition flex items-center gap-1 ${
                speakerEnabled
                  ? 'bg-blue-50 text-[#2166F5] border-blue-200'
                  : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}
              title={speakerEnabled ? 'Speaker Enabled' : 'Speaker Muted'}
            >
              {speakerEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* TAB 1: LIVE VOICE SUPPORT MODE */}
        {activeTab === 'voice' && (
          <div className="flex-1 flex flex-col justify-between p-6 bg-gradient-to-b from-[#F5F8FF] to-white overflow-y-auto">
            {/* Visual State & Animated Waveform Centerpiece */}
            <div className="flex-1 flex flex-col items-center justify-center py-4 space-y-4">
              {/* Dynamic State Pill */}
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-xs ${
                  assistantState === 'listening'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 animate-pulse'
                    : assistantState === 'processing'
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : assistantState === 'speaking'
                    ? 'bg-purple-100 text-purple-800 border border-purple-300'
                    : 'bg-slate-200 text-slate-700 border border-slate-300'
                }`}>
                  <span className={`w-2 h-2 rounded-full ${
                    assistantState === 'listening' ? 'bg-emerald-500' :
                    assistantState === 'processing' ? 'bg-amber-500 animate-ping' :
                    assistantState === 'speaking' ? 'bg-purple-500 animate-ping' : 'bg-slate-400'
                  }`} />
                  {assistantState === 'listening' && `Listening in ${SUPPORTED_LANGS.find(l => l.code === selectedLang)?.name}...`}
                  {assistantState === 'processing' && 'Processing Clinical Query...'}
                  {assistantState === 'speaking' && 'AI Assistant is Responding...'}
                  {assistantState === 'idle' && (isConversationActive ? 'Ready — Waiting to speak' : 'Assistant Idle')}
                </span>
              </div>

              {/* Animated Waveform & Avatar Orb */}
              <div className="relative flex items-center justify-center my-2">
                {/* Outer Glow Rings */}
                <div className={`w-36 h-36 rounded-full transition-all duration-700 flex items-center justify-center ${
                  assistantState === 'listening'
                    ? 'bg-emerald-500/10 ring-8 ring-emerald-500/20 scale-105'
                    : assistantState === 'processing'
                    ? 'bg-amber-500/10 ring-8 ring-amber-500/20 animate-spin'
                    : assistantState === 'speaking'
                    ? 'bg-[#2166F5]/10 ring-8 ring-[#2166F5]/25 scale-105'
                    : 'bg-slate-100 ring-2 ring-slate-200'
                }`}>
                  {/* Central Orb / Large Mic Button */}
                  <button
                    onClick={isConversationActive ? (assistantState === 'speaking' ? stopSpeaking : handleToggleMute) : handleStartConversation}
                    className={`w-24 h-24 rounded-full flex items-center justify-center shadow-xl transition-all duration-300 ${
                      assistantState === 'listening'
                        ? 'bg-gradient-to-tr from-emerald-500 to-teal-400 text-white shadow-emerald-500/40 scale-105'
                        : assistantState === 'processing'
                        ? 'bg-gradient-to-tr from-amber-500 to-orange-400 text-white shadow-amber-500/40'
                        : assistantState === 'speaking'
                        ? 'bg-gradient-to-tr from-[#2166F5] to-indigo-600 text-white shadow-blue-500/40 scale-105'
                        : 'bg-gradient-to-tr from-[#102A56] to-[#2166F5] text-white hover:scale-105'
                    }`}
                    title={isConversationActive ? (isMuted ? "Unmute Mic" : "Mute Mic") : "Start Conversation"}
                  >
                    {assistantState === 'speaking' ? (
                      <Square className="w-8 h-8 fill-current" />
                    ) : isMuted ? (
                      <MicOff className="w-9 h-9" />
                    ) : (
                      <Mic className={`w-10 h-10 ${assistantState === 'listening' ? 'animate-bounce' : ''}`} />
                    )}
                  </button>
                </div>
              </div>

              {/* Animated Waveform Bars */}
              <div className="flex items-center justify-center gap-1.5 h-12 w-full max-w-xs">
                {[...Array(12)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-1.5 rounded-full transition-all duration-300 ${
                      assistantState === 'speaking'
                        ? 'bg-gradient-to-t from-[#2166F5] to-cyan-400 voice-wave-bar'
                        : assistantState === 'listening'
                        ? 'bg-gradient-to-t from-emerald-500 to-teal-300 voice-wave-bar'
                        : assistantState === 'processing'
                        ? 'bg-amber-400 h-2'
                        : 'bg-slate-200 h-1.5'
                    }`}
                  />
                ))}
              </div>

              {/* Speech Recognition Text Display */}
              <div className="w-full max-w-lg bg-white rounded-2xl p-3 border border-slate-200 shadow-xs text-xs space-y-1">
                <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  <span>You Spoke ({SUPPORTED_LANGS.find(l => l.code === selectedLang)?.name})</span>
                  {assistantState === 'listening' && <span className="text-emerald-600 font-bold animate-pulse">● Listening</span>}
                </div>
                <p className="text-slate-800 font-semibold min-h-[22px] leading-snug">
                  {latestUserTranscript || <span className="text-slate-400 italic font-normal">Click 'Start Conversation' or speak into the microphone...</span>}
                </p>
              </div>

              {/* AI Response Display Card */}
              <div className="w-full max-w-lg bg-blue-50/70 rounded-2xl p-3.5 border border-blue-200/80 shadow-xs text-xs space-y-2">
                <div className="flex justify-between items-center text-[10px] font-bold text-[#102A56] uppercase tracking-wider">
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-[#2166F5]" /> Clinical Guidance
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => speakText(latestAiResponse)}
                      className="hover:text-[#2166F5] flex items-center gap-1 font-bold text-[10px]"
                      title="Replay Response"
                    >
                      <RotateCcw className="w-3 h-3" /> Replay
                    </button>
                    {assistantState === 'speaking' && (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={pauseSpeaking}
                          className="text-amber-700 font-bold hover:underline text-[10px]"
                        >
                          Pause
                        </button>
                        <button
                          onClick={stopSpeaking}
                          className="text-red-600 font-bold hover:underline text-[10px]"
                        >
                          Stop Audio
                        </button>
                      </div>
                    )}
                    {assistantState === 'paused' && (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={resumeSpeaking}
                          className="text-purple-700 font-bold hover:underline text-[10px]"
                        >
                          Resume
                        </button>
                        <button
                          onClick={stopSpeaking}
                          className="text-red-600 font-bold hover:underline text-[10px]"
                        >
                          Stop Audio
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                <p className="text-slate-800 leading-relaxed font-medium">
                  {latestAiResponse}
                </p>
              </div>
            </div>

            {/* Bottom Controls Bar */}
            <div className="pt-3 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {!isConversationActive ? (
                  <button
                    onClick={handleStartConversation}
                    className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl text-xs font-black shadow-md flex items-center gap-2 transition"
                  >
                    <Play className="w-4 h-4 fill-current" /> Start Conversation
                  </button>
                ) : (
                  <button
                    onClick={handleEndConversation}
                    className="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-black shadow-md flex items-center gap-2 transition"
                  >
                    <Square className="w-4 h-4 fill-current" /> End Conversation
                  </button>
                )}

                {isConversationActive && (
                  <button
                    onClick={handleToggleMute}
                    className={`px-3 py-2 rounded-xl text-xs font-bold border transition flex items-center gap-1.5 ${
                      isMuted
                        ? 'bg-amber-100 text-amber-900 border-amber-300'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
                    }`}
                  >
                    {isMuted ? <MicOff className="w-4 h-4 text-amber-700" /> : <Mic className="w-4 h-4" />}
                    {isMuted ? 'Muted' : 'Mute Mic'}
                  </button>
                )}
              </div>

              <div className="text-[11px] text-slate-500 font-medium">
                {isConversationActive
                  ? "Continuous listening active. Speak freely."
                  : "Click 'Start Conversation' to begin hands-free dialogue."}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TEXT SUPPORT CHAT MODE */}
        {activeTab === 'text' && (
          <div className="flex-1 flex flex-col justify-between overflow-hidden bg-[#F5F8FF]">
            {/* Message Log */}
            <div className="flex-1 p-4 overflow-y-auto space-y-3.5">
              {chatMessages.map((m, idx) => {
                const isUser = m.sender === 'patient';
                return (
                  <div
                    key={idx}
                    className={`flex gap-2.5 text-xs ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    {!isUser && (
                      <div className="w-8 h-8 rounded-xl bg-blue-100 text-[#2166F5] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                        <Stethoscope className="w-4 h-4" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] p-3.5 rounded-2xl shadow-xs leading-relaxed ${
                        isUser
                          ? 'bg-[#2166F5] text-white rounded-tr-none'
                          : m.isEmergency
                          ? 'bg-red-50 border border-red-300 text-red-950 rounded-tl-none'
                          : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none'
                      }`}
                    >
                      <div className="text-[10px] font-bold opacity-75 mb-1 flex justify-between gap-4">
                        <span>{m.name}</span>
                        <span>{m.time}</span>
                      </div>
                      <div className="whitespace-pre-wrap">{m.text}</div>
                      {!isUser && (
                        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                          <span>CDSCO / BNF 86 Curated</span>
                          <button
                            onClick={() => speakText(m.text)}
                            className="hover:text-[#2166F5] flex items-center gap-1 font-bold text-[10px]"
                          >
                            <Volume2 className="w-3.5 h-3.5" /> Listen
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {assistantState === 'processing' && (
                <div className="flex gap-2.5 text-xs items-center text-slate-500">
                  <div className="w-8 h-8 rounded-xl bg-blue-50 text-[#2166F5] flex items-center justify-center">
                    <div className="w-4 h-4 border-2 border-[#2166F5] border-t-transparent rounded-full animate-spin"></div>
                  </div>
                  <span className="italic font-medium">Assistant is evaluating against clinical databases...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSendText} className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
              <button
                type="button"
                onClick={startListeningSafe}
                className={`p-2.5 rounded-xl border transition flex items-center justify-center ${
                  assistantState === 'listening'
                    ? 'bg-red-500 text-white border-red-600 animate-pulse'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200'
                }`}
                title="Speak message"
              >
                <Mic className="w-4 h-4" />
              </button>

              <input
                type="text"
                placeholder={`Ask PharmIntel AI in ${SUPPORTED_LANGS.find(l => l.code === selectedLang)?.name}...`}
                value={msgInput}
                onChange={(e) => setMsgInput(e.target.value)}
                disabled={assistantState === 'processing'}
                className="flex-1 bg-slate-50 px-3.5 py-2.5 rounded-xl text-xs border border-slate-200 focus:outline-none focus:border-[#2166F5] focus:bg-white transition"
              />

              <button
                type="submit"
                disabled={!msgInput.trim() || assistantState === 'processing'}
                className="px-4 py-2.5 bg-[#2166F5] hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50 shadow-xs"
              >
                <Send className="w-3.5 h-3.5" /> Send
              </button>
            </form>
          </div>
        )}

        {/* Escalation Modal Drawer Overlay */}
        {isEscalateModalOpen && (
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-sm w-full p-5 shadow-2xl border border-slate-200 space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <h3 className="text-sm font-extrabold text-[#102A56] flex items-center gap-1.5">
                  <PhoneCall className="w-4 h-4 text-[#2166F5]" /> Escalate to Human Pharmacist
                </h3>
                <button
                  onClick={() => {
                    setIsEscalateModalOpen(false);
                    setEscalationResult(null);
                  }}
                  className="p-1 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {!escalationResult ? (
                <div className="space-y-3 text-xs">
                  <p className="text-slate-600 leading-relaxed">
                    Escalate this conversation to our registered on-duty human clinical pharmacist for formal clinical review:
                  </p>
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Patient Name</label>
                    <input
                      type="text"
                      value={patientName}
                      onChange={(e) => {
                        setPatientName(e.target.value);
                        localStorage.setItem('pharmintel_patient_name', e.target.value);
                      }}
                      placeholder="Enter Patient Name..."
                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 font-bold text-slate-800"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Clinical Notes / Reason</label>
                    <textarea
                      rows={2}
                      value={escalateNotes}
                      onChange={(e) => setEscalateNotes(e.target.value)}
                      placeholder="e.g. Needs dosage adjustment or allergy cross-reactivity evaluation..."
                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 text-slate-800"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setIsEscalateModalOpen(false)}
                      className="px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700 font-bold"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleEscalateSubmit}
                      disabled={escalating}
                      className="px-4 py-1.5 rounded-xl bg-[#2166F5] text-white font-bold flex items-center gap-1 shadow-xs"
                    >
                      {escalating ? 'Routing...' : 'Confirm Escalation'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 text-xs">
                  <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200 text-emerald-900 space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-emerald-800">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Ticket Created: {escalationResult.ticket_id}
                    </div>
                    <p className="text-[11px] leading-relaxed">
                      Assigned Clinician: <b>{escalationResult.assigned_pharmacist}</b><br/>
                      Direct Phone: <b>{escalationResult.contact_phone}</b>
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setIsEscalateModalOpen(false);
                      setEscalationResult(null);
                    }}
                    className="w-full py-2 bg-[#2166F5] text-white font-bold rounded-xl"
                  >
                    Return to Live Support
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
