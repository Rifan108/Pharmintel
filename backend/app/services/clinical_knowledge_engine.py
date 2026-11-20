"""
PHARMINTEL CLINICAL KNOWLEDGE & REASONING ENGINE
===============================================
Authoritative, evidence-based clinical reasoning layer for:
1. Pregnancy and Lactation Medication Safety (Dolo 650/Paracetamol, NSAIDs, Antibiotics, Teratogens, Accidental Ingestion)
2. Disease Pathophysiology & Management (Diabetes, Hypertension, Heart Disease, Fever, Kidney Disease, Dehydration, Cholesterol)
3. Symptom Educational Triage (Headache, Stomach Pain, Dizziness, Frequent Urination, Heart Attack Warning Signs)
4. Pharmacy Fundamentals (Generic vs Brand, Expiry Dates, Batch Numbers, Storage, Genuine Authentication, Overdose Triage)
5. In-Chat Drug-Drug Interactions (Losartan + Amlodipine, Triple Whammy, Duplicate Paracetamol Combiflam + Dolo)
6. 7 Supported Indian Languages (English, Kannada, Hindi, Malayalam, Tamil, Telugu, Marathi)

STRICT REGULATORY & CLINICAL SAFETY CONSTRAINTS:
- ZERO Gemini Flash or external Flash API dependencies.
- No blanket "100% safe" guarantees for any medicine in pregnancy.
- Never diagnose from a short message; provide educational evaluation and red flags.
- Distinguish active ingredients (e.g. Paracetamol) from commercial brands (e.g. Dolo 650).
- Never redirect medical questions to Drug Detection unless explicitly asked for multi-drug workflow.
"""

import re
from typing import Optional, Dict, Any, Tuple

SUPPORTED_LANGUAGES = ["en", "kn", "hi", "ml", "ta", "te", "mr"]

