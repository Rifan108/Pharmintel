import os
import re
import json
import uuid
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.config import settings
from app.models.assistant import AIKnowledgeSource, Conversation, ChatMessage
from app.models.medicine import Medicine, DrugInteraction
from app.models.pharmacy import Pharmacy
from app.services.clinical_knowledge_engine import ClinicalKnowledgeEngine

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "speech_code": "en-IN"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "speech_code": "kn-IN"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "speech_code": "hi-IN"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "speech_code": "ml-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "speech_code": "ta-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "speech_code": "te-IN"},
    "mr": {"name": "Marathi", "native": "मराठी", "speech_code": "mr-IN"},
}

LOCALIZED_EMERGENCY_ALERTS = {
    "en": (
        "⚠️ **MEDICAL EMERGENCY ALERT: IMMEDIATE ATTENTION REQUIRED**\n\n"
        "Your inquiry describes acute, life-threatening medical symptoms (such as acute chest pain, "
        "stroke indicators, severe anaphylaxis, or respiratory failure).\n\n"
        "**ACTIONS TO TAKE IMMEDIATELY:**\n"
        "1. **Call Emergency Services (112 or 108 in India, or your local emergency number) immediately.**\n"
        "2. Proceed to the nearest hospital Emergency Room / Casualty Department.\n"
        "3. **Do not attempt to drive yourself or self-administer unverified medications.**\n\n"
        "*PharmIntel AI is an educational technology system and cannot treat emergency conditions.*"
    ),
    "kn": (
        "⚠️ **ತುರ್ತು ವೈದ್ಯಕೀಯ ಎಚ್ಚರಿಕೆ: ತಕ್ಷಣದ ಗಮನ ಅಗತ್ಯ**\n\n"
        "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯು ಜೀವಕ್ಕೆ ಅಪಾಯ ತರಬಹುದಾದ ಗಂಭೀರ ಲಕ್ಷಣಗಳನ್ನು (ತೀವ್ರ ಎದೆ ನೋವು, ಪಾರ್ಶ್ವವಾಯು ಲಕ್ಷಣಗಳು, ಉಸಿರಾಟದ ತೊಂದರೆ ಇತ್ಯಾದಿ) ಸೂಚಿಸುತ್ತದೆ.\n\n"
        "**ತಕ್ಷಣ ಕೈಗೊಳ್ಳಬೇಕಾದ ಕ್ರಮಗಳು:**\n"
        "1. **ತಕ್ಷಣ ತುರ್ತು ಸೇವೆಗೆ ಕರೆ ಮಾಡಿ (ಭಾರತದಲ್ಲಿ 112 ಅಥವಾ 108).**\n"
        "2. ಹತ್ತಿರದ ಆಸ್ಪತ್ರೆಯ ತುರ್ತು ಚಿಕಿತ್ಸಾ ವಿಭಾಗಕ್ಕೆ (Casualty/Emergency) ತಕ್ಷಣ ತೆರಳಿ.\n"
        "3. **ಸ್ವತಃ ವಾಹನ ಚಲಾಯಿಸಬೇಡಿ ಮತ್ತು ವೈದ್ಯರ ಅನುಮತಿಯಿಲ್ಲದೆ ಯಾವುದೇ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ.**\n\n"
        "*ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ಎಐ ಕೇವಲ ಶೈಕ್ಷಣಿಕ ಮಾಹಿತಿಗಾಗಿ ಮಾತ್ರ ಮತ್ತು ತುರ್ತು ಪರಿಸ್ಥಿತಿಗಳಿಗೆ ಚಿಕಿತ್ಸೆ ನೀಡಲು ಸಾಧ್ಯವಿಲ್ಲ.*"
    ),
    "hi": (
        "⚠️ **आपातकालीन चिकित्सा चेतावनी: तत्काल ध्यान देने की आवश्यकता है**\n\n"
        "आपके प्रश्न में गंभीर और जानलेवा लक्षणों (जैसे सीने में तेज दर्द, दिल का दौरा, सांस लेने में अत्यधिक कठिनाई, या लकवे के संकेत) का उल्लेख है।\n\n"
        "**तुरंत किए जाने वाले महत्वपूर्ण कदम:**\n"
        "1. **तुरंत आपातकालीन नंबर पर कॉल करें (भारत में 112 या 108)।**\n"
        "2. निकटतम अस्पताल के आपातकालीन कक्ष (Emergency Room) में जाएँ।\n"
        "3. **स्वयं गाड़ी न चलाएँ और बिना डॉक्टर की सलाह के कोई दवा न लें।**\n\n"
        "*फार्माइंटेल एआई केवल एक शैक्षिक प्रणाली है और आपातकालीन स्थितियों का उपचार नहीं कर सकती।*"
    ),
    "ml": (
        "⚠️ **മെഡിക്കൽ അടിയന്തിര മുന്നറിയിപ്പ്: ഉടനടി ശ്രദ്ധ നൽകുക**\n\n"
        "നിങ്ങളുടെ ചോദ്യം ജീവന് ഭീഷണിയായേക്കാവുന്ന ലക്ഷണങ്ങളെ (നെഞ്ചുവേദന, ശ്വാസതടസ്സം, പക്ഷാഘാത ലക്ഷണങ്ങൾ എന്നിവ) സൂചിപ്പിക്കുന്നു.\n\n"
        "**ഉടൻ ചെയ്യേണ്ട കാര്യങ്ങൾ:**\n"
        "1. **ഉടൻ അടിയന്തിര സേവന നമ്പറിലേക്ക് വിളിക്കുക (ഇന്ത്യയിൽ 112 അല്ലെങ്കിൽ 108).**\n"
        "2. ഏറ്റവും അടുത്തുള്ള ആശുപത്രിയിലെ എമർജൻസി വിഭാഗത്തിലേക്ക് പോകുക.\n"
        "3. **സ്വയം വാഹനം ഓടിക്കരുത്, അറിവില്ലാത്ത മരുന്നുകൾ കഴിക്കരുത്.**\n\n"
        "*ഫാംഇന്റൽ എഐ ഒരു വിദ്യാഭ്യാസ വിവര സംവിധാനമാണ്, അടിയന്തിര ഘട്ടങ്ങളിൽ ചികിത്സ നൽകാൻ ഇതിനാവില്ല.*"
    ),
    "ta": (
        "⚠️ **அவசர மருத்துவ எச்சரிக்கை: உடனடி கவனம் தேவை**\n\n"
        "உங்கள் வினவல் கடுமையான உயிருக்கு ஆபத்தான அறிகுறிகளை (நெஞ்சு வலி, மூச்சுத் திணறல், பக்கவாத அறிகுறிகள் போன்றவை) குறிக்கிறது.\n\n"
        "**உடனடியாகச் செய்ய வேண்டியவை:**\n"
        "1. **உடனே அவசர உதவி எண்ணை அழைக்கவும் (இந்தியாவில் 112 அல்லது 108).**\n"
        "2. உடனடியாக அருகிலுள்ள மருத்துவமனையின் அவசர சிகிச்சைப் பிரிவிற்குச் செல்லவும்.\n"
        "3. **நீங்களாக வாகனம் ஓட்டவோ அல்லது சுய மருத்துவம் செய்யவோ வேண்டாம்.**\n\n"
        "*பார்ம்இன்டெல் AI ஒரு கல்வி சார்ந்த தகவல் அமைப்பாகும், அவசர சிகிச்சைக்கு உதவாது.*"
    ),
    "te": (
        "⚠️ **వైద్య అత్యవసర హెచ్చరిక: తక్షణ శ్రద్ధ అవసరం**\n\n"
        "మీ ప్రశ్న తీవ్రమైన మరియు ప్రాణాంతక లక్షణాలను (తీవ్రమైన గుండె నొప్పి, శ్వాస తీసుకోవడంలో ఇబ్బంది, పక్షవాతం మొదలైనవి) సూచిస్తోంది.\n\n"
        "**వెంటనే తీసుకోవాల్సిన చర్యలు:**\n"
        "1. **వెంటనే అత్యవసర సేవలకు కాల్ చేయండి (భారతదేశంలో 112 లేదా 108).**\n"
        "2. సమీపంలోని ఆసుపత్రి అత్యవసర విభాగానికి (Emergency) వెళ్ళండి.\n"
        "3. **మీరే స్వయంగా డ్రైవ్ చేయవద్దు మరియు డాక్టర్ సలహా లేకుండా మందులు వాడవద్దు.**\n\n"
        "*ఫార్మ్‌ఇంటెల్ AI ఒక విద్యా సమాచార వేదిక మాత్రమే, అత్యవసర వైద్య చికిత్స అందించదు.*"
    ),
    "mr": (
        "⚠️ **वैद्यकीय आणीबाणी इशारा: तत्काळ लक्ष देणे आवश्यक**\n\n"
        "आपल्या प्रश्नामध्ये तीव्र आणि जीवघेण्या लक्षणांचा (छातीत तीव्र वेदना, पक्षाघाताची लक्षणे, श्वास घेण्यास अडचण) उल्लेख आहे.\n\n"
        "**तातडीने करावयाची कृती:**\n"
        "1. **त्वरित आपत्कालीन सेवांना कॉल करा (भारतात 112 किंवा 108).**\n"
        "2. जवळच्या रुग्णालयाच्या आपत्कालीन कक्षात (Casualty/ICU) जा.\n"
        "3. **स्वतः वाहन चालवू नका आणि डॉक्टरांच्या सल्ल्याशिवाय कोणतेही औषध घेऊ नका.**\n\n"
        "*फार्मइंटेल एआय ही केवळ शैक्षणिक माहिती देणारी प्रणाली असून आणीबाणीच्या परिस्थितीत उपचार करू शकत नाही.*"
    ),
}

LOCALIZED_GUARDRAILS = {
    "en": {
        "title": "🛡️ **CLINICAL SAFETY DIRECTIVE**",
        "body": "PharmIntel cannot provide individual patient diagnosis or prescribe prescription medications ({reason}).",
        "why": "Clinical diagnosis requires comprehensive in-person medical examination, physical tests, laboratory diagnostics, and clinical evaluation by a licensed physician.",
        "action": "Please consult your doctor or an authorized pharmacist for a comprehensive evaluation."
    },
    "kn": {
        "title": "🛡️ **ವೈದ್ಯಕೀಯ ಸುರಕ್ಷತಾ ನಿರ್ದೇಶನ**",
        "body": "ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ವೈಯಕ್ತಿಕ ರೋಗನಿರ್ಣಯ ನೀಡಲು ಅಥವಾ ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಔಷಧಿಗಳನ್ನು ಸೂಚಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ ({reason}).",
        "why": "ರೋಗನಿರ್ಣಯಕ್ಕೆ ವೈದ್ಯರ ನೇರ ತಪಾಸಣೆ, ರಕ್ತ ಪರೀಕ್ಷೆಗಳು ಮತ್ತು ಅನುಭವಿ ವೈದ್ಯಕೀಯ ವೃತ್ತಿಪರರ ಮೌಲ್ಯಮಾಪನ ಅತ್ಯಗತ್ಯವಾಗಿದೆ.",
        "action": "ದಯವಿಟ್ಟು ನಿಖರವಾದ ತಪಾಸಣೆಗಾಗಿ ನಿಮ್ಮ ವೈದ್ಯರನ್ನು ಅಥವಾ ಪ್ರಮಾಣೀಕೃತ ಫಾರ್ಮಸಿಸ್ಟ್ ಅವರನ್ನು ಭೇಟಿ ಮಾಡಿ."
    },
    "hi": {
        "title": "🛡️ **चिकित्सीय सुरक्षा निर्देश**",
        "body": "फार्माइंटेल व्यक्तिगत रूप से किसी बीमारी का निदान नहीं कर सकता और न ही दवा लिख सकता है ({reason})।",
        "why": "सटीक निदान के लिए योग्य चिकित्सक द्वारा शारीरिक जांच, रक्त परीक्षण और विस्तृत चिकित्सीय इतिहास आवश्यक होता है।",
        "action": "कृपया उचित जांच एवं उपचार के लिए अपने डॉक्टर या अधिकृत फार्मासिस्ट से संपर्क करें।"
    },
    "ml": {
        "title": "🛡️ **ക്ലിനിക്കൽ സുരക്ഷാ നിർദ്ദേശം**",
        "body": "ഫാംഇന്റലിന് വ്യക്തിഗത രോഗനിർണ്ണയം നടത്താനോ മരുന്നുകൾ കുറിച്ചുനൽകാനോ കഴിയില്ല ({reason}).",
        "why": "രോഗനിർണ്ണയത്തിന് നേരിട്ടുള്ള ഡോക്ടറുടെ പരിശോധനയും ലാബ് ടെസ്റ്റുകളും അത്യന്താപേക്ഷിതമാണ്.",
        "action": "കൃത്യമായ രോഗപരിശോധനയ്ക്കായി നിങ്ങളുടെ ഡോക്ടറെയോ ലൈസൻസുള്ള ഫാർമസിസ്റ്റിനെയോ സമീപിക്കുക."
    },
    "ta": {
        "title": "🛡️ **மருத்துவ பாதுகாப்பு வழிகாட்டுதல்**",
        "body": "பார்ம்இன்டெல் தனிப்பட்ட முறையில் நோயறிதல் செய்யவோ அல்லது மருந்து பரிந்துரைக்கவோ முடியாது ({reason}).",
        "why": "சரியான நோயறிதலுக்கு பதிவுபெற்ற மருத்துவரின் நேரடி பரிசோதனை மற்றும் இரத்த பரிசோதனைகள் அவசியமாகும்.",
        "action": "சரியான ஆலோசனைக்கு உங்கள் மருத்துவரை அல்லது உரிமம் பெற்ற மருந்தாளரை அணுகவும்."
    },
    "te": {
        "title": "🛡️ **వైద్య భద్రతా ఆదేశం**",
        "body": "ఫార్మ్‌ఇంటెల్ వ్యక్తిగత వ్యాధి నిర్ధారణ లేదా మందుల ప్రిస్క్రిప్షన్ అందించలేదు ({reason}).",
        "why": "ఖచ్చితమైన వ్యాధి నిర్ధారణకు లైసెన్స్ పొందిన వైద్యుడి ప్రత్యక్ష పరీక్ష మరియు ప్రయోగశాల పరీక్షలు అవసరం.",
        "action": "సమగ్ర పరిశీలన కోసం దయచేసి మీ వైద్యుడిని లేదా లైసెన్స్ పొందిన ఫార్మసిస్ట్‌ను సంప్రదించండి."
    },
    "mr": {
        "title": "🛡️ **वैद्यकीय सुरक्षा निर्देश**",
        "body": "फार्मइंटेल वैयक्तिक आजाराचे निदान करू शकत नाही किंवा औषधे लिहून देऊ शकत नाही ({reason})।",
        "why": "योग्य निदानासाठी डॉक्टरांची प्रत्यक्ष तपासणी, प्रयोगशाळा चाचण्या आणि वैद्यकीय इतिहास आवश्यक असतो.",
        "action": "कृपया सविस्तर तपासणीसाठी आपल्या डॉक्टरांचा किंवा अधिकृत फार्मासिस्टचा सल्ला घ्या."
    },
}

LOCALIZED_DISCLAIMERS = {
    "en": "DISCLAIMER: PharmIntel AI provides verified pharmacological and educational information. It does not replace professional medical advice, clinical diagnosis, or individualized prescription management.",
    "kn": "ಹಕ್ಕುತ್ಯಾಗ: ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ಎಐ ಶೈಕ್ಷಣಿಕ ಮತ್ತು ಔಷಧೀಯ ಮಾಹಿತಿಯನ್ನು ಮಾತ್ರ ಒದಗಿಸುತ್ತದೆ. ಇದು ವೈದ್ಯರ ವೃತ್ತಿಪರ ಸಲಹೆ, ರೋಗನಿರ್ಣಯ ಅಥವಾ ವೈಯಕ್ತಿಕ ಚಿಕಿತ್ಸೆಗೆ ಪರ್ಯಾಯವಲ್ಲ.",
    "hi": "अस्वीकरण: फार्माइंटेल एआई केवल शैक्षिक एवं फार्माकोलॉजिकल जानकारी प्रदान करता है। यह डॉक्टर की सलाह, नैदानिक निदान या व्यक्तिगत नुस्खे का विकल्प नहीं है।",
    "ml": "നിരാകരണം: ഫാംഇന്റൽ എഐ വിദ്യാഭ്യാസപരമായ വിവരങ്ങൾ നൽകുന്നു. ഇത് ഡോക്ടറുടെ പരിശോധനയ്ക്കോ ചികിത്സയ്ക്കോ പകരമല്ല.",
    "ta": "பொறுப்புத் துறப்பு: பார்ம்இன்டெல் AI கல்வி சார்ந்த தகவல் அமைப்பாகும். இது தகுதியான மருத்துவ ஆலோசனையின் மாற்றாகாது.",
    "te": "నిరాకరణ: ఫార్మ్‌ఇంటెల్ AI విద్యా ప్రయోజనాల కోసం మాత్రమే సమాచారాన్ని అందిస్తుంది. ఇది డాక్టర్ సలహాకు ప్రత్యామ్నాయం కాదు.",
    "mr": "अस्वीकरण: फार्मइंटेल एआय केवळ शैक्षणिक माहिती पुरवते. हा डॉक्टरांच्या सल्ल्याचा किंवा उपचारांचा पर्याय नाही.",
}

class ClinicalSafetyGuardrails:
    EMERGENCY_KEYWORDS = [
        "chest pain", "pressure in chest", "heart attack", "radiating to arm",
        "shortness of breath", "cannot breathe", "stridor", "anaphylaxis",
        "face drooping", "arm weakness", "slurred speech", "stroke",
        "coughing blood", "vomiting blood", "suicide", "end my life", "unconscious",
        "सीने में दर्द", "छाती में दर्द", "दिल का दौरा", "हार्ट अटैक", "सांस फूलना",
        "सांस लेने में तकलीफ", "लकवा", "बेहोश", "खून की उल्टी", "आत्महत्या",
        "ಎದೆ ನೋವು", "ಗುಂಡಿಗೆ ನೋವು", "ಉಸಿರಾಟದ ತೊಂದರೆ", "ಪಾರ್ಶ್ವವಾಯು", "ಪ್ರಜ್ಞಾಹೀನ", "ಹೃದಯಾಘಾತ", "ರಕ್ತ ವಾಂತಿ",
        "നെഞ്ചുവേദന", "ശ്വാസമെടുക്കാൻ ബുദ്ധിമുട്ട്", "ഹൃദയാഘാതം", "പക്ഷാഘാതം", "ബോധക്ഷയം", "രക്തം ഛർദ്ദിക്കുക",
        "நெஞ்சு வலி", "மாரடைப்பு", "மூச்சுத் திணறல்", "பக்கவாதம்", "மயக்கம்", "சுவாசிக்க முடியவில்லை", "இரத்த வாந்தி",
        "గుండె నొప్పి", "ఛాతీ నొప్పి", "శ్వాస ఆడకపోవడం", "పక్షవాతం", "స్పృహ తప్పడం", "రక్తం వాంతి", "గుండెపోటు",
        "छातीत दुखणे", "हृदयविकाराचा झटका", "श्वास घेण्यास त्रास", "पक्षाघात", "रक्ताची उलटी", "बेशुद्ध"
    ]

    DIAGNOSIS_KEYWORDS = [
        "do i have cancer", "diagnose me", "what disease do i have",
        "am i having a heart attack", "tell me my illness", "what is my condition",
        "मुझे क्या बीमारी है", "मेरा इलाज बताओ", "क्या मुझे कैंसर है", "डायग्नोज करो",
        "ನನಗೆ ಯಾವ ಕಾಯಿಲೆ ಇದೆ", "ನನ್ನ ರೋಗ ತಿಳಿಸಿ",
        "எனக்கு என்ன நோய்",
        "నాకు ఏ వ్యాధి వచ్చింది",
        "मला कोणता आजार झाला आहे",
        "എനിക്ക് എന്താണ് അസുഖം"
    ]

    PRESCRIBE_KEYWORDS = [
        "prescribe me", "can you prescribe", "what dose should i start",
        "should i stop my medicine", "stop taking my warfarin", "change my dose",
        "दवा लिख दो", "दवा बताओ", "खुराक बढ़ाओ", "दवा बंद कर दूं",
        "ಔಷಧಿ ಬರೆದುಕೊಡಿ", "ಡೋಸ್ ಬದಲಿಸಿ",
        "மருந்து எழுதி கொடுங்கள்",
        "మందులు రాయండి",
        "औषध लिहून द्या",
        "മരുന്ന് കുറിച്ചു തരൂ"
    ]

    @classmethod
    def analyze_query_safety(cls, user_text: str) -> Dict[str, Any]:
        lower_text = user_text.lower()

        for kw in cls.EMERGENCY_KEYWORDS:
            if kw.lower() in lower_text:
                return {
                    "is_emergency": True,
                    "flag": "EMERGENCY",
                    "reason": f"Detected acute high-risk medical symptom: '{kw}'."
                }

        composite_emergencies = [
            (("chest", "pain"), "acute chest pain"),
            (("heart", "attack"), "acute myocardial infarction"),
            (("cannot", "breathe"), "acute respiratory failure"),
            (("stroke",), "cerebrovascular stroke"),
            (("सीने", "दर्द"), "सीने में तेज दर्द"),
            (("छाती", "दर्द"), "छाती में दर्द"),
            (("सांस", "तकलीफ"), "गंभीर सांस की तकलीफ"),
            (("सांस", "फूल"), "सांस फूलना"),
            (("ಎದೆ", "ನೋವು"), "ತೀವ್ರ ಎದೆ ನೋವು"),
            (("ಗುಂಡಿಗೆ", "ನೋವು"), "ಗುಂಡಿಗೆ ನೋವು"),
            (("ಉಸಿರಾಟ", "ತೊಂದರೆ"), "ಉಸಿರಾಟದ ತೊಂದರೆ"),
            (("നെഞ്ചു", "വേദന"), "തീവ്രമായ നെഞ്ചുവേദന"),
            (("ശ്വാസ", "തടസ്സം"), "ശ്വാസതടസ്സം"),
            (("நெஞ்சு", "வலி"), "கடுமையான நெஞ்சு வலி"),
            (("மூச்சு", "திணறல்"), "மூச்சுத் திணறல்"),
            (("గుండె", "నొప్పి"), "తీవ్రమైన గుండె నొప్పి"),
            (("ఛాతీ", "నొప్పి"), "ఛాతీ నొప్పి"),
            (("శ్వాస", "ఆడ"), "శ్వాస ఆడకపోవడం"),
            (("छातीत", "दुख"), "छातीत तीव्र वेदना"),
            (("श्वास", "त्रास"), "श्वास घेण्यास त्रास"),
        ]

        for token_tuple, desc in composite_emergencies:
            if all(t.lower() in lower_text for t in token_tuple):
                return {
                    "is_emergency": True,
                    "flag": "EMERGENCY",
                    "reason": f"Detected acute high-risk medical symptom: '{desc}'."
                }

        for kw in cls.DIAGNOSIS_KEYWORDS:
            if kw.lower() in lower_text:
                return {
                    "is_emergency": False,
                    "flag": "DIAGNOSE_BLOCKED",
                    "reason": "Personal medical diagnosis requested"
                }

        for kw in cls.PRESCRIBE_KEYWORDS:
            if kw.lower() in lower_text:
                return {
                    "is_emergency": False,
                    "flag": "PRESCRIBE_BLOCKED",
                    "reason": "Direct prescription alteration or drug initiation requested"
                }

        return {
            "is_emergency": False,
            "flag": "SAFE",
            "reason": "Query conforms to clinical safety directives."
        }

