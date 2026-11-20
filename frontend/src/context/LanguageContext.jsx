import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations, medicalGlossary } from './translations';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳' },
];

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try {
      return localStorage.getItem('pharmintel_lang') || 'en';
    } catch {
      return 'en';
    }
  });

  const setLanguage = (langCode) => {
    if (SUPPORTED_LANGUAGES.some(l => l.code === langCode)) {
      setLanguageState(langCode);
      try {
        localStorage.setItem('pharmintel_lang', langCode);
        document.documentElement.lang = langCode;
      } catch (e) {
        console.warn("Could not save language to storage:", e);
      }
    }
  };

  useEffect(() => {
    try {
      document.documentElement.lang = language;
    } catch {}
  }, [language]);

  // Main UI translation helper
  const t = (key, fallback = null) => {
    const langDict = translations[language] || translations.en;
    if (langDict && langDict[key] !== undefined) {
      return langDict[key];
    }
    // Fallback to English
    if (translations.en && translations.en[key] !== undefined) {
      return translations.en[key];
    }
    return fallback !== null ? fallback : key;
  };

  // Severity localized tag
  const getSeverityLabel = (severity) => {
    const sev = (severity || '').toUpperCase();
    if (sev === 'RED' || sev === 'HIGH' || sev === 'CRITICAL' || sev === 'CONTRAINDICATED') {
      return t('severity_high', 'High Risk');
    }
    if (sev === 'YELLOW' || sev === 'MODERATE' || sev === 'MAJOR') {
      return t('severity_moderate', 'Moderate Risk');
    }
    if (sev === 'GREEN' || sev === 'LOW' || sev === 'SAFE') {
      return t('severity_low', 'Safe / Low Risk');
    }
    return t('severity_grey', 'Insufficient Info');
  };

  // Controlled medical translation for clinical findings
  const getMedicalText = (termKey, defaultText = '') => {
    const glossary = medicalGlossary[language] || medicalGlossary.en;
    if (glossary && glossary[termKey]) {
      return glossary[termKey];
    }
    return defaultText || termKey;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
        getSeverityLabel,
        getMedicalText,
        supportedLanguages: SUPPORTED_LANGUAGES,
        currentLanguageMeta: SUPPORTED_LANGUAGES.find(l => l.code === language) || SUPPORTED_LANGUAGES[0]
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return ctx;
}