class ClinicalKnowledgeEngine:
    """
    Evidence-based clinical reasoning module providing direct conversational responses
    grounded in WHO, FDA/CDSCO, NHS, ACOG, and clinical compendia.
    """

    @classmethod
    def evaluate_pregnancy_and_lactation(
        cls,
        q_low: str,
        lang: str = "en",
        persona_header: str = "",
        escalation_footer: str = ""
    ) -> Optional[str]:
        """
        Evaluates pregnancy, lactation, and maternal-fetal medication inquiries.
        """
        # Detect pregnancy/breastfeeding intent
        is_pregnancy = any(w in q_low for w in [
            "pregnant", "pregnancy", "expecting", "trimester", "breastfeeding", "lactation", "nursing", "baby", "fetus",
            "गर्भावस्था", "गर्भवती", "स्तनपान", "शिशु",
            "ಗರ್ಭಿಣಿ", "ಗರ್ಭಾವಸ್ಥೆ", "ಎದೆಹಾಲು",
            "கர்ப்பம்", "கர்ப்பிணி", "தாய்ப்பால்",
            "గర్భధారణ", "గర్భిణీ", "తల్లిపాలు",
            "गरोदर", "गरोदरपण", "स्तनपान",
            "ഗർഭിണി", "മുലയൂട്ടൽ"
        ])

        if not is_pregnancy:
            return None

        # -------------------------------------------------------------
        # A. PARACETAMOL / DOLO 650 / CROCIN / CALPOL IN PREGNANCY
        # -------------------------------------------------------------
        if any(w in q_low for w in ["dolo", "paracetamol", "calpol", "crocin", "डोलो", "ಡೋಲೋ", "டோலோ", "డోలో", "डोलों", "पॅरासिटामॉल", "पैरासिटामोल", "ಪ್ಯಾರಸಿಟಮಾಲ್", "പാരസെറ്റമോൾ", "பாராசிட்டமால்", "పారాసిటమాల్"]):
            texts = {
                "en": (
                    "### 🤰 Pregnancy Medication Guidance: Dolo 650 (Paracetamol)\n\n"
                    "**1. Product & Active Ingredient Identification:**\n"
                    "**Dolo 650** is a commercial brand formulation containing **Paracetamol 650 mg** (Acetaminophen) as its single active pharmaceutical ingredient.\n\n"
                    "**2. Clinical Evidence & Regulatory Guidelines (WHO / NHS / ACOG):**\n"
                    "Paracetamol is widely recognized across authoritative international clinical guidelines as the preferred first-line analgesic (pain relief) and antipyretic (fever reduction) during pregnancy when clinically indicated and non-pharmacological comfort measures are insufficient.\n\n"
                    "**3. Crucial Nuance: Individual Suitability & Patient Context:**\n"
                    "- **No Blanket Guarantee:** No medicine can be declared '100% safe' or harmless for every pregnant individual without medical evaluation.\n"
                    "- **Individual Factors Matter:** Individual suitability depends strictly on your gestation stage (trimester), underlying medical history (such as liver or kidney function, pre-existing pregnancy complications like pre-eclampsia or gestational hypertension), and any other medications you may be taking.\n\n"
                    "**4. Safe Usage Principles:**\n"
                    "- **Lowest Effective Dose:** Use the lowest effective dose for the shortest possible duration.\n"
                    "- **Strict Maximum Daily Limits:** Never exceed **4,000 mg (4 grams) per 24 hours** from all sources. Taking more than recommended can cause maternal and fetal liver damage.\n"
                    "- **Avoid Multi-Ingredient Preparations:** Always inspect packaging to ensure you are taking pure paracetamol. Never take combination cold/flu remedies that combine paracetamol with decongestants (such as phenylephrine or pseudoephedrine) or caffeine, which are contraindicated during pregnancy.\n\n"
                    "**5. Obstetric Consultation:**\n"
                    "Always consult with your obstetrician, gynecologist, or healthcare provider before initiating any medication during pregnancy to ensure it is appropriate for your specific clinical circumstances.\n\n"
                    "🚨 **Warning Signs Requiring Immediate Emergency Care:**\n"
                    "Seek urgent medical evaluation if you experience high persistent fever ($>38.5^\\circ\\text{C}$), severe headache (particularly in the 2nd or 3rd trimester, which can indicate pre-eclampsia), visual disturbances, sudden facial/hand swelling, severe abdominal pain, or reduced fetal movement."
                ),
                "kn": (
                    "### 🤰 ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಔಷಧ ಮಾರ್ಗದರ್ಶನ: ಡೋಲೋ 650 (Dolo 650 - Paracetamol)\n\n"
                    "**1. ಸಕ್ರಿಯ ಘಟಕಾಂಶ:** ಡೋಲೋ 650 ಎಂಬುದು **ಪ್ಯಾರಸಿಟಮಾಲ್ 650 ಮಿಗ್ರಾಂ (Paracetamol)** ಅನ್ನು ಒಳಗೊಂಡಿರುವ ಒಂದು ಬ್ರಾಂಡ್ ಆಗಿದೆ.\n\n"
                    "**2. ವೈದ್ಯಕೀಯ ಪುರಾವೆಗಳು (WHO ಮತ್ತು ACOG):** ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಜ್ವರ ಮತ್ತು ಸಾಮಾನ್ಯ ಮೈಕೈನೋವಿಗೆ ವೈದ್ಯರ ಸಲಹೆಯ ಮೇರೆಗೆ ಪ್ಯಾರಸಿಟಮಾಲ್ ಅನ್ನು ಮೊದಲ ಆದ್ಯತೆಯ ಔಷಧಿಯಾಗಿ ಪರಿಗಣಿಸಲಾಗುತ್ತದೆ.\n\n"
                    "**3. ಮುಖ್ಯ ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು:**\n"
                    "- ಯಾವುದೇ ಔಷಧಿಯೂ ಪ್ರತಿಯೊಬ್ಬ ಗರ್ಭಿಣಿಗೂ ಸಂಪೂರ್ಣ ಸುರಕ್ಷಿತವೆಂದು ಖಾತರಿಪಡಿಸಲಾಗುವುದಿಲ್ಲ. ನಿಮ್ಮ ಗರ್ಭಧಾರಣೆಯ ಅವಧಿ (Trimester), ಹಿಂದಿನ ವೈದ್ಯಕೀಯ ಇತಿಹಾಸ ಮತ್ತು ಆರೋಗ್ಯ ಸ್ಥಿತಿ ಮುಖ್ಯ.\n"
                    "- ಕನಿಷ್ಠ ಅಗತ್ಯವಿರುವ ಡೋಸ್ ಅನ್ನು ಕಡಿಮೆ ಅವಧಿಗೆ ಮಾತ್ರ ತೆಗೆದುಕೊಳ್ಳಬೇಕು.\n"
                    "- ದಿನಕ್ಕೆ 4000 ಮಿಗ್ರಾಂ ಗಿಂತ ಹೆಚ್ಚು ತೆಗೆದುಕೊಳ್ಳಬಾರದು. ಹೆಚ್ಚುವರಿ ಪ್ರಮಾಣವು ಯಕೃತ್ತಿಗೆ (Liver) ಹಾನಿಯುಂಟುಮಾಡಬಹುದು.\n"
                    "- ಇತರ ಶೀತದ ಮಾತ್ರೆಗಳೊಂದಿಗೆ (Decongestants) ಮಿಶ್ರಿತ ಪ್ಯಾರಸಿಟಮಾಲ್ ತೆಗೆದುಕೊಳ್ಳಬಾರದು.\n\n"
                    "💡 **ತುರ್ತು ಎಚ್ಚರಿಕೆ:** ತೀವ್ರ ತಲೆನೋವು, ಕಣ್ಣು ಮಂಜಾಗುವುದು, ಮುಖದಲ್ಲಿ ಹಠಾತ್ ಊತ ಅಥವಾ ವಿಪರೀತ ಜ್ವರವಿದ್ದರೆ ತಕ್ಷಣ ನಿಮ್ಮ ಸ್ತ್ರೀರೋಗ ತಜ್ಞರನ್ನು (Obstetrician) ಭೇಟಿ ಮಾಡಿ."
                ),
                "hi": (
                    "### 🤰 गर्भावस्था में दवा मार्गदर्शन: डोलो 650 (Dolo 650 - Paracetamol)\n\n"
                    "**1. सक्रिय घटक की पहचान:** **डोलो 650** एक ब्रांड नाम है जिसमें सक्रिय घटक **पैरासिटामोल 650 मिलीग्राम** होता है।\n\n"
                    "**2. क्लिनिकल साक्ष्य (WHO एवं ACOG दिशानिर्देश):** गर्भावस्था के दौरान दर्द और बुखार के लिए पैरासिटामोल को आमतौर पर पहली पसंद माना जाता है जब गैर-दवा उपायों से आराम न मिले।\n\n"
                    "**3. व्यक्तिगत परिस्थितियां एवं महत्वपूर्ण सावधानियां:**\n"
                    "- किसी भी दवा को हर गर्भवती महिला के लिए पूरी तरह '100% सुरक्षित' नहीं कहा जा सकता। आपकी गर्भावस्था का चरण (ट्राइमेस्टर), लिवर/किडनी का स्वास्थ्य और अन्य चल रही दवाएं बहुत मायने रखती हैं।\n"
                    "- हमेशा न्यूनतम प्रभावी खुराक सबसे कम समय के लिए ही लें।\n"
                    "- 24 घंटे में कुल 4,000 मिलीग्राम से अधिक पैरासिटामोल कभी न लें।\n"
                    "- सर्दी-खांसी की ऐसी दवाओं से बचें जिनमें पैरासिटामोल के साथ डिकॉन्गेस्टेंट मिले होते हैं।\n\n"
                    "💡 **डॉक्टर से परामर्श:** कोई भी दवा लेने से पहले हमेशा अपने प्रसूति विशेषज्ञ (Obstetrician) से सलाह लें।\n\n"
                    "🚨 **आपातकालीन चेतावनी लक्षण:** यदि तेज सिरदर्द (विशेषकर दूसरी/तीसरी तिमाही में), आंखों से धुंधला दिखना, चेहरे पर अचानक सूजन या तेज बुखार हो, तो तुरंत अस्पताल जाएं।"
                ),
                "ml": (
                    "### 🤰 ഗർഭകാലത്തെ മരുന്ന് ഉപയോഗം: ഡോളോ 650 (Paracetamol)\n\n"
                    "ഡോളോ 650-ൽ **പാരസെറ്റമോൾ 650 മില്ലിഗ്രാം** അടങ്ങിയിരിക്കുന്നു. ഗർഭകാലത്ത് പനിക്കും ശരീരവേദനയ്ക്കും ഡോക്ടറുടെ നിർദ്ദേശപ്രകാരം കഴിക്കാവുന്ന ഏറ്റവും സുരക്ഷിതമായ ആദ്യ ഓപ്ഷനാണ് പാരസെറ്റമോൾ.\n\n"
                    "**പ്രധാന നിർദ്ദേശങ്ങൾ:**\n"
                    "- ഇത് എല്ലാവർക്കും പൂർണ്ണമായും സുരക്ഷിതമാണെന്ന് ഉറപ്പ് പറയാനാവില്ല; ഗർഭാവസ്ഥയുടെ ഘട്ടവും നിങ്ങളുടെ ആരോഗ്യസ്ഥിതിയും പ്രധാനമാണ്.\n"
                    "- ആവശ്യത്തിന് മാത്രം കുറഞ്ഞ അളവിൽ കഴിക്കുക. ദിവസേന 4000 മില്ലിഗ്രാമിൽ കൂടുതൽ കഴിക്കരുത്.\n"
                    "- കഴിക്കുന്നതിന് മുൻപ് നിർബന്ധമായും നിങ്ങളുടെ ഡോക്ടറുടെ അഭിപ്രായം തേടുക."
                ),
                "ta": (
                    "### 🤰 கர்ப்ப காலத்தில் டோலோ 650 (Dolo 650 - பாராசிட்டமால்)\n\n"
                    "டோலோ 650 என்பது **பாராசிட்டமால் (650mg)** அடங்கிய மருந்தாகும். கர்ப்ப காலத்தில் காய்ச்சல் மற்றும் வலிக்கு மருத்துவரின் வழிகாட்டுதலுடன் எடுக்கப்படும் முதல் நிலை மருந்தாக இது கருதப்படுகிறது.\n\n"
                    "**முக்கிய வழிகாட்டுதல்கள்:**\n"
                    "- எந்த மருந்தும் அனைவருக்கும் 100% பாதுகாப்பானது என்று உத்தரவாதம் அளிக்க முடியாது. கர்ப்பத்தின் நிலை மற்றும் தாயின் உடல்நலம் முக்கியம்.\n"
                    "- குறைந்த அளவை குறைந்த நாட்களுக்கு மட்டுமே பயன்படுத்தவும். ஒரு நாளில் 4000 மி.கிக்கு மேல் எடுக்கக் கூடாது.\n"
                    "- எடுப்பதற்கு முன் மருத்துவரை அணுகவும். கடுமையான தலைவலி அல்லது காய்ச்சல் இருந்தால் உடனடியாக மருத்துவமனை செல்லவும்."
                ),
                "te": (
                    "### 🤰 గర్భధారణలో డోలో 650 (Dolo 650 - పారాసిటమాల్)\n\n"
                    "డోలో 650 లో **పారాసిటమాల్ 650 మి.గ్రా** ఉంటుంది. గర్భధారణ సమయంలో జ్వరం మరియు నొప్పులకు వైద్యుల సలహాతో సాధారణంగా సిఫార్సు చేయబడే సురక్షితమైన మొదటి ఎంపిక పారాసిటమాల్.\n\n"
                    "**జాగ్రత్తలు:**\n"
                    "- ఏ మందూ ప్రతి ఒక్కరికీ 100% సురక్షితం కాదు. గర్భధారణ నెలలు మరియు మీ ఆరోగ్య పరిస్థితిని బట్టి వైద్యులు నిర్ణయిస్తారు.\n"
                    "- తక్కువ మోతాదులో, తక్కువ రోజులు మాత్రమే వాడండి. రోజుకు 4000 మి.గ్రా మించకూడదు.\n"
                    "- తీవ్రమైన తలనొప్పి, కంటి చూపు మసకబారడం వంటి లక్షణాలు ఉంటే వెంటనే వైద్యుడిని సంప్రదించండి."
                ),
                "mr": (
                    "### 🤰 गरोदरपणात डोलो ६५० (Dolo 650 - पॅरासिटामॉल) चा वापर\n\n"
                    "डोलो ६५० मध्ये **पॅरासिटामॉल (६५० मिग्रॅ)** हा सक्रिय घटक असतो. गरोदरपणात ताप आणि अंगदुखीसाठी डॉक्टरांच्या सल्ल्याने दिली जाणारी ही पहिली सुरक्षित निवड मानली जाते.\n\n"
                    "**महत्त्वाच्या सूचना:**\n"
                    "- कोणतेही औषध प्रत्येकासाठी १००% सुरक्षित नसते. गरोदरपणाचा महिना, यकृत/किडनीचे आरोग्य आणि इतर आजार लक्षात घेणे आवश्यक आहे.\n"
                    "- आवश्यक तेवढाच कमी डोस कमीत कमी दिवस घ्यावा. २४ तासांत ४००० मिग्रॅ पेक्षा जास्त डोस घेऊ नये.\n"
                    "- औषध सुरू करण्यापूर्वी आपल्या डॉक्टरांचा सल्ला नक्की घ्या."
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # -------------------------------------------------------------
        # B. NSAIDs IN PREGNANCY (IBUPROFEN, COMBIFLAM, BRUFEN, DICLOFENAC, ASPIRIN)
        # -------------------------------------------------------------
        if any(w in q_low for w in ["nsaid", "ibuprofen", "combiflam", "brufen", "diclofenac", "naproxen", "aspirin", "painkiller", "पेनकिलर"]):
            texts = {
                "en": (
                    "### ⚠️ Critical Warning: NSAIDs and Painkillers During Pregnancy\n\n"
                    "**Medications Included:** Non-Steroidal Anti-Inflammatory Drugs (NSAIDs) such as **Ibuprofen (Brufen, Combiflam), Diclofenac, Naproxen, and high-dose Aspirin**.\n\n"
                    "**Clinical Evidence & Risks (FDA & ACOG Safety Advisories):**\n"
                    "1. **From 20 Weeks Onward:** NSAIDs can cause fetal renal dysfunction, leading to abnormally low amniotic fluid levels (**oligohydramnios**), which can cause fetal lung hypoplasia and limb contractures.\n"
                    "2. **Strict 3rd Trimester Contraindication ($\\ge 28\\text{ weeks}$):** NSAIDs inhibit prostaglandins, which can trigger premature constriction or closure of the fetal **ductus arteriosus**. This leads to persistent pulmonary hypertension in the newborn (PPHN), fetal cardiac strain, delayed/prolonged labor, and increased maternal/fetal hemorrhage risk.\n\n"
                    "**Safe Alternative:**\n"
                    "For mild-to-moderate pain or fever during pregnancy, **Paracetamol** is the clinically preferred option when evaluated and approved by your obstetrician."
                ),
                "kn": (
                    "### ⚠️ ಗಂಭೀರ ಎಚ್ಚರಿಕೆ: ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ನೋವುನಿವಾರಕಗಳು (NSAIDs - Ibuprofen/Combiflam)\n\n"
                    "ಐಬುಪ್ರೊಫೇನ್ (Combiflam, Brufen), ಡಿಕ್ಲೋಫೆನಾಕ್ ಮತ್ತು ಆಸ್ಪಿರಿನ್ ಮುಂತಾದ ನೋವುನಿವಾರಕಗಳನ್ನು ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ **ತೆಗೆದುಕೊಳ್ಳಬಾರದು**.\n\n"
                    "- **ಅಪಾಯಗಳು:** 20 ವಾರಗಳ ನಂತರ ಇವು ಗರ್ಭದಲ್ಲಿರುವ ಮಗುವಿನ ಮೂತ್ರಪಿಂಡಗಳ ಮೇಲೆ ಪರಿಣಾಮ ಬೀರಿ ಉಲ್ಬಣ ದ್ರವವನ್ನು (Amniotic fluid) ಕಡಿಮೆ ಮಾಡಬಹುದು.\n"
                    "- 3ನೇ ತ್ರೈಮಾಸಿಕದಲ್ಲಿ (28 ವಾರಗಳ ನಂತರ) ಮಗುವಿನ ಹೃದಯದ ಪ್ರಮುಖ ರಕ್ತನಾಳವು (Ductus arteriosus) ಅವಧಿಗೆ ಮುನ್ನವೇ ಮುಚ್ಚಿಕೊಳ್ಳುವ ಅಪಾಯವಿದೆ.\n"
                    "- **ಪರ್ಯಾಯ:** ವೈದ್ಯರ ಸಲಹೆಯೊಂದಿಗೆ ಕೇವಲ **ಪ್ಯಾರಸಿಟಮಾಲ್** ಬಳಸುವುದು ಸುರಕ್ಷಿತ."
                ),
                "hi": (
                    "### ⚠️ गंभीर चेतावनी: गर्भावस्था में पेनकिलर (NSAIDs जैसे आइबूप्रोफेन/कॉम्बीफ्लाम)\n\n"
                    "गर्भावस्था में आइबूप्रोफेन (Brufen/Combiflam), डाइक्लोफेनाक और एस्पिरिन जैसी दर्दनिवारक दवाएं **वर्जित (Contraindicated)** हैं।\n\n"
                    "- **खतरे:** 20 सप्ताह के बाद ये दवाएं भ्रूण की किडनी को प्रभावित कर एम्नियोटिक फ्लूइड (गर्भ का पानी) कम कर सकती हैं।\n"
                    "- तीसरी तिमाही में यह गर्भस्थ शिशु के दिल की रक्त वाहिका (Ductus arteriosus) को समय से पहले बंद कर सकती हैं, जिससे शिशु को जानलेवा फेफड़ों की समस्या हो सकती है।\n"
                    "- **सुरक्षित विकल्प:** दर्द या बुखार के लिए डॉक्टर की सलाह से **पैरासिटामोल** लेना ही उचित है।"
                ),
                "ml": (
                    "### ⚠️ മുന്നറിയിപ്പ്: ഗർഭകാലത്ത് പെയിൻകില്ലറുകൾ (NSAIDs) ഒഴിവാക്കുക\n\n"
                    "ഐബുപ്രോഫെൻ (Combiflam), ഡിക്ലോഫെനാക് തുടങ്ങിയ വേദനസംഹാരികൾ ഗർഭകാലത്ത് ഗുരുതരമായ അപകടങ്ങൾ ഉണ്ടാക്കാം. ഇത് കുഞ്ഞിന്റെ കിഡ്നിയെയും ഹൃദയത്തിലെ രക്തക്കുഴലുകളെയും പ്രതികൂലമായി ബാധിക്കാം. പാരസെറ്റമോൾ മാത്രമാണ് സുരക്ഷിതമായ ബദൽ."
                ),
                "ta": (
                    "### ⚠️ எச்சரிக்கை: கர்ப்ப காலத்தில் வலி நிவாரணிகள் (NSAIDs)\n\n"
                    "இப்யூபுரூஃபன் (Combiflam), டைக்ளோஃபெனாக் போன்ற மருந்துகள் கர்ப்ப காலத்தில் சிசுவின் சிறுநீரகம் மற்றும் இதய ரத்த நாளங்களை பாதிக்கும். மூன்றாம் பருவத்தில் இவை முற்றிலும் தடைசெய்யப்பட்டுள்ளன."
                ),
                "te": (
                    "### ⚠️ హెచ్చరిక: గర్భధారణలో పెయిన్‌కిల్లర్లు (NSAIDs)\n\n"
                    "ఐబుప్రోఫెన్ (Combiflam), డైక్లోఫెనాక్ వంటి మందులు గర్భధారణ సమయంలో పిండం కిడ్నీలు మరియు గుండెపై తీవ్ర ప్రభావం చూపుతాయి. వీటికి బదులుగా వైద్యుల పర్యవేక్షణలో పారాసిటమాల్ వాడాలి."
                ),
                "mr": (
                    "### ⚠️ गंभीर इशारा: गरोदरपणात पेनकिलर्स (NSAIDs)\n\n"
                    "आयबुप्रोफेन (Combiflam), डायक्लोफेनाक यांसारख्या पेनकिलर्स गरोदरपणात गर्भातील बाळाच्या मूत्रपिंडावर आणि हृदयावर गंभीर परिणाम करू शकतात. वेदनेसाठी डॉक्टरांच्या सल्ल्याने केवळ पॅरासिटामॉल वापरावे."
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # -------------------------------------------------------------
        # C. ANTIBIOTICS IN PREGNANCY
        # -------------------------------------------------------------
        if any(w in q_low for w in ["antibiotic", "एंटीबायोटिक", "ಆಂಟಿಬಯೋಟಿಕ್", "அமில மருந்து", "ആൻ്റിബയോട്ടിക്"]):
            texts = {
                "en": (
                    "### 💊 Antibiotic Safety Guidelines During Pregnancy\n\n"
                    "**Clinical Principle:** Pregnant women can take certain antibiotics when a confirmed bacterial infection threatens maternal or fetal health, but antibiotic selection must be strictly directed by an obstetrician.\n\n"
                    "**1. Generally Considered Safer Classes When Clinically Indicated:**\n"
                    "- **Penicillins:** Amoxicillin, Ampicillin, and Amoxicillin-Clavulanate (Augmentin).\n"
                    "- **Cephalosporins:** Cephalexin, Cefixime, Cefuroxime.\n"
                    "- **Macrolides:** Erythromycin and Azithromycin (when penicillins cannot be used).\n\n"
                    "**2. High-Risk Classes Avoided in Pregnancy:**\n"
                    "- **Tetracyclines (e.g. Doxycycline):** Crosses placenta; causes permanent fetal tooth discoloration, enamel hypoplasia, and suppresses fetal bone growth.\n"
                    "- **Fluoroquinolones (e.g. Ciprofloxacin, Levofloxacin):** Risks fetal cartilage damage and arthropathy.\n"
                    "- **Sulfonamides (e.g. Co-trimoxazole):** Interferes with folate metabolism in the 1st trimester; causes neonatal jaundice/kernicterus in late 3rd trimester.\n\n"
                    "💡 *Never self-prescribe or reuse leftover antibiotics during pregnancy.*"
                ),
                "kn": (
                    "### 💊 ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಆಂಟಿಬಯೋಟಿಕ್ಸ್ ಸುರಕ್ಷತಾ ಮಾರ್ಗಸೂಚಿ\n\n"
                    "ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಬ್ಯಾಕ್ಟೀರಿಯಾ ಸೋಂಕಿದ್ದರೆ ಕೆಲವು ಆಂಟಿಬಯೋಟಿಕ್‌ಗಳನ್ನು ವೈದ್ಯರ ಸಲಹೆಯಂತೆ ಮಾತ್ರ ತೆಗೆದುಕೊಳ್ಳಬಹುದು.\n\n"
                    "- **ಸಾಮಾನ್ಯವಾಗಿ ಸುರಕ್ಷಿತವಾದವು:** ಅಮೋಕ್ಸಿಸಿಲಿನ್ (Amoxicillin), ಸೆಫಾಲೆಕ್ಸಿನ್ (Cephalexin), ಅಜಿತ್ರೊಮೈಸಿನ್ (Azithromycin).\n"
                    "- **ತೆಗೆದುಕೊಳ್ಳಬಾರದ ಅಪಾಯಕಾರಿ ಆಂಟಿಬಯೋಟಿಕ್ಸ್:** ಡಾಕ್ಸಿಸೈಕ್ಲಿನ್ (ಮಗುವಿನ ಹಲ್ಲು ಮತ್ತು ಮೂಳೆಗಳ ಬೆಳವಣಿಗೆಗೆ ಹಾನಿ), ಸಿಪ್ರೊಫ್ಲೋಕ್ಸಾಸಿನ್ (ಕೀಲುಗಳ ಬೆಳವಣಿಗೆಗೆ ಹಾನಿ).\n\n"
                    "ಸ್ತ್ರೀರೋಗ ತಜ್ಞರ ನೇರ ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಇಲ್ಲದೆ ಯಾವುದೇ ಆಂಟಿಬಯೋಟಿಕ್ ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ."
                ),
                "hi": (
                    "### 💊 गर्भावस्था में एंटीबायोटिक दवाओं की सुरक्षा\n\n"
                    "गर्भावस्था में बैक्टीरियल इन्फेक्शन होने पर डॉक्टर की देखरेख में कुछ खास एंटीबायोटिक्स ली जा सकती हैं:\n\n"
                    "- **सामान्यतः सुरक्षित एंटीबायोटिक्स:** अमोक्सिसिलिन (Amoxicillin), ऑगमेंटिन (Augmentin), सेफैलेक्सिन, एजिथ्रोमाइसिन।\n"
                    "- **गर्भावस्था में वर्जित एंटीबायोटिक्स:** डॉक्सीसाइक्लिन (शिशु के दांतों व हड्डियों को नुकसान), सिप्रोफ्लोक्सासिन (जोड़ों और कार्टिलेज को नुकसान)।\n\n"
                    "💡 *बिना डॉक्टर के पर्चे के कभी भी एंटीबायोटिक न लें।*"
                ),
                "ml": (
                    "### 💊 ഗർഭകാലത്തെ ആന്റിബയോട്ടിക് ഉപയോഗം\n\n"
                    "അമോക്സിസിലിൻ, സെഫാലക്സിൻ തുടങ്ങിയവ സുരക്ഷിതമായി ഡോക്ടർമാർ നിർദ്ദേശിക്കാറുണ്ട്. എന്നാൽ ഡോക്സിസൈക്ലിൻ, സിപ്രോഫ്ലോക്സാസിൻ തുടങ്ങിയവ കുഞ്ഞിന്റെ അസ്ഥികൾക്കും പല്ലുകൾക്കും ദോഷകരമായതിനാൽ ഒഴിവാക്കണം."
                ),
                "ta": (
                    "### 💊 கர்ப்ப காலத்தில் ஆன்டிபயாடிக் மருந்துகள்\n\n"
                    "அமாக்சிசிலின், செஃபாலெக்சின் போன்றவை மருத்துவரின் ஆலோசனையுடன் எடுக்கலாம். டாக்ஸிசைக்ளின், சிப்ரோஃப்ளோக்சாசின் போன்றவற்றை சிசுவின் எலும்பு மற்றும் பல் வளர்ச்சியை பாதிக்கும் என்பதால் தவிர்க்க வேண்டும்."
                ),
                "te": (
                    "### 💊 గర్భధారణలో యాంటీబయాటిక్స్ వాడకం\n\n"
                    "అమోక్సిసిలిన్, సెఫాలెక్సిన్ వంటివి డాక్టర్ పర్యవేక్షణలో సురక్షితం. డాక్సీసైక్లిన్, సిప్రోఫ్లోక్సాసిన్ వంటివి పిండం ఎముకలు, దంతాలకు హాని కలిగిస్తాయి కాబట్టి వాడకూడదు."
                ),
                "mr": (
                    "### 💊 गरोदरपणात अँटीबायोटिक्सचा वापर\n\n"
                    "अमोक्सिसिलिन आणि सेफॅलेक्सिन यांसारखी अँटीबायोटिक्स डॉक्टरांच्या सल्ल्याने सुरक्षित मानली जातात. परंतु डॉक्सीसायक्लिन आणि सिप्रोफ्लॉक्सॅसिन बाळाच्या हाडांसाठी घातक असल्याने टाळावीत."
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # -------------------------------------------------------------
        # D. ACCIDENTAL MEDICATION INGESTION DURING PREGNANCY
        # -------------------------------------------------------------
        if any(w in q_low for w in ["accident", "accidentally", "गलती से", "ಆಕಸ್ಮಿಕವಾಗಿ", "தவறுதலாக", "యాదృచ్ఛికంగా", "चुकून"]):
            texts = {
                "en": (
                    "### 🛡️ Step-by-Step Protocol: Accidental Medicine Ingestion During Pregnancy\n\n"
                    "If you accidentally took a medication while pregnant, follow this calm, evidence-based clinical procedure:\n\n"
                    "1. **Remain Calm:** A single accidental dose of most over-the-counter medications rarely produces severe congenital complications, but immediate evaluation is essential.\n"
                    "2. **Identify the Packaging:** Note the exact brand name, active ingredients, dosage strength (mg), and exact number of tablets taken.\n"
                    "3. **Contact Healthcare Providers Immediately:** Call your obstetrician, local maternity triage unit, or National Poison Information Centre (in India: 1800-116-117) with the medicine packaging in front of you.\n"
                    "4. **Do NOT Induce Vomiting:** Do not attempt home emetics, salt water, or home remedies unless explicitly instructed by medical toxicology personnel.\n"
                    "5. **Monitor Warning Signs:** Seek immediate emergency care if you experience vaginal bleeding, severe abdominal cramping, dizziness, vomiting, or shortness of breath."
                ),
                "kn": (
                    "### 🛡️ ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಆಕಸ್ಮಿಕವಾಗಿ ಮಾತ್ರೆ ಸೇವಿಸಿದರೆ ಏನು ಮಾಡಬೇಕು?\n\n"
                    "1. **ಶಾಂತರಾಗಿರಿ:** ಒಂದು ಬಾರಿಯ ಆಕಸ್ಮಿಕ ಸೇವನೆ ಸಾಮಾನ್ಯವಾಗಿ ತೀವ್ರ ಹಾನಿ ಮಾಡುವುದಿಲ್ಲ, ಆದರೆ ತಕ್ಷಣ ಪರೀಕ್ಷೆ ಅಗತ್ಯ.\n"
                    "2. **ಮಾತ್ರೆಯ ವಿವರ ತಿಳಿಯಿರಿ:** ತೆಗೆದುಕೊಂಡ ಔಷಧಿಯ ಹೆಸರು, ಶಕ್ತಿ (mg) ಮತ್ತು ಎಷ್ಟು ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡಿದ್ದೀರಿ ಎಂಬುದನ್ನು ಪರಿಶೀಲಿಸಿ.\n"
                    "3. **ತಕ್ಷಣ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ:** ನಿಮ್ಮ ಸ್ತ್ರೀರೋಗ ತಜ್ಞರಿಗೆ ಅಥವಾ ಹತ್ತಿರದ ಆಸ್ಪತ್ರೆಗೆ ಮಾತ್ರೆಯ ಪಟ್ಟಿಯೊಂದಿಗೆ ಕರೆ ಮಾಡಿ.\n"
                    "4. **ವಾಂತಿ ಮಾಡಿಸಲು ಪ್ರಯತ್ನಿಸಬೇಡಿ.**\n"
                    "5. ರಕ್ತಸ್ರಾವ ಅಥವಾ ತೀವ್ರ ಹೊಟ್ಟೆನೋವು ಕಂಡುಬಂದರೆ ತಕ್ಷಣ ಆಸ್ಪತ್ರೆಗೆ ಭೇಟಿ ನೀಡಿ."
                ),
                "hi": (
                    "### 🛡️ गर्भावस्था में गलती से दवा खा लेने पर क्या करें?\n\n"
                    "1. **घबराएं नहीं:** एक बार गलती से ली गई खुराक से आमतौर पर तुरंत बड़ा खतरा नहीं होता, लेकिन डॉक्टर की राय जरूरी है।\n"
                    "2. **दवा की पहचान करें:** दवा का नाम, मिलीग्राम (mg) और कितनी गोलियां ली हैं, यह देख लें।\n"
                    "3. **डॉक्टर से तुरंत संपर्क करें:** दवा का पत्ता अपने हाथ में रखकर अपने प्रसूति विशेषज्ञ (Obstetrician) को फोन करें।\n"
                    "4. **उल्टी कराने की कोशिश न करें।**\n"
                    "5. यदि पेट में तेज दर्द, चक्कर या रक्तस्राव हो, तो तुरंत नजदीकी अस्पताल के इमरजेंसी में जाएं।"
                ),
                "ml": (
                    "### 🛡️ ഗർഭകാലത്ത് അബദ്ധത്തിൽ മരുന്ന് കഴിച്ചാൽ എന്ത് ചെയ്യണം?\n\n"
                    "പരിഭ്രാന്തരാകാതിരിക്കുക. കഴിച്ച മരുന്നിന്റെ പേരും അളവും കുറിച്ചുവെച്ച് ഉടൻ തന്നെ നിങ്ങളുടെ ഗൈനക്കോളജിസ്റ്റിനെ വിളിക്കുക. സ്വയം ഛർദ്ദിക്കാൻ ശ്രമിക്കരുത്."
                ),
                "ta": (
                    "### 🛡️ கர்ப்ப காலத்தில் தவறுதலாக மருந்து உட்கொண்டால் செய்ய வேண்டியவை\n\n"
                    "பதற்றமடைய வேண்டாம். உட்கொண்ட மருந்தின் பெயர், அளவு ஆகியவற்றை கையில் வைத்துக்கொண்டு உடனடியாக உங்கள் மருத்துவரை அழைக்கவும். வாந்தி எடுக்க வைக்க முயற்சிக்காதீர்கள்."
                ),
                "te": (
                    "### 🛡️ గర్భధారణలో పొరపాటున మందు వేసుకుంటే ఏమి చేయాలి?\n\n"
                    "కంగారు పడవద్దు. వేసుకున్న మందు పేరు, మోతాదు వివరాలతో వెంటనే మీ గైనకాలజిస్ట్‌ను సంప్రదించండి. సొంతంగా వాంతి చేసుకోవడానికి ప్రయత్నించవద్దు."
                ),
                "mr": (
                    "### 🛡️ गरोदरपणात चुकून औषध घेतल्यास काय करावे?\n\n"
                    "घाबरून जाऊ नका. घेतलेल्या औषधाचे नाव आणि डोस लक्षात घेऊन त्वरित आपल्या डॉक्टरांशी संपर्क साधा. स्वतःहून उलट्या करण्याचा प्रयत्न करू नका."
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # -------------------------------------------------------------
        # E. BREASTFEEDING & LACTATION MEDICATION SAFETY
        # -------------------------------------------------------------
        if any(w in q_low for w in ["breastfeeding", "lactation", "nursing", "breast milk", "स्तनपान", "ಎದೆಹಾಲು", "தாய்ப்பால்", "తల్లిపాలు", "മുലയൂട്ടൽ"]):
            texts = {
                "en": (
                    "### 🤱 Medication Safety During Breastfeeding (Lactation)\n\n"
                    "**1. Principles of Drug Excretion into Breast Milk:**\n"
                    "Most maternal medications transfer into human breast milk in small amounts, quantified as the **Relative Infant Dose (RID)**. An $\\text{RID} < 10\\%$ is generally considered clinically compatible with breastfeeding for most therapeutic classes.\n\n"
                    "**2. Generally Safe Options During Lactation:**\n"
                    "- **Analgesics & Antipyretics:** **Paracetamol** and **Ibuprofen** have minimal milk transfer and documented safety records in nursing infants.\n"
                    "- **Antibiotics:** Penicillins (Amoxicillin) and Cephalosporins are generally compatible.\n\n"
                    "**3. Medications to Avoid While Breastfeeding:**\n"
                    "- **Opioids (Codeine / Tramadol):** Maternal ultra-rapid CYP2D6 metabolizers convert codeine to morphine at toxic levels, creating fatal respiratory depression risks in nursing infants.\n"
                    "- **Aspirin (high-dose):** Theoretical risk of Reye's syndrome in infants.\n"
                    "- **Oral Decongestants (Pseudoephedrine):** Dramatically reduces maternal milk supply.\n\n"
                    "**4. Best Administration Timing:**\n"
                    "Take your prescribed dose immediately after breastfeeding or before the infant's longest sleep stretch to minimize peak drug concentration in breast milk.\n\n"
                    "💡 *Monitor your baby for unusual drowsiness, poor feeding/latch, or diarrhea.*"
                ),
                "kn": (
                    "### 🤱 ಹಾಲುಣಿಸುವ ಸಮಯದಲ್ಲಿ (Breastfeeding) ಔಷಧಗಳ ಸುರಕ್ಷತೆ\n\n"
                    "ತಾಯಿ ತೆಗೆದುಕೊಳ್ಳುವ ಹೆಚ್ಚಿನ ಔಷಧಿಗಳು ಸಣ್ಣ ಪ್ರಮಾಣದಲ್ಲಿ ಎದೆಹಾಲಿನಲ್ಲಿ ಮಗುವಿಗೆ ತಲುಪುತ್ತವೆ.\n\n"
                    "- **ಸುರಕ್ಷಿತ ಔಷಧಿಗಳು:** ಪ್ಯಾರಸಿಟಮಾಲ್ (Paracetamol) ಮತ್ತು ಐಬುಪ್ರೊಫೇನ್ (Ibuprofen) ಕಡಿಮೆ ಪ್ರಮಾಣದಲ್ಲಿ ಹಾಲಿಗೆ ವರ್ಗಾವಣೆಯಾಗುವುದರಿಂದ ಸುರಕ್ಷಿತ.\n"
                    "- **ತೆಗೆದುಕೊಳ್ಳಬಾರದ ಔಷಧಿಗಳು:** ಕೊಡೆನ್ (Codeine) ಮತ್ತು ಟ್ರಮಡೋಲ್ ಇರುವ ನೋವುನಿವಾರಕಗಳು (ಮಗುವಿನಲ್ಲಿ ನಿದ್ರೆ ಮತ್ತು ಉಸಿರಾಟದ ತೊಂದರೆ ಉಂಟುಮಾಡಬಹುದು).\n\n"
                    "- **ಸಲಹೆ:** ಹಾಲೂಡಿಸಿದ ತಕ್ಷಣ ಔಷಧಿಯನ್ನು ಸೇವಿಸುವುದರಿಂದ ಮುಂದಿನ ಹಾಲೂಡಿಕೆಯ ಹೊತ್ತಿಗೆ ಹಾಲಿನಲ್ಲಿ ಔಷಧಿಯ ಪ್ರಮಾಣ ಕಡಿಮೆಯಾಗಿರುತ್ತದೆ."
                ),
                "hi": (
                    "### 🤱 स्तनपान (Breastfeeding) के दौरान दवा सुरक्षा\n\n"
                    "स्तनपान कराने वाली माताओं द्वारा ली जाने वाली अधिकांश दवाएं बहुत कम मात्रा में दूध में जाती हैं:\n\n"
                    "- **सुरक्षित विकल्प:** बुखार और दर्द के लिए **पैरासिटामोल** और **आइबूप्रोफेन** स्तनपान के दौरान सुरक्षित माने जाते हैं।\n"
                    "- **खतरनाक दवाएं:** कोडीन (Codeine) और ट्रामाडोल युक्त कफ सीरप व पेनकिलर्स से बचें, ये शिशु में अत्यधिक सुस्ती और सांस की समस्या पैदा कर सकते हैं।\n"
                    "- **सही समय:** बच्चे को दूध पिलाने के तुरंत बाद दवा लें ताकि अगली फीडिंग तक दवा का असर कम हो जाए।"
                ),
                "ml": (
                    "### 🤱 മുലയൂട്ടുന്ന അമ്മമാർ മരുന്ന് കഴിക്കുമ്പോൾ\n\n"
                    "പാരസെറ്റമോൾ, ഐബുപ്രോഫെൻ എന്നിവ മുലയൂട്ടുന്ന സമയത്ത് സുരക്ഷിതമായി ഉപയോഗിക്കാം. എന്നാൽ കൊഡൈൻ അടങ്ങിയ മരുന്നുകൾ ഒഴിവാക്കണം. കുഞ്ഞിന് അമിത ഉറക്കമോ ക്ഷീണമോ ഉണ്ടാകുന്നുണ്ടോ എന്ന് നിരീക്ഷിക്കുക."
                ),
                "ta": (
                    "### 🤱 தாய்ப்பால் கொடுக்கும் போது மருந்து உட்கொள்ளல்\n\n"
                    "பாராசிட்டமால் மற்றும் இப்யூபுரூஃபன் தாய்ப்பால் கொடுக்கும் போது பாதுகாப்பானவை. கொடீன் போன்ற போதை கலந்த மருந்துகளை தவிர்க்க வேண்டும். குழந்தைக்கு பால் கொடுத்த உடனே மருந்து எடுப்பது நல்லது."
                ),
                "te": (
                    "### 🤱 పాలిచ్చే తల్లులకు మందుల జాగ్రత్తలు\n\n"
                    "పారాసిటమాల్ మరియు ఐబుప్రోఫెన్ పాలిచ్చే సమయంలో సురక్షితమైనవి. కొడైన్ వంటి మందులను వాడకూడదు. పాలిచ్చిన వెంటనే మందు వేసుకోవడం మంచిది."
                ),
                "mr": (
                    "### 🤱 स्तनपान करताना औषधांची काळजी\n\n"
                    "पॅरासिटामॉल आणि आयबुप्रोफेन स्तनपानादरम्यान सुरक्षित मानली जातात. कोडीनयुक्त औषधे टाळावीत. बाळाला दूध पाजल्यानंतर लगेच औषध घेतल्यास उत्तम."
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # -------------------------------------------------------------
        # F. MEDICINES TO AVOID IN PREGNANCY (TERATOGEN LIST)
        # -------------------------------------------------------------
        if any(w in q_low for w in ["avoid", "dangerous", "unsafe", "harmful", "teratogen", "बचें", "ತಪ್ಪಿಸಬೇಕು"]):
            texts = {
                "en": (
                    "### 🚫 Major Medications to Strictly Avoid During Pregnancy\n\n"
                    "The following pharmacological agents have established teratogenic or adverse fetal toxicities and must be avoided during pregnancy unless specifically indicated in specialized clinical scenarios:\n\n"
                    "1. **ACE Inhibitors & ARBs (e.g. Enalapril, Losartan, Telmisartan):** Fetal renal failure, oligohydramnios, skull hypoplasia, and intrauterine growth restriction.\n"
                    "2. **Retinoids (e.g. Isotretinoin, oral Vitamin A derivatives):** Severe craniofacial, cardiac, and thymic malformations.\n"
                    "3. **Methotrexate & Chemotherapeutics:** Fetal death, skeletal anomalies, and severe teratogenesis.\n"
                    "4. **Oral Anticoagulants (Warfarin):** Warfarin embryopathy (nasal hypoplasia, stippled epiphyses) and fetal hemorrhage. Low Molecular Weight Heparin (LMWH) is preferred.\n"
                    "5. **Statins (e.g. Atorvastatin):** Cholesterol synthesis is vital for fetal organogenesis; contraindicated in pregnancy.\n"
                    "6. **Anticonvulsants (Valproate):** Neural tube defects and neurodevelopmental impairments.\n\n"
                    "💡 *Never discontinue chronic medications abruptly without consulting your specialist to transition to safer alternatives.*"
                ),
                "kn": (
                    "### 🚫 ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಕಡ್ಡಾಯವಾಗಿ ತಪ್ಪಿಸಬೇಕಾದ ಔಷಧಿಗಳು\n\n"
                    "1. **ಬಿಪಿ ಔಷಧಿಗಳು (ACEi / ARBs - ಲೊಸಾರ್ಟನ್, ಟೆಲ್ಮಿಸಾರ್ಟನ್):** ಮಗುವಿನ ಮೂತ್ರಪಿಂಡಗಳ ವೈಫಲ್ಯಕ್ಕೆ ಕಾರಣವಾಗಬಹುದು.\n"
                    "2. **ಐಸೊಟ್ರಿಟಿನೊಯಿನ್ (ಮೊಡವೆ ಕ್ರೀಮ್/ಮಾತ್ರೆ):** ತೀವ್ರ ಜನನ ದೋಷಗಳನ್ನು ಉಂಟುಮಾಡುತ್ತದೆ.\n"
                    "3. **ವಾರ್ಫರಿನ್ (ರಕ್ತ ತೆಳುಗೊಳಿಸುವ ಮಾತ್ರೆ):** ಭ್ರೂಣದಲ್ಲಿ ರಕ್ತಸ್ರಾವಕ್ಕೆ ಕಾರಣವಾಗಬಹುದು.\n"
                    "4. **ಕೊಲೆಸ್ಟ್ರಾಲ್ ಮಾತ್ರೆಗಳು (ಅಟೋರ್ವಾಸ್ಟಾಟಿನ್):** ಮಗುವಿನ ಬೆಳವಣಿಗೆಗೆ ಹಾನಿಕಾರಕ.\n\n"
                    "ನಿಮ್ಮ ಯಾವುದೇ ನಿರಂತರ ಔಷಧಿಯನ್ನು ನಿಲ್ಲಿಸುವ ಮುನ್ನ ತಜ್ಞ ವೈದ್ಯರ ಸಲಹೆ ಪಡೆಯಿರಿ."
                ),
                "hi": (
                    "### 🚫 गर्भावस्था में पूर्णतः वर्जित प्रमुख दवाएं\n\n"
                    "1. **बीपी की दवाएं (ACEi/ARBs जैसे लॉसार्टन, टेल्मीसार्टन):** शिशु की किडनी को नुकसान पहुंचा सकती हैं।\n"
                    "2. **आइसोट्रेटिनॉइन (मुंहासों की दवा):** गंभीर जन्मजात विकृतियां (Birth defects) पैदा करती हैं।\n"
                    "3. **वारफारिन (खून पतला करने की दवा):** शिशु में आंतरिक रक्तस्राव का खतरा।\n"
                    "4. **स्टेटिन्स (कोलेस्ट्रॉल की दवाएं जैसे एटोरवास्टेटिन):** भ्रूण के अंगों के विकास में बाधा डालती हैं।\n\n"
                    "💡 *अपनी नियमित दवाएं बदलने के लिए हमेशा डॉक्टर से संपर्क करें।*"
                ),
                "ml": (
                    "### 🚫 ഗർഭകാലത്ത് ഒഴിവാക്കേണ്ട പ്രധാന മരുന്നുകൾ\n\n"
                    "ലൊസാർട്ടൻ പോലുള്ള ബിപി മരുന്നുകൾ, ഐസോട്രെറ്റിനോയിൻ (മുഖക്കുരു മരുന്ന്), വാർഫറിൻ, കൊളസ്ട്രോൾ മരുന്നുകൾ എന്നിവ കുഞ്ഞിന് ഗുരുതരമായ വൈകല്യങ്ങൾ ഉണ്ടാക്കാം."
                ),
                "ta": (
                    "### 🚫 கர்ப்ப காலத்தில் முற்றிலும் தவிர்க்க வேண்டிய மருந்துகள்\n\n"
                    "லோசார்டன் போன்ற இரத்த அழுத்த மருந்துகள், முகப்பருவுக்கான ஐசோட்ரெடினோயின், வார்ஃபரின் மற்றும் கொலஸ்ட்ரால் மருந்துகள் சிசுவிற்கு கடுமையான பிறவி குறைபாடுகளை ஏற்படுத்தக்கூடும்."
                ),
                "te": (
                    "### 🚫 గర్భధారణలో తప్పక నివారించవలసిన మందులు\n\n"
                    "లోసార్టన్ వంటి బీపీ మందులు, మొటిమల ఐసోట్రిటినోయిన్, వార్ఫరిన్ మరియు కొలెస్ట్రాల్ మందులు పిండానికి తీవ్రమైన పుట్టుకతో వచ్చే లోపాలను కలిగిస్తాయి."
                ),
                "mr": (
                    "### 🚫 गरोदरपणात पूर्णपणे टाळावयाची औषधे\n\n"
                    "लॉसार्टनसारखी बीपीची औषधे, मुरुमांचे आयसोट्रेटिनॉइन, वॉरफेरिन आणि कोलेस्ट्रॉलची औषधे गर्भातील बाळासाठी अत्यंत घातक ठरतात."
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # General Pregnancy Safety fallback
        general_preg_texts = {
            "en": (
                "### 🤰 General Medication Safety Principles During Pregnancy\n\n"
                "1. **Never Assume Total Safety:** No medication is 100% risk-free during pregnancy. Suitability depends on gestational age, dosage, maternal health, and clinical necessity.\n"
                "2. **Modern Evaluation Standards:** Outdated letter categories (A, B, C, D, X) have been superseded by narrative clinical risk-benefit assessments under the FDA Pregnancy and Lactation Labeling Rule (PLLR).\n"
                "3. **Non-Drug Measures First:** Prioritize hydration, adequate rest, and physician-approved non-pharmacological comfort measures where appropriate.\n"
                "4. **Always Verify Active Ingredients:** Commercial brand names frequently alter formulations or combine multiple active substances. Always inspect the active drug name.\n"
                "5. **Physician Consultation:** Always obtain clear clearance from your obstetrician or pharmacist before taking prescription or over-the-counter remedies."
            ),
            "kn": (
                "### 🤰 ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಔಷಧಗಳ ಸಾಮಾನ್ಯ ಸುರಕ್ಷತಾ ನಿಯಮಗಳು\n\n"
                "1. ಯಾವುದೇ ಔಷಧಿಯನ್ನು ವೈದ್ಯರ ಸಲಹೆಯಿಲ್ಲದೆ ತೆಗೆದುಕೊಳ್ಳಬೇಡಿ.\n"
                "2. ಔಷಧಿಯ ಬ್ರಾಂಡ್ ಹೆಸರಿನ ಬದಲು ಅದರ ಸಕ್ರಿಯ ಘಟಕಾಂಶವನ್ನು (Active Ingredient) ಪರಿಶೀಲಿಸಿ.\n"
                "3. ಮೊದಲು ವಿಶ್ರಾಂತಿ, ನೀರು ಕುಡಿಯುವುದು ಮುಂತಾದ ನೈಸರ್ಗಿಕ ವಿಧಾನಗಳಿಗೆ ಆದ್ಯತೆ ನೀಡಿ.\n"
                "4. ಕಡ್ಡಾಯವಾಗಿ ನಿಮ್ಮ ಸ್ತ್ರೀರೋಗ ತಜ್ಞರನ್ನು ಭೇಟಿ ಮಾಡಿ ಸಲಹೆ ಪಡೆಯಿರಿ."
            ),
            "hi": (
                "### 🤰 गर्भावस्था में दवा उपयोग के सामान्य नियम\n\n"
                "1. बिना डॉक्टर की अनुमति के कोई भी दवा (एलोपैथिक, आयुर्वेदिक या सप्लीमेंट) न लें।\n"
                "2. दवा के ब्रांड नाम के साथ-साथ उसके सॉल्ट (सक्रिय घटक) की जांच करें।\n"
                "3. हमेशा सबसे कम खुराक सबसे कम समय के लिए ही लें।\n"
                "4. किसी भी असामान्य लक्षण पर तुरंत अस्पताल से संपर्क करें।"
            )
        }
        return f"{persona_header}{general_preg_texts.get(lang, general_preg_texts['en'])}{escalation_footer}"

    @classmethod
    def evaluate_symptoms_and_general_medical(
        cls,
        q_low: str,
        lang: str = "en",
        persona_header: str = "",
        escalation_footer: str = ""
    ) -> Optional[str]:
        """
        Evaluates educational symptom inquiries (headache, stomach pain, dizziness, urination, heart attack signs).
        Never diagnoses; provides evidence-based causes and red flag triage.
        """
        # A. Headache
        if any(w in q_low for w in ["headache", "head ache", "why do i have a headache", "causes of headache", "तलेनोवु", "ತಲೆನೋವು", "सिरदर्द", "सिर दर्द"]):
            texts = {
                "en": (
                    "### 🤕 Headache: Common Etiologies and Clinical Triage\n\n"
                    "**Educational Overview:** A headache is pain arising from the pain-sensitive structures of the head and neck (meninges, blood vessels, cranial nerves, and muscles).\n\n"
                    "**1. Common Primary & Secondary Causes:**\n"
                    "- **Tension-Type Headache:** Most frequent; dull, bilateral, band-like tightness around forehead or back of head, triggered by stress, eye strain, or poor posture.\n"
                    "- **Dehydration & Fatigue:** Inadequate fluid intake reduces intravascular volume and cerebral oxygenation.\n"
                    "- **Migraine:** Moderate-to-severe throbbing unilateral headache often accompanied by nausea, photophobia (light sensitivity), and phonophobia (sound sensitivity).\n"
                    "- **Caffeine Withdrawal or Sleep Deprivation:** Disruption of neurovascular tone.\n"
                    "- **Sinusitis:** Frontal pressure exacerbated by bending forward, often with nasal congestion.\n\n"
                    "🚨 **Red Flag Warning Signs (Seek Immediate Medical Care - 'SNOOP' Criteria):**\n"
                    "Consult an emergency physician immediately if you experience:\n"
                    "- Sudden, explosive 'thunderclap' headache reaching peak intensity within seconds.\n"
                    "- Headache accompanied by high fever, stiff neck, confusion, seizures, or personality changes (signs of meningitis/encephalitis).\n"
                    "- Focal neurological deficits (weakness, numbness, speech slurring, vision loss).\n"
                    "- New headache onset in individuals $>50\\text{ years}$ or during pregnancy/postpartum (pre-eclampsia risk)."
                ),
                "kn": (
                    "### 🤕 ತಲೆನೋವಿಗೆ ಸಾಮಾನ್ಯ ಕಾರಣಗಳು ಮತ್ತು ಮುನ್ನೆಚ್ಚರಿಕೆಗಳು\n\n"
                    "**ಸಾಮಾನ್ಯ ಕಾರಣಗಳು:**\n"
                    "1. **ಒತ್ತಡ ಮತ್ತು ದಣಿವು (Tension Headache):** ಅತಿಯಾದ ಕೆಲಸ, ಮಾನಸಿಕ ಒತ್ತಡ ಅಥವಾ ಕಂಪ್ಯೂಟರ್ ಪರದೆಯ ಹೆಚ್ಚು ನೋಡುವುದರಿಂದ.\n"
                    "2. **ನಿರ್ಜಲೀಕರಣ (Dehydration):** ದೇಹದಲ್ಲಿ ನೀರಿನ ಪ್ರಮಾಣ ಕಡಿಮೆಯಾದಾಗ.\n"
                    "3. **ಮೈಗ್ರೇನ್ (Migraine):** ತಲೆಯ ಒಂದು ಬದಿಯಲ್ಲಿ ವಿಪರೀತ ನೋವು, ಬೆಳಕು ಮತ್ತು ಶಬ್ದಕ್ಕೆ ಸೂಕ್ಷ್ಮತೆ.\n"
                    "4. ನಿದ್ರಾಹೀನತೆ ಮತ್ತು ಸೈನಸ್ ಸೋಂಕು.\n\n"
                    "🚨 **ತುರ್ತು ಎಚ್ಚರಿಕೆ:** ಹಠಾತ್ ತೀವ್ರ ಸಿಡಿಲಿನಂತಹ ತಲೆನೋವು, ಕುತ್ತಿಗೆ ಬಿಗಿತ, ಜ್ವರ, ಕಣ್ಣು ಮಂಜಾಗುವುದು ಅಥವಾ ಮಾತು ತೊದಲುವಿಕೆ ಇದ್ದರೆ ತಕ್ಷಣ ವೈದ್ಯರನ್ನು ಭೇಟಿ ಮಾಡಿ."
                ),
                "hi": (
                    "### 🤕 सिरदर्द के सामान्य कारण और सावधानियां\n\n"
                    "**सामान्य कारण:**\n"
                    "1. **तनाव एवं थकान (Tension Headache):** मानसिक तनाव, अनिद्रा या आंखों में खिंचाव के कारण सिर के दोनों तरफ भारीपन।\n"
                    "2. **पानी की कमी (Dehydration):** पर्याप्त पानी न पीने से दिमाग तक ऑक्सीजन का प्रवाह प्रभावित होना।\n"
                    "3. **माइग्रेन (Migraine):** सिर के एक हिस्से में तेज धड़कन जैसा दर्द, साथ में उल्टी या रोशनी से चिड़चिड़ापन।\n"
                    "4. साइनस या अत्यधिक चाय/कॉफी का सेवन।\n\n"
                    "🚨 **खतरे की घंटी (तुरंत डॉक्टर को दिखाएं):** अचानक बिजली के झटके जैसा असहनीय सिरदर्द, गर्दन में अकड़न, तेज बुखार, चक्कर आना या बोलने में लड़खड़ाहट होने पर तुरंत इमरजेंसी में जाएं।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # B. Stomach Pain
        if any(w in q_low for w in ["stomach pain", "abdominal pain", "causes of stomach pain", "हೊಟ್ಟೆ ನೋವು", "ಹೊಟ್ಟೆನೋವು", "पेट दर्द"]):
            texts = {
                "en": (
                    "### 🩺 Abdominal Pain: Potential Etiologies and Clinical Red Flags\n\n"
                    "**Educational Overview:** Abdominal pain can originate from gastrointestinal, hepatobiliary, renal, or reproductive organs.\n\n"
                    "**1. Common Benign Causes:**\n"
                    "- **Acute Gastritis & Acid Peptic Disease:** Burning epigastric pain often related to spicy meals, NSAID use, or stress.\n"
                    "- **Gastroenteritis (Food Poisoning):** Cramping pain with nausea, vomiting, and diarrhea.\n"
                    "- **Irritable Bowel Syndrome (IBS) or Constipation:** Bloating, crampy discomfort relieved by defecation.\n\n"
                    "🚨 **Critical Red Flags Requiring Immediate Emergency Evaluation:**\n"
                    "- Severe localized pain in the **Right Lower Quadrant** with rebound tenderness (classic appendicitis).\n"
                    "- Vomiting blood (hematemesis) or passing dark black/tarry stools (melena).\n"
                    "- Pain radiating to the back with persistent vomiting (pancreatitis).\n"
                    "- Sudden, rigid, 'board-like' abdomen (hollow organ perforation).\n"
                    "- Abdominal pain in females with missed period or pregnancy (ectopic pregnancy risk)."
                ),
                "kn": (
                    "### 🩺 ಹೊಟ್ಟೆ ನೋವಿಗೆ ಸಾಮಾನ್ಯ ಕಾರಣಗಳು\n\n"
                    "- **ಗ್ಯಾಸ್ಟ್ರಿಕ್ ಮತ್ತು ಅಜೀರ್ಣ:** ಅತಿಯಾದ ಆಮ್ಲೀಯತೆ, ಖಾರವಾದ ಊಟ ಅಥವಾ ನೋವುನಿವಾರಕ ಮಾತ್ರೆಗಳ ಸೇವನೆಯಿಂದ.\n"
                    "- **ಫುಡ್ ಪಾಯಿಸನಿಂಗ್ (Gastroenteritis):** ಕಲುಷಿತ ಆಹಾರದಿಂದ ವಾಂತಿ ಮತ್ತು ಭೇದಿ.\n"
                    "- ಮಲಬದ್ಧತೆ ಅಥವಾ ಜಂತುಹುಳು ಬಾಧೆ.\n\n"
                    "🚨 **ತುರ್ತು ಲಕ್ಷಣಗಳು:** ಹೊಟ್ಟೆಯ ಬಲಭಾಗದ ಕೆಳಗೆ ವಿಪರೀತ ನೋವು (ಅಪೆಂಡಿಸೈಟಿಸ್), ರಕ್ತವಾಂತಿ, ಮಲದಲ್ಲಿ ರಕ್ತ ಅಥವಾ ಕಪ್ಪು ಮಲ ಬಂದರೆ ತಕ್ಷಣ ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಿ."
                ),
                "hi": (
                    "### 🩺 पेट दर्द के सामान्य कारण और खतरे के संकेत\n\n"
                    "- **गैस्ट्राइटिस एवं एसिडिटी:** ज्यादा तला-भुना खाने या खाली पेट रहने से पेट के ऊपरी हिस्से में जलन व दर्द।\n"
                    "- **फूड पॉइजनिंग:** दूषित भोजन/पानी से उल्टी, दस्त और ऐंठन।\n"
                    "- कब्ज या गैस का बनना।\n\n"
                    "🚨 **आपातकालीन संकेत:** पेट के निचले दाहिने हिस्से में तेज दर्द (अपेंडिक्स का खतरा), उल्टी में खून आना, या असहनीय दर्द होने पर तुरंत अस्पताल जाएं।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # C. Dizziness
        if any(w in q_low for w in ["dizzy", "dizziness", "feeling dizzy", "lightheaded", "तಲೆತಿರುಗುವಿಕೆ", "ತಲೆ ತಿರುಗುವುದು", "चक्कर आना", "चक्कर"]):
            texts = {
                "en": (
                    "### 💫 Dizziness and Lightheadedness: Mechanisms and Clinical Triage\n\n"
                    "**1. Common Clinical Causes:**\n"
                    "- **Orthostatic (Postural) Hypotension:** Sudden blood pooling in lower extremities upon standing, causing transient cerebral hypoperfusion (common with BP meds like Amlodipine or Losartan).\n"
                    "- **Dehydration & Hypovolemia:** Insufficient fluid or electrolyte intake.\n"
                    "- **Hypoglycemia (Low Blood Sugar):** Especially in diabetic patients taking insulin or sulfonylureas.\n"
                    "- **Benign Paroxysmal Positional Vertigo (BPPV) / Inner Ear Disorders:** Sensation that the room is spinning, triggered by head position changes.\n"
                    "- **Anemia:** Reduced hemoglobin capacity limiting brain oxygen delivery.\n\n"
                    "🚨 **Red Flag Emergency Symptoms (Stroke / Cardiac Warning):**\n"
                    "Seek immediate emergency hospital care if dizziness occurs alongside: sudden facial drooping, one-sided limb weakness, slurred speech, chest pain, palpitations, or fainting (syncope)."
                ),
                "kn": (
                    "### 💫 ತಲೆತಿರುಗುವಿಕೆಗೆ (Dizziness) ಮುಖ್ಯ ಕಾರಣಗಳು\n\n"
                    "1. **ರಕ್ತದೊತ್ತಡದಲ್ಲಿ ಹಠಾತ್ ಇಳಿಕೆ (Postural Hypotension):** ಮಲಗಿದಲ್ಲಿಂದ ಹಠಾತ್ ಎದ್ದು ನಿಂತಾಗ.\n"
                    "2. **ನಿರ್ಜಲೀಕರಣ (Dehydration):** ದೇಹದಲ್ಲಿ ನೀರಿನ ಕೊರತೆ.\n"
                    "3. **ರಕ್ತದಲ್ಲಿ ಸಕ್ಕರೆ ಅಂಶ ಕಡಿಮೆಯಾಗುವುದು (Hypoglycemia):** ಊಟ ತಡವಾದಾಗ ಅಥವಾ ಶುಗರ್ ಔಷಧಿಗಳ ಪರಿಣಾಮ.\n"
                    "4. ಕಿವಿಯ ಒಳಗಿನ ಸಮತೋಲನ ತೊಂದರೆ (Vertigo) ಅಥವಾ ರಕ್ತಹೀನತೆ (Anemia).\n\n"
                    "🚨 ಎದೆನೋವು, ಎಡಗೈ ನಿಶ್ಯಕ್ತಿ ಅಥವಾ ಮಾತು ತೊದಲುವಿಕೆಯೊಂದಿಗೆ ತಲೆತಿರುಗಿದರೆ ತಕ್ಷಣ ತುರ್ತು ಚಿಕಿತ್ಸೆ ಪಡೆಯಿರಿ."
                ),
                "hi": (
                    "### 💫 चक्कर आने के कारण और सावधानियां\n\n"
                    "1. **अचानक बीपी कम होना:** लेटने या बैठने के बाद एकदम से खड़े होने पर दिमाग तक खून का प्रवाह कम होना।\n"
                    "2. **पानी की कमी (Dehydration):** शरीर में इलेक्ट्रोलाइट्स का असंतुलન।\n"
                    "3. **शुगर कम होना (Hypoglycemia):** समय पर भोजन न करने से ब्लड शुगर गिरना।\n"
                    "4. आंतरिक कान की समस्या (Vertigo) या खून की कमी (एनीमिया)।\n\n"
                    "🚨 यदि चक्कर के साथ सीने में दर्द, हाथ-पैर में कमजोरी या बोलने में दिक्कत हो, तो तुरंत अस्पताल जाएं।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # D. Frequent Urination
        if any(w in q_low for w in ["frequent urination", "urinating often", "peeing a lot", "बार बार पेशाब", "ಹೆಚ್ಚು ಮೂತ್ರ"]):
            texts = {
                "en": (
                    "### 🚽 Frequent Urination (Polyuria / Urinary Frequency)\n\n"
                    "**1. Common Etiologies:**\n"
                    "- **Diabetes Mellitus (Osmotic Diuresis):** Excess blood glucose spills into urine, drawing water with it (**polyuria** with polydipsia/increased thirst).\n"
                    "- **Urinary Tract Infection (UTI):** Frequency, urgency, burning sensation (dysuria), and suprapubic discomfort.\n"
                    "- **Diuretic Medications:** Medicines for hypertension or edema (such as Furosemide or Hydrochlorothiazide).\n"
                    "- **High Fluid, Caffeine, or Alcohol Intake:** Natural diuretic effects.\n"
                    "- **Benign Prostatic Hyperplasia (BPH):** In older men, enlarged prostate causing incomplete bladder emptying and nocturia.\n\n"
                    "💡 *Consult your physician for a simple urine analysis and fasting blood glucose test if frequency persists.*"
                ),
                "kn": (
                    "### 🚽 ಪದೇ ಪದೇ ಮೂತ್ರ ವಿಸರ್ಜನೆಗೆ ಮುಖ್ಯ ಕಾರಣಗಳು\n\n"
                    "1. **ಮಧುಮೇಹ (Diabetes):** ರಕ್ತದಲ್ಲಿ ಸಕ್ಕರೆ ಮಟ್ಟ ಹೆಚ್ಚಾದಾಗ ಅತಿಯಾದ ಬಾಯಾರಿಕೆ ಮತ್ತು ಪದೇ ಪದೇ ಮೂತ್ರ ಬರುತ್ತದೆ.\n"
                    "2. **ಮೂತ್ರನಾಳದ ಸೋಂಕು (UTI):** ಮೂತ್ರ ವಿಸರ್ಜನೆಯ ಸಮಯದಲ್ಲಿ ಉರಿ ಅಥವಾ ನೋವು.\n"
                    "3. **ಬಿಪಿ ಔಷಧಿಗಳು (Diuretics):** ಮೂತ್ರ ಹೆಚ್ಚಿಸುವ ಔಷಧಿಗಳ ಬಳಕೆ.\n"
                    "4. ಪುರುಷರಲ್ಲಿ ಪ್ರಾಸ್ಟೇಟ್ ಗ್ರಂಥಿಯ ಊತ (BPH) ಅಥವಾ ಹೆಚ್ಚು ನೀರು/ಕಾಫಿ ಕುಡಿಯುವುದು."
                ),
                "hi": (
                    "### 🚽 बार-बार पेशाब आने के मुख्य कारण\n\n"
                    "1. **डायबिटीज (शुगर की बीमारी):** जब खून में ग्लूकोज बढ़ता है, तो शरीर उसे पेशाब के जरिए बाहर निकालता है, जिससे अधिक प्यास और पेशाब लगता है।\n"
                    "2. **यूरिन इन्फेक्शन (UTI):** पेशाब में जलन, दर्द या बार-बार हाजत होना।\n"
                    "3. **बीपी की दवाएं (Diuretics):** जो शरीर से अतिरिक्त पानी निकालने के लिए दी जाती हैं।\n"
                    "4. पुरुषों में प्रोस्टेट ग्रंथि का बढ़ना (BPH) या अत्यधिक चाय/कॉफी का सेवन।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # E. Heart Attack Warning Signs
        if any(w in q_low for w in ["heart attack", "warning signs of heart attack", "heart attack symptoms", "हृदयाघात", "हार्ट अटैक के लक्षण"]):
            texts = {
                "en": (
                    "### 🚨 Warning Signs of an Acute Myocardial Infarction (Heart Attack)\n\n"
                    "**A heart attack is a critical medical emergency. Call emergency services (112 or 108 in India) immediately.**\n\n"
                    "**Classic Warning Signs:**\n"
                    "1. **Retrosternal Chest Discomfort:** Sensation of intense pressure, squeezing, fullness, or heaviness in the center of the chest lasting more than a few minutes or resolving and returning.\n"
                    "2. **Radiating Pain:** Discomfort spreading to the **left arm, neck, jaw, back, or epigastrium (stomach)**.\n"
                    "3. **Shortness of Breath (Dyspnea):** Often accompanies chest discomfort or precedes it.\n"
                    "4. **Associated Symptoms:** Cold diaphoresis (sudden cold sweat), nausea, lightheadedness, or unexplained extreme fatigue (frequent in women and diabetic patients).\n\n"
                    "**Immediate Action Protocol:**\n"
                    "- Call an emergency ambulance immediately. Do not drive yourself.\n"
                    "- Rest quietly in a half-sitting position.\n"
                    "- If not allergic or contraindicated, chew an un-coated adult Aspirin (300 mg) while awaiting medical responders."
                ),
                "kn": (
                    "### 🚨 ಹೃದಯಾಘಾತದ (Heart Attack) ಪ್ರಮುಖ ಮುನ್ಸೂಚನೆಗಳು\n\n"
                    "**ಹೃದಯಾಘಾತವು ತಕ್ಷಣದ ತುರ್ತು ಪರಿಸ್ಥಿತಿಯಾಗಿದೆ. ತಕ್ಷಣ ಆಂಬ್ಯುಲೆನ್ಸ್ (112 ಅಥವಾ 108) ಗೆ ಕರೆ ಮಾಡಿ.**\n\n"
                    "- **ಎದೆಯಲ್ಲಿ ತೀವ್ರ ಒತ್ತಡ:** ಎದೆಯ ಮಧ್ಯಭಾಗದಲ್ಲಿ ಭಾರ, ಸಂಕೋಚನ ಅಥವಾ ಹಿಂಡಿದಂತಹ ನೋವು.\n"
                    "- **ನೋವು ಹರಡುವುದು:** ಎದೆನೋವು ಎಡಗೈ, ದವಡೆ, ಕುತ್ತಿಗೆ ಅಥವಾ ಬೆನ್ನಿಗೆ ಹರಡುವುದು.\n"
                    "- **ಉಸಿರಾಟದ ತೊಂದರೆ ಮತ್ತು ಬೆವರು:** ಹಠಾತ್ ತಣ್ಣನೆ ಬೆವರು ಬರುವುದು, ಉಸಿರಾಡಲು ಕಷ್ಟವಾಗುವುದು ಮತ್ತು ತಲೆತಿರುಗುವಿಕೆ.\n\n"
                    "💡 *ಸ್ವತಃ ವಾಹನ ಚಾಲನೆ ಮಾಡಬೇಡಿ, ತಕ್ಷಣ ತುರ್ತು ಚಿಕಿತ್ಸಾ ವಿಭಾಗಕ್ಕೆ ತೆರಳಿ.*"
                ),
                "hi": (
                    "### 🚨 हार्ट अटैक (दिल के दौरे) के मुख्य चेतावनी लक्षण\n\n"
                    "**हार्ट अटैक एक गंभीर आपातकाल है। तुरंत एम्बुलेंस (112 या 108) को कॉल करें।**\n\n"
                    "1. **सीने में भारीपन व दर्द:** सीने के बीच में अत्यधिक दबाव, जकड़न या निचोड़ने जैसा दर्द जो कुछ मिनटों से अधिक रहे।\n"
                    "2. **दर्द का फैलना:** दर्द का बाएं हाथ, जबड़े, गर्दन, पीठ या पेट के ऊपरी हिस्से तक जाना।\n"
                    "3. **सांस फूलना:** सांस लेने में भारी तकलीफ या बेचैनी।\n"
                    "4. **अत्यधिक पसीना:** बिना कारण अचानक ठंडा पसीना आना, चक्कर आना या उल्टी जैसा महसूस होना।\n\n"
                    "💡 *खुद गाड़ी न चलाएं, तुरंत नजदीकी अस्पताल के इमरजेंसी आईसीयू में पहुंचें।*"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # F. Fever & Kidney Disease & When to Consult a Doctor
        if any(w in q_low for w in ["when should i consult a doctor", "when to see a doctor", "when to consult a doctor", "डॉक्टर को कब दिखाएं", "ವೈದ್ಯರನ್ನು ಯಾವಾಗ ಭೇಟಿ ಮಾಡಬೇಕು"]):
            texts = {
                "en": (
                    "### 🩺 Clinical Triage: When to Consult a Healthcare Professional\n\n"
                    "**You should seek timely medical evaluation from a physician if you experience:**\n\n"
                    "1. **Persistent or Worsening Symptoms:** A fever lasting $>3\\text{ days}$, continuous cough for $>2\\text{ weeks}$, or pain unresponsive to standard over-the-counter care.\n"
                    "2. **Unexplained Weight Loss or Chronic Fatigue:** Significant involuntary weight loss or night sweats.\n"
                    "3. **Adverse Drug Reactions:** Skin rashes, severe gastrointestinal disturbances, wheezing, or jaundice after taking a medication.\n"
                    "4. **High-Risk Vulnerable Groups:** Any illness in pregnant women, infants under 3 months, older adults ($>65$), or immunocompromised patients.\n"
                    "5. **New or Atypical Symptoms:** New onset headaches in adults $>50$, persistent changes in bowel or bladder habits, or palpable unusual lumps.\n\n"
                    "🚨 **Immediate Emergency Department Red Flags:** Chest pressure radiating to left arm/jaw, acute difficulty breathing, sudden one-sided facial/limb weakness, or sudden thunderclap headache."
                ),
                "kn": (
                    "### 🩺 ವೈದ್ಯರನ್ನು ಯಾವಾಗ ಭೇಟಿ ಮಾಡಬೇಕು? (Clinical Triage)\n\n"
                    "1. **ದೀರ್ಘಕಾಲದ ಲಕ್ಷಣಗಳು:** 3 ದಿನಗಳಿಗಿಂತ ಹೆಚ್ಚು ಕಾಲ ಇರುವ ಜ್ವರ, 2 ವಾರಗಳಿಗಿಂತ ಹೆಚ್ಚು ಇರುವ ಕೆಮ್ಮು.\n"
                    "2. **ಹಠಾತ್ ತೂಕ ಇಳಿಕೆ ಮತ್ತು ಅತಿಯಾದ ಸುಸ್ತು.**\n"
                    "3. **ಔಷಧಿಗಳ ಅಡ್ಡಪರಿಣಾಮ:** ಮಾತ್ರೆ ತಿಂದ ನಂತರ ಮೈಮೇಲೆ ದದ್ದುಗಳು, ತುರಿಕೆ ಅಥವಾ ಉಸಿರಾಟದ ತೊಂದರೆ.\n"
                    "4. ಗರ್ಭಿಣಿಯರು ಮತ್ತು 65 ವರ್ಷ ಮೇಲ್ಪಟ್ಟ ಹಿರಿಯರಲ್ಲಿ ಯಾವುದೇ ಅನಾರೋಗ್ಯ ಕಂಡುಬಂದರೆ ತಕ್ಷಣ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
                ),
                "hi": (
                    "### 🩺 डॉक्टर से कब परामर्श लें? (क्लिनिकल गाइड)\n\n"
                    "1. **लगातार बने रहने वाले लक्षण:** 3 दिन से अधिक का बुखार, 2 सप्ताह से अधिक की खांसी या बढ़ता हुआ दर्द।\n"
                    "2. **अकारण वजन कम होना या अत्यधिक कमजोरी महसूस होना।**\n"
                    "3. **दवा के साइड इफेक्ट्स:** दवा लेने के बाद शरीर पर चकत्ते, खुजली या सांस लेने में परेशानी।\n"
                    "4. **गर्भवती महिलाएं और बच्चे:** गर्भावस्था में कोई भी लक्षण होने पर तुरंत प्रसूति विशेषज्ञ से सलाह लें।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        if any(w in q_low for w in ["what causes fever", "cause of fever", "fever", "ಜ್ವರ", "बुखार"]):
            texts = {
                "en": (
                    "### 🌡️ Fever (Pyrexia): Pathophysiology and Causes\n\n"
                    "**Pathophysiology:** Fever is an elevation of body core temperature above normal diurnal variation ($>38.0^\\circ\\text{C}$ or $100.4^\\circ\\text{F}$) controlled by the hypothalamus. Pyrogens (such as interleukin-1 and TNF) stimulate hypothalamic prostaglandin E2 (PGE2) synthesis, shifting the thermal setpoint upward.\n\n"
                    "**1. Common Causes:**\n"
                    "- **Infections:** Viral infections (influenza, dengue, rhinovirus) and bacterial infections (pharyngitis, pneumonia, urinary tract infections).\n"
                    "- **Inflammatory Conditions:** Autoimmune flare-ups (rheumatoid arthritis, lupus).\n"
                    "- **Drug-Induced Fever or Immunizations.**\n\n"
                    "**2. Supportive Care:** Adequate fluid hydration, rest, light clothing, and antipyretics like Paracetamol if recommended by a physician.\n"
                    "🚨 **Red Flags:** Stiff neck, petechial rash, breathing difficulty, or fever $>40^\\circ\\text{C}$ requires urgent medical evaluation."
                ),
                "kn": (
                    "### 🌡️ ಜ್ವರಕ್ಕೆ (Fever) ಕಾರಣಗಳು ಮತ್ತು ನಿರ್ವಹಣೆ\n\n"
                    "ದೇಹದ ಉಷ್ಣತೆ $38.0^\\circ\\text{C}$ ($100.4^\\circ\\text{F}$) ಗಿಂತ ಹೆಚ್ಚಾಗುವುದನ್ನು ಜ್ವರ ಎನ್ನುತ್ತಾರೆ. ಇದು ರೋಗಾಣುಗಳ ವಿರುದ್ಧ ದೇಹದ ರೋಗನಿರೋಧಕ ವ್ಯವಸ್ಥೆಯ ನೈಸರ್ಗಿಕ ಹೋರಾಟವಾಗಿದೆ.\n\n"
                    "- **ಕಾರಣಗಳು:** ವೈರಲ್ ಸೋಂಕುಗಳು (ಫ್ಲೂ, ಡೆಂಗ್ಯೂ), ಬ್ಯಾಕ್ಟೀರಿಯಾ ಸೋಂಕುಗಳು (ಗಂಟಲು ನೋವು, ಯುಟಿಐ).\n"
                    "- **ಪರಿಹಾರ:** ಸಾಕಷ್ಟು ನೀರು ಕುಡಿಯುವುದು, ವಿಶ್ರಾಂತಿ ಮತ್ತು ವೈದ್ಯರ ಸಲಹೆಯ ಮೇರೆಗೆ ಪ್ಯಾರಸಿಟಮಾಲ್ ಬಳಕೆ."
                ),
                "hi": (
                    "### 🌡️ बुखार के कारण और सावधानियां\n\n"
                    "जब शरीर का तापमान $38^\\circ\\text{C}$ ($100.4^\\circ\\text{F}$) से ऊपर चला जाता है, तो उसे बुखार कहते हैं। यह किसी संक्रमण के खिलाफ शरीर की रोग प्रतिरोधक क्षमता की प्रतिक्रिया है।\n\n"
                    "- **कारण:** वायरल इन्फेक्शन (फ्लू, डेंगू), बैक्टीरियल इन्फेक्शन (गले का इन्फेक्शन, टाइफाइड)।\n"
                    "- **उपचार:** पर्याप्त पानी पिएं, आराम करें और डॉक्टर की सलाह से पैरासिटामोल लें।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        if any(w in q_low for w in ["kidney disease", "kidney failure", "ಮೂತ್ರಪಿಂಡ", "किडनी की बीमारी", "गुर्दे की बीमारी"]):
            texts = {
                "en": (
                    "### 🩺 Kidney Disease: Pathophysiology and Prevention\n\n"
                    "**Overview:** The kidneys filter metabolic wastes, regulate intravascular volume, balance electrolytes (potassium, sodium), and maintain acid-base homeostasis.\n\n"
                    "**1. Chronic Kidney Disease (CKD):** Progressive loss of nephrons lasting $>3\\text{ months}$, staged by estimated Glomerular Filtration Rate (eGFR).\n"
                    "**2. Leading Causes:** Longstanding, poorly managed **Hypertension** (hypertensive nephrosclerosis) and **Diabetes Mellitus** (diabetic kidney disease).\n"
                    "**3. Medication Caution:** Avoid repetitive use of nephrotoxic drugs like NSAIDs (Ibuprofen, Diclofenac) and unmonitored aminoglycoside antibiotics.\n"
                    "💡 *Patients with diabetes or high blood pressure should screen urine albumin-to-creatinine ratio (uACR) and serum creatinine annually.*"
                ),
                "kn": (
                    "### 🩺 ಮೂತ್ರಪಿಂಡದ (Kidney) ಕಾಯಿಲೆಗಳು ಮತ್ತು ಮುನ್ನೆಚ್ಚರಿಕೆ\n\n"
                    "ಮೂತ್ರಪಿಂಡಗಳು ರಕ್ತದಲ್ಲಿನ ತ್ಯಾಜ್ಯ ಮತ್ತು ಹೆಚ್ಚುವರಿ ನೀರನ್ನು ಹೊರಹಾಕುವ ಪ್ರಮುಖ ಅಂಗಗಳಾಗಿವೆ.\n\n"
                    "- **ಮುಖ್ಯ ಕಾರಣಗಳು:** ಅನಿಯಂತ್ರಿತ ಸಕ್ಕರೆ ಕಾಯಿಲೆ (Diabetes) ಮತ್ತು ಅಧಿಕ ರಕ್ತದೊತ್ತಡ (BP).\n"
                    "- **ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಐಬುಪ್ರೊಫೇನ್ ಮತ್ತು ಡಿಕ್ಲೊಫೆನಾಕ್‌ನಂತಹ ನೋವುನಿವಾರಕ ಮಾತ್ರೆಗಳನ್ನು ಅತಿಯಾಗಿ ಸೇವಿಸಬೇಡಿ; ಇವು ಮೂತ್ರಪಿಂಡಗಳಿಗೆ ಗಂಭೀರ ಹಾನಿಯನ್ನುಂಟುಮಾಡುತ್ತವೆ."
                ),
                "hi": (
                    "### 🩺 किडनी (गुर्दे) की बीमारी और बचाव\n\n"
                    "किडनी हमारे शरीर से विषाक्त पदार्थों और अतिरिक्त पानी को छानकर बाहर निकालती है।\n\n"
                    "- **प्रमुख कारण:** अनियंत्रित डायबिटीज (शुगर) और हाई ब्लड प्रेशर।\n"
                    "- **बचाव:** पेनकिलर दवाओं का अनावश्यक सेवन न करें क्योंकि ये किडनी को सीधे नुकसान पहुंचाती हैं। पर्याप्त पानी पिएं और नमक का सेवन कम करें।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        return None

    @classmethod
    def evaluate_pharmacy_and_regulations(
        cls,
        q_low: str,
        lang: str = "en",
        persona_header: str = "",
        escalation_footer: str = ""
    ) -> Optional[str]:
        """
        Evaluates pharmacy education questions:
        - Generic vs Brand medicines
        - Medicine Expiry Dates
        - Batch Numbers
        - Medicine Storage rules
        - Genuine medicine authentication
        - Prescription Schedule regulations
        - Accidental Overdose triage
        """
        # A. Generic vs Brand
        if any(w in q_low for w in ["generic medicine", "brand and generic", "difference between brand", "difference between generic", "जेनेरिक दवा", "ಜನೆರಿಕ್"]):
            texts = {
                "en": (
                    "### 💊 Understanding Generic vs. Brand-Name Medicines\n\n"
                    "**1. Active Pharmaceutical Ingredient (API):**\n"
                    "A **Generic Medicine** contains the exact same active pharmaceutical ingredient in the identical dosage strength, route, and clinical formulation as the branded originator drug (e.g., generic *Paracetamol 650 mg* vs. branded *Dolo 650*).\n\n"
                    "**2. Bioequivalence Standards (CDSCO & FDA):**\n"
                    "Regulatory agencies mandate that generic drugs demonstrate **bioequivalence** through rigorous pharmacokinetic studies (ensuring rate and extent of systemic absorption falls within a strict $80\\text{--}125\\%$ confidence interval of the reference brand).\n\n"
                    "**3. Differences:**\n"
                    "- **Inactive Ingredients (Excipients):** Binders, fillers, colors, or flavors may differ, provided they do not alter bioavailability or therapeutic performance.\n"
                    "- **Cost:** Generic medications cost significantly less (often 50% to 80% cheaper) because generic manufacturers do not incur initial drug discovery, patent licensing, or heavy brand marketing expenses.\n\n"
                    "💡 *Generic medicines approved by CDSCO or FDA are bioequivalent, safe, and therapeutically interchangeable with their branded counterparts.*"
                ),
                "kn": (
                    "### 💊 ಜೆನೆರಿಕ್ ಮತ್ತು ಬ್ರಾಂಡೆಡ್ ಔಷಧಿಗಳ ನಡುವಿನ ವ್ಯತ್ಯಾಸ\n\n"
                    "1. **ಒಂದೇ ಸಕ್ರಿಯ ಘಟಕಾಂಶ:** ಜೆನೆರಿಕ್ ಔಷಧಿಯಲ್ಲಿ ಬ್ರಾಂಡೆಡ್ ಔಷಧಿಯಲ್ಲಿರುವಷ್ಟೇ ಪ್ರಮಾಣದ ಅದೇ ರಾಸಾಯನಿಕ ಘಟಕವಿರುತ್ತದೆ (ಉದಾಹರಣೆಗೆ: ಪ್ಯಾರಸಿಟಮಾಲ್ 650 ಮಿಗ್ರಾಂ ಜೆನೆರಿಕ್ ಮತ್ತು ಡೋಲೋ 650 ಬ್ರಾಂಡ್).\n"
                    "2. **ಗುಣಮಟ್ಟ ಮತ್ತು ಸುರಕ್ಷತೆ:** ಜೆನೆರಿಕ್ ಔಷಧಿಗಳು ಸರ್ಕಾರಿ ಔಷಧ ನಿಯಂತ್ರಣ ಮಂಡಳಿಗಳಿಂದ (CDSCO) ಕಟ್ಟುನಿಟ್ಟಿನ ಗುಣಮಟ್ಟ ಮತ್ತು ಸಮಾನ ಪರಿಣಾಮದ (Bioequivalence) ಪರೀಕ್ಷೆಗೆ ಒಳಪಡುತ್ತವೆ.\n"
                    "3. **ಬೆಲೆ ವ್ಯತ್ಯಾಸ:** ಜೆನೆರಿಕ್ ಔಷಧಿಗಳು ಜಾಹೀರಾತು ಮತ್ತು ಬ್ರ್ಯಾಂಡಿಂಗ್ ವೆಚ್ಚವಿಲ್ಲದಿರುವುದರಿಂದ ಶೇ. 50 ರಿಂದ 80 ರಷ್ಟು ಕಡಿಮೆ ಬೆಲೆಯಲ್ಲಿ ದೊರೆಯುತ್ತವೆ."
                ),
                "hi": (
                    "### 💊 जेनेरिक और ब्रांडेड दवाओं में क्या अंतर है?\n\n"
                    "1. **समान सक्रिय घटक:** जेनेरिक दवा में वही मुख्य साल्ट (सक्रिय घटक) उसी क्षमता में होता है जो ब्रांडेड दवा में होता है (जैसे: जेनेरिक पैरासिटामोल 650mg और ब्रांडेड डोलो 650)।\n"
                    "2. **गुणवत्ता और असर:** सरकारी नियमों (CDSCO एवं FDA) के अनुसार जेनेरिक दवा का असर और सुरक्षा ब्रांडेड दवा के बिल्कुल समान (Bioequivalent) होना अनिवार्य है।\n"
                    "3. **कीमत में अंतर:** जेनेरिक दवाओं पर विज्ञापन और मार्केटिंग का खर्च नहीं होता, इसलिए ये ब्रांडेड दवाओं की तुलना में 50% से 80% तक सस्ती होती हैं।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # B. Expiry Date & Batch Number
        if any(w in q_low for w in ["expiry date", "expired medicine", "medicine expiry", "batch number", "दवा की एक्सपायरी", "ಎಕ್ಸ್‌ಪೈರಿ", "ಬ್ಯಾಚ್"]):
            texts = {
                "en": (
                    "### 📅 Medicine Expiry Dates and Batch Numbers Explained\n\n"
                    "**1. What is an Expiry Date?**\n"
                    "The expiration date reflects the final day the pharmaceutical manufacturer guarantees full chemical potency, structural stability, sterility, and safety under specified storage conditions.\n\n"
                    "**Why You Must Never Take Expired Medicines:**\n"
                    "- **Loss of Therapeutic Potency:** Degraded active molecules fail to treat conditions (critical for antibiotics, insulin, nitroglycerin, and cardiac drugs).\n"
                    "- **Toxic Breakdown Products:** Certain drugs (such as expired tetracyclines) decompose into toxic chemical metabolites causing renal Fanconi syndrome.\n"
                    "- **Bacterial Contamination:** Liquid suspensions and eye/ear drops lose preservative efficacy and harbor pathogen growth.\n\n"
                    "**2. What is a Batch / Lot Number?**\n"
                    "A unique alpha-numeric code assigned to a specific production run. It allows complete retrospective traceability across raw material batches, quality control records, manufacturing lines, and targeted recall isolation if a defect is identified."
                ),
                "kn": (
                    "### 📅 ಔಷಧಿಗಳ ಎಕ್ಸ್‌ಪೈರಿ ದಿನಾಂಕ ಮತ್ತು ಬ್ಯಾಚ್ ಸಂಖ್ಯೆಯ ಮಹತ್ವ\n\n"
                    "1. **ಎಕ್ಸ್‌ಪೈರಿ ದಿನಾಂಕ:** ಔಷಧಿಯ ಶಕ್ತಿ ಮತ್ತು ಸುರಕ್ಷತೆಯ ಅಂತಿಮ ದಿನಾಂಕ. ಅವಧಿ ಮೀರಿದ ಔಷಧಿಗಳನ್ನು ಸೇವಿಸಿದರೆ ಔಷಧಿಯ ಗುಣ ಕಡಿಮೆಯಾಗುತ್ತದೆ ಅಥವಾ ರಾಸಾಯನಿಕ ಬದಲಾವಣೆಯಿಂದ ದೇಹಕ್ಕೆ ವಿಷಕಾರಿಯಾಗಬಹುದು.\n"
                    "2. **ಬ್ಯಾಚ್ ಸಂಖ್ಯೆ (Batch No):** ಆ ಔಷಧಿಯನ್ನು ಯಾವಾಗ, ಯಾವ ಘಟಕದಲ್ಲಿ ತಯಾರಿಸಲಾಗಿದೆ ಎಂಬುದನ್ನು ಪತ್ತೆಹಚ್ಚುವ ವಿಶಿಷ್ಟ ಗುರುತಿನ ಸಂಖ್ಯೆ. ಗುಣಮಟ್ಟದಲ್ಲಿ ದೋಷವಿದ್ದಾಗ ಆ ನಿರ್ದಿಷ್ಟ ಬ್ಯಾಚ್ ಅನ್ನು ಹಿಂಪಡೆಯಲು ಇದು ಸಹಕಾರಿ."
                ),
                "hi": (
                    "### 📅 दवा की एक्सपायरी डेट और बैच नंबर का महत्व\n\n"
                    "1. **एक्सपायरी डेट:** वह अंतिम तारीख जब तक कंपनी दवा के असर और सुरक्षा की गारंटी देती है। एक्सपायर्ड दवा लेने से दवा का असर खत्म हो जाता है या वह विषैली (Toxic) हो सकती है।\n"
                    "2. **बैच नंबर (Batch No):** यह उस दवा के निर्माण का विशिष्ट कोड होता है जिससे पता चलता है कि दवा कब और किस फैक्ट्री में बनी। गुणवत्ता में खराबी आने पर उसी बैच को वापस मंगाया जाता है।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # C. Storage & Genuine Medicine Identification
        if any(w in q_low for w in ["how should medicines be stored", "store medicine", "medicine storage", "genuine medicine", "identify genuine", "असली दवा", "ಔಷಧಿ ಶೇಖರಣೆ"]):
            texts = {
                "en": (
                    "### 🛡️ How to Identify Genuine Medicines & Proper Storage Protocols\n\n"
                    "**1. Identifying Genuine CDSCO-Verified Pharmaceuticals:**\n"
                    "- **Track & Trace 2D QR Code:** Mandatory on India's top 300 pharmaceutical brands; scan using the PharmIntel Medicine Scanner to verify batch provenance.\n"
                    "- **Tamper-Evident Packaging:** Check seals, blister integrity, and sharp, error-free printing.\n"
                    "- **Valid GST Tax Invoice:** Always purchase from registered, state-licensed retail pharmacies.\n\n"
                    "**2. Evidence-Based Medicine Storage Guidelines:**\n"
                    "- **Standard Oral Tablets/Capsules:** Store in a cool, dry place below $25^\\circ\\text{C}$ ($77^\\circ\\text{F}$), protected from direct sunlight and humidity. **Never store medicines in steamy bathroom cabinets.**\n"
                    "- **Cold Chain Biologics (Insulin, Vaccines, Eye Drops):** Refrigerate between $2^\\circ\\text{C}$ and $8^\\circ\\text{C}$ ($36^\\circ\\text{--}46^\\circ\\text{F}$). Do NOT freeze.\n"
                    "- **Keep Out of Reach of Children:** Store securely in original packaging."
                ),
                "kn": (
                    "### 🛡️ ಅಸಲಿ ಔಷಧಿಗಳ ಗುರುತಿಸುವಿಕೆ ಮತ್ತು ಶೇಖರಣಾ ನಿಯಮಗಳು\n\n"
                    "1. **ಅಸಲಿ ಔಷಧಿ ಗುರುತಿಸುವುದು:** ಪ್ಯಾಕೆಟ್ ಮೇಲಿನ ಕ್ಯೂಆರ್ ಕೋಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ, ಮುದ್ರಣ ದೋಷಗಳಿಲ್ಲದಿರುವುದನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ ಮತ್ತು ಯಾವಾಗಲೂ ಪರವಾನಗಿ ಪಡೆದ ಫಾರ್ಮಸಿಗಳಿಂದ ಬಿಲ್ ಸಹಿತ ಖರೀದಿಸಿ.\n"
                    "2. **ಶೇಖರಣೆ:** ಮಾತ್ರೆಗಳನ್ನು ತಂಪಾದ, ಒಣ ಸ್ಥಳದಲ್ಲಿ ನೇರ ಸೂರ್ಯನ ಬೆಳಕಿನಿಂದ ದೂರವಿಡಿ (ಬಾತ್‌ರೂಮ್‌ನಲ್ಲಿ ಇಡಬೇಡಿ). ಇನ್ಸುಲಿನ್ ಮತ್ತು ಕೆಲವು ಡ್ರಾಪ್ಸ್‌ಗಳನ್ನು ರೆಫ್ರಿಜರೇಟರ್‌ನಲ್ಲಿ ($2-8^\\circ\\text{C}$) ಇಡಬೇಕು."
                ),
                "hi": (
                    "### 🛡️ असली दवा की पहचान और दवा रखने के नियम\n\n"
                    "1. **असली दवा की पहचान:** पैकेजिंग पर 2D बारकोड/क्यूआर कोड चेक करें, सील बंद पैकेट लें और हमेशा पक्के बिल के साथ लाइसेंस प्राप्त मेडिकल स्टोर से ही खरीदें।\n"
                    "2. **दवा रखने के नियम:** दवाओं को नमी और सीधी धूप से दूर ठंडी व सूखी जगह ($25^\\circ\\text{C}$ से कम) रखें। बाथरूम में दवाएं न रखें। इंसुलिन जैसी दवाओं को फ्रिज ($2-8^\\circ\\text{C}$) में रखें, फ्रीजर में नहीं।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # D. Prescription Medicine (Schedule H/H1/X)
        if any(w in q_low for w in ["prescription medicine", "what is a prescription medicine", "schedule h", "पर्चे की दवा", "ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಔಷಧಿ"]):
            texts = {
                "en": (
                    "### 📋 What is a Prescription Medicine? (Schedule H / H1 Regulations)\n\n"
                    "**Regulatory Definition:** Under the Drugs and Cosmetics Rules, a **Prescription Medicine** (such as Schedule H, H1, or X drugs) is a pharmaceutical agent that cannot legally be dispensed without a valid prescription from a Registered Medical Practitioner (RMP).\n\n"
                    "- **Why Restrictions Exist:** These drugs carry potent systemic pharmacodynamic actions, narrow therapeutic windows, habit-forming dependencies, or serious adverse event profiles if taken without medical supervision.\n"
                    "- **Schedule H1 Examples:** Powerful 3rd-generation antibiotics, anti-tubercular drugs, and psychotropics (monitored to prevent antibiotic resistance and drug abuse).\n"
                    "- **Over-the-Counter (OTC) Drugs:** Lower-risk formulations (like antacids or low-strength paracetamol) permitted for direct purchase."
                ),
                "kn": (
                    "### 📋 ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಔಷಧಿ ಎಂದರೇನು? (Schedule H / H1)\n\n"
                    "ವೈದ್ಯರ ಅಧಿಕೃತ ಚೀಟಿ (Prescription) ಇಲ್ಲದೆ ಮಾರಾಟ ಮಾಡಲು ಕಾನೂನಿನಲ್ಲಿ ಅನುಮತಿಯಿಲ್ಲದ ಔಷಧಿಗಳನ್ನು **ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಔಷಧಿಗಳು** ಎನ್ನುತ್ತಾರೆ.\n\n"
                    "ಪ್ರಬಲ ಆಂಟಿಬಯೋಟಿಕ್‌ಗಳು, ನಿದ್ರೆ ಮಾತ್ರೆಗಳು ಮತ್ತು ಬಿಪಿ/ಹೃದಯದ ಔಷಧಿಗಳು ಈ ವರ್ಗಕ್ಕೆ ಸೇರುತ್ತವೆ. ಇವುಗಳನ್ನು ಅತಿಯಾಗಿ ಅಥವಾ ತಪ್ಪಾಗಿ ಬಳಸಿದರೆ ಪ್ರಾಣಾಪಾಯ ಉಂಟಾಗುವ ಸಾಧ್ಯತೆ ಇರುವುದರಿಂದ ಈ ನಿಯಮವಿದೆ."
                ),
                "hi": (
                    "### 📋 पर्चे वाली दवा (Prescription Medicine) क्या होती है?\n\n"
                    "ड्रग्स एंड कॉस्मेटिक्स एक्ट के अनुसार, ऐसी दवाएं जिन्हें बिना डॉक्टर के वैध पर्चे के मेडिकल स्टोर से नहीं खरीदा जा सकता, उन्हें **प्रिस्क्रिप्शन दवाएं (Schedule H/H1)** कहते हैं।\n\n"
                    "एंटीबायोटिक्स, हृदय रोग की दवाएं और नींद की दवाएं इसी श्रेणी में आती हैं ताकि इनके गलत इस्तेमाल या ओवरडोज से बचा जा सके।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # E. Accidental Overdose First-Aid
        if any(w in q_low for w in ["too much medicine", "overdose", "accidentally took too much", "ज्यादा दवा खा ली", "ಹೆಚ್ಚು ಮಾತ್ರೆ"]):
            texts = {
                "en": (
                    "### 🚨 Urgent Clinical Protocol: Suspected Medication Overdose\n\n"
                    "**An acute medication overdose requires immediate emergency medical evaluation. Take these actions at once:**\n\n"
                    "1. **Stop Taking the Medicine Immediately.**\n"
                    "2. **Call Emergency Services:** Dial **112 or 108** in India, or call the National Poison Information Centre immediately.\n"
                    "3. **Do NOT Induce Vomiting:** Never give salt water, home remedies, or force emesis, which can cause chemical aspiration into the lungs.\n"
                    "4. **Preserve Packaging:** Bring the exact pill strip, container, and any remaining tablets to the emergency room so doctors can identify the active chemical and administer specific antidotes (e.g., N-Acetylcysteine for paracetamol overdose).\n"
                    "5. **Monitor Vital Signs:** Note responsiveness, breathing rate, and pulse until emergency help arrives."
                ),
                "kn": (
                    "### 🚨 ತುರ್ತು ಮಾರ್ಗದರ್ಶನ: ತಪ್ಪಿ ಹೆಚ್ಚು ಮಾತ್ರೆ ಸೇವಿಸಿದರೆ (Overdose)\n\n"
                    "1. **ತಕ್ಷಣ ಔಷಧಿಯನ್ನು ನಿಲ್ಲಿಸಿ.**\n"
                    "2. **ತುರ್ತು ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ (112 ಅಥವಾ 108).**\n"
                    "3. ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ಬಲವಂತವಾಗಿ ವಾಂತಿ ಮಾಡಿಸಲು ಪ್ರಯತ್ನಿಸಬೇಡಿ.\n"
                    "4. ಸೇವಿಸಿದ ಔಷಧಿಯ ಪ್ಯಾಕೆಟ್ ಅಥವಾ ಬಾಟಲಿಯನ್ನು ತಕ್ಷಣ ಸಮೀಪದ ಆಸ್ಪತ್ರೆಯ ತುರ್ತು ವಿಭಾಗಕ್ಕೆ (Emergency) ತೆಗೆದುಕೊಂಡು ಹೋಗಿ."
                ),
                "hi": (
                    "### 🚨 आपातकालीन प्रोटोकॉल: दवा का ओवरडोज होने पर क्या करें?\n\n"
                    "1. **तुरंत दवा बंद करें।**\n"
                    "2. **आपातकालीन नंबर पर कॉल करें (112 या 108)।**\n"
                    "3. जबरन उल्टी कराने की कोशिश न करें, इससे फेफड़ों को नुकसान हो सकता है।\n"
                    "4. दवा का खाली रैपर या डिब्बा साथ लेकर तुरंत अस्पताल के इमरजेंसी वार्ड में जाएं ताकि डॉक्टर सही एंटीडोट दे सकें।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        return None

    @classmethod
    def evaluate_in_chat_drug_interactions(
        cls,
        q_low: str,
        lang: str = "en",
        persona_header: str = "",
        escalation_footer: str = ""
    ) -> Optional[str]:
        """
        Evaluates drug-drug compatibility and interaction queries directly in chat.
        Never redirects the user away from chat.
        """
        # A. Dolo 650 + Combiflam (Duplicate Paracetamol active ingredient)
        has_dolo = any(w in q_low for w in ["dolo", "paracetamol", "calpol", "crocin"])
        has_combiflam = any(w in q_low for w in ["combiflam", "कॉम्बीफ्लाम", "ಕಾಂಬಿಫ್ಲಾಮ್"])
        if has_dolo and has_combiflam:
            texts = {
                "en": (
                    "### ⚠️ Dangerous Interaction Warning: Dolo 650 + Combiflam\n\n"
                    "**Clinical Evaluation: NOT RECOMMENDED (Severe Duplicate Active Ingredient Risk)**\n\n"
                    "- **Formulation Breakdown:**\n"
                    "  - **Dolo 650:** Contains **Paracetamol 650 mg**.\n"
                    "  - **Combiflam:** A combination formulation containing **Ibuprofen 400 mg + Paracetamol 325 mg**.\n"
                    "- **Pharmacological Danger:** Taking both medications simultaneously causes **unintentional paracetamol double-dosing** ($\\text{total single dose} = 650\\text{ mg} + 325\\text{ mg} = 975\\text{ mg}$). Taking another dose within the same day can rapidly exceed the strict adult ceiling of 4,000 mg/day.\n"
                    "- **Toxicity Risk:** Excess paracetamol depletes hepatic glutathione, causing toxic accumulation of **NAPQI** (N-acetyl-p-benzoquinone imine), leading to severe hepatocellular necrosis (**liver injury**).\n"
                    "- **Clinical Recommendation:** Do NOT take Dolo 650 and Combiflam together. Use only one medication under your doctor's direction."
                ),
                "kn": (
                    "### ⚠️ ತೀವ್ರ ಅಪಾಯದ ಎಚ್ಚರಿಕೆ: ಡೋಲೋ 650 + ಕಾಂಬಿಫ್ಲಾಮ್ (Dolo 650 + Combiflam)\n\n"
                    "**ವೈದ್ಯಕೀಯ ಮೌಲ್ಯಮಾಪನ: ಇವೆರಡನ್ನು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳಬಾರದು.**\n\n"
                    "- **ಕಾರಣ:** ಡೋಲೋ 650 ನಲ್ಲಿ **650 ಮಿಗ್ರಾಂ ಪ್ಯಾರಸಿಟಮಾಲ್** ಇರುತ್ತದೆ. ಕಾಂಬಿಫ್ಲಾಮ್ ಮಾತ್ರೆ ಈಗಾಗಲೇ **ಐಬುಪ್ರೊಫೇನ್ 400 ಮಿಗ್ರಾಂ + ಪ್ಯಾರಸಿಟಮಾಲ್ 325 ಮಿಗ್ರಾಂ** ಅನ್ನು ಒಳಗೊಂಡಿದೆ.\n"
                    "- ಇವೆರಡನ್ನೂ ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಂಡರೆ ಪ್ಯಾರಸಿಟಮಾಲ್ ಪ್ರಮಾಣ ಅಪಾಯಕಾರಿ ಮಟ್ಟಕ್ಕೆ ಏರಿ **ಯಕೃತ್ತಿಗೆ (Liver) ಗಂಭೀರ ಹಾನಿ** ಉಂಟುಮಾಡಬಹುದು.\n"
                    "- **ಸಲಹೆ:** ಇವೆರಡರಲ್ಲಿ ಯಾವುದಾದರೂ ಒಂದನ್ನು ಮಾತ್ರ ವೈದ್ಯರ ಮಾರ್ಗದರ್ಶನದಲ್ಲಿ ಬಳಸಿ."
                ),
                "hi": (
                    "### ⚠️ गंभीर चेतावनी: डोलो 650 + कॉम्बीफ्लाम एक साथ न लें\n\n"
                    "**क्लिनिकल सलाह: यह संयोजन असुरक्षित है (दवा का दोहराव)।**\n\n"
                    "- **कारण:** डोलो 650 में **650mg पैरासिटामोल** होता है। कॉम्बीफ्लाम में पहले से ही **आइबूप्रोफेन 400mg + पैरासिटामोल 325mg** मौजूद होता है।\n"
                    "- दोनों को एक साथ लेने से पैरासिटामोल की मात्रा अत्यधिक बढ़ जाती है, जिससे **लिवर (यकृत) फेल होने का गंभीर खतरा** होता है।\n"
                    "- **सलाह:** इन दोनों दवाओं को एक साथ कभी न लें। डॉक्टर द्वारा सुझाई गई केवल एक ही दवा का उपयोग करें।"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        # B. General Drug Interaction Concept ("can two medicines interact?")
        if any(w in q_low for w in ["can two medicines interact", "can medicines interact", "what happens if two medicines interact", "how do drugs interact"]):
            texts = {
                "en": (
                    "### 🔬 How Drug-Drug Interactions Occur in the Human Body\n\n"
                    "When two or more medications are administered concurrently, they can interact through two primary pharmacological mechanisms:\n\n"
                    "**1. Pharmacokinetic Interactions (What the Body Does to the Drug):**\n"
                    "- **Metabolism (CYP450 Enzyme Alteration):** One drug may inhibit or induce cytochrome P450 liver enzymes (like CYP3A4 or CYP2D6), causing the second drug to accumulate to toxic levels or be eliminated too rapidly to work.\n"
                    "- **Absorption:** Antacids or calcium binders can chelate antibiotics (like ciprofloxacin or tetracycline) in the stomach, blocking absorption into the bloodstream.\n"
                    "- **Renal Excretion:** Drugs competing for the same renal tubular transport mechanisms delay excretion.\n\n"
                    "**2. Pharmacodynamic Interactions (What the Drug Does to the Body):**\n"
                    "- **Synergistic Toxicity:** Combining two CNS depressants (e.g. benzodiazepines and opioids) causes fatal respiratory depression.\n"
                    "- **Antagonistic Effects:** A beta-agonist bronchodilator opposes a non-selective beta-blocker.\n\n"
                    "💡 *Always verify your complete medication regimen with your doctor or pharmacist to prevent preventable adverse drug events.*"
                ),
                "kn": (
                    "### 🔬 ಎರಡು ಔಷಧಿಗಳು ಪರಸ್ಪರ ಹೇಗೆ ವರ್ತಿಸುತ್ತವೆ? (Drug Interactions)\n\n"
                    "ಒಂದಕ್ಕಿಂತ ಹೆಚ್ಚು ಔಷಧಿಗಳನ್ನು ಒಟ್ಟಿಗೆ ಸೇವಿಸಿದಾಗ ಅವು ದೇಹದಲ್ಲಿ ಎರಡು ರೀತಿಯಲ್ಲಿ ಪರಸ್ಪರ ಪರಿಣಾಮ ಬೀರಬಹುದು:\n\n"
                    "1. **ಮೆಟಾಬಾಲಿಸಮ್ ಬದಲಾವಣೆ:** ಒಂದು ಔಷಧಿಯು ಯಕೃತ್ತಿನ ಕಿಣ್ವಗಳನ್ನು ತಡೆದು ಇನ್ನೊಂದು ಔಷಧಿಯು ರಕ್ತದಲ್ಲಿ ವಿಷಕಾರಿ ಮಟ್ಟಕ್ಕೆ ಏರುವಂತೆ ಮಾಡಬಹುದು.\n"
                    "2. **ಅಡ್ಡಪರಿಣಾಮಗಳ ಹೆಚ್ಚಳ:** ಉದಾಹರಣೆಗೆ ಬಿಪಿ ಮಾತ್ರೆ ಮತ್ತು ಮೂತ್ರವರ್ಧಕವನ್ನು ನೋವುನಿವಾರಕದೊಂದಿಗೆ ತೆಗೆದುಕೊಂಡರೆ ಮೂತ್ರಪಿಂಡಗಳಿಗೆ ತೀವ್ರ ಹಾನಿಯುಂಟಾಗುತ್ತದೆ.\n\n"
                    "ಯಾವುದೇ ಹೊಸ ಔಷಧಿಯನ್ನು ಪ್ರಾರಂಭಿಸುವ ಮುನ್ನ ನಿಮ್ಮ ವೈದ್ಯರಿಗೆ ನೀವು ಈಗಾಗಲೇ ತೆಗೆದುಕೊಳ್ಳುತ್ತಿರುವ ಎಲ್ಲಾ ಔಷಧಿಗಳ ವಿವರ ನೀಡಿ."
                ),
                "hi": (
                    "### 🔬 दो दवाएं आपस में कैसे इंटरैक्ट करती हैं?\n\n"
                    "जब दो या अधिक दवाएं एक साथ ली जाती हैं, तो उनके बीच ड्रग इंटरैक्शन दो तरह से हो सकता है:\n\n"
                    "1. **लिवर में मेटाबॉलिज्म पर असर:** एक दवा दूसरी दवा को शरीर में पचने से रोक सकती है, जिससे खून में उस दवा का स्तर खतरनाक रूप से बढ़ सकता है।\n"
                    "2. **विपरीत या दोहरा असर:** उदाहरण के लिए, दो दर्दनिवारक एक साथ लेने से पेट में अल्सर या ब्लीडिंग का खतरा बढ़ जाता है।\n\n"
                    "💡 *सुरक्षा के लिए हमेशा अपने डॉक्टर को अपनी सभी चालू दवाओं की सूची अवश्य दिखाएं।*"
                )
            }
            return f"{persona_header}{texts.get(lang, texts['en'])}{escalation_footer}"

        return None
