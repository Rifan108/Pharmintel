import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles, Send, ShieldCheck, AlertTriangle, BookOpen,
  Info, RefreshCw, User, Bot, Mic, MicOff, Volume2,
  VolumeX, Globe, Radio, Square, Play, Pause, RotateCcw
} from 'lucide-react';
import { api } from '../services/api';
import { speechService } from '../services/speechService';

const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English', speech: 'en-IN' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', speech: 'kn-IN' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', speech: 'hi-IN' },
  { code: 'ml', name: 'Malayalam', native: 'മലയാളം', speech: 'ml-IN' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்', speech: 'ta-IN' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', speech: 'te-IN' },
  { code: 'mr', name: 'Marathi', native: 'मराठी', speech: 'mr-IN' },
];

const LOCALIZED_UI = {
  en: {
    welcome: "Hello! I am the **PharmIntel AI Health Assistant**, powered by verified clinical pharmacology monographs and direct reasoning.\n\nYou can ask general medical, tech, pharmacology, and health questions via text or voice in 7 Indian languages.\n\n*Safety Notice: I provide evidence-based educational pharmacology information and cannot diagnose individual medical emergencies or alter prescriptions.*",
    placeholder: "Ask about medicines, diseases, science, technology, or health in English...",
    speaking: "Voice Assistant Speaking...",
    listening: "Listening to your voice...",
    voiceHint: "Speak clearly into your microphone...",
    tryAsking: "Try asking:",
    autoSpeak: "Speaker On",
    disclaimer: "Educational pharmacology information. Always consult a physician for individual medical advice.",
    samples: [
      "What is artificial intelligence?",
      "Explain the function of the human heart",
      "Why is blood pressure important?",
      "Explain diabetes Type 1 vs Type 2",
      "Difference between bacteria and viruses",
      "Can I take Losartan with Amlodipine?",
      "What are the side effects of Paracetamol?",
      "Why are some medicines taken with food?"
    ]
  },
  kn: {
    welcome: "ನಮಸ್ಕಾರ! ನಾನು **ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ಎಐ ಆರೋಗ್ಯ ಸಹಾಯಕ**, ಅಧಿಕೃತ ವೈದ್ಯಕೀಯ ಮೊನೊಗ್ರಾಫ್‌ಗಳು ಮತ್ತು ಕ್ಲಿನಿಕಲ್ ಜ್ಞಾನದ ಆಧಾರದಲ್ಲಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತೇನೆ.\n\nನೀವು ಧ್ವನಿ (Voice) ಅಥವಾ ಪಠ್ಯ (Text) ಮೂಲಕ ಸಾಮಾನ್ಯ ವಿಜ್ಞಾನ, ಕಾಯಿಲೆಗಳು, ಔಷಧಿಗಳ ಮಾಹಿತಿ ಮತ್ತು ಸುರಕ್ಷತಾ ಮುನ್ನೆಚ್ಚರಿಕೆಗಳನ್ನು ಕನ್ನಡದಲ್ಲಿ ಕೇಳಬಹುದು.\n\n*ಸುರಕ್ಷತಾ ಸೂಚನೆ: ಇದು ಕೇವಲ ಶೈಕ್ಷಣಿಕ ಮಾಹಿತಿಗಾಗಿ ಮಾತ್ರ ಮತ್ತು ಯಾವುದೇ ರೋಗನಿರ್ಣಯ ಅಥವಾ ಔಷಧ ಬರೆದುಕೊಡಲು ಸಾಧ್ಯವಿಲ್ಲ.*",
    placeholder: "ಔಷಧಿಗಳು, ಕಾಯಿಲೆಗಳು ಅಥವಾ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ...",
    speaking: "ಧ್ವನಿ ಸಹಾಯಕ ಮಾತನಾಡುತ್ತಿದೆ...",
    listening: "ನಿಮ್ಮ ಧ್ವನಿಯನ್ನು ಆಲಿಸಲಾಗುತ್ತಿದೆ...",
    voiceHint: "ಮೈಕ್ರೊಫೋನ್‌ನಲ್ಲಿ ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ...",
    tryAsking: "ಉದಾಹರಣೆ ಪ್ರಶ್ನೆಗಳು:",
    autoSpeak: "ಸ್ಪೀಕರ್ ಆನ್",
    disclaimer: "ಶೈಕ್ಷಣಿಕ ಔಷಧೀಯ ಮಾಹಿತಿ ಮಾತ್ರ. ವೈದ್ಯರ ಸಲಹೆಯನ್ನು ತಪ್ಪದೇ ಪಡೆಯಿರಿ.",
    samples: [
      "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ (AI) ಎಂದರೇನು?",
      "ಹೃದಯದ ಕಾರ್ಯವಿಧಾನವನ್ನು ವಿವರಿಸಿ",
      "ರಕ್ತದೊತ್ತಡ ಏಕೆ ಮುಖ್ಯ?",
      "ಮಧುಮೇಹದ ವಿಧಗಳು ಯಾವುವು?",
      "ಲೊಸಾರ್ಟನ್ ಮತ್ತು ಅಮ್ಲೋಡಿಪಿನ್ ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ?",
      "ಪ್ಯಾರಸಿಟಮಾಲ್ ಅಡ್ಡಪರಿಣಾಮಗಳೇನು?"
    ]
  },
  hi: {
    welcome: "नमस्ते! मैं **फार्माइंटेल एआई हेल्थ असिस्टेंट** हूँ, जो सत्यापित क्लिनिकल मोनोग्राफ और फार्माकोलॉजी डेटाबेस द्वारा संचालित है।\n\nआप आवाज़ (Voice) या लिखकर (Text) दवाओं के उपयोग, सामान्य विज्ञान, बीमारियों और सावधानियों के बारे में हिंदी में पूछ सकते हैं।\n\n*सुरक्षा निर्देश: यह केवल शैक्षिक स्वास्थ्य प्रणाली है और किसी बीमारी का निदान या दवा का पर्चा नहीं लिख सकती।*",
    placeholder: "दवाओं के उपयोग, बीमारियों या सावधानियों के बारे में हिंदी में पूछें...",
    speaking: "वॉयस असिस्टेंट बोल रहा है...",
    listening: "आपकी आवाज़ सुनी जा रही है...",
    voiceHint: "कृपया माइक में साफ़-साफ़ बोलें...",
    tryAsking: "सुझाए गए प्रश्न:",
    autoSpeak: "स्पीकर ऑन",
    disclaimer: "केवल शैक्षिक फार्माकोलॉजिकल जानकारी। हमेशा डॉक्टर से परामर्श लें।",
    samples: [
      "आर्टिफिशियल इंटेलिजेंस (AI) क्या है?",
      "मानव हृदय कैसे काम करता है?",
      "ब्लड प्रेशर का क्या महत्व है?",
      "डायबिटीज टाइप 1 और टाइप 2 में क्या अंतर है?",
      "क्या लॉसार्टन और अम्लोडिपिन एक साथ ले सकते हैं?",
      "पैरासिटामोल के क्या साइड इफेक्ट्स हैं?"
    ]
  },
  ml: {
    welcome: "നമസ്കാരം! ഞാൻ **ഫാംഇന്റൽ എഐ ഹെൽത്ത് അസിസ്റ്റന്റ്** ആണ്. സ്ഥിരീകരിച്ച ക്ലിനിക്കൽ മോണോഗ്രാഫുകളുടെ അടിസ്ഥാനത്തിൽ ഞാൻ വിവരങ്ങൾ നൽകുന്നു.\n\nമരുന്നുകളെക്കുറിച്ചും ആരോഗ്യത്തെക്കുറിച്ചും നിങ്ങൾക്ക് ശബ്ദത്തിലൂടെയോ എഴുതിക്കൊണ്ടോ മലയാളത്തിൽ ചോദിക്കാം.",
    placeholder: "മരുന്നുകളെക്കുറിച്ചും ആരോഗ്യത്തെക്കുറിച്ചും മലയാളത്തിൽ ചോദിക്കുക...",
    speaking: "വോയ്‌സ് അസിസ്റ്റന്റ് സംസാരിക്കുന്നു...",
    listening: "ശ്രദ്ധിക്കുന്നു...",
    voiceHint: "മൈക്കിലേക്ക് വ്യക്തമായി സംസാരിക്കുക...",
    tryAsking: "ചോദിച്ചു നോക്കൂ:",
    autoSpeak: "സ്പീക്കർ",
    disclaimer: "വിദ്യാഭ്യാസപരമായ വിവരങ്ങൾ മാത്രം. യോഗ്യതയുള്ള ഡോക്ടറുടെ നിർദ്ദേശം തേടുക.",
    samples: [
      "ഹൃദയത്തിന്റെ പ്രവർത്തനം വിശദീകരിക്കുക",
      "പ്രമേഹം ടൈപ്പ് 1 ഉം 2 ഉം തമ്മിലുള്ള വ്യത്യാസം",
      "വാർഫറിനും ആസ്പിരിനും ഒരുമിച്ച് കഴിക്കാൻ പാടില്ലാത്തത് എന്തുകൊണ്ട്?",
      "പാരസെറ്റമോളിന്റെ പാർശ്വഫലങ്ങൾ"
    ]
  },
  ta: {
    welcome: "வணக்கம்! நான் **பார்ம்இன்டெல் AI சுகாதார உதவியாளர்**. சரிபார்க்கப்பட்ட மருந்தியல் குறிப்புகளின் அடிப்படையில் தகவல்களை வழங்குகிறேன்.\n\nமருந்துகள், அறிவியல் மற்றும் சுகாதாரம் பற்றி தமிழில் குரல் அல்லது உரை வழியாகக் கேட்கலாம்.",
    placeholder: "மருந்துகள் மற்றும் பயன்பாடு குறித்து தமிழில் கேளுங்கள்...",
    speaking: "குரல் உதவியாளர் பேசுகிறது...",
    listening: "உங்கள் குரலைக் கேட்கிறது...",
    voiceHint: "மைக்ரோஃபோனில் தெளிவாகப் பேசுங்கள்...",
    tryAsking: "மாதிரி கேள்விகள்:",
    autoSpeak: "ஒலி பெருக்கி",
    disclaimer: "கல்வி நோக்கங்களுக்கான தகவல் மட்டுமே. மருத்துவரிடம் ஆலோசனை பெறவும்.",
    samples: [
      "மனித இதயத்தின் செயல்பாடு என்ன?",
      "சர்க்கரை நோய் வகைகள் யாவை?",
      "பாராசிட்டமால் பக்க விளைவுகள் என்ன?",
      "உயர் இரத்த அழுத்தம் என்றால் என்ன?"
    ]
  },
  te: {
    welcome: "నమస్కారం! నేను **ఫార్మ్‌ఇంటెల్ AI హెల్త్ అసిస్టెంట్**. ధృవీకరించబడిన క్లినికల్ మోనోగ్రాఫ్‌ల ఆధారంగా పనిచేస్తున్నాను.\n\nమీరు వాయిస్ లేదా టెక్స్ట్ ద్వారా మందులు మరియు ఆరోగ్య సమాచారాన్ని తెలుగులో అడగవచ్చు.",
    placeholder: "మందుల ఉపయోగాలు, విజ్ఞానం గురించి తెలుగులో అడగండి...",
    speaking: "వాయిస్ అసిస్టెంట్ మాట్లాడుతోంది...",
    listening: "మీ వాయిస్ వినబడుతోంది...",
    voiceHint: "మైక్రోఫోన్‌లో స్పష్టంగా మాట్లాడండి...",
    tryAsking: "నమూనా ప్రశ్నలు:",
    autoSpeak: "స్పీకర్ ఆన్",
    disclaimer: "విద్యా సంబంధిత సమాచారం మాత్రమే. వైద్యుడిని సంప్రదించండి.",
    samples: [
      "గుండె ఎలా పనిచేస్తుంది?",
      "రక్తపోటు ప్రాముఖ్యత ఏమిటి?",
      "డయాబెటిస్ రకాలు ఏమిటి?",
      "పారాసిటమాల్ జాగ్రత్తలు ఏమిటి?"
    ]
  },
  mr: {
    welcome: "नमस्कार! मी **फार्मइंटेल एआय आरोग्य सहाय्यक** आहे, जो अधिकृत क्लिनिकल माहिती देतो.\n\nतुम्ही व्हॉईस किंवा मजकूर द्वारे औषधांविषयी मराठीत माहिती विचारू शकता.",
    placeholder: "औषधांचा वापर, दुष्परिणाम याबद्दल मराठीत विचारा...",
    speaking: "व्हॉईस असिस्टंट बोलत आहे...",
    listening: "ऐकत आहे...",
    voiceHint: "मायक्रोफोनमध्ये स्पष्टपणे बोला...",
    tryAsking: "उदाहरणे:",
    autoSpeak: "स्पीकर सुरू",
    disclaimer: "केवळ शैक्षणिक माहिती. नेहमी डॉक्टरांचा सल्ला घ्या.",
    samples: [
      "हृदयाचे कार्य काय आहे?",
      "रक्तदाबाचे महत्त्व काय?",
      "मधुमेहाचे प्रकार कोणते?",
      "पॅरासिटामॉलचे दुष्परिणाम काय?"
    ]
  }
};