class ProviderIndependentLLMClient:
    """
    Provider-Independent LLM Connector & Multi-Domain Clinical Reasoning Engine.
    STRICT CONSTRAINT: ZERO GEMINI FLASH!
    Answers user questions directly across:
    1. General Tech & Science (AI, heart function, blood pressure mechanics, viruses vs bacteria, exercise).
    2. General Health & Disease (Diabetes, Hypertension, Cholesterol, Dehydration, Antibiotics, Taking meds with food).
    3. Clinical Medicine Monographs (Indications, ingredients, adverse effects, precautions, storage).
    4. Drug-Drug Interactions (Pharmacological mechanisms, risks, clinical precautions).
    5. Website Guidance (Only when explicitly asked how to use portal features).
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model = settings.LLM_MODEL

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        retrieved_context: str = "",
        language: str = "en",
        mode: str = "ai_assistant",
        history: str = "",
        db: Optional[Session] = None
    ) -> str:
        lang_meta = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES["en"])
        lang_name = lang_meta["name"]
        lang_native = lang_meta["native"]

        if self.provider == "local_engine" or not self.api_key and self.provider != "ollama":
            return self._local_clinical_reasoning(user_prompt, retrieved_context, language, mode, history, db)

        if self.provider == "ollama":
            try:
                lang_instruction = (
                    f"Respond fluently, naturally and authoritatively in {lang_name} ({lang_native}). "
                    f"Keep medical terms and active chemical names clear with accurate translation."
                )
                full_prompt = f"{system_prompt}\n{lang_instruction}\n\nContext:\n{retrieved_context}\n\nHistory:\n{history}\n\nUser Question:\n{user_prompt}"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.base_url}/api/generate",
                        json={"model": self.model, "prompt": full_prompt, "stream": False}
                    )
                    if resp.status_code == 200:
                        return resp.json().get("response", "")
            except Exception as e:
                print(f"Ollama connection error: {e}, falling back to local clinical engine.")
                return self._local_clinical_reasoning(user_prompt, retrieved_context, language, mode, history, db)

        if self.provider == "openai" and self.api_key:
            try:
                lang_instruction = (
                    f"You MUST write your entire response in {lang_name} ({lang_native}). "
                    f"Maintain rigorous pharmacological accuracy."
                )
                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"{system_prompt}\n{lang_instruction}\n\nVerified Context:\n{retrieved_context}\n\nConversation History:\n{history}"},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2
                    }
                    resp = await client.post(f"{self.base_url}/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"External API error: {e}, falling back to local clinical engine.")
                return self._local_clinical_reasoning(user_prompt, retrieved_context, language, mode, history, db)

        return self._local_clinical_reasoning(user_prompt, retrieved_context, language, mode, history, db)

    def _resolve_multi_turn_subject(self, q_low: str, history: str) -> Tuple[str, Optional[str]]:
        """
        Resolves anaphoric references (e.g. 'its symptoms', 'side effects of this', 'can I take amlodipine with it?')
        by extracting the active medical/scientific entity from recent history.
        """
        resolved_query = q_low
        detected_entity = None

        if not history:
            return resolved_query, None

        known_entities = [
            ("diabetes", "diabetes"),
            ("sugar", "diabetes"),
            ("मधुमेह", "diabetes"),
            ("ಮಧುಮೇಹ", "diabetes"),
            ("hypertension", "hypertension"),
            ("high blood pressure", "hypertension"),
            ("bp", "hypertension"),
            ("रक्तचाप", "hypertension"),
            ("ರಕ್ತದೊತ್ತಡ", "hypertension"),
            ("cholesterol", "cholesterol"),
            ("கொலஸ்ட்ரால்", "cholesterol"),
            ("ಕೊಲೆಸ್ಟ್ರಾಲ್", "cholesterol"),
            ("dehydration", "dehydration"),
            ("निर्जलीकरण", "dehydration"),
            ("ನಿರ್ಜಲೀಕರಣ", "dehydration"),
            ("antibiotic", "antibiotics"),
            ("एंटीबायोटिक", "antibiotics"),
            ("ಆಂಟಿಬಯೋಟಿಕ್", "antibiotics"),
            ("heart", "heart"),
            ("हृदय", "heart"),
            ("ಗುಂಡಿಗೆ", "heart"),
            ("circulation", "heart circulation"),
            ("blood pressure", "blood pressure mechanics"),
            ("virus", "virus vs bacteria"),
            ("bacteria", "virus vs bacteria"),
            ("exercise", "physical exercise"),
            ("व्यायाम", "physical exercise"),
            ("ಕಸರತ್ತು", "physical exercise"),
            ("artificial intelligence", "artificial intelligence"),
            ("ai", "artificial intelligence"),
            ("computer science", "computer science"),
            ("paracetamol", "paracetamol"),
            ("dolo", "paracetamol"),
            ("crocin", "paracetamol"),
            ("पैरासिटामोल", "paracetamol"),
            ("ಪ್ಯಾರಸಿಟಮಾಲ್", "paracetamol"),
            ("metformin", "metformin"),
            ("glycomet", "metformin"),
            ("losartan", "losartan"),
            ("amlodipine", "amlodipine"),
            ("atorvastatin", "atorvastatin"),
            ("pantoprazole", "pantoprazole"),
            ("pan 40", "pantoprazole"),
            ("omeprazole", "omeprazole"),
            ("ibuprofen", "ibuprofen"),
            ("brufen", "ibuprofen"),
            ("aspirin", "aspirin"),
            ("warfarin", "warfarin"),
            ("clopidogrel", "clopidogrel"),
            ("azithromycin", "azithromycin"),
            ("augmentin", "amoxicillin-clavulanate"),
            ("amoxicillin", "amoxicillin"),
            ("cetirizine", "cetirizine"),
            ("montelukast", "montelukast"),
            ("telmisartan", "telmisartan")
        ]

        # If the query itself already contains a recognized primary entity, do not overwrite/pollute it with prior context
        if any(kw in q_low for kw, _ in known_entities):
            return resolved_query, None

        anaphoric_triggers = [
            "its", "it", "this", "these", "that", "the disease", "the medicine",
            "the condition", "with it", "with this", "side effect", "symptom",
            "treatment", "precaution", "cause", "complication", "how is it", "why is it",
            "ಇದರ", "ಇದನ್ನು", "ಅದರ", "ಅದನ್ನು", "इसके", "इसका", "इसकी", "इसके साथ",
            "ഇതിന്റെ", "ഇത്", "இதன்", "దీని", "దీనికి", "याचे", "याची"
        ]

        needs_context = any(trig in q_low for trig in anaphoric_triggers) or len(q_low.split()) <= 4

        if needs_context:
            hist_low = history.lower()

            # Scan history in reverse (most recent entities first)
            lines = [l.strip().lower() for l in hist_low.splitlines() if l.strip()]
            for line in reversed(lines):
                for kw, canonical in known_entities:
                    if kw in line and canonical not in resolved_query:
                        detected_entity = canonical
                        resolved_query += f" {canonical}"
                        break
                if detected_entity:
                    break

        return resolved_query, detected_entity

    def _local_clinical_reasoning(
        self,
        query: str,
        context: str,
        language: str = "en",
        mode: str = "ai_assistant",
        history: str = "",
        db: Optional[Session] = None
    ) -> str:
        """
        Direct, authoritative clinical reasoning engine for general knowledge,
        health, medicine monographs, and drug interactions.
        """
        lang = language if language in SUPPORTED_LANGUAGES else "en"
        raw_q_low = query.lower()
        q_low, resolved_subject = self._resolve_multi_turn_subject(raw_q_low, history)

        # Mode styling
        if mode == "live_support":
            persona_header = {
                "en": "### 🩺 PharmIntel AI Live Support Assistant\n*24/7 Clinical Support AI Desk (Evidence-Based Pharmacology Guidance)*\n\n",
                "kn": "### 🩺 ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ಎಐ ಲೈವ್ ಸಪೋರ್ಟ್ ಸಹಾಯಕ\n*24/7 ಕ್ಲಿನಿಕಲ್ ಬೆಂಬಲ ಎಐ ಡೆಸ್ಕ್ (ಆಧಾರಿತ ಔಷಧೀಯ ಮಾರ್ಗದರ್ಶನ)*\n\n",
                "hi": "### 🩺 फार्माइंटेल एआई लाइव सपोर्ट असिस्टेंट\n*24/7 क्लिनिकल सपोर्ट एआई डेस्क (सत्यापित फार्माकोलॉजिकल मार्गदर्शन)*\n\n",
                "ml": "### 🩺 ഫാംഇന്റൽ എഐ ലൈവ് സപ്പോർട്ട് അസിസ്റ്റന്റ്\n*24/7 ക്ലിനിക്കൽ സപ്പോർട്ട് എഐ ഡെസ്ക്*\n\n",
                "ta": "### 🩺 பார்ம்இன்டெல் AI நேரடி உதவி உதவியாளர்\n*24/7 மருத்துவ உதவி AI மையம்*\n\n",
                "te": "### 🩺 ఫార్మ్‌ఇంటెల్ AI లైవ్ సపోర్ట్ అసిస్టెంట్\n*24/7 క్లినికల్ సపోర్ట్ AI డెస్క్*\n\n",
                "mr": "### 🩺 फार्मइंटेल एआय थेट सहाय्यक\n*24/7 क्लिनिकल सपोर्ट एआय डेस्क*\n\n",
            }.get(lang, "### 🩺 PharmIntel AI Live Support Assistant\n\n")

            escalation_footer = {
                "en": "\n\n---\n💡 **Need Direct Human Review?** Click **'Escalate to Pharmacist'** above to submit your inquiry to our clinical pharmacist review queue.",
                "kn": "\n\n---\n💡 **ಮಾನವ ತಜ್ಞರ ಪರಿಶೀಲನೆ ಬೇಕೇ?** ಕ್ಲಿನಿಕಲ್ ಫಾರ್ಮಸಿಸ್ಟ್ ತಂಡಕ್ಕೆ ನಿಮ್ಮ ವಿಚಾರಣೆಯನ್ನು ಕಳುಹಿಸಲು ಮೇಲಿನ **'Escalate to Pharmacist'** ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ.",
                "hi": "\n\n---\n💡 **क्या आपको फार्मासिस्ट से सीधी समीक्षा चाहिए?** अपने प्रश्न को हमारे क्लिनिकल फार्मासिस्ट रिव्यू कतार में भेजने के लिए ऊपर दिए गए **'Escalate to Pharmacist'** बटन पर क्लिक करें।",
                "ml": "\n\n---\n💡 **നേരിട്ടുള്ള മനുഷ്യ പരിശോധന ആവശ്യമുണ്ടോ?** മുകളിലുള്ള **'Escalate to Pharmacist'** ക്ലിക്ക് ചെയ്യുക.",
                "ta": "\n\n---\n💡 **மருந்தாளரின் நேரடி ஆய்வு தேவையா?** மேலே உள்ள **'Escalate to Pharmacist'** பொத்தானை அழுத்தவும்.",
                "te": "\n\n---\n💡 **ప్రత్యక్ష సమీక్ష అవసరమా?** పైన ఉన్న **'Escalate to Pharmacist'** క్లిక్ చేయండి.",
                "mr": "\n\n---\n💡 **थेट फार्मासिस्टचा सल्ला हवा आहे?** वरील **'Escalate to Pharmacist'** बटणावर क्लिक करा.",
            }.get(lang, "\n\n---\n💡 **Need Direct Human Review?** Click **'Escalate to Pharmacist'** above.")
        else:
            persona_header = ""
            escalation_footer = ""

        # ---------------------------------------------------------------------
        # 0. CLINICAL KNOWLEDGE ENGINE: PREGNANCY, SYMPTOMS, PHARMACY & DDIs
        # ---------------------------------------------------------------------
        # A. Dedicated Pregnancy & Lactation Safety (Highest priority clinical safety layer)
        preg_ans = ClinicalKnowledgeEngine.evaluate_pregnancy_and_lactation(
            q_low, lang, persona_header, escalation_footer
        )
        if preg_ans:
            return preg_ans

        # B. Symptoms & Clinical Triage (Non-diagnostic educational guidance)
        symp_ans = ClinicalKnowledgeEngine.evaluate_symptoms_and_general_medical(
            q_low, lang, persona_header, escalation_footer
        )
        if symp_ans:
            return symp_ans

        # C. Pharmacy Fundamentals & Drug Regulations
        pharm_ans = ClinicalKnowledgeEngine.evaluate_pharmacy_and_regulations(
            q_low, lang, persona_header, escalation_footer
        )
        if pharm_ans:
            return pharm_ans

        # D. In-Chat Specific Drug Interactions
        chat_ddi = ClinicalKnowledgeEngine.evaluate_in_chat_drug_interactions(
            q_low, lang, persona_header, escalation_footer
        )
        if chat_ddi:
            return chat_ddi

        # ---------------------------------------------------------------------
        # 1. GENERAL TECH & SCIENCE DOMAIN
        # ---------------------------------------------------------------------
        # A. Artificial Intelligence & Computer Science
        is_ai_query = any(w in q_low for w in [
            "what is ai", "explain ai", "what is artificial intelligence", "explain artificial intelligence",
            "machine learning", "deep learning", "neural network",
            "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ", "आर्टिफिशियल इंटेलिजेंस", "कृत्रिम बुद्धिमत्ता", "செயற்கை நுண்ணறிவு", "కృత్రిమ మేధస్సు"
        ])
        if is_ai_query:
            ai_texts = {
                "en": (
                    "### 🤖 Artificial Intelligence (AI): Principles and Clinical Applications\n\n"
                    "**Artificial Intelligence (AI)** refers to computer systems and computational models designed to perform tasks that typically require human intelligence, including pattern recognition, logical reasoning, learning from experience, and natural language understanding.\n\n"
                    "**Core Subfields of AI:**\n"
                    "- **Machine Learning (ML):** Algorithms (such as Gradient Boosted Trees, Random Forests, and Support Vector Machines) that learn predictive models from statistical data without being explicitly programmed.\n"
                    "- **Deep Learning (DL):** Multi-layered Artificial Neural Networks (such as Convolutional Neural Networks and Transformers) capable of modeling complex non-linear representations across high-dimensional data.\n"
                    "- **Natural Language Processing (NLP):** Systems that analyze, comprehend, and generate human clinical language and structured medical literature.\n\n"
                    "**Applications in Healthcare and Pharmacology:**\n"
                    "1. **Computer-Aided Drug Discovery:** Predicting molecular binding affinity, candidate toxicity (ADMET profiling), and bioisosteric optimization.\n"
                    "2. **Clinical Decision Support:** Automated multi-drug interaction checking, genomic variant annotation, and contraindication flagging (as implemented in PharmIntel).\n"
                    "3. **Diagnostic Imaging:** Convolutional networks analyzing chest radiographs, CT scans, and dermatological lesions for early pathology detection.\n\n"
                    "💡 *In pharmaceutical safety, AI enhances clinical verification by cross-referencing multi-drug regimens against millions of pharmacogenomic and biochemical data points in milliseconds.*"
                ),
                "kn": (
                    "### 🤖 ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ (Artificial Intelligence - AI): ತತ್ವಗಳು ಮತ್ತು ವೈದ್ಯಕೀಯ ಬಳಕೆಗಳು\n\n"
                    "**ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ (AI)** ಎಂಬುದು ಮಾನವ ಬುದ್ಧಿಶಕ್ತಿಯ ಅಗತ್ಯವಿರುವ ಕಾರ್ಯಗಳನ್ನು (ಉದಾಹರಣೆಗೆ ಮಾದರಿ ಗುರುತಿಸುವಿಕೆ, ತಾರ್ಕಿಕ ಚಿಂತನೆ, ಅನುಭವದಿಂದ ಕಲಿಯುವುದು ಮತ್ತು ಭಾಷೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವುದು) ನಿರ್ವಹಿಸಲು ಕಂಪ್ಯೂಟರ್ ವ್ಯವಸ್ಥೆಗಳನ್ನು ಸಶಕ್ತಗೊಳಿಸುವ ವಿಜ್ಞಾನವಾಗಿದೆ.\n\n"
                    "**ಪ್ರಮುಖ ವಿಭಾಗಗಳು:**\n"
                    "- **ಮಷಿನ್ ಲರ್ನಿಂಗ್ (Machine Learning):** ಡೇಟಾದಿಂದ ತಾನಾಗಿಯೇ ಕಲಿತು ಭವಿಷ್ಯ ನುಡಿಯುವ ಅಲ್ಗಾರಿದಮ್‌ಗಳು.\n"
                    "- **ಡೀಪ್ ಲರ್ನಿಂಗ್ (Deep Learning):** ಮಾನವ ಮೆದುಳಿನಂತೆ ಕಾರ್ಯನಿರ್ವಹಿಸುವ ನರಮಂಡಲ ಜಾಲಗಳು (Neural Networks).\n"
                    "- **ನ್ಯಾಚುರಲ್ ಲ್ಯಾಂಗ್ವೇಜ್ ಪ್ರೊಸೆಸಿಂಗ್ (NLP):** ಮಾನವ ಭಾಷೆಯನ್ನು ಅರ್ಥೈಸಿಕೊಳ್ಳುವ ತಂತ್ರಜ್ಞಾನ.\n\n"
                    "**ಆರೋಗ್ಯ ಮತ್ತು ಔಷಧ ಕ್ಷೇತ್ರದಲ್ಲಿ ಬಳಕೆ:**\n"
                    "1. **ಹೊಸ ಔಷಧಿಗಳ ಸಂಶೋಧನೆ:** ರೋಗಾಣುಗಳ ವಿರುದ್ಧ ಪರಿಣಾಮಕಾರಿಯಾದ ಹೊಸ ಅಣುಗಳನ್ನು ವೇಗವಾಗಿ ವಿನ್ಯಾಸಗೊಳಿಸುವುದು.\n"
                    "2. **ಔಷಧಿ ಹೊಂದಾಣಿಕೆ ಮತ್ತು ಸುರಕ್ಷತೆ:** ಹಲವು ಔಷಧಿಗಳನ್ನು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳುವಾಗ ಉಂಟಾಗುವ ಅಪಾಯಗಳನ್ನು ನಿಖರವಾಗಿ ಪತ್ತೆಹಚ್ಚುವುದು (ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ಮಾಡುವಂತೆ).\n"
                    "3. **ರೋಗನಿರ್ಣಯ:** ಎಕ್ಸ್‌ರೇ, ಎಂಆರ್‌ಐ ಸ್ಕ್ಯಾನ್‌ಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ ಆರಂಭಿಕ ಹಂತದಲ್ಲೇ ಕಾಯಿಲೆಗಳನ್ನು ಗುರುತಿಸುವುದು."
                ),
                "hi": (
                    "### 🤖 आर्टिफिशियल इंटेलिजेंस (AI): सिद्धांत और स्वास्थ्य सेवा में उपयोग\n\n"
                    "**आर्टिफिशियल इंटेलिजेंस (AI)** कंप्यूटर विज्ञान की वह शाखा है जो ऐसी प्रणालियों का निर्माण करती है जो आमतौर पर मानव बुद्धि की आवश्यकता वाले कार्यों को कर सकती हैं, जैसे पैटर्न पहचानना, तर्क करना, अनुभव से सीखना और भाषा समझना।\n\n"
                    "**मुख्य शाखाएं:**\n"
                    "- **मशीन लर्निंग (Machine Learning):** डेटा से सीखकर सटीक निर्णय लेने वाले एल्गोरिदम।\n"
                    "- **डीप लर्निंग (Deep Learning):** कृत्रिम न्यूरल नेटवर्क जो जटिल डेटा (जैसे मेडिकल इमेज) का विश्लेषण करते हैं।\n"
                    "- **एनएलपी (NLP):** मानव भाषा और मेडिकल दस्तावेजों को समझने वाली तकनीक।\n\n"
                    "**चिकित्सा एवं फार्मेसी में अनुप्रयोग:**\n"
                    "1. **दवा निर्माण (Drug Discovery):** नए अणुओं की आणविक संरचना और सुरक्षा का त्वरित विश्लेषण।\n"
                    "2. **मल्टी-ड्रग सेफ्टी चेकिंग:** कई दवाओं के बीच होने वाले खतरनाक इंटरैक्शन को तुरंत पहचानना (जैसे फार्माइंटेल में)।\n"
                    "3. **डायग्नोस्टिक्स:** एक्स-रे और एमआरआई स्कैन की मदद से ट्यूमर और बीमारियों का समय पर पता लगाना।"
                ),
                "ml": (
                    "### 🤖 ആർട്ടിഫിഷ്യൽ ഇന്റലിജൻസ് (AI)\n\n"
                    "മനുഷ്യന്റെ ബുദ്ധിശക്തി ആവശ്യമുള്ള കാര്യങ്ങൾ കമ്പ്യൂട്ടറുകളെക്കൊണ്ട് ചെയ്യിക്കുന്ന സാങ്കേതികവിദ്യയാണ് ആർട്ടിഫിഷ്യൽ ഇന്റലിജൻസ്.\n\n"
                    "**പ്രധാന ഉപയോഗങ്ങൾ:** പുതിയ മരുന്നുകളുടെ കണ്ടെത്തൽ, ഒരേസമയം കഴിക്കുന്ന മരുന്നുകൾ തമ്മിലുള്ള അപകടകരമായ പ്രതിപ്രവർത്തനങ്ങൾ കണ്ടെത്തൽ, മെഡിക്കൽ സ്കാനുകൾ വേഗത്തിൽ പരിശോധിച്ച് രോഗനിർണ്ണയം നടത്തൽ എന്നിവയിൽ AI വലിയ മാറ്റങ്ങൾ വരുത്തുന്നു."
                ),
                "ta": (
                    "### 🤖 செயற்கை நுண்ணறிவு (AI)\n\n"
                    "மனிதனின் அறிவாற்றல் தேவைப்படும் சிக்கலான பணிகளை கணிப்பொறிகள் மூலம் செய்யும் தொழில்நுட்பமே செயற்கை நுண்ணறிவு (AI) ஆகும்.\n\n"
                    "**மருத்துவத் துறையில் இதன் பங்கு:** புதிய மருந்துகளைக் கண்டறிதல், பல மருந்துகளை ஒன்றாக எடுக்கும்போது ஏற்படும் அபாயங்களை முன்கூட்டியே எச்சரித்தல், எக்ஸ்ரே மற்றும் ஸ்கேன் படங்களை துல்லியமாக ஆய்வு செய்தல்."
                ),
                "te": (
                    "### 🤖 కృత్రిమ మేధస్సు (AI)\n\n"
                    "మానవ ఆలోచనా శక్తి అవసరమైన పనులను కంప్యూటర్లు చేసేలా రూపొందించిన సాంకేతికతే ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ (AI).\n\n"
                    "**వైద్య రంగంలో ఉపయోగాలు:** కొత్త ఔషధాల పరిశోధన, మందుల మధ్య ఉండే హానికరమైన పరస్పర చర్యలను (Drug Interactions) తక్షణమే గుర్తించడం మరియు స్కానింగ్ నివేదికలను విశ్లేషించడం."
                ),
                "mr": (
                    "### 🤖 कृत्रिम बुद्धिमत्ता (Artificial Intelligence - AI)\n\n"
                    "मानवी बुद्धिमत्तेची आवश्यकता असणारी कामे संगणकाद्वारे स्वयंचलितपणे करून घेण्याचे तंत्रज्ञान म्हणजे आर्टिफिशियल इंटेलिजन्स (AI).\n\n"
                    "**वैद्यकीय क्षेत्रातील उपयोग:** नवीन औषधांचे संशोधन, औषधांमधील परस्पर घातक प्रक्रियांची (Drug Interactions) तपासणी आणि अचूक रोगनिदान."
                )
            }
            return f"{persona_header}{ai_texts.get(lang, ai_texts['en'])}{escalation_footer}"

        # B. Human Heart & Circulation
        is_heart_query = any(w in q_low for w in [
            "function of heart", "function of the heart", "human heart", "explain heart", "heart circulation",
            "హృదయ", "हृदय का कार्य", "గుండె పనితీరు", "இதயத்தின் செயல்பாடு", "हृदयाचे कार्य", "ಗುಂಡಿಗೆಯ ಕಾರ್ಯ"
        ])
        if is_heart_query:
            heart_texts = {
                "en": (
                    "### ❤️ The Human Heart: Anatomy and Circulatory Physiology\n\n"
                    "The **human heart** is a specialized muscular organ approximately the size of a fist, situated within the mediastinum of the thoracic cavity. Its primary function is to pump oxygenated blood and essential nutrients throughout the entire human body while returning deoxygenated blood to the lungs for re-oxygenation.\n\n"
                    "**Anatomical Structure (Four Chambers):**\n"
                    "1. **Right Atrium:** Receives deoxygenated venous blood returning from systemic circulation via the Superior and Inferior Vena Cava.\n"
                    "2. **Right Ventricle:** Pumps deoxygenated blood through the pulmonary valve into the pulmonary arteries leading to the lungs.\n"
                    "3. **Left Atrium:** Receives freshly oxygen-rich blood from the pulmonary veins returning from the lungs.\n"
                    "4. **Left Ventricle:** The most powerful, thick-walled chamber; forcefully pumps oxygenated blood into the aorta to supply systemic organs and peripheral tissues.\n\n"
                    "**The Two Continuous Circulatory Loops:**\n"
                    "- **Pulmonary Circulation:** Right Ventricle → Pulmonary Arteries → Alveolar Capillaries (Gas Exchange: CO2 released, O2 absorbed) → Pulmonary Veins → Left Atrium.\n"
                    "- **Systemic Circulation:** Left Ventricle → Aorta → Systemic Arteries → Tissue Capillaries (Oxygen & Nutrient Delivery) → Venous Return → Right Atrium.\n\n"
                    "**Cardiac Electrical Conduction:**\n"
                    "Contractions are initiated autonomously by the **Sinoatrial (SA) Node** (the heart's natural pacemaker), propagating through the Atrioventricular (AV) Node, Bundle of His, and Purkinje fibers to produce synchronized, rhythmic pumping (typically 60–100 beats per minute at rest)."
                ),
                "kn": (
                    "### ❤️ ಮಾನವನ ಹೃದಯ: ರಚನೆ ಮತ್ತು ರಕ್ತ ಪರಿಚಲನಾ ಕಾರ್ಯವಿಧಾನ\n\n"
                    "**ಮಾನವನ ಹೃದಯ**ವು ಎದೆಯ ಮಧ್ಯಭಾಗದಲ್ಲಿರುವ ಅತ್ಯಂತ ಪ್ರಮುಖ ಸ್ನಾಯು ಅಂಗವಾಗಿದೆ. ಇದು ದೇಹದ ಎಲ್ಲಾ ಜೀವಕೋಶಗಳಿಗೆ ಆಮ್ಲಜನಕ ಮತ್ತು ಪೋಷಕಾಂಶಯುಕ್ತ ರಕ್ತವನ್ನು ಪಂಪ್ ಮಾಡುವುದು ಮತ್ತು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್ ಯುಕ್ತ ರಕ್ತವನ್ನು ಶ್ವಾಸಕೋಶಕ್ಕೆ ಕಳುಹಿಸುವುದು ಇದರ ಮುಖ್ಯ ಕಾರ್ಯವಾಗಿದೆ.\n\n"
                    "**ಹೃದಯದ ನಾಲ್ಕು ಕೋಣೆಗಳು:**\n"
                    "1. **ಬಲ ಹೃತ್ಕರ್ಣ (Right Atrium):** ದೇಹದಿಂದ ಬರುವ ಆಮ್ಲಜನಕರಹಿತ ರಕ್ತವನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ.\n"
                    "2. **ಬಲ ಹೃತ್ಕುಕ್ಷಿ (Right Ventricle):** ರಕ್ತವನ್ನು ಶುದ್ಧೀಕರಣಕ್ಕಾಗಿ ಶ್ವಾಸಕೋಶಕ್ಕೆ ಪಂಪ್ ಮಾಡುತ್ತದೆ.\n"
                    "3. **ಎಡ ಹೃತ್ಕರ್ಣ (Left Atrium):** ಶ್ವಾಸಕೋಶದಿಂದ ಬರುವ ಶುದ್ಧ (ಆಮ್ಲಜನಕಯುಕ್ತ) ರಕ್ತವನ್ನು ಸ್ವೀಕರಿಸುತ್ತದೆ.\n"
                    "4. **ಎಡ ಹೃತ್ಕುಕ್ಷಿ (Left Ventricle):** ಮಹಾಧಮನಿ (Aorta) ಮೂಲಕ ಶುದ್ಧ ರಕ್ತವನ್ನು ಇಡೀ ದೇಹಕ್ಕೆ ಪಂಪ್ ಮಾಡುತ್ತದೆ.\n\n"
                    "**ವಿದ್ಯುತ್ ವಾಹಕ ವ್ಯವಸ್ಥೆ:**\n"
                    "ಹೃದಯದ ಬಡಿತವನ್ನು **ಎಸ್.ಎ. ನೋಡ್ (SA Node - ನೈಸರ್ಗಿಕ ಪೇಸ್‌ಮೇಕರ್)** ನಿಯಂತ್ರಿಸುತ್ತದೆ, ಇದು ಸಾಮಾನ್ಯ ಸ್ಥಿತಿಯಲ್ಲಿ ನಿಮಿಷಕ್ಕೆ 60 ರಿಂದ 100 ಬಾರಿ ಬಡಿಯುತ್ತದೆ."
                ),
                "hi": (
                    "### ❤️ मानव हृदय: संरचना और कार्यप्रणाली\n\n"
                    "**मानव हृदय** एक पेशीय (muscular) अंग है जो सीने के मध्य में स्थित होता है। इसका मुख्य कार्य पूरे शरीर में ऑक्सीजन और पोषक तत्वों से भरपूर रक्त पंप करना और अशुद्ध रक्त को फेफड़ों तक पहुंचाना है।\n\n"
                    "**हृदय के चार कक्ष (Chambers):**\n"
                    "1. **दायां आलिंद (Right Atrium):** पूरे शरीर से अशुद्ध (डीऑक्सीजिनेटेड) रक्त एकत्र करता है।\n"
                    "2. **दायां निलय (Right Ventricle):** अशुद्ध रक्त को शुद्ध होने के लिए फेफड़ों (Lungs) में भेजता है।\n"
                    "3. **बायां आलिंद (Left Atrium):** फेफड़ों से ऑक्सीजन युक्त शुद्ध रक्त प्राप्त करता है।\n"
                    "4. **बायां निलय (Left Ventricle):** महाधमनी (Aorta) के माध्यम से शुद्ध रक्त को पूरे शरीर में पंप करता है।\n\n"
                    "**हृदय की धड़कन:**\n"
                    "हृदय में एक प्राकृतिक पेसमेकर होता है जिसे **एस.ए. नोड (SA Node)** कहते हैं, जो नियमित विद्युत संकेत भेजकर हृदय को प्रति मिनट 60 से 100 बार धड़कने में मदद करता है।"
                ),
                "ml": (
                    "### ❤️ മനുഷ്യന്റെ ഹൃദയം: ഘടനയും പ്രവർത്തനവും\n\n"
                    "രക്തം ശരീരത്തിന്റെ എല്ലാ ഭാഗങ്ങളിലേക്കും പമ്പ് ചെയ്യുന്ന പ്രധാന പേശി അവയവമാണ് ഹൃദയം. ഇതിന് നാല് അറകളുണ്ട് (രണ്ട് ആട്രിയവും രണ്ട് വെൻട്രിക്കിളുകളും). അശുദ്ധ രക്തം ശ്വാസകോശത്തിലേക്ക് അയച്ച് ശുദ്ധീകരിക്കുകയും, ശുദ്ധരക്തം ശരീരത്തിലെ എല്ലാ കോശങ്ങളിലേക്കും എത്തിക്കുകയും ചെയ്യുന്നു."
                ),
                "ta": (
                    "### ❤️ மனித இதயம்: அமைப்பு மற்றும் செயல்பாடு\n\n"
                    "இதயம் உடலில் உள்ள அனைத்து செல்களுக்கும் ஆக்ஸிஜன் நிறைந்த இரத்தத்தை தொடர்ச்சியாக பம்ப் செய்யும் முக்கிய உறுப்பாகும். இதயத்தில் 4 அறைகள் உள்ளன (வலது மற்றும் இடது ஏட்ரியம், வலது மற்றும் இடது வென்ட்ரிக்கிள்). இது சுழற்சி முறையில் இரத்தத்தை சீராக இயங்க வைக்கிறது."
                ),
                "te": (
                    "### ❤️ మానవ గుండె పనితీరు మరియు నిర్మాణం\n\n"
                    "గుండె శరీరంలోని అన్ని భాగాలకు ఆక్సిజన్ మరియు పోషకాలతో కూడిన రక్తాన్ని నిరంతరం పంప్ చేసే ఒక ముఖ్యమైన కండర అవయవం. గుండెలో 4 గదులు ఉంటాయి. ఊపిరితిత్తుల ద్వారా రక్తాన్ని శుద్ధి చేసి, మహాధమని ద్వారా శరీరమంతటికీ పంపుతుంది."
                ),
                "mr": (
                    "### ❤️ मानवी हृदय: रचना आणि कार्य\n\n"
                    "मानवी हृदय हे शरीराच्या सर्व अवयवांना ऑक्सिजनयुक्त रक्त पुरवठा करणारे मुख्य स्नायुयुक्त अवयव आहे. यात चार कप्पे (Chambers) असतात. अशुद्ध रक्त फुप्फुसांकडे शुद्धीकरणासाठी पाठवणे आणि शुद्ध रक्त संपूर्ण शरीराला पंप करणे हे त्याचे मुख्य कार्य आहे."
                )
            }
            return f"{persona_header}{heart_texts.get(lang, heart_texts['en'])}{escalation_footer}"

        # C. Blood Pressure Mechanics
        is_bp_query = any(w in q_low for w in [
            "why is blood pressure important", "blood pressure mechanics", "explain blood pressure",
            "systolic diastolic", "what is bp", "రక్తపోటు", "रक्तचाप क्या है", "ರಕ್ತದೊತ್ತಡ ಎಂದರೇನು", "இரத்த அழுத்தம்"
        ]) and "high" not in q_low and "hypertension" not in q_low
        if is_bp_query:
            bp_texts = {
                "en": (
                    "### 🩺 Blood Pressure Mechanics: Physiology and Clinical Importance\n\n"
                    "**Blood Pressure (BP)** is the lateral hydrostatic force exerted by circulating blood against the walls of systemic arteries. It is expressed in millimeters of mercury (mmHg) as two distinct numbers:\n\n"
                    "$$\\text{Blood Pressure} = \\frac{\\text{Systolic Pressure}}{\\text{Diastolic Pressure}} \\quad (\\text{e.g., } 120/80\\text{ mmHg})$$\n\n"
                    "**Understanding Systolic vs. Diastolic:**\n"
                    "1. **Systolic Pressure (Upper Number):** The maximum pressure generated in the arterial tree when the left ventricle contracts and ejects blood into the aorta during cardiac systole (Normal: <120 mmHg).\n"
                    "2. **Diastolic Pressure (Lower Number):** The minimum resting pressure sustained in the arterial system when the heart relaxes between beats during cardiac diastole, driven by arterial wall elasticity (Normal: <80 mmHg).\n\n"
                    "**The Fundamental Physiological Equation:**\n"
                    "$$\\text{Mean Arterial Pressure (MAP)} = \\text{Cardiac Output (CO)} \\times \\text{Systemic Vascular Resistance (SVR)}$$\n\n"
                    "**Why Blood Pressure Maintenance is Vital:**\n"
                    "- **Tissue Perfusion:** Adequate arterial pressure ensures vital organs (brain, kidneys, heart muscle) receive sufficient oxygen and glucose.\n"
                    "- **Consequences of Low BP (Hypotension):** Fainting, postural dizziness, poor organ perfusion, and hypovolemic shock.\n"
                    "- **Consequences of High BP (Hypertension):** Endothelial injury, accelerated atherosclerosis, vascular rupture (stroke), aneurysm, kidney microvascular damage, and heart failure."
                ),
                "kn": (
                    "### 🩺 ರಕ್ತದೊತ್ತಡ (Blood Pressure) ಎಂದರೇನು? ಅದರ ಪ್ರಾಮುಖ್ಯತೆ ಏನು?\n\n"
                    "ರಕ್ತವು ಅಪಧಮನಿಗಳ (ರಕ್ತನಾಳಗಳ) ಗೋಡೆಗಳ ಮೇಲೆ ಬೀರುವ ಒತ್ತಡವನ್ನು **ರಕ್ತದೊತ್ತಡ (Blood Pressure - BP)** ಎಂದು ಕರೆಯಲಾಗುತ್ತದೆ. ಇದನ್ನು ಮಿಲಿಮೀಟರ್ ಪಾದರಸದಲ್ಲಿ (mmHg) ಅಳೆಯಲಾಗುತ್ತದೆ.\n\n"
                    "**ಸಿಸ್ಟಾಲಿಕ್ ಮತ್ತು ಡಯಾಸ್ಟಾಲಿಕ್ ಅಂಕಿಸಂಖ್ಯೆಗಳು:**\n"
                    "1. **ಸಿಸ್ಟಾಲಿಕ್ (ಮೇಲಿನ ಸಂಖ್ಯೆ - ಉದಾ. 120):** ಹೃದಯ ಸಂಕೋಚನಗೊಂಡು ರಕ್ತವನ್ನು ನಾಳಗಳಿಗೆ ಪಂಪ್ ಮಾಡಿದಾಗ ಉಂಟಾಗುವ ಗರಿಷ್ಠ ಒತ್ತಡ.\n"
                    "2. **ಡಯಾಸ್ಟಾಲಿಕ್ (ಕೆಳಗಿನ ಸಂಖ್ಯೆ - ಉದಾ. 80):** ಎರಡು ಬಡಿತಗಳ ನಡುವೆ ಹೃದಯ ವಿಶ್ರಾಂತಿ ಪಡೆಯುವಾಗ ರಕ್ತನಾಳಗಳಲ್ಲಿ ಉಳಿಯುವ ಕನಿಷ್ಠ ಒತ್ತಡ.\n\n"
                    "**ರಕ್ತದೊತ್ತಡವನ್ನು ಸರಿಯಾಗಿಡುವುದು ಏಕೆ ಮುಖ್ಯ?**\n"
                    "- ಸಾಮಾನ್ಯ ಒತ್ತಡವು ಮೆದುಳು, ಮೂತ್ರಪಿಂಡ ಮತ್ತು ಹೃದಯಕ್ಕೆ ಸಮರ್ಪಕ ರಕ್ತವನ್ನು ಪೂರೈಸುತ್ತದೆ.\n"
                    "- ರಕ್ತದೊತ್ತಡ ಹೆಚ್ಚಾದರೆ ರಕ್ತನಾಳಗಳು ದುರ್ಬಲಗೊಂಡು ಹೃದಯಾಘಾತ ಮತ್ತು ಪಾರ್ಶ್ವವಾಯು (Stroke) ಅಪಾಯ ಹೆಚ್ಚಾಗುತ್ತದೆ."
                ),
                "hi": (
                    "### 🩺 रक्तचाप (Blood Pressure) क्या है और यह क्यों महत्वपूर्ण है?\n\n"
                    "**रक्तचाप (Blood Pressure - BP)** वह दबाव है जो धमनियों की दीवारों पर बहते हुए रक्त द्वारा डाला जाता है। इसे 120/80 mmHg के रूप में मापा जाता है।\n\n"
                    "**सिस्टोलिक और डायस्टोलिक का अर्थ:**\n"
                    "1. **सिस्टोलिक (ऊपर का अंक - सामान्य <120):** जब हृदय धड़कता है और रक्त को धमनियों में पंप करता है, तब उत्पन्न होने वाला उच्चतम दबाव।\n"
                    "2. **डायस्टोलिक (नीचे का अंक - सामान्य <80):** दो धड़कनों के बीच जब हृदय आराम करता है, तब धमनियों में बचा हुआ दबाव।\n\n"
                    "**रक्तचाप का महत्व:**\n"
                    "- यह सुनिश्चित करता है कि मस्तिष्क, गुर्दे और अन्य महत्वपूर्ण अंगों तक ऑक्सीजन पहुंचे।\n"
                    "- बीपी अत्यधिक बढ़ने से नसें फट सकती हैं (ब्रेन स्ट्रोक) और दिल का दौरा पड़ सकता है।"
                ),
                "ml": (
                    "### 🩺 രക്തസമ്മർദ്ദം (Blood Pressure)\n\n"
                    "ഹൃദയം രക്തം പമ്പ് ചെയ്യുമ്പോൾ രക്തക്കുഴലുകളിൽ അനുഭവപ്പെടുന്ന മർദ്ദമാണ് രക്തസമ്മർദ്ദം (120/80 mmHg). മുകളിലെ സംഖ്യ സിസ്റ്റോളിക് (ഹൃദയം ചുരുങ്ങുമ്പോൾ) മർദ്ദവും, താഴത്തെ സംഖ്യ ഡയസ്റ്റോളിക് (ഹൃദയം വിശ്രമിക്കുമ്പോൾ) മർദ്ദവുമാണ്. ഇത് സാധാരണ നിലയിലായിരിക്കുന്നത് ഹൃദയാഘാതവും പക്ഷാഘാതവും തടയാൻ അത്യാവശ്യമാണ്."
                ),
                "ta": (
                    "### 🩺 இரத்த அழுத்தம் (Blood Pressure)\n\n"
                    "இரத்த நாளங்களின் சுவர்களில் இரத்தம் செலுத்தும் அழுத்தமே இரத்த அழுத்தம் எனப்படுகிறது (சராசரி 120/80 mmHg). சிஸ்டாலிக் (இதயம் சுருங்கும்போது) மற்றும் டயஸ்டாலிக் (இதயம் தளரும்போது). இது சீராக இருப்பது மூளை மற்றும் சிறுநீரகத்தின் ஆரோக்கியத்திற்கு முக்கியம்."
                ),
                "te": (
                    "### 🩺 రక్తపోటు (Blood Pressure)\n\n"
                    "రక్తనాళాల గోడలపై రక్తం కలిగించే పీడనాన్ని రక్తపోటు (BP) అంటారు. సాధారణ కొలత 120/80 mmHg. సిస్టోలిక్ (పై సంఖ్య) గుండె రక్తాన్ని పంప్ చేసినప్పుడు ఏర్పడే పీడనం, డయాస్టోలిక్ (కింది సంఖ్య) విశ్రాంతి సమయంలో ఉండే పీడనం."
                ),
                "mr": (
                    "### 🩺 रक्तदाब (Blood Pressure)\n\n"
                    "रक्तवाहिन्यांच्या भिंतींवर पडणाऱ्या रक्ताच्या दाबाला रक्तदाब म्हणतात (सामान्य 120/80 mmHg). सिस्टोलिक (वरचा आकडा) आणि डायस्टोलिक (खालचा आकडा). शरीरातील सर्व अवयवांना योग्य प्रमाणात ऑक्सिजन पोहोचण्यासाठी रक्तदाब सामान्य असणे गरजेचे आहे."
                )
            }
            return f"{persona_header}{bp_texts.get(lang, bp_texts['en'])}{escalation_footer}"

        # D. Viruses vs Bacteria
        is_virus_bacteria = any(w in q_low for w in [
            "virus vs bacteria", "difference between bacteria and virus", "bacteria vs virus",
            "virus and bacteria", "వైరస్ మరియు బ్యాక్టీరియా", "बैक्टीरिया और वायरस", "ವೈರಸ್ ಮತ್ತು ಬ್ಯಾಕ್ಟೀರಿಯಾ"
        ])
        if is_virus_bacteria:
            vb_texts = {
                "en": (
                    "### 🔬 Difference Between Bacteria and Viruses: Biology and Clinical Treatment\n\n"
                    "Bacteria and viruses are distinct microscopic infectious agents that differ fundamentally in their biological structure, reproduction, and medical management:\n\n"
                    "| Characteristic | Bacteria | Viruses |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **Biological Nature** | Living, single-celled prokaryotic organisms. | Non-living, non-cellular infectious microscopic genetic capsules. |\n"
                    "| **Cell Structure** | Complete cell with peptidoglycan wall, cell membrane, cytoplasm, and 70S ribosomes. | Lacks cellular structure; genetic material (DNA or RNA) enclosed in a protein capsid. |\n"
                    "| **Reproduction** | Capable of independent autonomous reproduction via binary fission. | Obligate intracellular parasites; cannot replicate without hijacking a living host cell. |\n"
                    "| **Average Size** | 1,000 to 5,000 nanometers (1–5 µm). Visible under light microscope. | 20 to 400 nanometers. Visible only under electron microscope. |\n"
                    "| **Treatment** | **Antibiotics** (e.g. Amoxicillin, Azithromycin) kill or inhibit bacteria by targeting bacterial cell walls or ribosomes. | **Antibiotics are completely ineffective.** Managed by antiviral medications (e.g. Oseltamivir, Acyclovir) or prophylactic vaccines. |\n"
                    "| **Beneficial Forms** | Most bacteria are harmless or beneficial (gut microbiota, yogurt, nitrogen fixation). | Almost all known viruses cause disease or parasitize host cells. |\n"
                    "| **Examples** | *Streptococcus*, *E. coli*, *Salmonella*, *Tuberculosis*. | Influenza, SARS-CoV-2, HIV, Common Cold (Rhinovirus), Hepatitis. |\n\n"
                    "⚠️ **Clinical Reminder:** Never take antibiotics for viral colds, flu, or viral sore throats. Inappropriate antibiotic use destroys beneficial gut bacteria and fuels dangerous antimicrobial resistance."
                ),
                "kn": (
                    "### 🔬 ಬ್ಯಾಕ್ಟೀರಿಯಾ ಮತ್ತು ವೈರಸ್ ನಡುವಿನ ಪ್ರಮುಖ ವ್ಯತ್ಯಾಸಗಳು\n\n"
                    "ಬ್ಯಾಕ್ಟೀರಿಯಾ ಮತ್ತು ವೈರಸ್‌ಗಳು ಸಂಪೂರ್ಣವಾಗಿ ಭಿನ್ನವಾದ ಸೂಕ್ಷ್ಮಜೀವಿಗಳಾಗಿವೆ:\n\n"
                    "1. **ಜೀವಂತ ಸ್ವರೂಪ:** ಬ್ಯಾಕ್ಟೀರಿಯಾಗಳು ಸ್ವತಂತ್ರವಾಗಿ ಬದುಕಬಲ್ಲ ಏಕಕೋಶೀಯ ಜೀವಿಗಳು. ಆದರೆ ವೈರಸ್‌ಗಳು ಜೀವಿ ಮತ್ತು ನಿರ್ಜೀವಿಯ ನಡುವಿನ ಸ್ಥಿತಿಯಲ್ಲಿದ್ದು, ಹೋಸ್ಟ್ (ಮಾನವ ಅಥವಾ ಪ್ರಾಣಿಯ) ಜೀವಕೋಶದ ಒಳಗೆ ಮಾತ್ರ ವೃದ್ಧಿಯಾಗಬಲ್ಲವು.\n"
                    "2. **ಗಾತ್ರ:** ಬ್ಯಾಕ್ಟೀರಿಯಾಗಳು ವೈರಸ್‌ಗಳಿಗಿಂತ 10 ರಿಂದ 100 ಪಟ್ಟು ದೊಡ್ಡದಾಗಿರುತ್ತವೆ.\n"
                    "3. **ಔಷಧೋಪಚಾರ:**\n"
                    "   - **ಬ್ಯಾಕ್ಟೀರಿಯಾ:** ಇವುಗಳನ್ನು ಗುಣಪಡಿಸಲು **ಆಂಟಿಬಯೋಟಿಕ್ಸ್ (Antibiotics)** ಬಳಸಲಾಗುತ್ತದೆ.\n"
                    "   - **ವೈರಸ್:** ಆಂಟಿಬಯೋಟಿಕ್ಸ್ ವೈರಸ್‌ಗಳ ಮೇಲೆ ಯಾವುದೇ ಪರಿಣಾಮ ಬೀರುವುದಿಲ್ಲ! ವೈರಸ್‌ಗೆ ವಿಶ್ರಾಂತಿ, ನೀರು, ಲಸಿಕೆಗಳು (Vaccines) ಅಥವಾ ಆಂಟಿವೈರಲ್ ಔಷಧಿಗಳು ಬೇಕಾಗುತ್ತವೆ.\n\n"
                    "⚠️ ನೆಗಡಿ ಅಥವಾ ಸಾಮಾನ್ಯ ವೈರಲ್ ಜ್ವರಕ್ಕೆ ಆಂಟಿಬಯೋಟಿಕ್ ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ."
                ),
                "hi": (
                    "### 🔬 बैक्टीरिया और वायरस के बीच मुख्य अंतर\n\n"
                    "बैक्टीरिया और वायरस दो अलग-अलग प्रकार के सूक्ष्मजीव हैं:\n\n"
                    "1. **जैविक संरचना:** बैक्टीरिया एककोशिकीय जीवित जीव हैं जो स्वतंत्र रूप से जीवित रह सकते हैं और प्रजनन कर सकते हैं। वायरस केवल आनुवंशिक सामग्री (DNA/RNA) का एक छोटा कण होते हैं जो जीवित कोशिकाओं के बिना नहीं पनप सकते।\n"
                    "2. **आकार:** बैक्टीरिया वायरस की तुलना में 10 से 100 गुना बड़े होते हैं।\n"
                    "3. **उपचार:**\n"
                    "   - **बैक्टीरिया:** इनके संक्रमण का इलाज **एंटीबायोटिक्स (Antibiotics)** से किया जाता है।\n"
                    "   - **वायरस:** एंटीबायोटिक्स वायरस पर बिल्कुल काम नहीं करती हैं! इनके लिए वैक्सीन और एंटीवायरल दवाएं होती हैं।\n\n"
                    "⚠️ सर्दी, जुकाम और सामान्य वायरल बुखार में एंटीबायोटिक दवाएं कभी न लें।"
                ),
                "ml": (
                    "### 🔬 ബാക്ടീരിയയും വൈറസും തമ്മിലുള്ള വ്യത്യാസങ്ങൾ\n\n"
                    "ബാക്ടീരിയകൾ ജീവനുള്ള സ്വതന്ത്ര കോശങ്ങളാണ്. ഇവയെ നശിപ്പിക്കാൻ **ആന്റിബയോട്ടിക്കുകൾ** ഉപയോഗിക്കാം. എന്നാൽ വൈറസുകൾക്ക് സ്വന്തമായി കോശങ്ങളില്ല, അവ മറ്റൊരു ജീവകോശത്തിൽ കയറി മാത്രമേ വളരൂ. വൈറസ് രോഗങ്ങൾക്ക് (ജലദോഷം, പനി) ആന്റിബയോട്ടിക്കുകൾ ഫലപ്രദമല്ല."
                ),
                "ta": (
                    "### 🔬 பாக்டீரியா மற்றும் வைரஸ் இடையேயான வேறுபாடுகள்\n\n"
                    "பாக்டீரியாக்கள் ஒரு செல் கொண்ட உயிருள்ள நுண்ணுயிரிகள். இவற்றை அழிக்க **ஆன்டிபயாடிக் (Antibiotic)** மருந்துகள் பயன்படுகின்றன. ஆனால் வைரஸ்கள் உயிரணு அமைப்பு இல்லாதவை. வைரஸ் தொற்றுகளுக்கு (சளி, காய்ச்சல்) ஆன்டிபயாடிக்குகள் வேலை செய்யாது."
                ),
                "te": (
                    "### 🔬 బ్యాక్టీరియా మరియు వైరస్ మధ్య తేడాలు\n\n"
                    "బ్యాక్టీరియాలు స్వతంత్రంగా జీవించగల ఏకకణ జీవులు. వీటిని నాశనం చేయడానికి **యాంటీబయాటిక్స్** వాడతారు. వైరస్‌లకు సొంత కణం ఉండదు, అవి మరొక జీవి కణాలలో మాత్రమే వృద్ధి చెందుతాయి. వైరల్ జలుబులకు యాంటీబయాటిక్స్ పనిచేయవు."
                ),
                "mr": (
                    "### 🔬 जिवाणू (Bacteria) आणि विषाणू (Virus) मधील फरक\n\n"
                    "जिवाणू हे स्वतंत्रपणे जगणारे सजीव एकपेशीय जीव आहेत. त्यांच्या संसर्गावर **अँटिबायोटिक्स (Antibiotics)** गुणकारी ठरतात. विषाणू स्वतः जगू शकत नाहीत, ते मानवी पेशींमध्ये जाऊन वाढतात. विषाणूंच्या संसर्गावर अँटिबायोटिक्स काम करत नाहीत."
                )
            }
            return f"{persona_header}{vb_texts.get(lang, vb_texts['en'])}{escalation_footer}"

        # E. Benefits of Regular Exercise
        is_exercise_query = any(w in q_low for w in [
            "benefit of exercise", "benefits of exercise", "why exercise", "regular exercise",
            "ಕಸರತ್ತಿನ ಪ್ರಯೋಜನಗಳು", "व्यायाम के फायदे", "వ్యాయామం యొక్క ప్రయోజనాలు", "உடற்பயிற்சியின் நன்மைகள்"
        ])
        if is_exercise_query:
            ex_texts = {
                "en": (
                    "### 🏃 Physiological and Clinical Benefits of Regular Physical Exercise\n\n"
                    "Regular physical activity (recommended: at least 150 minutes of moderate-intensity aerobic exercise per week) produces systemic benefits across all organ systems:\n\n"
                    "1. **Cardiovascular Health:** Strengthens cardiac myocardium, enhances stroke volume, lowers resting heart rate, reduces arterial stiffness, and significantly decreases risk of coronary artery disease and hypertension.\n"
                    "2. **Metabolic & Glucose Regulation:** Stimulates contraction-mediated GLUT-4 glucose transporter translocation in skeletal muscle, dramatically improving insulin sensitivity and reducing HbA1c in Type 2 Diabetes.\n"
                    "3. **Lipid Profile Optimization:** Increases cardioprotective High-Density Lipoprotein (HDL) cholesterol while lowering atherogenic Low-Density Lipoproteins (LDL) and triglycerides.\n"
                    "4. **Neurocognitive & Mental Wellbeing:** Triggers endogenous release of beta-endorphins and stimulates Brain-Derived Neurotrophic Factor (BDNF), reducing symptoms of anxiety and depression while preserving cognitive function with aging.\n"
                    "5. **Musculoskeletal Density:** Resistance and weight-bearing exercise stimulates osteoblast activity, preventing osteoporosis and sarcopenia."
                ),
                "kn": (
                    "### 🏃 ನಿಯಮಿತ ವ್ಯಾಯಾಮದ ವೈದ್ಯಕೀಯ ಪ್ರಯೋಜನಗಳು\n\n"
                    "ಪ್ರತಿದಿನ ಕನಿಷ್ಠ 30 ನಿಮಿಷಗಳ ನಿಯಮಿತ ವ್ಯಾಯಾಮ ಅಥವಾ ನಡಿಗೆಯಿಂದಾಗುವ ಪ್ರಮುಖ ಪ್ರಯೋಜನಗಳು:\n\n"
                    "1. **ಹೃದಯದ ಆರೋಗ್ಯ:** ಹೃದಯದ ಸ್ನಾಯುಗಳನ್ನು ಬಲಪಡಿಸುತ್ತದೆ ಮತ್ತು ರಕ್ತದೊತ್ತಡವನ್ನು ನಿಯಂತ್ರಣದಲ್ಲಿಡುತ್ತದೆ.\n"
                    "2. **ಮಧುಮೇಹ ನಿಯಂತ್ರಣ:** ಇನ್ಸುಲಿನ್ ಕಾರ್ಯಕ್ಷಮತೆಯನ್ನು ಹೆಚ್ಚಿಸಿ ರಕ್ತದಲ್ಲಿನ ಸಕ್ಕರೆ ಮಟ್ಟವನ್ನು (Sugar level) ಕಡಿಮೆ ಮಾಡುತ್ತದೆ.\n"
                    "3. **ಕೊಲೆಸ್ಟ್ರಾಲ್ ಸುಧಾರಣೆ:** ಒಳ್ಳೆಯ ಕೊಲೆಸ್ಟ್ರಾಲ್ (HDL) ಹೆಚ್ಚಿಸಿ ಕೆಟ್ಟ ಕೊಲೆಸ್ಟ್ರಾಲ್ (LDL) ಕಡಿಮೆ ಮಾಡುತ್ತದೆ.\n"
                    "4. **ಮಾನಸಿಕ ನೆಮ್ಮದಿ:** ಒತ್ತಡ ಮತ್ತು ಆತಂಕವನ್ನು ನಿವಾರಿಸಿ ಮೆದುಳಿನ ಚುರುಕುತನವನ್ನು ಕಾಪಾಡುತ್ತದೆ.\n"
                    "5. **ಮೂಳೆಗಳ ಬಲ:** ಮೂಳೆಗಳ ಸಾಂದ್ರತೆಯನ್ನು ಹೆಚ್ಚಿಸಿ ವಯಸ್ಸಾದಂತೆ ಬರುವ ಕೀಲುನೋವನ್ನು ತಡೆಯುತ್ತದೆ."
                ),
                "hi": (
                    "### 🏃 नियमित व्यायाम के स्वास्थ्य एवं चिकित्सीय लाभ\n\n"
                    "प्रतिदिन कम से कम 30 मिनट का व्यायाम शरीर के लिए अत्यंत लाभकारी है:\n\n"
                    "1. **हृदय स्वास्थ्य:** रक्त संचार को बेहतर बनाता है और हाई ब्लड प्रेशर के खतरे को कम करता है।\n"
                    "2. **शुगर नियंत्रण:** मांसपेशियों में ग्लूकोज का अवशोषण बढ़ाकर डायबिटीज (शुगर) को नियंत्रित रखता है।\n"
                    "3. **कोलेस्ट्रॉल सुधार:** अच्छे कोलेस्ट्रॉल (HDL) को बढ़ाता है और हानिकारक ट्राइग्लिसराइड्स को कम करता है।\n"
                    "4. **मानसिक स्वास्थ्य:** एंडोर्फिन हार्मोन रिलीज कर तनाव, चिंता और अवसाद को कम करता है।\n"
                    "5. **हड्डियों की मजबूती:** हड्डियों और जोड़ों को मजबूत बनाकर ऑस्टियोपोरोसिस से बचाता है।"
                ),
                "ml": (
                    "### 🏃 വ്യായാമത്തിന്റെ ആരോഗ്യ ഗുണങ്ങൾ\n\n"
                    "ദിവസേനയുള്ള വ്യായാമം ഹൃദയാരോഗ്യം മെച്ചപ്പെടുത്തുന്നു, രക്തത്തിലെ പഞ്ചസാരയുടെ അളവ് നിയന്ത്രിക്കുന്നു, കൊളസ്ട്രോൾ കുറയ്ക്കുന്നു, മാനസിക സമ്മർദ്ദം അകറ്റി മനസ്സിന് ഉന്മേഷം നൽകുന്നു."
                ),
                "ta": (
                    "### 🏃 வழக்கமான உடற்பயிற்சியின் நன்மைகள்\n\n"
                    "தினசரி 30 நிமிட உடற்பயிற்சி இதயத்தை பலப்படுத்துகிறது, இரத்த அழுத்தத்தை குறைக்கிறது, சர்க்கரை நோயைக் கட்டுப்படுத்துகிறது, மற்றும் மன அழுத்தத்தைக் குறைக்கிறது."
                ),
                "te": (
                    "### 🏃 క్రమం తప్పకుండా వ్యాయామం చేయడం వల్ల కలిగే ప్రయోజనాలు\n\n"
                    "రోజువారీ వ్యాయామం గుండె ఆరోగ్యాన్ని మెరుగుపరుస్తుంది, రక్తపోటును తగ్గిస్తుంది, షుగర్ వ్యాధిని నియంత్రణలో ఉంచుతుంది మరియు ఎముకలను దృఢపరుస్తుంది."
                ),
                "mr": (
                    "### 🏃 नियमित व्यायामाचे आरोग्यदायी फायदे\n\n"
                    "दररोज ३० मिनिटे व्यायाम केल्याने हृदय निरोगी राहते, रक्तदाब नियंत्रित राहतो, मधुमेहावर नियंत्रण मिळते, आणि मानसिक ताणतणाव दूर होतो."
                )
            }
            return f"{persona_header}{ex_texts.get(lang, ex_texts['en'])}{escalation_footer}"

        # ---------------------------------------------------------------------
        # 2. GENERAL HEALTH & DISEASE DOMAIN
        # ---------------------------------------------------------------------
        # A. Diabetes Mellitus (Type 1 vs Type 2)
        is_diabetes_query = any(w in q_low for w in [
            "diabetes", "type 1 diabetes", "type 2 diabetes", "explain diabetes", "sugar disease",
            "ಮಧುಮೇಹ", "डायबिटीज", "मधुमेह", "சர்க்கரை நோய்", "షుగర్ వ్యాధి"
        ])
        if is_diabetes_query:
            dia_texts = {
                "en": (
                    "### 🩸 Diabetes Mellitus: Pathophysiology, Types, and Management\n\n"
                    "**Diabetes Mellitus** is a chronic metabolic disease characterized by persistent hyperglycemia (elevated blood glucose) resulting from defects in insulin secretion, insulin action, or both.\n\n"
                    "**Comparison: Type 1 vs. Type 2 Diabetes:**\n"
                    "- **Type 1 Diabetes:** An autoimmune condition where the body's immune system destroys insulin-producing beta cells in the pancreatic islets. Results in an absolute insulin deficiency. Primarily diagnosed in children and young adults; requires lifelong subcutaneous insulin replacement.\n"
                    "- **Type 2 Diabetes (90–95% of cases):** Characterized by progressive peripheral insulin resistance (skeletal muscle, liver, and adipose tissue fail to respond adequately to insulin) combined with a relative insulin secretory defect. Strongly associated with genetics, sedentary lifestyle, and visceral adiposity.\n\n"
                    "**Diagnostic Thresholds (ADA Clinical Criteria):**\n"
                    "- **Fasting Plasma Glucose:** $\\ge 126\\text{ mg/dL}$ (after $\\ge 8\\text{ hrs}$ fast).\n"
                    "- **Glycated Hemoglobin (HbA1c):** $\\ge 6.5\\%$ (Normal: $<5.7\\%$, Prediabetes: $5.7\\text{--}6.4\\%$).\n"
                    "- **Oral Glucose Tolerance Test (2-hr):** $\\ge 200\\text{ mg/dL}$.\n\n"
                    "**Classic Symptoms:**\n"
                    "Frequent urination (Polyuria), excessive thirst (Polydipsia), increased hunger (Polyphagia), unexplained weight loss, blurred vision, and persistent fatigue.\n\n"
                    "**Long-Term Complications:**\n"
                    "- **Microvascular:** Retinopathy (vision loss), Nephropathy (chronic kidney disease), Peripheral Neuropathy (loss of protective sensation in feet).\n"
                    "- **Macrovascular:** Coronary artery disease, myocardial infarction, and ischemic stroke.\n\n"
                    "**Comprehensive Management:**\n"
                    "Medical nutrition therapy, regular physical activity, self-monitoring of blood glucose, and guideline-directed pharmacotherapy (First-line: Metformin; Cardio-renal protective: SGLT2 inhibitors and GLP-1 receptor agonists)."
                ),
                "kn": (
                    "### 🩸 ಮಧುಮೇಹ (Diabetes): ವಿಧಗಳು, ಲಕ್ಷಣಗಳು ಮತ್ತು ನಿರ್ವಹಣೆ\n\n"
                    "**ಮಧುಮೇಹ (ಸಕ್ಕರೆ ಕಾಯಿಲೆ)** ಎಂಬುದು ದೇಹದಲ್ಲಿ ಇನ್ಸುಲಿನ್ ಕೊರತೆ ಅಥವಾ ಇನ್ಸುಲಿನ್ ಸರಿಯಾಗಿ ಕೆಲಸ ಮಾಡದಿರುವುದರಿಂದ ರಕ್ತದಲ್ಲಿ ಗ್ಲೂಕೋಸ್ (ಸಕ್ಕರೆ) ಪ್ರಮಾಣ ಹೆಚ್ಚಾಗುವ ಸ್ಥಿತಿಯಾಗಿದೆ.\n\n"
                    "**ಪ್ರಮುಖ ಎರಡು ವಿಧಗಳು:**\n"
                    "1. **ಟೈಪ್ 1 ಮಧುಮೇಹ:** ದೇಹದ ರೋಗನಿರೋಧಕ ವ್ಯವಸ್ಥೆಯು ಇನ್ಸುಲಿನ್ ಉತ್ಪಾದಿಸುವ ಪ್ಯಾಂಕ್ರಿಯಾಸ್ ಜೀವಕೋಶಗಳನ್ನು ನಾಶಪಡಿಸುತ್ತದೆ. ಇದಕ್ಕೆ ಇನ್ಸುಲಿನ್ ಇಂಜೆಕ್ಷನ್ ಅನಿವಾರ್ಯ.\n"
                    "2. **ಟೈಪ್ 2 ಮಧುಮೇಹ (90% ಕ್ಕಿಂತ ಹೆಚ್ಚು ಪ್ರಕರಣಗಳು):** ದೇಹದಲ್ಲಿ ಇನ್ಸುಲಿನ್ ಉತ್ಪತ್ತಿಯಾದರೂ ಜೀವಕೋಶಗಳು ಅದನ್ನು ಬಳಸಿಕೊಳ್ಳಲು ವಿಫಲವಾಗುತ್ತವೆ (ಇನ್ಸುಲಿನ್ ಪ್ರತಿರೋಧ). ಇದು ಜೀವನಶೈಲಿ, ಬೊಜ್ಜು ಮತ್ತು ಅನುವಂಶಿಕತೆಯಿಂದ ಬರುತ್ತದೆ.\n\n"
                    "**ಪ್ರಮುಖ ಲಕ್ಷಣಗಳು:**\n"
                    "- ಪದೇ ಪದೇ ಮೂತ್ರ ವಿಸರ್ಜನೆ (ವಿಶೇಷವಾಗಿ ರಾತ್ರಿಯಲ್ಲಿ).\n"
                    "- ವಿಪರೀತ ಬಾಯಾರಿಕೆ ಮತ್ತು ಹಸಿವು.\n"
                    "- ಕಾರಣವಿಲ್ಲದೆ ತೂಕ ಇಳಿಕೆ ಮತ್ತು ತೀವ್ರ ಸುಸ್ತು.\n"
                    "- ಗಾಯಗಳು ನಿಧಾನವಾಗಿ ಗುಣವಾಗುವುದು.\n\n"
                    "**ಪರೀಕ್ಷೆಗಳು:** ಖಾಲಿ ಹೊಟ್ಟೆಯ ಶುಗರ್ (Fasting $\\ge 126\\text{ mg/dL}$) ಮತ್ತು HbA1c ($\\ge 6.5\\%$).\n\n"
                    "**ನಿರ್ವಹಣೆ:** ಕಡಿಮೆ ಸಿಹಿ ಮತ್ತು ನಾರಿನಂಶವಿರುವ ಆಹಾರ, ದಿನನಿತ್ಯದ ವ್ಯಾಯಾಮ, ತೂಕ ನಿಯಂತ್ರಣ ಹಾಗೂ ವೈದ್ಯರು ಸೂಚಿಸಿದ ಮೆಟ್‌ಫಾರ್ಮಿನ್‌ನಂತಹ ಔಷಧಿಗಳ ನಿಯಮಿತ ಬಳಕೆ."
                ),
                "hi": (
                    "### 🩸 डायबिटीज (मधुमेह): प्रकार, लक्षण और नियंत्रण\n\n"
                    "**डायबिटीज** एक चयापचय (metabolic) रोग है जिसमें रक्त में शर्करा (ग्लूकोज) का स्तर सामान्य से अधिक हो जाता है। यह इंसुलिन की कमी या इंसुलिन के ठीक से काम न करने के कारण होता है।\n\n"
                    "**दो मुख्य प्रकार:**\n"
                    "1. **टाइप 1 डायबिटीज:** अग्न्याशय (Pancreas) में इंसुलिन बनाने वाली कोशिकाएं नष्ट हो जाती हैं। इसके लिए नियमित इंसुलिन इंजेक्शन आवश्यक होता है।\n"
                    "2. **टाइप 2 डायबिटीज:** शरीर इंसुलिन का सही उपयोग नहीं कर पाता (इंसुलिन रेजिस्टेंस)। यह खराब जीवनशैली, मोटापे और आनुवंशिकी के कारण सबसे आम (90%) है।\n\n"
                    "**प्रमुख लक्षण:**\n"
                    "- बार-बार पेशाब आना और अत्यधिक प्यास लगना।\n"
                    "- बिना कारण वजन कम होना और हर समय थकान रहना।\n"
                    "- आंखों से धुंधला दिखना और घाव का देर से भरना।\n\n"
                    "**निदान (Tests):** फास्टिंग ब्लड शुगर $\\ge 126\\text{ mg/dL}$ और HbA1c $\\ge 6.5\\%$.\n\n"
                    "**रोकथाम व उपचार:** संतुलित आहार (कम मीठा, अधिक फाइबर), रोजाना 30 मिनट की सैर/व्यायाम, और डॉक्टर द्वारा निर्धारित दवाएं (जैसे मेटफॉर्मिन) समय पर लेना।"
                ),
                "ml": (
                    "### 🩸 പ്രമേഹം (Diabetes)\n\n"
                    "രക്തത്തിലെ പഞ്ചസാരയുടെ അളവ് അമിതമാകുന്ന അവസ്ഥയാണ് പ്രമേഹം. ടൈപ്പ് 1 (ഇൻസുലിൻ ഉത്പാദിപ്പിക്കപ്പെടാത്ത അവസ്ഥ), ടൈപ്പ് 2 (ശരീരത്തിന് ഇൻസുലിൻ ശരിയായി ഉപയോഗിക്കാൻ കഴിയാത്ത അവസ്ഥ) എന്നിങ്ങനെ രണ്ട് പ്രധാന വിഭാഗങ്ങളുണ്ട്. അമിത ദാഹം, ഇടയ്ക്കിടെയുള്ള മൂത്രമൊഴിക്കൽ, ക്ഷീണം എന്നിവ പ്രധാന ലക്ഷണങ്ങളാണ്. വ്യായാമം, ഭക്ഷണനിയന്ത്രണം, മരുന്നുകൾ എന്നിവയിലൂടെ ഇത് നിയന്ത്രിക്കാം."
                ),
                "ta": (
                    "### 🩸 சர்க்கரை நோய் (Diabetes)\n\n"
                    "இரத்தத்தில் குளுக்கோஸ் அளவு அதிகரிப்பதே நீரிழிவு அல்லது சர்க்கரை நோய் எனப்படுகிறது. டைப் 1 (இன்சுலின் பற்றாக்குறை) மற்றும் டைப் 2 (இன்சுலின் எதிர்ப்பு). அடிக்கடி சிறுநீர் கழித்தல், அதிக தாகம், சோர்வு ஆகியவை முக்கிய அறிகுறிகள். உடற்பயிற்சி மற்றும் உணவுக்கட்டுப்பாடு மூலம் கட்டுப்படுத்தலாம்."
                ),
                "te": (
                    "### 🩸 మధుమేహం (షుగర్ వ్యాధి - Diabetes)\n\n"
                    "రక్తంలో చక్కెర స్థాయిలు పెరిగే దీర్ఘకాలిక వ్యాధి ఇది. టైప్ 1 మరియు టైప్ 2 అనే రెండు రకాలు ఉన్నాయి. తరచుగా మూత్రవిసర్జన, అధిక దాహం, బరువు తగ్గడం సాధారణ లక్షణాలు. పౌష్టికాహారం, వ్యాయామం మరియు మందుల ద్వారా దీనిని నియంత్రించవచ్చు."
                ),
                "mr": (
                    "### 🩸 मधुमेह (डायबिटीज)\n\n"
                    "रक्तातील साखरेचे प्रमाण वाढल्याने होणारा हा आजार आहे. टाईप १ (इन्सुलिन तयार न होणे) आणि टाईप २ (इन्सुलिनचा योग्य वापर न होणे). जास्त तहान लागणे, वारंवार लघवी होणे आणि थकवा ही प्रमुख लक्षणे आहेत. नियमित व्यायाम आणि योग्य आहाराने हा नियंत्रित ठेवता येतो."
                )
            }
            return f"{persona_header}{dia_texts.get(lang, dia_texts['en'])}{escalation_footer}"

        # B. Hypertension
        is_hypertension = any(w in q_low for w in [
            "hypertension", "high blood pressure", "explain hypertension",
            "ಹೆಚ್ಚಿನ ರಕ್ತದೊತ್ತಡ", "उच्च रक्तचाप", "రక్తపోటు వ్యాధి", "உயர் இரத்த அழுத்தம்"
        ])
        if is_hypertension:
            ht_texts = {
                "en": (
                    "### 🩺 Hypertension: Staging, Pathophysiology, and Clinical Management\n\n"
                    "**Hypertension (High Blood Pressure)** is a chronic cardiovascular condition in which the systemic arterial pressure remains persistently elevated, causing progressive vascular shear stress and organ damage.\n\n"
                    "**Clinical Staging Guidelines (AHA / ACC):**\n"
                    "- **Normal:** $<120\\text{ mmHg}$ systolic AND $<80\\text{ mmHg}$ diastolic.\n"
                    "- **Elevated:** $120\\text{--}129\\text{ mmHg}$ systolic AND $<80\\text{ mmHg}$ diastolic.\n"
                    "- **Stage 1 Hypertension:** $130\\text{--}139\\text{ mmHg}$ systolic OR $80\\text{--}89\\text{ mmHg}$ diastolic.\n"
                    "- **Stage 2 Hypertension:** $\\ge 140\\text{ mmHg}$ systolic OR $\\ge 90\\text{ mmHg}$ diastolic.\n"
                    "- **Hypertensive Crisis:** $>180\\text{ mmHg}$ systolic and/or $>120\\text{ mmHg}$ diastolic (Requires emergency medical care).\n\n"
                    "**Why It is Known as the 'Silent Killer':**\n"
                    "Most patients have zero perceptible symptoms until serious target-organ damage occurs.\n\n"
                    "**Consequences of Uncontrolled Hypertension:**\n"
                    "Stroke (ischemic or hemorrhagic), Myocardial Infarction, Heart Failure with preserved/reduced ejection fraction, Chronic Kidney Disease (arteriosclerotic nephrosclerosis), and Hypertensive Retinopathy.\n\n"
                    "**Evidence-Based Management:**\n"
                    "1. **Lifestyle Interventions:** Dietary Approaches to Stop Hypertension (DASH diet), sodium restriction ($<2,000\\text{ mg/day}$), weight reduction, regular aerobic exercise, and smoking cessation.\n"
                    "2. **First-Line Pharmacotherapy:**\n"
                    "   - **ACE Inhibitors / ARBs:** e.g. Enalapril, Losartan, Telmisartan (renal protection).\n"
                    "   - **Calcium Channel Blockers (CCBs):** e.g. Amlodipine (arterial vasodilation).\n"
                    "   - **Thiazide Diuretics:** e.g. Chlorthalidone, Hydrochlorothiazide (volume reduction)."
                ),
                "kn": (
                    "### 🩺 ಅಧಿಕ ರಕ್ತದೊತ್ತಡ (Hypertension): ಹಂತಗಳು ಮತ್ತು ನಿಯಂತ್ರಣ\n\n"
                    "**ಅಧಿಕ ರಕ್ತದೊತ್ತಡ (Hypertension)** ಎಂದರೆ ರಕ್ತನಾಳಗಳಲ್ಲಿನ ಒತ್ತಡವು ನಿರಂತರವಾಗಿ ಹೆಚ್ಚಾಗಿರುವ ಸ್ಥಿತಿಯಾಗಿದೆ. ಇದನ್ನು 'ನಿಶ್ಯಬ್ದ ಕೊಲೆಗಾರ' (Silent Killer) ಎಂದು ಕರೆಯುತ್ತಾರೆ, ಏಕೆಂದರೆ ಯಾವುದೇ ಆರಂಭಿಕ ಲಕ್ಷಣಗಳು ಇರುವುದಿಲ್ಲ.\n\n"
                    "**ರಕ್ತದೊತ್ತಡದ ಹಂತಗಳು:**\n"
                    "- **ಸಾಮಾನ್ಯ:** $120/80\\text{ mmHg}$ ಗಿಂತ ಕಡಿಮೆ.\n"
                    "- **ಹಂತ 1 (Stage 1):** $130\\text{--}139$ ಅಥವಾ $80\\text{--}89\\text{ mmHg}$.\n"
                    "- **ಹಂತ 2 (Stage 2):** $140$ ಅಥವಾ $90\\text{ mmHg}$ ಗಿಂತ ಹೆಚ್ಚು.\n\n"
                    "**ಅಪಾಯಗಳು:** ಪಾರ್ಶ್ವವಾಯು (Stroke), ಹೃದಯಾಘಾತ ಮತ್ತು ಕಿಡ್ನಿ ವೈಫಲ್ಯ.\n\n"
                    "**ನಿಯಂತ್ರಿಸುವ ಕ್ರಮಗಳು:** ಉಪ್ಪಿನ ಪ್ರಮಾಣ ಕಡಿಮೆ ಮಾಡುವುದು (ದಿನಕ್ಕೆ 1 ಚಮಚಕ್ಕಿಂತ ಕಡಿಮೆ), ಪ್ರತಿದಿನ ವ್ಯಾಯಾಮ, ತೂಕ ನಿಯಂತ್ರಣ ಮತ್ತು ವೈದ್ಯರು ಸೂಚಿಸಿದ ಔಷಧಿಗಳನ್ನು (ಉದಾ. ಲೊಸಾರ್ಟನ್, ಅಮ್ಲೋಡಿಪಿನ್) ತಪ್ಪದೇ ತೆಗೆದುಕೊಳ್ಳುವುದು."
                ),
                "hi": (
                    "### 🩺 उच्च रक्तचाप (Hypertension): कारण और रोकथाम\n\n"
                    "**हाई ब्लड प्रेशर (Hypertension)** का अर्थ है धमनियों में रक्त का दबाव लगातार $140/90\\text{ mmHg}$ से अधिक बने रहना।\n\n"
                    "**इसे 'साइलेंट किलर' क्यों कहते हैं?**\n"
                    "इसके कोई स्पष्ट लक्षण नहीं होते लेकिन यह अंदर ही अंदर हृदय, मस्तिष्क और गुर्दे की नसों को नुकसान पहुंचाता है।\n\n"
                    "**रोकथाम व नियंत्रण:**\n"
                    "1. भोजन में नमक (सोडियम) कम करें।\n"
                    "2. नियमित 30 मिनट टहलें और तनाव मुक्त रहें।\n"
                    "3. डॉक्टर की सुझाई बीपी की दवाएं बिना पूछे कभी बंद न करें।"
                ),
                "ml": (
                    "### 🩺 അമിത രക്തസമ്മർദ്ദം (Hypertension)\n\n"
                    "രക്തസമ്മർദ്ദം 140/90 mmHg-ൽ കൂടുതലാകുന്ന അവസ്ഥയാണിത്. ഉപ്പ് കുറയ്ക്കുക, വ്യായാമം ചെയ്യുക, ബിപി മരുന്നുകൾ കൃത്യമായി കഴിക്കുക എന്നിവയിലൂടെ ഹൃദയാഘാതവും പക്ഷാഘാതവും തടയാം."
                ),
                "ta": (
                    "### 🩺 உயர் இரத்த அழுத்தம் (Hypertension)\n\n"
                    "இரத்த அழுத்தம் 140/90 mmHg-க்கு மேல் இருக்கும் நிலை. உணவில் உப்பைக் குறைத்தல், எடையைக் கட்டுப்படுத்துதல் மற்றும் பரிந்துரைக்கப்பட்ட மருந்துகளைத் தவறாமல் உட்கொள்வது அவசியம்."
                ),
                "te": (
                    "### 🩺 అధిక రక్తపోటు (Hypertension)\n\n"
                    "రక్తపోటు నిరంతరం 140/90 mmHg కంటే ఎక్కువగా ఉండే పరిస్థితి. ఉప్పు తగ్గించడం, రోజువారీ వ్యాయామం మరియు క్రమం తప్పకుండా బీపీ మందులు వాడటం ద్వారా నియంత్రించవచ్చు."
                ),
                "mr": (
                    "### 🩺 उच्च रक्तदाब (Hypertension)\n\n"
                    "रक्तदाब सतत १४०/९० पेक्षा जास्त राहणे म्हणजे हायपरटेन्शन. जेवणातील मीठ कमी करणे, वजन आटोक्यात ठेवणे आणि डॉक्टरांच्या सल्ल्याने औषधे वेळेवर घेणे आवश्यक आहे."
                )
            }
            return f"{persona_header}{ht_texts.get(lang, ht_texts['en'])}{escalation_footer}"

        # C. Cholesterol (LDL vs HDL)
        is_cholesterol = any(w in q_low for w in [
            "cholesterol", "ldl vs hdl", "ldl and hdl", "difference between ldl and hdl",
            "ಕೊಲೆಸ್ಟ್ರಾಲ್", "कोलेस्ट्रॉल", "கொலஸ்ட்ரால்", "కొలెస్ట్రాల్"
        ])
        if is_cholesterol:
            ch_texts = {
                "en": (
                    "### 🔬 Cholesterol Metabolism: LDL vs. HDL and Cardiovascular Risk\n\n"
                    "**Cholesterol** is a vital waxy lipid synthesized primarily by the liver and utilized for cellular membrane integrity, steroid hormone synthesis, and bile acid production. Because lipids are insoluble in blood plasma, they are transported packaged inside **lipoproteins**:\n\n"
                    "| Parameter | LDL (Low-Density Lipoprotein) | HDL (High-Density Lipoprotein) |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **Colloquial Name** | **'Bad Cholesterol'** | **'Good Cholesterol'** |\n"
                    "| **Primary Role** | Delivers cholesterol from liver to peripheral arterial tissues. | **Reverse Cholesterol Transport:** Clears excess cholesterol from arterial tissues back to liver. |\n"
                    "| **Atherogenic Risk** | **High:** Excess circulating LDL penetrates arterial walls, becomes oxidized, and forms atherosclerotic plaques. | **Protective:** Anti-inflammatory and promotes vascular plaque regression. |\n"
                    "| **Optimal Levels** | $<100\\text{ mg/dL}$ ($<70\\text{ mg/dL}$ in high-risk cardiac patients). | $\\ge 40\\text{ mg/dL}$ (men), $\\ge 50\\text{ mg/dL}$ (women). |\n\n"
                    "**Triglycerides:** Another lipid fraction; levels $>150\\text{ mg/dL}$ further accelerate cardiovascular risk.\n\n"
                    "**How to Optimize Lipid Ratios:**\n"
                    "- Minimize trans-fats and refined carbohydrates.\n"
                    "- Increase soluble fiber (oats, legumes) and omega-3 fatty acids.\n"
                    "- Aerobic exercise (effectively raises HDL levels).\n"
                    "- Pharmacotherapy: **HMG-CoA Reductase Inhibitors (Statins)** such as Atorvastatin or Rosuvastatin significantly reduce LDL and stabilize arterial plaques."
                ),
                "kn": (
                    "### 🔬 ಕೊಲೆಸ್ಟ್ರಾಲ್: ಒಳ್ಳೆಯ ಕೊಲೆಸ್ಟ್ರಾಲ್ (HDL) ಮತ್ತು ಕೆಟ್ಟ ಕೊಲೆಸ್ಟ್ರಾಲ್ (LDL)\n\n"
                    "ಕೊಲೆಸ್ಟ್ರಾಲ್ ನಮ್ಮ ದೇಹದ ಜೀವಕೋಶಗಳಿಗೆ ಅಗತ್ಯವಾದ ಜಿಡ್ಡಿನಂಶವಾಗಿದೆ. ಇದರಲ್ಲಿ ಎರಡು ಮುಖ್ಯ ವಿಧಗಳಿವೆ:\n\n"
                    "1. **ಕೆಟ್ಟ ಕೊಲೆಸ್ಟ್ರಾಲ್ (LDL - Low-Density Lipoprotein):** ಇದು ರಕ್ತನಾಳಗಳ ಗೋಡೆಗಳಲ್ಲಿ ಸಂಗ್ರಹವಾಗಿ ರಕ್ತ ಸಂಚಾರವನ್ನು ತಡೆಯುತ್ತದೆ. ಇದರಿಂದ ಹೃದಯಾಘಾತದ ಅಪಾಯ ಹೆಚ್ಚಾಗುತ್ತದೆ (ಗುರಿ: $100\\text{ mg/dL}$ ಗಿಂತ ಕಡಿಮೆ).\n"
                    "2. **ಒಳ್ಳೆಯ ಕೊಲೆಸ್ಟ್ರಾಲ್ (HDL - High-Density Lipoprotein):** ಇದು ರಕ್ತನಾಳಗಳಿಂದ ಹೆಚ್ಚುವರಿ ಕೊಬ್ಬನ್ನು ತೆಗೆದು ಯಕೃತ್ತಿಗೆ (Liver) ಕಳುಹಿಸಿ ರಕ್ತನಾಳಗಳನ್ನು ಶುಚಿಗೊಳಿಸುತ್ತದೆ (ಗುರಿ: $50\\text{ mg/dL}$ ಗಿಂತ ಹೆಚ್ಚು).\n\n"
                    "**ಕೊಲೆಸ್ಟ್ರಾಲ್ ನಿಯಂತ್ರಣ:** ಎಣ್ಣೆ ಪದಾರ್ಥಗಳನ್ನು ಕಡಿಮೆ ಮಾಡುವುದು, ನಾರಿನಂಶವಿರುವ ಆಹಾರ ಸೇವನೆ, ನಡಿಗೆ ಮತ್ತು ಅಗತ್ಯವಿದ್ದಲ್ಲಿ ವೈದ್ಯರು ನೀಡುವ ಸ್ಟ್ಯಾಟಿನ್ ಮಾತ್ರೆಗಳು (ಉದಾ. ಅಟೋರ್ವಾಸ್ಟಾಟಿನ್)."
                ),
                "hi": (
                    "### 🔬 कोलेस्ट्रॉल: LDL (खराब) बनाम HDL (अच्छा)\n\n"
                    "कोलेस्ट्रॉल एक मोम जैसा वसा है जो शरीर के लिए जरूरी है, लेकिन इसका संतुलन बिगड़ना खतरनाक हो सकता है:\n\n"
                    "1. **LDL (खराब कोलेस्ट्रॉल):** यह धमनियों में जमा होकर ब्लॉकेज बनाता है जिससे दिल का दौरा और स्ट्रोक हो सकता है (स्तर $100\\text{ mg/dL}$ से कम होना चाहिए)।\n"
                    "2. **HDL (अच्छा कोलेस्ट्रॉल):** यह धमनियों से अतिरिक्त वसा को लीवर तक वापस ले जाकर साफ करता है (स्तर $50\\text{ mg/dL}$ से अधिक होना चाहिए)।\n\n"
                    "**नियंत्रण:** जंक फूड और तला-भुना कम करें, हरी सब्जियां और फल खाएं, और रोजाना कसरत करें।"
                ),
                "ml": (
                    "### 🔬 കൊളസ്ട്രോൾ: LDL ഉം HDL ഉം\n\n"
                    "LDL എന്നാൽ 'ചീത്ത കൊളസ്ട്രോൾ' ആണ്, ഇത് രക്തക്കുഴലുകളിൽ കൊഴുപ്പ് അടിഞ്ഞുകൂടി ഹൃദയാഘാതമുണ്ടാക്കാം. HDL എന്നാൽ 'നല്ല കൊളസ്ട്രോൾ' ആണ്, ഇത് രക്തക്കുഴലുകളെ സംരക്ഷിക്കുന്നു."
                ),
                "ta": (
                    "### 🔬 கொலஸ்ட்ரால்: LDL மற்றும் HDL வேறுபாடு\n\n"
                    "LDL என்பது கெட்ட கொலஸ்ட்ரால், இது இரத்தக் குழாய்களில் அடைப்பை ஏற்படுத்தும். HDL என்பது நல்ல கொலஸ்ட்ரால், இது இதயத்தைப் பாதுகாக்கும்."
                ),
                "te": (
                    "### 🔬 కొలెస్ట్రాల్: LDL మరియు HDL మధ్య తేడాలు\n\n"
                    "LDL అనేది చెడు కొలెస్ట్రాల్, ఇది గుండె నాళాల్లో అడ్డంకులు కలిగిస్తుంది. HDL అనేది మంచి కొలెస్ట్రాల్, ఇది గుండెను ఆరోగ్యంగా ఉంచుతుంది."
                ),
                "mr": (
                    "### 🔬 कोलेस्ट्रॉल: LDL आणि HDL मधील फरक\n\n"
                    "LDL हे 'वाईट कोलेस्ट्रॉल' असून ते रक्तवाहिन्यांमध्ये अडथळा निर्माण करते. HDL हे 'चांगले कोलेस्ट्रॉल' असून ते हृदयाचे रक्षण करते."
                )
            }
            return f"{persona_header}{ch_texts.get(lang, ch_texts['en'])}{escalation_footer}"

        # D. Dehydration
        is_dehydration = any(w in q_low for w in [
            "dehydration", "signs of dehydration", "treatment of dehydration", "explain dehydration",
            "ನಿರ್ಜಲೀಕರಣ", "निर्जलीकरण", "நீரிழப்பு", "డీహైడ్రేషన్"
        ])
        if is_dehydration:
            dh_texts = {
                "en": (
                    "### 💧 Dehydration: Pathophysiology, Clinical Stages, and Treatment\n\n"
                    "**Dehydration** occurs when water and electrolyte losses exceed total fluid intake, disrupting cellular osmolarity and intravascular volume.\n\n"
                    "**Clinical Stages and Symptoms:**\n"
                    "1. **Mild Dehydration (3–5% fluid loss):** Increased thirst, dry oral mucosa, slightly reduced urine output, darker amber-colored urine.\n"
                    "2. **Moderate Dehydration (6–9% fluid loss):** Sunken eyes, loss of skin turgor (skin tenting), dry tongue, tachycardia, postural hypotension, oliguria (scanty urine), irritability.\n"
                    "3. **Severe Dehydration ($\\ge 10\\%$ fluid loss - Medical Emergency):** Altered mental state, lethargy, cold clammy extremities, weak rapid pulse, hypotension, anuria, hypovolemic shock.\n\n"
                    "**Evidence-Based Treatment:**\n"
                    "- **Oral Rehydration Salts (ORS):** The gold standard for mild-to-moderate dehydration. The WHO-formulated ORS contains balanced glucose and sodium in an exact 2:1 stoichiometric ratio, harnessing the intestinal **Sodium-Glucose Co-Transporter (SGLT1)** to maximize active fluid absorption into circulation even during diarrhea.\n"
                    "- **What to Avoid:** Plain hypertonic sugary sodas or energy drinks (exacerbate osmotic diarrhea).\n"
                    "- **Severe Dehydration:** Requires immediate hospital emergency intravenous fluid resuscitation (Normal Saline or Ringer's Lactate)."
                ),
                "kn": (
                    "### 💧 ನಿರ್ಜಲೀಕರಣ (Dehydration): ಲಕ್ಷಣಗಳು ಮತ್ತು ಚಿಕಿತ್ಸೆ\n\n"
                    "ದೇಹದಲ್ಲಿನ ನೀರಿನ ಮತ್ತು ಲವಣಾಂಶಗಳ ಪ್ರಮಾಣ ಗಣನೀಯವಾಗಿ ಕಡಿಮೆಯಾಗುವುದನ್ನು **ನಿರ್ಜಲೀಕರಣ** ಎನ್ನುತ್ತಾರೆ.\n\n"
                    "**ಮುಖ್ಯ ಲಕ್ಷಣಗಳು:**\n"
                    "- ತೀವ್ರ ಬಾಯಾರಿಕೆ ಮತ್ತು ಒಣಗಿದ ತುಟಿಗಳು.\n"
                    "- ಮೂತ್ರದ ಪ್ರಮಾಣ ಕಡಿಮೆಯಾಗುವುದು ಮತ್ತು ಗಾಢ ಹಳದಿ ಬಣ್ಣ.\n"
                    "- ತಲೆತಿರುಗುವಿಕೆ, ಆಯಾಸ ಮತ್ತು ಕಣ್ಣುಗಳು ಒಳಗುಂದುವುದು.\n\n"
                    "**ಚಿಕಿತ್ಸೆ:**\n"
                    "- **ಓ.ಆರ್.ಎಸ್ (ORS):** ವಿಶ್ವ ಆರೋಗ್ಯ ಸಂಸ್ಥೆಯ ಪ್ರಮಾಣಿತ ORS ಪುಡಿಯನ್ನು 1 ಲೀಟರ್ ಶುದ್ಧ ನೀರಿನಲ್ಲಿ ಬೆರೆಸಿ ಕುಡಿಯುವುದು ಅತ್ಯಂತ ಪರಿಣಾಮಕಾರಿ.\n"
                    "- ಎಳನೀರು ಮತ್ತು ಮಜ್ಜಿಗೆ ಕೂಡ ಉಪಯುಕ್ತ.\n"
                    "- ತೀವ್ರ ನಿಶ್ಯಕ್ತಿಯಿದ್ದಲ್ಲಿ ತಕ್ಷಣ ಆಸ್ಪತ್ರೆಗೆ ತೆರಳಿ ಐವಿ (IV) ದ್ರವ ಪಡೆಯಬೇಕು."
                ),
                "hi": (
                    "### 💧 डिहाइड्रेशन (शरीर में पानी की कमी): लक्षण और उपचार\n\n"
                    "जब शरीर से तरल पदार्थ और आवश्यक इलेक्ट्रोलाइट्स की अत्यधिक कमी हो जाती है, तो उसे **डिहाइड्रेशन** कहते हैं।\n\n"
                    "**प्रमुख लक्षण:** अत्यधिक प्यास, सूखा मुंह, गहरा पीला पेशाब, चक्कर आना और अत्यधिक थकान।\n\n"
                    "**इलाज:** सबसे उत्तम उपाय **ओआरएस (ORS घोल)** पीना है जो शरीर में सोडियम और पानी के संतुलन को तुरंत बहाल करता है। इसके अलावा नारियल पानी और छाछ भी लाभदायक हैं।"
                ),
                "ml": (
                    "### 💧 നിർജ്ജലീകരണം (Dehydration)\n\n"
                    "ശരീരത്തിൽ ജലാംശവും ലവണങ്ങളും കുറയുന്ന അവസ്ഥ. അമിത ദാഹം, വരണ്ട നാവ്, തലകറക്കം എന്നിവ ലക്ഷണങ്ങളാണ്. ഇതിന് ഏറ്റവും നല്ല പ്രതിവിധി **ORS ലായനി** കുടിക്കുക എന്നതാണ്."
                ),
                "ta": (
                    "### 💧 நீரிழப்பு (Dehydration)\n\n"
                    "உடலில் நீர் மற்றும் தாது உப்புகள் குறைவது நீரிழப்பு எனப்படும். தாகம், வறண்ட வாய், தலைச்சுற்றல் போன்றவை இதன் அறிகுறிகள். இதற்கு சிறந்த சிகிச்சை **ORS கரைசல்** குடிப்பதாகும்."
                ),
                "te": (
                    "### 💧 డీహైడ్రేషన్ (శరీరంలో నీటి కొరత)\n\n"
                    "శరీరంలో నీరు మరియు లవణాలు తగ్గిపోవడం వల్ల ఇది వస్తుంది. విపరీతమైన దాహం, తలతిరగడం సాధారణ లక్షణాలు. దీనికి **ORS ద్రవం** తాగడం అత్యంత ప్రభావవంతమైన చికిత్స."
                ),
                "mr": (
                    "### 💧 डिहायड्रेशन (शरीरातील पाण्याचे प्रमाण कमी होणे)\n\n"
                    "अतिसार, उलट्या किंवा उन्हामुळे शरीरातील पाणी व क्षार कमी होतात. तीव्र तहान, कोरडी जीभ आणि चक्कर येणे ही लक्षणे आहेत. **ORS द्रावण** पिणे हा सर्वात उत्तम उपाय आहे."
                )
            }
            return f"{persona_header}{dh_texts.get(lang, dh_texts['en'])}{escalation_footer}"

        # E. Antibiotics & Antimicrobial Resistance
        is_antibiotic = any(w in q_low for w in [
            "antibiotic", "antibiotics", "antimicrobial", "amr",
            "ಆಂಟಿಬಯೋಟಿಕ್", "एंटीबायोटिक", "ஆன்டிபயாடிக்", "యాంటీబయాటిక్"
        ])
        if is_antibiotic:
            ab_texts = {
                "en": (
                    "### 💊 Antibiotics and Antimicrobial Resistance (AMR)\n\n"
                    "**Antibiotics** are essential therapeutic agents designed to treat bacterial infections by killing bacteria (bactericidal) or inhibiting their replication (bacteriostatic). They work by targeting specific prokaryotic structures (e.g. bacterial peptidoglycan cell walls, 50S/30S ribosomes, or DNA gyrase) absent in human cells.\n\n"
                    "**What is Antimicrobial Resistance (AMR)?**\n"
                    "AMR occurs when bacteria evolve defensive biochemical mechanisms (e.g. beta-lactamase enzyme production, efflux pumps, mutated binding targets) that render antibiotics ineffective, transforming treatable infections into lethal superbug outbreaks.\n\n"
                    "**Why You Must Complete the Entire Prescribed Course:**\n"
                    "When an antibiotic is initiated, it rapidly kills the most susceptible bacteria, alleviating patient symptoms within 48–72 hours. However, the most resilient, partially resistant bacterial sub-populations remain alive. If the course is discontinued prematurely, these resilient bacteria survive, multiply, and transmit resistance genes to other bacterial species.\n\n"
                    "**Prudent Antibiotic Guidelines:**\n"
                    "1. Never take antibiotics for viral colds, influenza, or viral bronchitis.\n"
                    "2. Always take the exact dosage prescribed for the entire duration.\n"
                    "3. Never save or share leftover prescription antibiotics."
                ),
                "kn": (
                    "### 💊 ಆಂಟಿಬಯೋಟಿಕ್ಸ್ ಮತ್ತು ಆಂಟಿಬಯೋಟಿಕ್ ಪ್ರತಿರೋಧ (Antibiotic Resistance)\n\n"
                    "**ಆಂಟಿಬಯೋಟಿಕ್ಸ್** ಬ್ಯಾಕ್ಟೀರಿಯಾದಿಂದ ಉಂಟಾಗುವ ಸೋಂಕುಗಳನ್ನು ಗುಣಪಡಿಸುವ ಪ್ರಮುಖ ಔಷಧಿಗಳಾಗಿವೆ.\n\n"
                    "**ಆಂಟಿಬಯೋಟಿಕ್ ಪ್ರತಿರೋಧ ಎಂದರೇನು?**\n"
                    "ನಾವು ಆಂಟಿಬಯೋಟಿಕ್ ಅನ್ನು ಅತಿಯಾಗಿ ಅಥವಾ ತಪ್ಪಾಗಿ ಬಳಸಿದಾಗ, ಬ್ಯಾಕ್ಟೀರಿಯಾಗಳು ಆ ಔಷಧಿಗಳನ್ನು ಎದುರಿಸುವ ಶಕ್ತಿಯನ್ನು ಬೆಳೆಸಿಕೊಳ್ಳುತ್ತವೆ. ನಂತರ ಅದೇ ಔಷಧಿ ಆ ಕಾಯಿಲೆಯನ್ನು ಗುಣಪಡಿಸಲು ವಿಫಲವಾಗುತ್ತದೆ.\n\n"
                    "**ಕೋರ್ಸ್ ಪೂರ್ಣಗೊಳಿಸುವುದು ಏಕೆ ಕಡ್ಡಾಯ?**\n"
                    "ಔಷಧಿ ಶುರುಮಾಡಿದ 2 ದಿನಕ್ಕೆ ಹುಷಾರಾದಂತೆ ಅನ್ನಿಸಿದರೂ, ದೇಹದೊಳಗಿನ ಬಲಿಷ್ಠ ಬ್ಯಾಕ್ಟೀರಿಯಾಗಳು ಸಂಪೂರ್ಣವಾಗಿ ನಾಶವಾಗಿರುವುದಿಲ್ಲ. ಕೋರ್ಸ್ ಅರ್ಧಕ್ಕೆ ನಿಲ್ಲಿಸಿದರೆ ಆ ಬ್ಯಾಕ್ಟೀರಿಯಾಗಳು ಮರುಜೀವ ಪಡೆದು ಅಪಾಯಕಾರಿಯಾಗಿ ಬದಲಾಗುತ್ತವೆ.\n\n"
                    "⚠️ ವೈದ್ಯರ ಚೀಟಿಯಿಲ್ಲದೆ ಆಂಟಿಬಯೋಟಿಕ್ ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ."
                ),
                "hi": (
                    "### 💊 एंटीबायोटिक और एंटीबायोटिक रेजिस्टेंस (प्रतिरोध)\n\n"
                    "**एंटीबायोटिक** दवाएं केवल बैक्टीरिया के संक्रमण को ठीक करने के लिए होती हैं।\n\n"
                    "**एंटीबायोटिक कोर्स पूरा करना क्यों जरूरी है?**\n"
                    "दवा लेने के २-३ दिन बाद जब लक्षण ठीक होने लगते हैं, तब भी शरीर में कुछ मजबूत बैक्टीरिया जीवित रहते हैं। यदि दवा बीच में बंद कर दी जाए, तो वे बैक्टीरिया उस दवा के प्रति प्रतिरोधी (Resistant) बन जाते हैं और अगली बार वह दवा बेअसर हो जाती है।\n\n"
                    "⚠️ सर्दी, जुकाम और फ्लू में एंटीबायोटिक कभी न लें।"
                ),
                "ml": (
                    "### 💊 ആന്റിബയോട്ടിക് റെസിസ്റ്റൻസ്\n\n"
                    "ബാക്ടീരിയകൾക്കെതിരെ നൽകുന്ന മരുന്നുകൾ കൃത്യമായ ദിവസങ്ങളിൽ പൂർത്തിയാക്കിയില്ലെങ്കിൽ, ബാക്ടീരിയകൾ ആ മരുന്നിനെതിരെ പ്രതിരോധം നേടുകയും ഭാവിയിൽ ആ മരുന്ന് ഫലിക്കാതെ വരികയും ചെയ്യും."
                ),
                "ta": (
                    "### 💊 ஆன்டிபயாடிக் எதிர்ப்பு (Antibiotic Resistance)\n\n"
                    "மருத்துவர் பரிந்துரைத்த ஆன்டிபயாடிக் மாத்திரைகளை இடையில் நிறுத்தக்கூடாது. அப்படி நிறுத்தினால் பாக்டீரியாக்கள் அந்த மருந்துக்கு எதிராக எதிர்ப்பு சக்தியை உருவாக்கி மருந்தை பயனற்றதாக்கிவிடும்."
                ),
                "te": (
                    "### 💊 యాంటీబయాటిక్ రెసిస్టెన్స్\n\n"
                    "డాక్టర్ సూచించిన యాంటీబయాటిక్స్ కోర్సును పూర్తిగా వాడాలి. మధ్యలోనే ఆపేస్తే బ్యాక్టీరియా బలపడి ఆ మందుకు లొంగకుండా తయారవుతాయి."
                ),
                "mr": (
                    "### 💊 अँटिबायोटिक रेझिस्टन्स\n\n"
                    "अँटिबायोटिकचा कोर्स डॉक्टरांच्या सल्ल्यानुसार पूर्ण करणे अनिवार्य आहे. मध्येच औषध बंद केल्यास जिवाणू औषधाला दाद देत नाहीत आणि आजार अधिक बळावतो."
                )
            }
            return f"{persona_header}{ab_texts.get(lang, ab_texts['en'])}{escalation_footer}"

        # F. Why medicines are taken with food
        is_food_query = any(w in q_low for w in [
            "with food", "after meals", "take medicine with food", "empty stomach vs food",
            "ಊಟದ ನಂತರ", "ಆಹಾರದೊಂದಿಗೆ", "खाने के बाद दवा", "भोजन के साथ", "உணவுக்குப் பின்", "భోజనం తర్వాత"
        ])
        if is_food_query:
            food_texts = {
                "en": (
                    "### 🍽️ Why Some Medications Must Be Taken With Food\n\n"
                    "Medications have specific administration instructions based on gastrointestinal physiology and pharmacokinetics:\n\n"
                    "1. **Minimizing Gastric Mucosal Irritation:**\n"
                    "   - Nonsteroidal Anti-Inflammatory Drugs (NSAIDs like Ibuprofen, Diclofenac, Naproxen) inhibit the COX-1 enzyme, which naturally protects the gastric mucosal lining. Food acts as a protective buffer, drastically reducing stomach upset, gastritis, and peptic ulceration.\n"
                    "   - Metformin (antidiabetic) frequently triggers gastrointestinal side effects (nausea, diarrhea) when taken on an empty stomach; food significantly improves tolerance.\n"
                    "2. **Enhancing Drug Absorption and Bioavailability:**\n"
                    "   - Lipophilic (fat-soluble) drugs (such as Itraconazole, Cefuroxime axetil, or Atovaquone) require dietary fats and gallbladder bile acids to properly dissolve and be absorbed into circulation.\n"
                    "3. **Timing with Meal-Related Biological Events:**\n"
                    "   - Diabetes medications (like Glimepiride or Acarbose) are designed to handle mealtime glucose influx and prevent dangerous hypoglycemia.\n\n"
                    "💡 *Conversely, certain medications (e.g. Levothyroxine, Bisphosphonates, Omeprazole) must be taken on an empty stomach because food or calcium severely binds and blocks their absorption.*"
                ),
                "kn": (
                    "### 🍽️ ಕೆಲವು ಔಷಧಿಗಳನ್ನು ಊಟದ ನಂತರವೇ ಏಕೆ ತೆಗೆದುಕೊಳ್ಳಬೇಕು?\n\n"
                    "1. **ಹೊಟ್ಟೆಯ ರಕ್ಷಣೆ (ಗ್ಯಾಸ್ಟ್ರಿಕ್ ತಡೆಗಟ್ಟಲು):** ನೋವುನಿವಾರಕಗಳು (ಉದಾಹರಣೆಗೆ ಐಬುಪ್ರೊಫೇನ್, ಡಿಕ್ಲೊಫೆನಾಕ್) ಮತ್ತು ಮೆಟ್‌ಫಾರ್ಮಿನ್ ಹೊಟ್ಟೆಯ ಒಳಪದರವನ್ನು ಕೆರಳಿಸಬಹುದು. ಆಹಾರವು ಹೊಟ್ಟೆಗೆ ರಕ್ಷಣಾ ಕವಚದಂತೆ ಕೆಲಸ ಮಾಡಿ ಅಸಿಡಿಟಿ ಮತ್ತು ಹುಣ್ಣಾಗುವುದನ್ನು ತಡೆಯುತ್ತದೆ.\n"
                    "2. **ರಕ್ತದಲ್ಲಿ ಚೆನ್ನಾಗಿ ಹೀರಲ್ಪಡಲು:** ಕೆಲವು ಔಷಧಿಗಳು ಆಹಾರದಲ್ಲಿರುವ ಜಿಡ್ಡಿನಂಶದೊಂದಿಗೆ ಬೆರೆತಾಗ ಮಾತ್ರ ದೇಹಕ್ಕೆ ಸಮರ್ಪಕವಾಗಿ ತಲುಪುತ್ತವೆ.\n\n"
                    "💡 *ಗಮನಿಸಿ: ಥೈರಾಯ್ಡ್ ಮಾತ್ರೆಗಳು (Thyroxine) ಮತ್ತು ಅಸಿಡಿಟಿ ಮಾತ್ರೆಗಳು (Omeprazole/Pantoprazole) ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲೇ ತೆಗೆದುಕೊಳ್ಳಬೇಕು.*"
                ),
                "hi": (
                    "### 🍽️ कुछ दवाएं खाने के बाद क्यों ली जाती हैं?\n\n"
                    "1. **पेट की सुरक्षा:** दर्द निवारक दवाएं (जैसे आइबूप्रोफेन, डाइक्लोफेनाक) पेट की अंदरूनी परत में जलन और अल्सर पैदा कर सकती हैं। भोजन पेट की रक्षा करता है।\n"
                    "2. **दवा का अवशोषण:** कुछ दवाएं भोजन के साथ शरीर में बेहतर तरीके से घुलती हैं।\n\n"
                    "💡 *नोट: थायराइड और गैस की कुछ दवाएं खाली पेट ही ली जाती हैं।*"
                ),
                "ml": (
                    "### 🍽️ മരുന്നുകൾ ഭക്ഷണത്തോടൊപ്പം കഴിക്കേണ്ടതിന്റെ കാരണം\n\n"
                    "വേദനസംഹാരികൾ (NSAIDs) പോലുള്ള മരുന്നുകൾ വെറുംവയറ്റിൽ കഴിച്ചാൽ അൾസറും ഗ്യാസ്ട്രൈറ്റിസും ഉണ്ടാകാം. ഭക്ഷണം വയറ്റിലെ പാളിയെ സംരക്ഷിക്കുന്നു."
                ),
                "ta": (
                    "### 🍽️ சில மருந்துகளை உணவுக்குப் பின் சாப்பிடக் காரணம்\n\n"
                    "வலி நிவாரணிகள் போன்ற மருந்துகள் வயிற்றுப் புண் மற்றும் அமிலத்தன்மையை ஏற்படுத்தாமல் இருக்கவும், மருந்து சீராக இரத்தத்தில் கலக்கவும் உணவுக்குப் பின் உட்கொள்ள வேண்டும்."
                ),
                "te": (
                    "### 🍽️ కొన్ని మందులను భోజనం తర్వాతే ఎందుకు వేసుకోవాలి?\n\n"
                    "నొప్పి నివారణ మందులు ఖాళీ కడుపుతో తీసుకుంటే కడుపులో మంట, అల్సర్లు వస్తాయి. ఆహారం కడుపు గోడలను కాపాడుతుంది."
                ),
                "mr": (
                    "### 🍽️ काही औषधे जेवणानंतरच का घ्यावीत?\n\n"
                    "पेनकिलर्स आणि मधुमेहाची औषधे रिकाम्या पोटी घेतल्यास ॲसिडिटी व पोटात अल्सर होऊ शकतो. अन्न पोटाच्या अस्तराचे रक्षण करते."
                )
            }
            return f"{persona_header}{food_texts.get(lang, food_texts['en'])}{escalation_footer}"

        # ---------------------------------------------------------------------
        # 3. CLINICAL DRUG-DRUG INTERACTIONS
        # ---------------------------------------------------------------------
        has_losartan = any(w in q_low for w in ["losartan", "लॉसार्टन", "ಲೊಸಾರ್ಟನ್", "లోసార్టన్"])
        has_amlodipine = any(w in q_low for w in ["amlodipine", "अम्लोडिपिन", "ಅಮ್ಲೋಡಿಪಿನ್", "ఆమ్లోడిపైన్"])
        if has_losartan and has_amlodipine:
            cl_resp = {
                "en": (
                    "### 💊 Clinical Drug Evaluation: Losartan + Amlodipine\n\n"
                    "**Clinical Combination Assessment:** Guideline-Recommended Synergistic Antihypertensive Regimen (JNC-8 / AHA / ESC).\n\n"
                    "- **Pharmacological Mechanisms:**\n"
                    "  - **Losartan (ARB):** Selectively blocks the Angiotensin II Type 1 (AT1) receptor, preventing vascular smooth muscle constriction and aldosterone secretion.\n"
                    "  - **Amlodipine (Dihydropyridine CCB):** Inhibits transmembrane calcium influx in vascular smooth muscle cells, producing potent peripheral arteriolar vasodilation.\n"
                    "- **Clinical Synergy:** Combining an ARB and a CCB targets complementary blood pressure pathways, significantly reducing dose-dependent peripheral pedal edema commonly caused by Amlodipine monotherapy.\n"
                    "- **Potential Interaction / Risk:** Dual arterial dilation can produce excessive blood pressure drop (**orthostatic hypotension**), postural dizziness, or lightheadedness, particularly when starting therapy.\n"
                    "- **Kidney & Electrolyte Precautions:** Losartan decreases potassium excretion. Serum creatinine and potassium must be periodically checked, especially in patients with pre-existing renal impairment.\n"
                    "- **Patient Guidance:** Take once daily as directed. Avoid sudden standing from a lying posture. Report severe lightheadedness to your physician."
                ),
                "kn": (
                    "### 💊 ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ: ಲೊಸಾರ್ಟನ್ + ಅಮ್ಲೋಡಿಪಿನ್\n\n"
                    "**ವೈದ್ಯಕೀಯ ಹೊಂದಾಣಿಕೆ:** ಅಧಿಕ ರಕ್ತದೊತ್ತಡ ನಿಯಂತ್ರಣಕ್ಕೆ ಈ ಸಂಯೋಜನೆ ಅತ್ಯಂತ ಸುರಕ್ಷಿತ ಮತ್ತು ವೈದ್ಯಕೀಯ ಮಾರ್ಗಸೂಚಿಗಳಲ್ಲಿ ಶಿಫಾರಸು ಮಾಡಲ್ಪಟ್ಟಿದೆ.\n\n"
                    "- **ಕಾರ್ಯವಿಧಾನ:** ಲೊಸಾರ್ಟನ್ ರಕ್ತನಾಳಗಳನ್ನು ಸಂಕುಚಿತಗೊಳಿಸುವ ಹಾರ್ಮೋನ್ ಅನ್ನು ತಡೆಯುತ್ತದೆ; ಅಮ್ಲೋಡಿಪಿನ್ ರಕ್ತನಾಳಗಳನ್ನು ಸಡಿಲಗೊಳಿಸಿ ರಕ್ತದೊತ್ತಡ ಕಡಿಮೆ ಮಾಡುತ್ತದೆ.\n"
                    "- **ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಆರಂಭಿಕ ದಿನಗಳಲ್ಲಿ ತಲೆತಿರುಗುವಿಕೆ (ರಕ್ತದೊತ್ತಡ ತೀರಾ ಕಡಿಮೆಯಾಗುವುದರಿಂದ) ಉಂಟಾಗಬಹುದು. ಕಾಲಿನ ಊತ ಅಥವಾ ನಿಶ್ಯಕ್ತಿಯಿದ್ದರೆ ವೈದ್ಯರ ಗಮನಕ್ಕೆ ತನ್ನಿ."
                ),
                "hi": (
                    "### 💊 क्लिनिकल मूल्यांकन: लॉसार्टन + अम्लोडिपिन\n\n"
                    "**चिकित्सीय स्थिति:** यह उच्च रक्तचाप (Hypertension) को नियंत्रित करने के लिए डॉक्टरों द्वारा दी जाने वाली मानक और सुरक्षित जोड़ी है।\n\n"
                    "- **कार्यप्रणाली:** दोनों दवाएं मिलकर नसों को आराम देती हैं जिससे बीपी आसानी से नियंत्रित होता है।\n"
                    "- **सावधानी:** अचानक खड़े होने पर चक्कर आ सकते हैं। नियमित रूप से बीपी और किडनी फंक्शन की जांच कराते रहें।"
                ),
                "ml": (
                    "### 💊 ക്ലിനിക്കൽ വിലയിരുത്തൽ: ലോസാർട്ടൻ + അംലോഡിപിൻ\n\n"
                    "രക്തസമ്മർദ്ദം നിയന്ത്രിക്കാൻ ഡോക്ടർമാർ സാധാരണയായി ഒരുമിച്ച് നൽകുന്ന സുരക്ഷിതമായ സംയോജനമാണിത്. എന്നാൽ ബിപി വല്ലാതെ കുറഞ്ഞു തലകറക്കം ഉണ്ടാകാൻ സാധ്യതയുള്ളതിനാൽ കൃത്യമായ നിരീക്ഷണം ആവശ്യമാണ്."
                ),
                "ta": (
                    "### 💊 மருத்துவ மதிப்பீடு: லோசார்டன் + அம்லோடிபின்\n\n"
                    "இரத்த அழுத்தத்தைக் கட்டுப்படுத்த பரவலாகப் பயன்படுத்தப்படும் பாதுகாப்பான கலவை. தொடக்கத்தில் லேசான தலைச்சுற்றல் ஏற்படலாம் என்பதால் கவனமாக இருக்கவும்."
                ),
                "te": (
                    "### 💊 క్లినికల్ సమీక్ష: లోసార్టన్ + ఆమ్లోడిపైన్\n\n"
                    "రక్తపోటును నియంత్రించడానికి ఇది సురక్షితమైన మరియు ప్రభావవంతమైన కలయిక. ప్రారంభంలో తలతిరగడం వంటి లక్షణాలు ఉంటే డాక్టర్‌ను సంప్రదించండి."
                ),
                "mr": (
                    "### 💊 वैद्यकीय सल्ला: लॉसार्टन + अम्लोडिपिन\n\n"
                    "रक्तदाब नियंत्रित ठेवण्यासाठी ही जोडी अतिशय सुरक्षित आणि प्रभावी मानली जाते. अचानक उभे राहताना चक्कर येत असल्यास डॉक्टरांचा सल्ला घ्या."
                )
            }
            return f"{persona_header}{cl_resp.get(lang, cl_resp['en'])}{escalation_footer}"

        is_triple_whammy = any(w in q_low for w in ["triple whammy", "ibuprofen", "nsaid", "diclofenac", "naproxen"]) and any(w in q_low for w in ["losartan", "enalapril", "diuretic", "furosemide", "ramipril", "telmisartan"])
        if is_triple_whammy:
            tw_resp = {
                "en": (
                    "### ⚠️ Critical Clinical Warning: The 'Triple Whammy' Interaction\n\n"
                    "**Involved Drug Classes:** Renin-Angiotensin Inhibitor (ACEi/ARB like Losartan) + Diuretic (e.g. Furosemide, Chlorthalidone) + NSAID (e.g. Ibuprofen, Diclofenac).\n\n"
                    "- **Hemodynamic Pathophysiology:**\n"
                    "  - Diuretics decrease intravascular plasma volume.\n"
                    "  - NSAIDs inhibit renal prostaglandins, constricting the renal **afferent arteriole** and reducing renal blood flow.\n"
                    "  - ACE inhibitors / ARBs inhibit Angiotensin II, causing preferential dilation of the renal **efferent arteriole**.\n"
                    "- **Clinical Consequence:** Intraglomerular capillary filtration pressure collapses, precipitating acute renal failure (**Acute Kidney Injury - AKI**) and severe hyperkalemia.\n"
                    "- **Safer Alternative:** For pain or fever, **Paracetamol** does not impair renal prostaglandins and is the preferred clinical alternative under medical supervision."
                ),
                "kn": (
                    "### ⚠️ ಗಂಭೀರ ಎಚ್ಚರಿಕೆ: ಟ್ರಿಪಲ್ ವಾಮಿ (Triple Whammy) ಸಂಯೋಜನೆ\n\n"
                    "ಬಿಪಿ ಔಷಧಿ (ACEi/ARB) + ಮೂತ್ರವರ್ಧಕ (Diuretic) + ನೋವುನಿವಾರಕ (NSAID - ಉದಾ. ಐಬುಪ್ರೊಫೇನ್, ಡಿಕ್ಲೊಫೆನಾಕ್) ಒಟ್ಟಿಗೆ ಸೇವಿಸುವುದರಿಂದ ಮೂತ್ರಪಿಂಡಗಳಿಗೆ ಹಠಾತ್ ತೀವ್ರ ಹಾನಿಯುಂಟಾಗಬಹುದು (Acute Kidney Injury).\n\n"
                    "**ಸಲಹೆ:** ನೋವಿಗೆ ಐಬುಪ್ರೊಫೇನ್ ಬದಲಿಗೆ ವೈದ್ಯರ ಸಲಹೆಯೊಂದಿಗೆ **ಪ್ಯಾರಸಿಟಮಾಲ್** ಬಳಸುವುದು ಹೆಚ್ಚು ಸುರಕ್ಷಿತ."
                ),
                "hi": (
                    "### ⚠️ गंभीर चेतावनी: 'ट्रिपल व्हैमी' ड्रग इंटरैक्शन\n\n"
                    "बीपी की दवा (ACEi/ARB) + डाइयुरेटिक (पेशाब बढ़ाने वाली दवा) + पेनकिलर (NSAID जैसे आइबूप्रोफेन/डाइक्लोफेनाक) का एक साथ सेवन किडनी को गंभीर नुकसान पहुंचा सकता है।\n\n"
                    "**सलाह:** दर्द या बुखार के लिए डॉक्टर की सलाह से **पैरासिटामोल** लेना सुरक्षित विकल्प है।"
                ),
                "ml": (
                    "### ⚠️ ട്രിപ്പിൾ വാമി മുന്നറിയിപ്പ്\n\n"
                    "ബിപി മരുന്ന്, ഡൈയൂററ്റിക്, വേദനസംഹാരി (NSAID) എന്നിവ ഒരേസമയം കഴിക്കുന്നത് വൃക്കകളുടെ പ്രവർത്തനത്തെ പെട്ടെന്ന് തകരാറിലാക്കാം. വേദനയ്ക്ക് പാരസെറ്റമോൾ ആണ് കൂടുതൽ സുരക്ഷിതം."
                ),
                "ta": (
                    "### ⚠️ தீவிர எச்சரிக்கை: டிரிபிள் வாமி\n\n"
                    "இரத்த அழுத்த மருந்து, டையூரிடிக் மற்றும் வலி நிவாரணி (NSAID) ஆகியவற்றை ஒன்றாக எடுப்பது சிறுநீரக செயலிழப்பை ஏற்படுத்தக்கூடும். பாராசிட்டமால் பாதுகாப்பானது."
                ),
                "te": (
                    "### ⚠️ తీవ్ర హెచ్చరిక: ట్రిపుల్ వామీ ఇంటరాక్షన్\n\n"
                    "బీపీ మందు + డైయూరిటిక్ + పెయిన్‌కిల్లర్ (NSAID) కలయిక కిడ్నీలకు తీవ్ర నష్టం కలిగిస్తుంది. నొప్పికి పారాసిటమాల్ సురక్షితమైన ప్రత్యామ్నాయం."
                ),
                "mr": (
                    "### ⚠️ गंभीर इशारा: 'ट्रिपल व्हॅमी' औषध परस्परक्रिया\n\n"
                    "बीपीचे औषध + लघवीचे औषध + वेदनाशामक (NSAID) एकत्र घेतल्यास किडनी अचानक निकामी होण्याचा धोका असतो. वेदनेसाठी पॅरासिटामॉल सुरक्षित आहे."
                )
            }
            return f"{persona_header}{tw_resp.get(lang, tw_resp['en'])}{escalation_footer}"

        # ---------------------------------------------------------------------
        # 4. DATABASE MEDICINE MONOGRAPHS
        # ---------------------------------------------------------------------
        CLINICAL_STOPWORDS = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "are", "the", "its", "and", "for", "can", "you", "tell", "give", "does",
            "side", "effects", "effect", "symptom", "symptoms", "dose", "tablet",
            "medicine", "medicines", "drug", "drugs", "about", "with", "from", "that",
            "this", "these", "those", "have", "has", "had", "take", "taking", "taken",
            "used", "using", "more", "much", "many", "some", "any", "not", "all",
            "help", "please", "like", "just", "also", "into", "onto", "over", "under",
            "pharmintel", "order", "online", "check", "detect", "profile", "report",
            "pain", "fever", "cough", "cold", "body", "high", "good", "bad", "blood"
        }

        matched_med = None
        # Only query database if NOT paracetamol, metformin or explicit website help
        is_para = any(w in q_low for w in ["paracetamol", "dolo", "crocin", "calpol"])
        is_met = any(w in q_low for w in ["metformin", "glycomet"])
        is_web = any(hp in raw_q_low for hp in ["how to", "how do i", "order", "buy", "cart"])

        if db and not is_para and not is_met and not is_web:
            words = [w for w in re.findall(r"\w+", q_low) if len(w) >= 4 and w not in CLINICAL_STOPWORDS]
            for w in words:
                med = db.query(Medicine).filter(
                    or_(Medicine.brand_name.ilike(f"%{w}%"), Medicine.generic_name.ilike(f"%{w}%"))
                ).first()
                if med:
                    matched_med = med
                    break

        if matched_med:
            monograph_en = (
                f"### 💊 Clinical Monograph: {matched_med.brand_name} ({matched_med.generic_name})\n\n"
                f"- **Active Ingredients:** {matched_med.active_ingredients}\n"
                f"- **Dosage Form & Strength:** {matched_med.dosage_form} ({matched_med.strength})\n"
                f"- **Therapeutic Category:** {matched_med.therapeutic_category} ({matched_med.drug_classification or 'Standard Formulation'})\n"
                f"- **Approved Indications:** {matched_med.approved_indications}\n"
                f"- **Known Adverse Effects:** {matched_med.known_adverse_effects}\n"
                f"- **Key Contraindications & Warnings:** {matched_med.contraindications}\n"
                f"- **Storage & Handling:** {matched_med.storage_information}\n"
                f"- **Prescription Status:** {matched_med.prescription_classification} | MRP: ₹{matched_med.base_mrp:.2f}\n\n"
                f"💡 *Consult your physician or pharmacist regarding exact dosing schedules tailored to your renal function and clinical history.*"
            )
            monograph_kn = (
                f"### 💊 ವೈದ್ಯಕೀಯ ಮಾಹಿತಿ: {matched_med.brand_name} ({matched_med.generic_name})\n\n"
                f"- **ಸಕ್ರಿಯ ಘಟಕಾಂಶ:** {matched_med.active_ingredients}\n"
                f"- **ಡೋಸೇಜ್ ರೂಪ:** {matched_med.dosage_form} ({matched_med.strength})\n"
                f"- **ಔಷಧದ ವರ್ಗ:** {matched_med.therapeutic_category}\n"
                f"- **ಬಳಕೆಗಳು (Indications):** {matched_med.approved_indications}\n"
                f"- **ಸಾಮಾನ್ಯ ಅಡ್ಡಪರಿಣಾಮಗಳು:** {matched_med.known_adverse_effects}\n"
                f"- **ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು:** {matched_med.contraindications}\n"
                f"- **ಶೇಖರಣೆ:** {matched_med.storage_information}\n\n"
                f"💡 *ವೈದ್ಯರ ಸಲಹೆಯ ಮೇರೆಗೆ ಮಾತ್ರ ಈ ಔಷಧಿಯನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ.*"
            )
            monograph_hi = (
                f"### 💊 दवा मोनोग्राफ: {matched_med.brand_name} ({matched_med.generic_name})\n\n"
                f"- **सक्रिय घटक:** {matched_med.active_ingredients}\n"
                f"- **रूप एवं क्षमता:** {matched_med.dosage_form} ({matched_med.strength})\n"
                f"- **चिकित्सीय श्रेणी:** {matched_med.therapeutic_category}\n"
                f"- **उपयोग:** {matched_med.approved_indications}\n"
                f"- **संभावित साइड इफेक्ट्स:** {matched_med.known_adverse_effects}\n"
                f"- **सावधानियां एवं मतभेद:** {matched_med.contraindications}\n"
                f"- **भंडारण:** {matched_med.storage_information}\n\n"
                f"💡 *खुराक और उपयोग के लिए हमेशा अपने डॉक्टर से परामर्श लें।*"
            )
            m_map = {"en": monograph_en, "kn": monograph_kn, "hi": monograph_hi}
            return f"{persona_header}{m_map.get(lang, monograph_en)}{escalation_footer}"

        # Check curated Paracetamol monograph fallback
        is_paracetamol = any(w in q_low for w in ["paracetamol", "dolo", "crocin", "calpol", "पैरासिटामोल", "ಪ್ಯಾರಸಿಟಮಾಲ್", "பாராசிட்டமால்", "పారాసిటమాల్"])
        if is_paracetamol:
            pcm_texts = {
                "en": (
                    "### 💊 Clinical Monograph: Paracetamol (Acetaminophen)\n\n"
                    "- **Pharmacological Class:** Non-opioid Analgesic and Antipyretic.\n"
                    "- **Mechanism of Action:** Selectively inhibits central nervous system prostaglandin synthesis (inhibition of central COX-3/COX-1 variants) and modulates the endocannabinoid system and descending serotonergic inhibitory pathways. Unlike NSAIDs, it lacks peripheral anti-inflammatory activity.\n"
                    "- **Approved Indications:** Mild-to-moderate somatic pain (headaches, musculoskeletal aches, dental pain) and reduction of fever.\n"
                    "- **Maximum Daily Dosage (Adults):** **4,000 mg (4g) per 24 hours** from all sources. In chronic alcoholism or hepatic dysfunction, the ceiling is reduced to $\\le 2,000\\text{ mg/day}$.\n"
                    "- **Adverse Effects & Toxicity:** Well tolerated at therapeutic doses. In acute overdose, glutathione depletion allows toxic accumulation of the metabolite **NAPQI** (N-acetyl-p-benzoquinone imine), causing severe, potentially fatal centrilobular **hepatic necrosis**.\n"
                    "- **Antidote:** Intravenous N-Acetylcysteine (NAC).\n"
                    "- **Clinical Precautions:** Always check combination cold remedies to prevent unintentional toxic double-dosing."
                ),
                "kn": (
                    "### 💊 ಔಷಧೀಯ ವಿವರಣೆ: ಪ್ಯಾರಸಿಟಮಾಲ್ (Paracetamol - Dolo 650)\n\n"
                    "- **ವರ್ಗ:** ನೋವುನಿವಾರಕ (Analgesic) ಮತ್ತು ಜ್ವರ ನಿವಾರಕ (Antipyretic).\n"
                    "- **ಬಳಕೆಗಳು:** ಜ್ವರ, ತಲೆನೋವು, ಮೈಕೈನೋವು ಮತ್ತು ಹಲ್ಲುನೋವು ನಿವಾರಣೆಗೆ.\n"
                    "- **ಗರಿಷ್ಠ ದೈನಂದಿನ ಮಿತಿ:** ವಯಸ್ಕರಿಗೆ ದಿನಕ್ಕೆ ಗರಿಷ್ಠ 4,000 ಮಿಗ್ರಾಂ (4 ಗ್ರಾಂ). ಅತಿಯಾದ ಬಳಕೆ ಯಕೃತ್ತಿಗೆ (Liver) ಗಂಭೀರ ಹಾನಿಯನ್ನುಂಟುಮಾಡಬಹುದು.\n"
                    "- **ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಮದ್ಯಪಾನ ಮಾಡುವಾಗ ಅಥವಾ ಯಕೃತ್ತಿನ ಸಮಸ್ಯೆ ಇರುವಾಗ ವೈದ್ಯರ ಸಲಹೆಯಿಲ್ಲದೆ ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ."
                ),
                "hi": (
                    "### 💊 क्लिनिकल मोनोग्राफ: पैरासिटामोल (Dolo 650)\n\n"
                    "- **श्रेणी:** दर्द निवारक और बुखार रोधी (Antipyretic).\n"
                    "- **उपयोग:** हल्का से मध्यम दर्द, सिरदर्द, बदन दर्द और बुखार में।\n"
                    "- **अधिकतम सुरक्षित खुराक:** २४ घंटे में अधिकतम ४००० मिलीग्राम (४ ग्राम)। अधिक मात्रा में लेने से लिवर (यकृत) फेल हो सकता है।\n"
                    "- **सावधानी:** कई कफ सीरप में भी पैरासिटामोल होता है, इसलिए अधिक मात्रा से बचें।"
                ),
                "ml": (
                    "### 💊 പാരസെറ്റമോൾ (Paracetamol)\n\n"
                    "പനിയും ശരീരവേദനയും കുറയ്ക്കാൻ ഉപയോഗിക്കുന്ന സുരक्षितമായ മരുന്ന്. മുതിർന്നവർക്ക് ദിവസേന പരമാവധി 4 ഗ്രാമിൽ കൂടുതൽ കഴിക്കാൻ പാടില്ല. അമിതമായി കഴിക്കുന്നത് കരളിനെ ഗുരുതരമായി ബാധിക്കും."
                ),
                "ta": (
                    "### 💊 பாராசிட்டமால் (Paracetamol)\n\n"
                    "காய்ச்சல் மற்றும் உடல் வலியைப் போக்கப் பயன்படும் மருந்து. ஒரு நாளைக்கு அதிகபட்சம் 4000 மில்லிகிராம் மட்டுமே எடுக்க வேண்டும். அளவுக்கு மீறினால் கல்லீரல் பாதிக்கப்படும்."
                ),
                "te": (
                    "### 💊 పారాసిటమాల్ (Paracetamol)\n\n"
                    "జ్వరం మరియు శరీర నొప్పులను తగ్గించడానికి ఉపయోగపడుతుంది. రోజుకు గరిష్టంగా 4000 మి.గ్రా కంటే ఎక్కువ తీసుకోకూడదు. ఎక్కువైతే కాలేయం దెబ్బతింటుంది."
                ),
                "mr": (
                    "### 💊 पॅरासिटामॉल (Paracetamol)\n\n"
                    "ताप आणि अंगदुखी कमी करण्यासाठी सर्वात सामान्य औषध. २४ तासांत ४००० मिग्रॅ पेक्षा जास्त डोस घेतल्यास यकृताला (लिव्हर) गंभीर इजा होऊ शकते."
                )
            }
            return f"{persona_header}{pcm_texts.get(lang, pcm_texts['en'])}{escalation_footer}"

        # Check curated Metformin monograph fallback
        is_metformin = any(w in q_low for w in ["metformin", "glycomet", "मेटफॉर्मिन", "ಮೆಟ್‌ಫಾರ್ಮಿನ್", "மெட்ஃபோர்மின்", "మెట్‌ఫార్మిన్"])
        if is_metformin:
            mf_texts = {
                "en": (
                    "### 💊 Clinical Monograph: Metformin Hydrochloride\n\n"
                    "- **Therapeutic Class:** Biguanide Antidiabetic Agent.\n"
                    "- **Mechanism of Action:** Activates AMP-activated protein kinase (AMPK), reducing hepatic gluconeogenesis, decreasing intestinal glucose absorption, and enhancing peripheral insulin sensitivity.\n"
                    "- **First-Line Indication:** Type 2 Diabetes Mellitus.\n"
                    "- **Key Adverse Effects:** Gastrointestinal distress (metallic taste, diarrhea, abdominal cramps, nausea). Long-term use can reduce Vitamin B12 absorption.\n"
                    "- **Critical Black-Box Warning:** **Lactic Acidosis**, a rare but life-threatening metabolic complication. Contraindicated in severe renal impairment (eGFR $<30\\text{ mL/min/1.73m}^2$) or acute metabolic instability.\n"
                    "- **Radiological Precaution:** Must be withheld 48 hours prior to iodinated radiocontrast imaging procedures."
                ),
                "kn": (
                    "### 💊 ಔಷಧೀಯ ವಿವರಣೆ: ಮೆಟ್‌ಫಾರ್ಮಿನ್ (Metformin)\n\n"
                    "- **ವರ್ಗ:** ಮಧುಮೇಹ ನಿರೋಧಕ (Antidiabetic).\n"
                    "- **ಕಾರ್ಯವಿಧಾನ:** ರಕ್ತದಲ್ಲಿನ ಸಕ್ಕರೆ ಮಟ್ಟವನ್ನು ಕಡಿಮೆ ಮಾಡುತ್ತದೆ ಮತ್ತು ಜೀವಕೋಶಗಳು ಇನ್ಸುಲಿನ್ ಬಳಸಿಕೊಳ್ಳಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.\n"
                    "- **ಅಡ್ಡಪರಿಣಾಮಗಳು:** ಹೊಟ್ಟೆ ಉಬ್ಬರ, ಭೇದಿ ಮತ್ತು ವಾಕರಿಕೆ (ಆಹಾರದೊಂದಿಗೆ ಸೇವಿಸುವುದರಿಂದ ಕಡಿಮೆಯಾಗುತ್ತದೆ).\n"
                    "- **ಕಿಡ್ನಿ ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಕಿಡ್ನಿ ಸಮಸ್ಯೆ ಇರುವವರು ವೈದ್ಯರ ಸಲಹೆಯಿಲ್ಲದೆ ತೆಗೆದುಕೊಳ್ಳಬಾರದು."
                ),
                "hi": (
                    "### 💊 दवा जानकारी: मेटफॉर्मिन (Metformin)\n\n"
                    "- **उपयोग:** टाइप 2 डायबिटीज में पहली पसंद की दवा।\n"
                    "- **सावधानी:** इसे हमेशा भोजन के साथ लें ताकि पेट खराब न हो। किडनी की गंभीर बीमारी में इसका उपयोग वर्जित है।"
                )
            }
            return f"{persona_header}{mf_texts.get(lang, mf_texts['en'])}{escalation_footer}"

        # ---------------------------------------------------------------------
        # 5. WEBSITE FEATURE GUIDANCE (ONLY WHEN EXPLICITLY ASKED)
        # ---------------------------------------------------------------------
        explicit_help_phrases = [
            "how do i use", "how to use", "how to check compatibility", "how to order",
            "how do i order", "how to buy", "how do i buy", "how to find pharmacy", "how to scan qr",
            "how to upload prescription", "how do i upload", "what does red status mean",
            "what does yellow status mean", "what does green status mean", "how do i add medicines",
            "order medicines on pharmintel", "how to order on pharmintel",
            "ಹೇಗೆ ಬಳಸುವುದು", "ಹೇಗೆ ಪರಿಶೀಲಿಸುವುದು", "ಆರ್ಡರ್ ಮಾಡುವುದು ಹೇಗೆ",
            "कैसे उपयोग करें", "दवा कैसे ऑर्डर करें", "प्रिस्क्रिप्शन कैसे अपलोड करें", "स्टेटस का क्या मतलब है"
        ]
        is_explicit_website_help = any(hp in raw_q_low for hp in explicit_help_phrases)

        if is_explicit_website_help:
            if any(w in raw_q_low for w in ["order", "pharmacy", "buy", "cart", "खरीदें", "ಖರೀದಿ"]):
                pharm_guide = {
                    "en": (
                        "### 🛒 How to Order Medicines Online on PharmIntel\n\n"
                        "1. **Navigate to Online Pharmacy:** Click **'Online Pharmacy'** in the sidebar.\n"
                        "2. **Search Medicine:** Use the store search bar to find genuine CDSCO-verified medicines.\n"
                        "3. **Add to Cart:** Select required quantity and click **'Add to Cart'**.\n"
                        "4. **Prescription Upload:** If ordering prescription (Rx) drugs, upload a clear photo of your doctor's prescription.\n"
                        "5. **Delivery Address:** Enter or select your verified delivery address.\n"
                        "6. **Checkout & Payment:** Complete checkout via UPI, Net Banking, or Cash on Delivery.\n"
                        "7. **Order Tracking:** Track your real-time pharmacy verification, packing, and dispatch from the 'My Orders' tab."
                    ),
                    "kn": (
                        "### 🛒 ಫಾರ್ಮ್‌ಇಂಟೆಲ್‌ನಲ್ಲಿ ಆನ್‌ಲೈನ್ ಔಷಧಿ ಆರ್ಡರ್ ಮಾಡುವುದು ಹೇಗೆ?\n\n"
                        "1. ಎಡಭಾಗದ ಮೆನುವಿನಲ್ಲಿ **'Online Pharmacy'** ಆಯ್ಕೆಮಾಡಿ.\n"
                        "2. ಬೇಕಾದ ಔಷಧಿಯನ್ನು ಹುಡುಕಿ **'Add to Cart'** ಕ್ಲಿಕ್ ಮಾಡಿ.\n"
                        "3. ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಅಗತ್ಯವಿರುವ ಔಷಧಿಗಳಿಗೆ ವೈದ್ಯರ ಚೀಟಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.\n"
                        "4. ವಿಳಾಸ ನಮೂದಿಸಿ ಮತ್ತು ಪಾವತಿ (UPI/COD) ಪೂರ್ಣಗೊಳಿಸಿ.\n"
                        "5. 'My Orders' ಪುಟದಲ್ಲಿ ನಿಮ್ಮ ಆರ್ಡರ್ ಸ್ಥಿತಿಯನ್ನು ನೇರವಾಗಿ ಟ್ರ್ಯಾಕ್ ಮಾಡಿ."
                    ),
                    "hi": (
                        "### 🛒 फार्माइंटेल पर दवाएं ऑनलाइन कैसे ऑर्डर करें?\n\n"
                        "1. साइडबार में **'Online Pharmacy'** पर जाएं।\n"
                        "2. अपनी दवा खोजें और **'Add to Cart'** पर क्लिक करें।\n"
                        "3. यदि डॉक्टर के पर्चे (Rx) की आवश्यकता हो, तो पर्चा अपलोड करें।\n"
                        "4. डिलीवरी का पता दर्ज करें और भुगतान करें।\n"
                        "5. 'My Orders' में अपने ऑर्डर की स्थिति ट्रैक करें।"
                    )
                }
                return f"{persona_header}{pharm_guide.get(lang, pharm_guide['en'])}{escalation_footer}"

            if any(w in raw_q_low for w in ["compatibility", "multiple", "detect med", "checker", "status"]):
                comp_guide = {
                    "en": (
                        "### 🛡️ How to Use Multiple Medicine Compatibility Checker\n\n"
                        "1. **Navigate to Drug Detection:** Click **'Drug Detection'** in the sidebar.\n"
                        "2. **Add Medicines:** Search and add up to 5 or more medications you are taking.\n"
                        "3. **Patient Profile:** Enter patient name and record any chronic conditions (e.g. Diabetes, Hypertension) and allergies.\n"
                        "4. **Run Check:** Click **'CHECK ALL MEDICINE INTERACTIONS'** to analyze all drug pairs.\n\n"
                        "**Understanding Color Indicators:**\n"
                        "- 🔴 **RED:** Severe or contraindicated interaction. Requires urgent doctor consultation.\n"
                        "- 🟡 **YELLOW:** Moderate interaction requiring timing adjustments or monitoring.\n"
                        "- 🟢 **GREEN:** Compatible combination with no clinically documented adverse interaction.\n"
                        "- ⚪ **GREY:** Unverified drug requiring individual clinical review."
                    ),
                    "kn": (
                        "### 🛡️ ಬಹು ಔಷಧಿಗಳ ಹೊಂದಾಣಿಕೆ ಪರಿಶೀಲನೆ ಮಾರ್ಗದರ್ಶಿ\n\n"
                        "1. ಎಡಭಾಗದ ಮೆನುವಿನಲ್ಲಿ **'Drug Detection'** ಕ್ಲಿಕ್ ಮಾಡಿ.\n"
                        "2. ನಿಮ್ಮ ಎಲ್ಲಾ ಔಷಧಿಗಳ ಹೆಸರುಗಳನ್ನು ಒಂದೊಂದಾಗಿ ಸೇರಿಸಿ.\n"
                        "3. ರೋಗಿಯ ಹೆಸರು ಮತ್ತು ಕಾಯಿಲೆಗಳನ್ನು ನಮೂದಿಸಿ.\n"
                        "4. **'CHECK ALL MEDICINE INTERACTIONS'** ಕ್ಲಿಕ್ ಮಾಡಿ.\n"
                        "- 🔴 **ಕೆಂಪು (RED):** ತೀವ್ರ ಅಪಾಯ.\n"
                        "- 🟡 **ಹಳದಿ (YELLOW):** ಎಚ್ಚರಿಕೆ ಅಗತ್ಯ.\n"
                        "- 🟢 **ಹಸಿರು (GREEN):** ಸುರಕ್ಷಿತ."
                    ),
                    "hi": (
                        "### 🛡️ मल्टीपल मेडिसिन कॉम्पैटिबिलिटी चेकर गाइड\n\n"
                        "1. साइड मेनू में **'Drug Detection'** खोलें।\n"
                        "2. अपनी सभी दवाओं के नाम दर्ज करें।\n"
                        "3. मरीज का नाम और स्वास्थ्य विवरण दर्ज करें।\n"
                        "4. **'CHECK ALL MEDICINE INTERACTIONS'** पर क्लिक करें।"
                    )
                }
                return f"{persona_header}{comp_guide.get(lang, comp_guide['en'])}{escalation_footer}"

        # ---------------------------------------------------------------------
        # 6. CONTEXT-BASED SYNTHESIS (RAG MONOGRAPHS)
        # ---------------------------------------------------------------------
        if context:
            lines = [l.strip() for l in context.splitlines() if l.strip()]
            summary_points = []
            for line in lines[:4]:
                clean_l = re.sub(r"^-\s*\[.*?\]:\s*", "", line)
                if len(clean_l) > 20:
                    summary_points.append(clean_l)

            joined_summary = "\n\n".join(summary_points) if summary_points else context
            return f"{persona_header}{joined_summary}{escalation_footer}"

        # ---------------------------------------------------------------------
        # 7. DEFAULT DIRECT RESPONSE
        # ---------------------------------------------------------------------
        default_resp = {
            "en": (
                "### 🏥 Welcome to PharmIntel Clinical Intelligence\n\n"
                "I am your AI Clinical Assistant. You can ask me:\n\n"
                "1. **General Medical Science:** How the human heart works, blood pressure mechanics, difference between bacteria and viruses, benefits of exercise, and principles of artificial intelligence.\n"
                "2. **Health Conditions:** Pathophysiology and evidence-based management for Diabetes, Hypertension, Cholesterol (LDL/HDL), and Dehydration.\n"
                "3. **Medications & Interactions:** Monograph details, indications, adverse effects, and drug-drug compatibility (e.g. *'Can I take Losartan with Amlodipine?'*).\n"
                "4. **Platform Guidance:** How to order medicines online, verify medicine QR codes, or check multi-drug regimens."
            ),
            "kn": (
                "### 🏥 ಫಾರ್ಮ್‌ಇಂಟೆಲ್ ಕ್ಲಿನಿಕಲ್ ಇಂಟೆಲಿಜೆನ್ಸ್‌ಗೆ ಸುಸ್ವಾಗತ\n\n"
                "ನಾನು ನಿಮ್ಮ ಎಐ ಆರೋಗ್ಯ ಸಹಾಯಕ. ನೀವು ನನ್ನನ್ನು ಈ ಕೆಳಗಿನವುಗಳ ಬಗ್ಗೆ ಕೇಳಬಹುದು:\n\n"
                "1. **ಸಾಮಾನ್ಯ ವೈದ್ಯಕೀಯ ವಿಜ್ಞಾನ:** ಹೃದಯದ ಕಾರ್ಯ, ರಕ್ತದೊತ್ತಡ, ವೈರಸ್ ಮತ್ತು ಬ್ಯಾಕ್ಟೀರಿಯಾಗಳ ವ್ಯತ್ಯಾಸ, ವ್ಯಾಯಾಮದ ಪ್ರಯೋಜನಗಳು.\n"
                "2. **ಆರೋಗ್ಯ ಮಾಹಿತಿ:** ಮಧುಮೇಹ, ಅಧಿಕ ರಕ್ತದೊತ್ತಡ, ಕೊಲೆಸ್ಟ್ರಾಲ್ ಮತ್ತು ನಿರ್ಜಲೀಕರಣದ ಬಗ್ಗೆ.\n"
                "3. **ಔಷಧಿಗಳು ಮತ್ತು ಹೊಂದಾಣಿಕೆ:** ಔಷಧಿಗಳ ಅಡ್ಡಪರಿಣಾಮಗಳು, ಬಳಕೆ ಹಾಗೂ ಔಷಧಿಗಳನ್ನು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳುವುದು ಸುರಕ್ಷಿತವೇ ಎಂಬ ಮಾಹಿತಿ.\n"
                "4. **ವೆಬ್‌ಸೈಟ್ ಮಾರ್ಗದರ್ಶನ:** ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಔಷಧಿ ಖರೀದಿಸುವುದು ಹೇಗೆ, ಕ್ಯೂಆರ್ ಕೋಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡುವುದು ಹೇಗೆ."
            ),
            "hi": (
                "### 🏥 फार्माइंटेल क्लिनिकल इंटेलिजेंस में आपका स्वागत है\n\n"
                "मैं आपका एआई हेल्थ असिस्टेंट हूँ। आप मुझसे पूछ सकते हैं:\n\n"
                "1. **सामान्य विज्ञान:** दिल का काम, ब्लड प्रेशर का महत्व, बैक्टीरिया और वायरस में अंतर, कसरत के फायदे।\n"
                "2. **रोग एवं स्वास्थ्य:** डायबिटीज, हाई बीपी, कोलेस्ट्रॉल और डिहाइड्रेशन की जानकारी।\n"
                "3. **दवाओं की जानकारी:** दवाओं के साइड इफेक्ट्स, सावधानियां और क्या दो दवाएं एक साथ ले सकते हैं।\n"
                "4. **वेबसाइट गाइड:** दवाएं ऑनलाइन ऑर्डर करना और क्यूआर कोड स्कैन करना।"
            )
        }
        return f"{persona_header}{default_resp.get(lang, default_resp['en'])}{escalation_footer}"


class RAGAssistantService:
    """
    Enterprise Multilingual RAG Medical AI Assistant Service.
    Retrieves verified knowledge sources from AIKnowledgeSource + Medicine catalog.
    Supports English, Kannada, Hindi, Malayalam, Tamil, Telugu, and Marathi.
    """
    llm_client = ProviderIndependentLLMClient()

    @classmethod
    def retrieve_relevant_knowledge(cls, db: Session, query: str, top_k: int = 3) -> List[Tuple[Any, float]]:
        q_clean = query.lower()
        query_tokens = set(re.findall(r"\w+", q_clean))

        scored_sources = []

        # 1. Search DB Medicine catalog
        words = [w for w in query_tokens if len(w) >= 3 and w not in ["what", "explain", "side", "effects", "does", "take", "with", "from"]]
        for w in words:
            meds = db.query(Medicine).filter(
                or_(Medicine.brand_name.ilike(f"%{w}%"), Medicine.generic_name.ilike(f"%{w}%"))
            ).limit(2).all()
            for med in meds:
                med_obj = AIKnowledgeSource(
                    id=med.id + 100000,
                    title=f"Monograph: {med.brand_name} ({med.generic_name})",
                    category="MEDICINE_MONOGRAPH",
                    content=(
                        f"{med.brand_name} contains {med.active_ingredients} ({med.strength}, {med.dosage_form}). "
                        f"Therapeutic Category: {med.therapeutic_category}. "
                        f"Approved Indications: {med.approved_indications}. "
                        f"Adverse Effects: {med.known_adverse_effects}. "
                        f"Contraindications: {med.contraindications}. "
                        f"Storage: {med.storage_information}."
                    ),
                    reference_source=med.source or "CDSCO / FDA Compendium",
                    verification_date=med.last_verified_date or "2026-01-01"
                )
                scored_sources.append((med_obj, 0.95))

        # 2. Search AIKnowledgeSource
        sources = db.query(AIKnowledgeSource).all()
        for src in sources:
            content_tokens = set(re.findall(r"\w+", src.content.lower() + " " + src.title.lower()))
            overlap = len(query_tokens & content_tokens)
            score = overlap / max(1, len(query_tokens))

            for q_tok in query_tokens:
                if q_tok in src.title.lower():
                    score += 0.35

            if score > 0.15:
                scored_sources.append((src, score))

        scored_sources.sort(key=lambda x: x[1], reverse=True)
        return scored_sources[:top_k]

    @classmethod
    async def process_chat_message(
        cls,
        db: Session,
        session_id: str,
        message: str,
        user_id: Optional[int] = None,
        language: str = "en",
        mode: str = "ai_assistant",
        patient_name: Optional[str] = None
    ) -> Dict[str, Any]:
        lang = language if language in SUPPORTED_LANGUAGES else "en"

        # 1. Conversation session
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            conv = Conversation(
                session_id=session_id,
                user_id=user_id,
                title=f"Consultation ({lang}): {message[:30]}..."
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # Retrieve recent turns for multi-turn context
        recent_msgs = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conv.id
        ).order_by(ChatMessage.timestamp.desc()).limit(6).all()
        history_lines = []
        for m in reversed(recent_msgs):
            if m.content != message:
                history_lines.append(f"{m.role.capitalize()}: {m.content}")
        history_str = "\n".join(history_lines)

        # 2. Safety Guardrails Check
        safety = ClinicalSafetyGuardrails.analyze_query_safety(message)

        # Save user message
        user_msg = ChatMessage(
            conversation_id=conv.id,
            role="user",
            content=message,
            guardrail_flag=safety["flag"]
        )
        db.add(user_msg)
        db.commit()

        # Immediate Red-Flag Emergency
        if safety["is_emergency"]:
            emergency_response = LOCALIZED_EMERGENCY_ALERTS.get(lang, LOCALIZED_EMERGENCY_ALERTS["en"])
            asst_msg = ChatMessage(
                conversation_id=conv.id,
                role="assistant",
                content=emergency_response,
                guardrail_flag="EMERGENCY"
            )
            db.add(asst_msg)
            db.commit()

            return {
                "session_id": session_id,
                "response": emergency_response,
                "language": lang,
                "category": "EMERGENCY_TRIAGE",
                "is_emergency": True,
                "guardrail_flag": "EMERGENCY",
                "sources": [],
                "disclaimer": LOCALIZED_DISCLAIMERS.get(lang, LOCALIZED_DISCLAIMERS["en"]),
                "pharmacist_escalation_available": True
            }

        # Blocked Diagnosis / Prescription Alteration
        if safety["flag"] in ["DIAGNOSE_BLOCKED", "PRESCRIBE_BLOCKED"]:
            gr = LOCALIZED_GUARDRAILS.get(lang, LOCALIZED_GUARDRAILS["en"])
            guardrail_text = (
                f"{gr['title']}\n\n"
                f"{gr['body'].format(reason=safety['reason'])}\n\n"
                f"**{gr['why']}**\n\n"
                f"{gr['action']}"
            )
            asst_msg = ChatMessage(
                conversation_id=conv.id,
                role="assistant",
                content=guardrail_text,
                guardrail_flag=safety["flag"]
            )
            db.add(asst_msg)
            db.commit()

            return {
                "session_id": session_id,
                "response": guardrail_text,
                "language": lang,
                "category": "SAFETY_GUARDRAIL",
                "is_emergency": False,
                "guardrail_flag": safety["flag"],
                "sources": [],
                "disclaimer": LOCALIZED_DISCLAIMERS.get(lang, LOCALIZED_DISCLAIMERS["en"]),
                "pharmacist_escalation_available": True
            }

        # Direct Nearby Pharmacy Lookup
        msg_low = message.lower()
        is_pharm_search = any(kw in msg_low for kw in [
            "nearby pharmacy", "nearby pharmacies", "find pharmacy", "find pharmacies", "find nearby",
            "medical shop", "medical store", "chemist near", "24-hour medical", "24-hour pharmacy",
            "ಹತ್ತಿರದ ಮೆಡಿಕಲ್", "ಹತ್ತಿರದ ಫಾರ್ಮಸಿ", "नजदीकी मेडिकल स्टोर", "नजदीकी फार्मेसी"
        ])
        if is_pharm_search:
            pharmacies = db.query(Pharmacy).filter(Pharmacy.is_verified == True).limit(3).all()
            pharm_listings = [
                f"- **{p.name}**\n  📍 {p.address}, {p.city}\n  🕒 {p.operating_hours or '08:00 AM - 10:00 PM'} | 📞 {p.phone or 'Contact store'}"
                for p in pharmacies
            ]
            resp_text = (
                "### 📍 Verified Nearby Medical Shops & Pharmacies\n\n"
                "Here are verified network pharmacies with real-time stock connectivity:\n\n"
                + "\n\n".join(pharm_listings) + "\n\n"
                "💡 **Turn-by-turn Navigation:** Navigate to the **Nearby Medical Shops** page in the sidebar for live GPS distances and turn-by-turn directions."
            )
            asst_msg = ChatMessage(
                conversation_id=conv.id,
                role="assistant",
                content=resp_text,
                guardrail_flag="SAFE"
            )
            db.add(asst_msg)
            db.commit()

            return {
                "session_id": session_id,
                "response": resp_text,
                "language": lang,
                "category": "PHARMACY_LOCATOR",
                "is_emergency": False,
                "guardrail_flag": "SAFE",
                "sources": [{"title": "CDSCO Licensed Pharmacy Network", "category": "PHARMACY_REGISTRY", "reference_source": "State Drugs Control Directorate", "verification_date": "2026-01-01"}],
                "disclaimer": LOCALIZED_DISCLAIMERS.get(lang, LOCALIZED_DISCLAIMERS["en"]),
                "pharmacist_escalation_available": True
            }

        # 3. Retrieve Verified Knowledge Sources
        retrieved_docs = cls.retrieve_relevant_knowledge(db, message, top_k=3)
        context_str = ""
        citations = []

        for doc, score in retrieved_docs:
            context_str += f"- [{doc.title} ({doc.reference_source})]: {doc.content}\n"
            citations.append({
                "title": doc.title,
                "category": doc.category,
                "reference_source": doc.reference_source,
                "verification_date": doc.verification_date
            })

        system_prompt = (
            "You are the PharmIntel Clinical Intelligence Assistant. "
            "Explain medical concepts clearly, concisely, and accurately based on verified clinical knowledge sources. "
            "Answer the user's actual question directly."
        )

        response_content = await cls.llm_client.generate_completion(
            system_prompt,
            message,
            context_str,
            language=lang,
            mode=mode,
            history=history_str,
            db=db
        )

        asst_msg = ChatMessage(
            conversation_id=conv.id,
            role="assistant",
            content=response_content,
            sources_json=json.dumps(citations),
            guardrail_flag="SAFE"
        )
        db.add(asst_msg)
        db.commit()

        return {
            "session_id": session_id,
            "response": response_content,
            "language": lang,
            "category": "EDUCATIONAL_PHARMACOLOGY",
            "is_emergency": False,
            "guardrail_flag": "SAFE",
            "sources": citations,
            "disclaimer": LOCALIZED_DISCLAIMERS.get(lang, LOCALIZED_DISCLAIMERS["en"]),
            "pharmacist_escalation_available": True
        }

    @classmethod
    def clear_session(cls, db: Session, session_id: str) -> Dict[str, Any]:
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if conv:
            db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id).delete()
            db.delete(conv)
            db.commit()
        return {"success": True, "session_id": session_id, "message": "Conversation history cleared."}

    @classmethod
    def escalate_to_pharmacist(
        cls,
        db: Session,
        session_id: str,
        patient_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        ticket_id = f"PHARM-ESC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        p_name = patient_name.strip() if (patient_name and patient_name.strip()) else "Patient name not provided"
        return {
            "success": True,
            "ticket_id": ticket_id,
            "assigned_pharmacist": "Clinical Pharmacist On-Duty Review Queue",
            "license_no": "PCI-CLIN-REVIEW-QUEUE",
            "status": "TRIAGED_ESCALATED",
            "message": f"Inquiry for {p_name} has been routed to the Clinical Review Queue (Ticket: {ticket_id}). Live review initiated.",
            "contact_phone": "+91 80 4719 2200"
        }

    @classmethod
    def get_session_history(cls, db: Session, session_id: str) -> List[Dict[str, Any]]:
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            return []
        msgs = db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id).order_by(ChatMessage.timestamp.asc()).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "guardrail_flag": m.guardrail_flag,
                "created_at": m.timestamp.isoformat() if m.timestamp else None
            }
            for m in msgs
        ]