export default function AIHealthAssistant() {
  const [selectedLang, setSelectedLang] = useState('en');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [isListening, setIsListening] = useState(false);
  const [speechInterim, setSpeechInterim] = useState('');

  // Unified Speech State from singleton service
  const [speechState, setSpeechState] = useState(() => speechService.getState());
  const [activeSpeakingMsgId, setActiveSpeakingMsgId] = useState(null);

  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const t = LOCALIZED_UI[selectedLang] || LOCALIZED_UI.en;

  // Subscribe to speechService updates
  useEffect(() => {
    const unsubscribe = speechService.subscribe((state) => {
      setSpeechState(state);
      if (state.state === 'idle') {
        setActiveSpeakingMsgId(null);
      }
    });

    return () => {
      unsubscribe();
      speechService.stop();
    };
  }, []);

  // Initialize or update welcome message when language changes
  useEffect(() => {
    speechService.stop();
    setMessages([
      {
        id: 'msg-welcome',
        role: 'assistant',
        content: t.welcome,
        sources: [],
        is_emergency: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  }, [selectedLang]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, speechInterim]);

  // Check for prefilled inquiry from Medicine Scanner or external navigation
  useEffect(() => {
    const prefill = sessionStorage.getItem('pharmintel_assistant_initial_query');
    if (prefill && prefill.trim()) {
      sessionStorage.removeItem('pharmintel_assistant_initial_query');
      setTimeout(() => {
        handleSend(prefill.trim());
      }, 400);
    }
  }, []);

  // Speech-to-Text (STT) Voice Input
  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not natively support Speech Recognition. Please use Chrome, Edge, or Safari, or enter your query via text.");
      return;
    }

    try {
      speechService.stop();

      const recognition = new SpeechRecognition();
      const langMeta = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0];
      recognition.lang = langMeta.speech;
      recognition.interimResults = true;
      recognition.continuous = false;

      recognition.onstart = () => {
        setIsListening(true);
        setSpeechInterim('');
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setSpeechInterim(transcript);

        if (event.results[event.results.length - 1].isFinal) {
          setInput(transcript);
          setIsListening(false);
          setSpeechInterim('');
          handleSend(transcript);
        }
      };

      recognition.onerror = (event) => {
        console.warn("Speech Recognition Error:", event.error);
        setIsListening(false);
        setSpeechInterim('');
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Failed to start voice recognition:", err);
      setIsListening(false);
    }
  };

  const handleClearSession = async () => {
    speechService.stop();
    try {
      await api.clearAssistantSession(sessionId);
    } catch (e) {
      console.warn("Clear session error:", e);
    }
    setMessages([
      {
        id: 'msg-welcome-cleared',
        role: 'assistant',
        content: t.welcome,
        sources: [],
        is_emergency: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const handleSend = async (textToSend) => {
    const queryText = (textToSend || input).trim();
    if (!queryText || loading) return;

    speechService.stop();

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const activePatientName = localStorage.getItem('pharmintel_patient_name') || '';
      const res = await api.chatWithAssistant(
        sessionId,
        queryText,
        selectedLang,
        'ai_assistant',
        activePatientName || undefined
      );

      const msgId = `asst-${Date.now()}`;
      const assistantMessage = {
        id: msgId,
        role: 'assistant',
        content: res.response,
        sources: res.sources || [],
        is_emergency: res.is_emergency,
        guardrail_flag: res.guardrail_flag,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // If user enabled "always speak" and not muted, auto-speak
      if (speechService.getMode() === 'always' && !speechService.isMuted()) {
        setActiveSpeakingMsgId(msgId);
        speechService.speak(res.response, selectedLang, () => {
          setActiveSpeakingMsgId(null);
        });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `asst-err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Error processing consultation: ${err.message}`,
          sources: [],
          is_emergency: false,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleMessagePlay = (msg) => {
    if (activeSpeakingMsgId === msg.id && speechState.isSpeaking) {
      speechService.pause();
    } else if (activeSpeakingMsgId === msg.id && speechState.isPaused) {
      speechService.resume();
    } else {
      setActiveSpeakingMsgId(msg.id);
      speechService.speak(msg.content, selectedLang, () => {
        setActiveSpeakingMsgId(null);
      });
    }
  };

  const handleMessageStop = () => {
    speechService.stop();
    setActiveSpeakingMsgId(null);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Top Banner & Voice Controls Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200">
              Multilingual Voice & Text AI
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
              7 Languages Supported
            </span>
            <span className="text-xs font-mono text-slate-400">Local Reasoning Engine</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-600" /> PharmIntel AI Health Assistant
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ask medicine-information, scientific, or disease questions using voice or text in 7 Indian languages.
          </p>
        </div>

        {/* Global Speaker & Playback Controls Bar */}
        <div className="flex items-center gap-2 flex-wrap self-stretch md:self-auto justify-end">
          {/* Speaker On / Off Toggle (Global Mute) */}
          <button
            onClick={() => speechService.toggleMute()}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 border transition shadow-xs ${
              speechState.isMuted
                ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
                : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'
            }`}
            title={speechState.isMuted ? "Speaker is currently OFF (Muted). Click to turn on." : "Speaker is ON. Click to mute."}
          >
            {speechState.isMuted ? (
              <>
                <VolumeX className="w-4 h-4 text-red-600" />
                <span>Speaker Off</span>
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4 text-emerald-600" />
                <span>Speaker On</span>
              </>
            )}
          </button>

          {/* Speech Playback Mode Dropdown */}
          <select
            value={speechState.mode}
            onChange={(e) => speechService.setMode(e.target.value)}
            className="text-xs font-semibold bg-white border border-slate-300 rounded-xl px-2.5 py-1.5 text-slate-700 shadow-xs focus:outline-none focus:border-purple-600"
            title="Choose when assistant audio plays"
          >
            <option value="always">🔊 Auto-Speak Responses</option>
            <option value="manual">▶️ Manual Audio Playback</option>
            <option value="text_only">🔇 Text Only (No Audio)</option>
          </select>

          {/* Active Audio State Controls */}
          {speechState.isSpeaking && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => speechService.pause()}
                className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition flex items-center gap-1"
                title="Pause speaking"
              >
                <Pause className="w-3.5 h-3.5" /> Pause
              </button>
              <button
                onClick={handleMessageStop}
                className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-red-600 text-white hover:bg-red-700 transition flex items-center gap-1"
                title="Stop speaking"
              >
                <Square className="w-3.5 h-3.5 fill-current" /> Stop
              </button>
            </div>
          )}

          {speechState.isPaused && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => speechService.resume()}
                className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-purple-600 text-white hover:bg-purple-700 transition flex items-center gap-1"
                title="Resume speaking"
              >
                <Play className="w-3.5 h-3.5 fill-current" /> Resume
              </button>
              <button
                onClick={handleMessageStop}
                className="px-2.5 py-1.5 rounded-xl text-xs font-bold bg-red-600 text-white hover:bg-red-700 transition flex items-center gap-1"
                title="Stop speaking"
              >
                <Square className="w-3.5 h-3.5 fill-current" /> Stop
              </button>
            </div>
          )}

          {/* Clear Session */}
          <button
            onClick={handleClearSession}
            className="px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 flex items-center gap-1 shadow-xs transition"
            title="Clear Conversation"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Language Selector Pills */}
      <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-xs mb-4">
        <div className="flex items-center gap-2 mb-2 px-1 text-xs font-bold text-slate-700">
          <Globe className="w-4 h-4 text-purple-600" />
          <span>Consultation Language / ಭಾಷೆ ಆಯ್ಕೆ / भाषा चुनें:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((lang) => {
            const isSelected = selectedLang === lang.code;
            return (
              <button
                key={lang.code}
                onClick={() => setSelectedLang(lang.code)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 border ${
                  isSelected
                    ? 'bg-purple-600 text-white border-purple-600 shadow-xs'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <span>{lang.native}</span>
                <span className={`text-[10px] ${isSelected ? 'text-purple-200' : 'text-slate-400'}`}>
                  ({lang.name})
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col h-[580px] overflow-hidden">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
          {messages.map((msg, idx) => (
            <div
              key={msg.id || idx}
              className={`flex gap-3 text-xs ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 font-bold ${
                  msg.is_emergency
                    ? 'bg-red-600 text-white shadow-sm'
                    : 'bg-purple-600 text-white shadow-xs'
                }`}>
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`relative max-w-[85%] rounded-2xl p-4 shadow-xs ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-none'
                    : msg.is_emergency
                    ? 'bg-red-50 text-red-950 border-2 border-red-300 rounded-tl-none'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
                }`}
              >
                {/* Voice Play/Pause/Stop Buttons for Assistant messages */}
                {msg.role === 'assistant' && (
                  <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
                    {activeSpeakingMsgId === msg.id && speechState.isSpeaking ? (
                      <>
                        <button
                          onClick={() => speechService.pause()}
                          className="p-1 rounded-lg bg-amber-100 text-amber-800 hover:bg-amber-200 transition"
                          title="Pause"
                        >
                          <Pause className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={handleMessageStop}
                          className="p-1 rounded-lg bg-red-100 text-red-700 hover:bg-red-200 transition"
                          title="Stop"
                        >
                          <Square className="w-3.5 h-3.5 fill-current" />
                        </button>
                      </>
                    ) : activeSpeakingMsgId === msg.id && speechState.isPaused ? (
                      <>
                        <button
                          onClick={() => speechService.resume()}
                          className="p-1 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition"
                          title="Resume"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                        </button>
                        <button
                          onClick={handleMessageStop}
                          className="p-1 rounded-lg bg-red-100 text-red-700 hover:bg-red-200 transition"
                          title="Stop"
                        >
                          <Square className="w-3.5 h-3.5 fill-current" />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleMessagePlay(msg)}
                        disabled={speechState.isMuted || speechState.mode === 'text_only'}
                        className={`p-1.5 rounded-lg border transition ${
                          speechState.isMuted || speechState.mode === 'text_only'
                            ? 'opacity-40 cursor-not-allowed bg-slate-50 text-slate-400 border-slate-200'
                            : 'bg-slate-100 text-slate-600 border-slate-200 hover:bg-purple-50 hover:text-purple-700'
                        }`}
                        title="Listen to this explanation"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                )}

                {/* Content with markdown formatting */}
                <div className="whitespace-pre-line leading-relaxed pr-12">
                  {msg.content}
                </div>

                {/* Cited Sources Badge */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                    <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider flex items-center gap-1">
                      <BookOpen className="w-3 h-3 text-teal-600" /> Grounded In Verified Monographs:
                    </span>
                    {msg.sources.map((src, sIdx) => (
                      <div key={sIdx} className="bg-slate-50 p-2 rounded text-[10px] border border-slate-200/80">
                        <span className="font-bold text-slate-800">{src.title}</span>
                        <span className="text-slate-500 block">Source: {src.reference_source} • Verified: {src.verification_date}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className={`text-[9px] mt-2 flex justify-end ${
                  msg.role === 'user' ? 'text-blue-200' : 'text-slate-400'
                }`}>
                  {msg.timestamp}
                </div>
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-800 flex items-center justify-center shrink-0 font-bold">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {/* Real-time Voice Listening Indicator */}
          {isListening && (
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-2xl flex items-center gap-3 animate-pulse">
              <div className="w-9 h-9 rounded-full bg-red-600 text-white flex items-center justify-center shadow-md animate-ping">
                <Mic className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="text-xs font-bold text-purple-900 flex items-center gap-2">
                  <span>{t.listening}</span>
                  <span className="px-2 py-0.5 rounded bg-purple-200 text-purple-800 text-[10px]">
                    {LANGUAGES.find(l => l.code === selectedLang)?.native}
                  </span>
                </div>
                <div className="text-xs text-purple-700 mt-0.5 italic">
                  {speechInterim || t.voiceHint}
                </div>
              </div>
              <button
                onClick={toggleListening}
                className="px-3 py-1.5 rounded-xl bg-purple-600 text-white text-xs font-bold hover:bg-purple-700 transition"
              >
                Done
              </button>
            </div>
          )}

          {loading && (
            <div className="flex gap-3 text-xs items-center text-slate-400 p-2">
              <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                <RefreshCw className="w-4 h-4 animate-spin" />
              </div>
              <span className="italic">Synthesizing clinical knowledge in {LANGUAGES.find(l => l.code === selectedLang)?.native}...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Suggested Queries */}
        <div className="px-4 py-2 bg-slate-100/70 border-t border-slate-200 flex flex-wrap gap-2 text-[11px] overflow-x-auto max-h-24">
          <span className="text-slate-500 font-bold self-center shrink-0">{t.tryAsking}</span>
          {t.samples.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSend(p)}
              disabled={loading}
              className="px-2.5 py-1 bg-white hover:bg-purple-50 hover:text-purple-800 text-slate-600 border border-slate-200 rounded-lg transition text-[11px] shadow-2xs whitespace-nowrap"
            >
              {p}
            </button>
          ))}
        </div>

        {/* Text & Voice Input Bar */}
        <div className="p-3 bg-white border-t border-slate-200 flex gap-2 items-center">
          <button
            onClick={toggleListening}
            disabled={loading}
            className={`p-2.5 rounded-xl transition flex items-center justify-center shadow-xs shrink-0 ${
              isListening
                ? 'bg-red-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-700 hover:bg-purple-100 hover:text-purple-700'
            }`}
            title={isListening ? "Stop listening" : "Speak your question"}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={t.placeholder}
            disabled={loading}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-purple-600 focus:bg-white transition"
          />

          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl transition shadow-xs flex items-center gap-1.5 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed shrink-0"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>

      <div className="mt-3 text-center text-[11px] text-slate-400">
        {t.disclaimer}
      </div>
    </div>
  );
}
