"""
Script to update PatientSafetyIntelligenceService in patient_safety_service.py with:
- Global medicine resolver integration
- Multi-constituent combination evaluation
- Duplicate active ingredient detection
- Multi-drug complex syndromes (Triple Whammy, Serotonin Syndrome, QT Prolongation, CNS Depression, Bleeding, Therapeutic Duplication)
- Precise diagnostic statuses
- 7-language localization
"""

import sys
import re

SERVICE_FILE = "backend/app/services/patient_safety_service.py"

NEW_RESOLVER_AND_ANALYSIS = '''    THERAPEUTIC_CLASSES = {
        "Proton Pump Inhibitor (PPI)": ["pantoprazole", "omeprazole", "rabeprazole", "esomeprazole", "lansoprazole", "dexlansoprazole"],
        "HMG-CoA Reductase Inhibitor (Statin)": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "pitavastatin", "lovastatin"],
        "Beta-Adrenoceptor Blocker": ["metoprolol", "atenolol", "bisoprolol", "nebivolol", "carvedilol", "propranolol", "labetalol"],
        "Non-Steroidal Anti-inflammatory Drug (NSAID)": ["ibuprofen", "diclofenac", "aceclofenac", "naproxen", "piroxicam", "etoricoxib", "celecoxib", "mefenamic", "ketorolac", "nimesulide"],
        "DPP-4 Inhibitor (Gliptin)": ["sitagliptin", "vildagliptin", "teneligliptin", "linagliptin", "saxagliptin", "alogliptin"],
        "SGLT2 Inhibitor (Gliflozin)": ["empagliflozin", "dapagliflozin", "canagliflozin", "remogliflozin"],
        "Angiotensin II Receptor Blocker (ARB)": ["telmisartan", "losartan", "valsartan", "olmesartan", "candesartan", "irbesartan"],
        "ACE Inhibitor": ["ramipril", "enalapril", "lisinopril", "perindopril", "captopril"],
        "Direct Oral Anticoagulant (DOAC)": ["apixaban", "rivaroxaban", "dabigatran", "edoxaban"]
    }

    @classmethod
    def _resolve_medicine_entry(cls, db: Session, m: Any) -> Dict[str, Any]:
        """
        Global Medicine Intelligence Resolver for PHARMINTEL.
        Resolves brand names, generics, combinations, dosage variations, and typos
        via MedicineIntelligenceService with live continuous discovery and diagnostics.
        """
        raw_name = (getattr(m, "medicine_name", None) or getattr(m, "brand_name", None) or "").strip()
        med_id = getattr(m, "medicine_id", None) or getattr(m, "id", None)

        db_med = None
        if med_id:
            db_med = db.query(Medicine).filter(Medicine.id == med_id).first()

        if db_med:
            substances = MedicineIntelligenceService._extract_substances(db_med)
            comp_score, _ = MedicineIntelligenceService.calculate_completeness(db_med)
            return {
                "item": m,
                "db_med": db_med,
                "brand": db_med.brand_name,
                "generic": db_med.generic_name,
                "ingredients": db_med.active_ingredients,
                "strength": db_med.strength or "Standard",
                "blob": f"{db_med.brand_name} {db_med.generic_name} {db_med.active_ingredients}".lower(),
                "active_substances": substances if substances else [db_med.generic_name],
                "is_combination": db_med.is_combination or len(substances) > 1,
                "is_unidentified": False,
                "diagnostic_code": "VERIFIED_COMPLETE",
                "diagnostic": DIAGNOSTIC_CODES["VERIFIED_COMPLETE"],
                "completeness_score": comp_score,
                "candidate_matches": []
            }

        res = MedicineIntelligenceService.resolve_medicine(db, raw_name)
        best_med = res.get("medicine")

        brand = (best_med.brand_name if best_med else None) or getattr(m, "brand_name", None) or raw_name
        generic = (best_med.generic_name if best_med else None) or getattr(m, "generic_name", None) or raw_name
        ingredients = (best_med.active_ingredients if best_med else None) or getattr(m, "active_ingredients", None) or generic
        strength = (best_med.strength if best_med else None) or getattr(m, "strength", None) or "Standard"

        substances = res.get("active_substances") or []
        if not substances and ingredients:
            substances = [s.strip() for s in re.split(r"[\+/&,;]|\band\b", ingredients) if s.strip()]
        if not substances:
            substances = [brand] if brand else []

        status = res.get("status", "UNIDENTIFIED")
        is_unidentified = (status == "UNIDENTIFIED") or (best_med is None and not res.get("active_substances"))

        diag_code = res.get("diagnostic_code") or ("VERIFIED_COMPLETE" if not is_unidentified else "MEDICINE_NOT_IDENTIFIED")
        diag_obj = res.get("diagnostic") or DIAGNOSTIC_CODES.get(diag_code, DIAGNOSTIC_CODES["MEDICINE_NOT_IDENTIFIED"])

        return {
            "item": m,
            "db_med": best_med,
            "brand": brand,
            "generic": generic,
            "ingredients": ingredients,
            "strength": strength,
            "blob": f"{brand} {generic} {ingredients} {raw_name} {' '.join(substances)}".lower(),
            "active_substances": substances,
            "is_combination": res.get("is_combination", False) or len(substances) > 1,
            "is_unidentified": is_unidentified,
            "diagnostic_code": diag_code,
            "diagnostic": diag_obj,
            "completeness_score": res.get("completeness_score", 1.0 if not is_unidentified else 0.0),
            "candidate_matches": res.get("candidate_matches", [])
        }

    @classmethod
    def analyze_multiple_medicines_compatibility(
        cls,
        db: Session,
        req: MultiMedicineCheckRequest
    ) -> MultiMedicineReportResponse:
        """
        Multiple Medicine Compatibility Engine.
        Analyses every relevant pair in an N-medicine regimen across all active constituents,
        multi-drug (3+) syndromes (Triple Whammy, Serotonin Syndrome, QT Prolongation, CNS Depression, Bleeding),
        therapeutic duplications, duplicate active ingredients, drug-disease contraindications, and drug-allergy warnings.
        Supports 7 Indian languages: English, Kannada, Hindi, Malayalam, Tamil, Telugu, Marathi.
        """
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        lang = (req.language or "en").lower()

        disclaimer = (
            "MANDATORY CLINICAL SAFETY NOTICE: PharmIntel Multiple Medicine Compatibility Checker is an advanced "
            "clinical decision-support system. It does NOT guarantee that any combination of medicines is 100% safe, "
            "nor does it replace individualized medical diagnosis or prescription. Never stop or modify your prescribed "
            "medications without direct evaluation by your treating physician or a licensed pharmacist."
        )

        patient_conditions = [c.title() for c in (req.health_profile.medical_conditions if req.health_profile and req.health_profile.medical_conditions else [])]
        patient_allergies = [a.title() for a in (req.health_profile.allergies if req.health_profile and req.health_profile.allergies else [])]
        patient_name = (getattr(req, "patient_name", None) or (req.health_profile.patient_name if req.health_profile else None) or "").strip() or None

        med_items = req.medicines or []
        valid_items = [m for m in med_items if (m.medicine_name or m.brand_name or "").strip()]

        # Handle Empty Inputs Gracefully
        if not valid_items:
            empty_msg = {
                "en": "No medicines were entered for safety analysis. Please search and add your medicines above to check for interactions, contraindications, and allergy conflicts.",
                "kn": "ಸುರಕ್ಷತಾ ವಿಶ್ಲೇಷಣೆಗಾಗಿ ಯಾವುದೇ ಔಷಧಗಳನ್ನು ನಮೂದಿಸಲಾಗಿಲ್ಲ. ಔಷಧಗಳ ಹೊಂದಾಣಿಕೆ ಮತ್ತು ಅಡ್ಡಪರಿಣಾಮಗಳನ್ನು ಪರೀಕ್ಷಿಸಲು ದಯವಿಟ್ಟು ಮೇಲಿನ ಹುಡುಕಾಟ ಪೆಟ್ಟಿಗೆಯಲ್ಲಿ ನಿಮ್ಮ ಔಷಧಗಳನ್ನು ಸೇರಿಸಿ.",
                "hi": "सुरक्षा विश्लेषण के लिए कोई दवा दर्ज नहीं की गई है। कृपया परस्पर प्रभाव और एलर्जी की जांच के लिए ऊपर अपनी दवाएं खोजें और जोड़ें।",
                "ml": "സുരക്ഷാ പരിശോധനയ്ക്കായി മരുന്നുകളൊന്നും നൽകിയിട്ടില്ല. ദയവായി മരുന്നുകൾ ചേർക്കുക.",
                "ta": "மருந்து பாதுகாப்பு பகுப்பாய்விற்கு எந்த மருந்தும் உள்ளிடப்படவில்லை. தயவுசெய்து உங்கள் மருந்துகளை மேலே சேர்க்கவும்.",
                "te": "భద్రతా విశ్లేషణ కోసం ఎటువంటి మందులు నమోదు చేయబడలేదు. దయచేసి పైన మీ మందులను శోధించి జోడించండి.",
                "mr": "सुरक्षा विश्लेषणासाठी कोणतीही औषधे प्रविष्ट केलेली नाहीत. कृपया परस्पर परिणाम तपासण्यासाठी वरील चौकटीत औषधे जोडा."
            }.get(lang, "No medicines were entered for safety analysis. Please search and add your medicines above.")

            return MultiMedicineReportResponse(
                assessment_timestamp=now_str,
                patient_name=patient_name,
                total_medicines_analyzed=0,
                overall_status="GREY",
                overall_status_label="GREY – No Medicines Entered",
                summary_headline="Please Enter at Least One Medicine to Check Compatibility",
                language=lang,
                total_interactions_identified=0,
                serious_potential_interactions=0,
                caution_warnings=0,
                safe_combinations=0,
                duplicate_medicines_count=0,
                missing_information_count=0,
                interaction_table=[],
                what_does_this_mean=empty_msg,
                why_they_interact="Drug interaction analysis requires medication names to evaluate pharmacological compatibility.",
                what_could_happen="Unchecked medication combinations can result in unmonitored drug-drug interactions.",
                how_conditions_affect_risk="Patient health conditions and allergies can only be assessed once active medicines are provided.",
                what_to_discuss_with_doctor=["What medicines am I currently taking?", "Are there any contraindications with my medical history?"],
                action_guidance="Please enter your prescribed or over-the-counter medicines into the search fields above and click 'CHECK ALL MEDICINE INTERACTIONS'.",
                action_bullets=[
                    "Enter medicine names in the search boxes above.",
                    "Select from suggestions or enter manually.",
                    "Click 'CHECK ALL MEDICINE INTERACTIONS'."
                ],
                missing_information=["No medicines provided in the request."],
                unidentified_medicines=[],
                patient_conditions_evaluated=patient_conditions,
                allergies_evaluated=patient_allergies,
                medicines_analyzed=[],
                diagnostics_summary=[],
                candidate_selections_needed=[],
                therapeutic_duplications_count=0,
                disclaimer=disclaimer
            )

        resolved_meds = []
        missing_info_list = []
        unidentified_meds = []
        diagnostics_summary = []
        candidate_selections_needed = []

        # 1. Resolve metadata for each medicine in list
        for m in valid_items:
            res = cls._resolve_medicine_entry(db, m)
            raw_input_name = (m.medicine_name or m.brand_name or res["brand"]).strip()

            if res["is_unidentified"]:
                unidentified_meds.append(raw_input_name)
                missing_info_list.append(f"Chemical monograph for '{raw_input_name}' unverified in CDSCO/WHO compendia.")

            diag_code = res.get("diagnostic_code") or ("VERIFIED_COMPLETE" if not res["is_unidentified"] else "MEDICINE_NOT_IDENTIFIED")
            diag_obj = res.get("diagnostic") or DIAGNOSTIC_CODES.get(diag_code, {
                "code": diag_code,
                "label": diag_code.replace("_", " ").title(),
                "description": f"Diagnostic status for {res['brand']}."
            })

            diagnostics_summary.append({
                "medicine_name": res["brand"],
                "raw_input": raw_input_name,
                "diagnostic_code": diag_code,
                "diagnostic_label": diag_obj.get("label", diag_code),
                "description": diag_obj.get("description", ""),
                "completeness_score": res.get("completeness_score", 1.0 if not res["is_unidentified"] else 0.0),
                "is_unidentified": res["is_unidentified"],
                "has_ambiguity": bool(res.get("candidate_matches"))
            })

            if res.get("candidate_matches"):
                candidate_selections_needed.append({
                    "query": raw_input_name,
                    "candidates": res["candidate_matches"]
                })

            resolved_meds.append(res)

        table_rows: List[MultiInteractionTableRow] = []
        row_id_counter = 1
        duplicate_count = 0
        therapeutic_dup_count = 0
        num_meds = len(resolved_meds)

        # 2. Pairwise Analysis (N * (N-1) / 2 pairs)
        if num_meds >= 2:
            for i in range(num_meds):
                for j in range(i + 1, num_meds):
                    med1 = resolved_meds[i]
                    med2 = resolved_meds[j]

                    # 2A. Duplicate Active Ingredients
                    matched_subs = []
                    for s1 in med1["active_substances"]:
                        s1_norm = re.sub(r"[^a-zA-Z]", "", s1).lower()
                        for s2 in med2["active_substances"]:
                            s2_norm = re.sub(r"[^a-zA-Z]", "", s2).lower()
                            if s1_norm and s2_norm and (s1_norm == s2_norm or s1_norm in s2_norm or s2_norm in s1_norm):
                                if len(s1_norm) >= 4 and len(s2_norm) >= 4:
                                    matched_subs.append(s1.title())

                    if matched_subs:
                        duplicate_count += 1
                        matched_chem = matched_subs[0]

                        dup_expl = {
                            "en": f"DUPLICATE ACTIVE INGREDIENT: Both '{med1['brand']}' and '{med2['brand']}' contain '{matched_chem}'. Taking both simultaneously may cause accidental double-dosing, toxic organ accumulation, and severe adverse effects.",
                            "kn": f"ನಕಲಿ ಸಕ್ರಿಯ ಅಂಶ: '{med1['brand']}' ಮತ್ತು '{med2['brand']}' ಎರಡರಲ್ಲೂ '{matched_chem}' ಇದೆ. ಎರಡನ್ನೂ ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಂಡರೆ ಅತಿಯಾದ ಪ್ರಮಾಣ (Overdose) ಮತ್ತು ವಿಷತ್ವ ಉಂಟಾಗುವ ಅಪಾಯವಿದೆ.",
                            "hi": f"समान सक्रिय घटक: '{med1['brand']}' और '{med2['brand']}' दोनों में '{matched_chem}' शामिल है। दोनों को एक साथ लेने से ओवरडोज और विषाक्तता का खतरा है।",
                            "ml": f"ഇരട്ട ഘടകം: '{med1['brand']}', '{med2['brand']}' എന്നിവ രണ്ടിലും '{matched_chem}' അടങ്ങിയിരിക്കുന്നു. ഇത് അമിത അളവിനും പാർശ്വഫലങ്ങൾക്കും കാരണമാകും.",
                            "ta": f"ஒரே மூலக்கூறு: '{med1['brand']}' மற்றும் '{med2['brand']}' இரண்டிலும் '{matched_chem}' உள்ளது. இரண்டையும் ஒன்றாக உட்கொள்வது அதிகப்படியான நச்சுத்தன்மையை உண்டாக்கும்.",
                            "te": f"ఒకే రసాయన పదార్థం: '{med1['brand']}' మరియు '{med2['brand']}' రెండింటిలోనూ '{matched_chem}' ఉంది. రెండూ కలిపి తీసుకుంటే ఓవర్‌డోస్ మరియు విషపూరితమయ్యే ప్రమాదం ఉంది.",
                            "mr": f"समान घटक: '{med1['brand']}' आणि '{med2['brand']}' दोघांमध्येही '{matched_chem}' आहे. यामुळे ओव्हरडोज आणि विषबाधा होण्याचा गंभीर धोका आहे."
                        }.get(lang, f"Both contain '{matched_chem}'. Risk of toxic overdose.")

                        table_rows.append(MultiInteractionTableRow(
                            id=f"DDI-{row_id_counter}",
                            medicines_involved=[med1["brand"], med2["brand"]],
                            interaction_title=f"Duplicate Active Ingredient ({matched_chem})",
                            severity="RED",
                            severity_label="High Risk (Duplicate)",
                            explanation=dup_expl,
                            clinical_mechanism=f"Therapeutic duplication: simultaneous intake of identical chemical substance ({matched_chem}).",
                            clinical_consequences="Dose-dependent adverse toxicity, organ overload, and elevated drug plasma concentrations.",
                            recommended_action=f"Do NOT take '{med1['brand']}' and '{med2['brand']}' concurrently without explicit prescriber confirmation.",
                            evidence_source="CDSCO / WHO Safe Medication Practice Guidelines",
                            ml_predicted=False
                        ))
                        row_id_counter += 1

                    # 2B. Therapeutic Duplication (Same pharmacological drug class)
                    for class_name, drugs_in_class in cls.THERAPEUTIC_CLASSES.items():
                        has_m1 = any(k in med1["blob"] for k in drugs_in_class)
                        has_m2 = any(k in med2["blob"] for k in drugs_in_class)
                        if has_m1 and has_m2 and not matched_subs:
                            therapeutic_dup_count += 1
                            tdup_expl = {
                                "en": f"THERAPEUTIC DUPLICATION: Both '{med1['brand']}' and '{med2['brand']}' belong to the {class_name} class. Co-prescribing two drugs in the same class rarely provides additive therapeutic benefit and significantly multiplies adverse reaction rates.",
                                "kn": f"ಔಷಧ ವರ್ಗ ನಕಲು: '{med1['brand']}' ಮತ್ತು '{med2['brand']}' ಎರಡೂ {class_name} ವರ್ಗಕ್ಕೆ ಸೇರಿವೆ. ಒಂದೇ ವರ್ಗದ ಎರಡು ಔಷಧಗಳನ್ನು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳುವುದು ಅಡ್ಡಪರಿಣಾಮಗಳನ್ನು ಹೆಚ್ಚಿಸುತ್ತದೆ.",
                                "hi": f"चिकित्सीय दोहराव: '{med1['brand']}' और '{med2['brand']}' दोनों {class_name} वर्ग से संबंधित हैं। एक ही वर्ग की दो दवाएं लेने से दुष्प्रभाव बढ़ जाते हैं।",
                                "ml": f"ഒരേ മരുന്ന് വിഭാഗം: '{med1['brand']}', '{med2['brand']}' എന്നിവ രണ്ടും {class_name} വിഭാഗത്തിൽപ്പെടുന്നു. ഇത് പാർശ്വഫലങ്ങൾ വർദ്ധിപ്പിക്കും.",
                                "ta": f"ஒரே சிகிச்சை வகை: '{med1['brand']}' மற்றும் '{med2['brand']}' இரண்டும் {class_name} வகையைச் சேர்ந்தவை. பக்கவிளைவுகள் அதிகரிக்கும்.",
                                "te": f"చికిత్సా పునరావృతం: '{med1['brand']}' మరియు '{med2['brand']}' రెండూ {class_name} వర్గానికి చెందినవి. ఇది దుష్ప్రభావాల ప్రమాదాన్ని పెంచుతుంది.",
                                "mr": f"समान औषध वर्ग: '{med1['brand']}' आणि '{med2['brand']}' दोघेही {class_name} वर्गातील आहेत. यामुळे दुष्परिणाम वाढतात."
                            }.get(lang, f"Both medicines belong to {class_name}. Multiplies side effects.")

                            table_rows.append(MultiInteractionTableRow(
                                id=f"DDI-{row_id_counter}",
                                medicines_involved=[med1["brand"], med2["brand"]],
                                interaction_title=f"Therapeutic Duplication: {class_name}",
                                severity="RED" if class_name in ["HMG-CoA Reductase Inhibitor (Statin)", "Beta-Adrenoceptor Blocker", "Non-Steroidal Anti-inflammatory Drug (NSAID)"] else "YELLOW",
                                severity_label="High Risk (Therapeutic Duplication)" if class_name in ["HMG-CoA Reductase Inhibitor (Statin)", "Beta-Adrenoceptor Blocker", "Non-Steroidal Anti-inflammatory Drug (NSAID)"] else "Caution (Class Duplication)",
                                explanation=tdup_expl,
                                clinical_mechanism=f"Redundant receptor saturation or metabolic pathway competition within {class_name} class.",
                                clinical_consequences="Elevated toxicity risks without proportional therapeutic advantage.",
                                recommended_action="Consult your physician to determine if both medications are intentionally prescribed or if one should be deprescribed.",
                                evidence_source="WHO Guide to Good Prescribing / BNF 86",
                                ml_predicted=False
                            ))
                            row_id_counter += 1
                            break

                    # 2C. Multi-Constituent Pairwise Interaction Checking
                    # Evaluate all pairs of active substances and names across med1 and med2
                    tested_pairs = set()
                    pair_found = False

                    all_s1 = med1["active_substances"] + [med1["generic"], med1["brand"]]
                    all_s2 = med2["active_substances"] + [med2["generic"], med2["brand"]]

                    for s1 in all_s1:
                        if pair_found:
                            break
                        for s2 in all_s2:
                            pk = tuple(sorted([s1.lower().strip(), s2.lower().strip()]))
                            if pk in tested_pairs:
                                continue
                            tested_pairs.add(pk)

                            rule = DDILayer1Service.check_pair(db, s1, s2)
                            if rule:
                                sev = "RED" if rule.severity in ["Contraindicated", "Major"] else "YELLOW"
                                sev_label = "High Risk (Contraindicated)" if rule.severity == "Contraindicated" else (
                                    "High Risk (Major)" if rule.severity == "Major" else "Moderate Risk (Caution)"
                                )

                                plain_expl = {
                                    "en": f"CLINICAL INTERACTION: '{med1['brand']}' interacts with '{med2['brand']}' (via {s1} + {s2}). Clinical consequence: {rule.clinical_consequences}.",
                                    "kn": f"ಔಷಧ ಪ್ರತಿಕ್ರಿಯೆ: '{med1['brand']}' ಮತ್ತು '{med2['brand']}' ಪರಸ್ಪರ ತೀವ್ರವಾಗಿ ವರ್ತಿಸುತ್ತವೆ ({s1} + {s2}). ಪರಿಣಾಮ: {rule.clinical_consequences}.",
                                    "hi": f"दवा परस्पर प्रभाव: '{med1['brand']}' और '{med2['brand']}' एक साथ लेने पर दुष्प्रभाव डाल सकती हैं ({s1} + {s2})। प्रभाव: {rule.clinical_consequences}।",
                                    "ml": f"മരുന്ന് പ്രതിപ്രവർത്തനം: '{med1['brand']}', '{med2['brand']}' എന്നിവ ഒരുമിച്ച് കഴിക്കുന്നത് പാർശ്വഫലങ്ങൾക്ക് കാരണമാകുന്നു. കാരണം: {rule.clinical_consequences}.",
                                    "ta": f"மருந்து எதிர்வினை: '{med1['brand']}' மற்றும் '{med2['brand']}' இரண்டும் ஒன்றோடொன்று முரண்படுகின்றன. விளைவு: {rule.clinical_consequences}.",
                                    "te": f"మందుల పరస్పర ప్రభావం: '{med1['brand']}' మరియు '{med2['brand']}' కలిపి తీసుకుంటే దుష్ప్రభావాలు రావచ్చు. ప్రభావం: {rule.clinical_consequences}.",
                                    "mr": f"औषध परस्पर परिणाम: '{med1['brand']}' आणि '{med2['brand']}' एकत्र घेतल्यास गंभीर परिणाम होऊ शकतात. परिणाम: {rule.clinical_consequences}."
                                }.get(lang, f"Interaction between '{med1['brand']}' and '{med2['brand']}': {rule.clinical_consequences}")

                                table_rows.append(MultiInteractionTableRow(
                                    id=f"DDI-{row_id_counter}",
                                    medicines_involved=[med1["brand"], med2["brand"]],
                                    interaction_title=f"{rule.severity} Interaction: {med1['brand']} + {med2['brand']}",
                                    severity=sev,
                                    severity_label=sev_label,
                                    explanation=plain_expl,
                                    clinical_mechanism=rule.mechanism,
                                    clinical_consequences=rule.clinical_consequences,
                                    recommended_action="Speak with your doctor or pharmacist before taking these medicines together. Do not independently stop prescribed therapy.",
                                    evidence_source=rule.source,
                                    ml_predicted=False
                                ))
                                row_id_counter += 1
                                pair_found = True
                                break

                    if not pair_found and req.enable_ml_prediction and med1["db_med"] and med2["db_med"]:
                        # Layer 2 HYBRIDGNN Prediction
                        try:
                            gnn = DDILayer2Service.predict_pair_ml(db, med1["db_med"], med2["db_med"])
                            if gnn and gnn.get("severity") in ["Contraindicated", "Major"] and gnn.get("confidence", 0) > 0.65:
                                table_rows.append(MultiInteractionTableRow(
                                    id=f"DDI-{row_id_counter}",
                                    medicines_involved=[med1["brand"], med2["brand"]],
                                    interaction_title=f"Experimental Model Prediction: {med1['brand']} + {med2['brand']} ({gnn['severity']})",
                                    severity="YELLOW",
                                    severity_label="Caution (GNN Prediction)",
                                    explanation=f"Research Model ({gnn['confidence']*100:.0f}% confidence) predicts potential {gnn['severity'].lower()} interaction.",
                                    clinical_mechanism=gnn.get("mechanism") or "Biological graph topological structural clash.",
                                    clinical_consequences=gnn.get("clinical_consequences") or "Potential pharmacodynamic competition.",
                                    recommended_action="Consult a pharmacist to review this potential interaction prior to co-administration.",
                                    evidence_source="PHARMINTEL-HYBRIDGNN (Heterogeneous Graph Transformer)",
                                    ml_predicted=True
                                ))
                                row_id_counter += 1
                        except Exception:
                            pass

        # 3. Multi-Drug (3+ Medicines) Regimen Syndromes
        if num_meds >= 3:
            all_blobs = " ".join([m["blob"] for m in resolved_meds]).lower()

            # 3A. Triple Whammy: ACEi/ARB + Diuretic + NSAID
            has_ace_arb = any(k in all_blobs for k in ["losartan", "ramipril", "telmisartan", "enalapril", "lisinopril", "valsartan", "olmesartan", "candesartan"])
            has_diuretic = any(k in all_blobs for k in ["hydrochlorothiazide", "furosemide", "torsemide", "chlorthalidone", "indapamide", "spironolactone"])
            has_nsaid = any(k in all_blobs for k in ["ibuprofen", "diclofenac", "aceclofenac", "naproxen", "piroxicam", "etoricoxib", "celecoxib", "mefenamic", "ketorolac", "nimesulide"])

            if has_ace_arb and has_diuretic and has_nsaid:
                involved = []
                for m in resolved_meds:
                    b = m["blob"]
                    if any(k in b for k in ["losartan", "ramipril", "telmisartan", "enalapril", "lisinopril", "valsartan", "olmesartan", "candesartan"]):
                        involved.append(m["brand"])
                    elif any(k in b for k in ["hydrochlorothiazide", "furosemide", "torsemide", "chlorthalidone", "indapamide", "spironolactone"]):
                        involved.append(m["brand"])
                    elif any(k in b for k in ["ibuprofen", "diclofenac", "aceclofenac", "naproxen", "piroxicam", "etoricoxib", "celecoxib", "mefenamic", "ketorolac", "nimesulide"]):
                        involved.append(m["brand"])

                tw_expl = {
                    "en": "TRIPLE WHAMMY CLINICAL RISK: You have combined an ACE-Inhibitor/ARB (BP medicine) + Diuretic (water pill) + NSAID (painkiller). This 3-drug combination causes acute reduction in glomerular perfusion pressure, leading to sudden acute kidney injury and severe hyperkalemia.",
                    "kn": "ಟ್ರಿಪಲ್ ವ್ಹಾಮಿ ಗಂಭೀರ ಅಪಾಯ: ನೀವು ರಕ್ತದೊತ್ತಡ ಔಷಧ (ACEi/ARB) + ಮೂತ್ರವರ್ಧಕ (Diuretic) + ನೋವುನಿವಾರಕ (NSAID) ಮೂರನ್ನೂ ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಂಡಿದ್ದೀರಿ. ಇದು ಕಿಡ್ನಿಯ ರಕ್ತ ಪರಿಚಲನೆಯನ್ನು ತೀವ್ರವಾಗಿ ಕುಗ್ಗಿಸಿ ಹಠಾತ್ ಕಿಡ್ನಿ ವೈಫಲ್ಯಕ್ಕೆ ಕಾರಣವಾಗಬಹುದು.",
                    "hi": "ट्रिपल व्हैमी गंभीर जोखिम: आपने बीपी की दवा (ACEi/ARB) + मूत्रवर्धक (Diuretic) + दर्द निवारक (NSAID) तीनों को मिलाया है। यह 3-दवा संयोजन गुर्दे (Kidney) के रक्त प्रवाह को तेजी से कम करके अचानक गुर्दे की विफलता (Acute Kidney Injury) का कारण बन सकता है।",
                    "ml": "ട്രിപ്പിൾ വാമി അപകടം: രക്തസമ്മർദ്ദ മരുന്ന് + ഡൈയൂററ്റിക് + വേദനസംഹാരി എന്നിവയുടെ സംയോജനം വൃക്കകളുടെ പ്രവർത്തനത്തെ പെട്ടെന്ന് തകരാറിലാക്കാം.",
                    "ta": "டிரிபிள் வாமி ஆபத்து: இரத்த அழுத்த மருந்து + சிறுநீர் பெருக்கி + வலி நிவாரணி ஆகிய மூன்று மருந்துகளின் கலவை சிறுநீரகத்தின் இரத்த ஓட்டத்தை முடக்கி திடீர் சிறுநீரக செயலிழப்பை ஏற்படுத்தலாம்.",
                    "te": "ట్రిపుల్ వామీ తీవ్ర ప్రమాదం: బీపీ మందు + మూత్రవిసర్జన మందు + పెయిన్‌కిల్లర్ మూడింటి కలయిక మూత్రపిండాల రక్తప్రసరణను దెబ్బతీసి ఆకస్మిక కిడ్నీ వైఫల్యానికి దారితీస్తుంది.",
                    "mr": "ट्रिपल व्हॅमी धोका: बीपीचे औषध + लघवीचे औषध + वेदनाशामक या तिन्हींचे एकत्रीकरण मूत्रपिंडाचा रक्तप्रवाह अचानक कमी करून किडनी फेल्युअरचा धोका निर्माण करते."
                }.get(lang, "Triple Whammy: ACEi/ARB + Diuretic + NSAID risks Acute Kidney Injury.")

                table_rows.append(MultiInteractionTableRow(
                    id=f"DDI-{row_id_counter}",
                    medicines_involved=list(dict.fromkeys(involved)) if involved else ["ACEi/ARB", "Diuretic", "NSAID"],
                    interaction_title="Triple Whammy Multi-Drug Syndrome (3+ Drugs)",
                    severity="RED",
                    severity_label="High Risk (Syndrome)",
                    explanation=tw_expl,
                    clinical_mechanism="Simultaneous afferent arteriolar constriction (NSAIDs), efferent arteriolar vasodilation (ACEi/ARB), and intravascular plasma volume reduction (Diuretic).",
                    clinical_consequences="Acute kidney failure, oliguria, fluid overload, severe hyperkalemia.",
                    recommended_action="Strictly avoid NSAIDs with this regimen. Consult your doctor immediately for renal-safe analgesia (e.g. Paracetamol).",
                    evidence_source="KDIGO Clinical Practice Guideline for Acute Kidney Injury / BNF 86",
                    ml_predicted=False
                ))
                row_id_counter += 1

            # 3B. Serotonin Syndrome: 2+ Serotonergic Medicines
            serotonergic_agents = ["sertraline", "escitalopram", "fluoxetine", "paroxetine", "citalopram", "duloxetine", "venlafaxine", "tramadol", "linezolid", "sumatriptan", "dextromethorphan"]
            found_serotonin = [m["brand"] for m in resolved_meds if any(k in m["blob"] for k in serotonergic_agents)]
            if len(dict.fromkeys(found_serotonin)) >= 2:
                ss_expl = {
                    "en": f"SEROTONIN SYNDROME ALERT: Your regimen combines multiple serotonergic agents ({', '.join(dict.fromkeys(found_serotonin))}). Excessive synaptic serotonin accumulation can precipitate life-threatening Serotonin Syndrome.",
                    "kn": f"ಸೆರೋಟೋನಿನ್ ಸಿಂಡ್ರೋಮ್ ಎಚ್ಚರಿಕೆ: ನಿಮ್ಮ ಔಷಧ ಪಟ್ಟಿಯಲ್ಲಿ ಬಹು ಸೆರೋಟೋನೆರ್ಜಿಕ್ ಔಷಧಗಳಿವೆ ({', '.join(dict.fromkeys(found_serotonin))}). ಇದು ಜೀವಕ್ಕೆ ಅಪಾಯಕಾರಿಯಾದ ಸೆರೋಟೋನಿನ್ ಸಿಂಡ್ರೋಮ್‌ಗೆ ಕಾರಣವಾಗಬಹುದು.",
                    "hi": f"सेरोटोनिन सिंड्रोम चेतावनी: आपके संयोजन में एक से अधिक सेरोटोनर्जिक दवाएं ({', '.join(dict.fromkeys(found_serotonin))}) शामिल हैं, जो जानलेवा सेरोटोनिन सिंड्रोम का कारण बन सकती हैं।",
                    "ml": f"സെറോടോണിൻ സിൻഡ്രോം മുന്നറിയിപ്പ്: ഒന്നിലധികം സെറോടോണർജിക് മരുന്നുകൾ ഒരുമിച്ച് കഴിക്കുന്നത് ജീവന് തന്നെ അപകടകരമായ സെറോടോണിൻ സിൻഡ്രോമിന് കാരണമാകാം.",
                    "ta": f"செரோடோனின் நோய்க்குறி எச்சரிக்கை: உங்கள் மருந்துகளில் பல செரோடோனெர்ஜிக் மருந்துகள் உள்ளன, இது உயிருக்கு ஆபத்தான செரோடோனின் நோய்க்குறியை உண்டாக்கலாம்.",
                    "te": f"సెరోటోనిన్ సిండ్రోమ్ హెచ్చరిక: మీ మందులలో బహుళ సెరోటోనెర్జిక్ మందులు ఉన్నాయి, ఇది ప్రాణాంతక సెరోటోనిన్ సిండ్రోమ్‌కు కారణం కావచ్చు.",
                    "mr": f"सेरोटोनिन सिंड्रोम चेतावणी: तुमच्या संयोजनात एकापेक्षा जास्त सेरोटोनर्जिक औषधे आहेत, ज्यामुळे सेरोटोनिन सिंड्रोमचा धोका वाढतो."
                }.get(lang, "Multiple serotonergic agents risk Serotonin Syndrome.")

                table_rows.append(MultiInteractionTableRow(
                    id=f"DDI-{row_id_counter}",
                    medicines_involved=list(dict.fromkeys(found_serotonin)),
                    interaction_title="Serotonin Syndrome Hazard (3+ Drugs)",
                    severity="RED",
                    severity_label="High Risk (Syndrome)",
                    explanation=ss_expl,
                    clinical_mechanism="Synergistic elevation of intrasynaptic 5-HT concentrations via simultaneous reuptake inhibition and direct/indirect receptor agonism.",
                    clinical_consequences="Hyperthermia, neuromuscular excitation (clonus, hyperreflexia), autonomic instability, delirium, seizures.",
                    recommended_action="Do NOT take these medicines together without specialist psychiatric or neurological supervision. Seek immediate medical attention if agitation or tremors develop.",
                    evidence_source="FDA Drug Safety Alerts / American Psychiatric Association (APA)",
                    ml_predicted=False
                ))
                row_id_counter += 1

            # 3C. Additive QT Prolongation: 2+ QT Prolonging Medicines
            qt_prolonging_agents = ["azithromycin", "clarithromycin", "ciprofloxacin", "levofloxacin", "escitalopram", "citalopram", "ondansetron", "amiodarone", "haloperidol", "domperidone", "fluconazole"]
            found_qt = [m["brand"] for m in resolved_meds if any(k in m["blob"] for k in qt_prolonging_agents)]
            if len(dict.fromkeys(found_qt)) >= 2:
                qt_expl = {
                    "en": f"ADDITIVE QT PROLONGATION HAZARD: Multiple medications in your regimen ({', '.join(dict.fromkeys(found_qt))}) prolong the cardiac QT interval, significantly elevating the risk of fatal cardiac arrhythmias (Torsades de Pointes).",
                    "kn": f"ಹೃದಯ ಬಡಿತದ ವ್ಯತ್ಯಾಸದ ಅಪಾಯ (QT Prolongation): ನಿಮ್ಮ ಔಷಧಗಳಲ್ಲಿ ({', '.join(dict.fromkeys(found_qt))}) ಹೃದಯದ ಎಲೆಕ್ಟ್ರಿಕಲ್ ಸೈಕಲ್ ಅನ್ನು ವಿಳಂಬಗೊಳಿಸುವ ಅಂಶಗಳಿವೆ, ಇದು ಅಪಾಯಕಾರಿ ಅರಿಥ್ಮಿಯಾಕ್ಕೆ ಕಾರಣವಾಗಬಹುದು.",
                    "hi": f"हृदय ताल असामान्यता जोखिम (QT Prolongation): आपकी दवाओं ({', '.join(dict.fromkeys(found_qt))}) में हृदय की धड़कन को प्रभावित करने वाले घटक हैं, जिससे गंभीर अतालता (Arrhythmia) का खतरा बढ़ जाता है।",
                    "ml": f"ഹൃദയതാള വ്യതിയാന സാധ്യത: നിങ്ങളുടെ മരുന്നുകൾ ({', '.join(dict.fromkeys(found_qt))}) ഹൃദയമിടിപ്പിൽ അപകടകരമായ വ്യതിയാനങ്ങൾ ഉണ്ടാക്കാൻ സാധ്യതയുണ്ട്.",
                    "ta": f"இதய துடிப்பு ஒழுங்கின்மை ஆபத்து: உங்கள் மருந்துகளில் பல மருந்துகள் ({', '.join(dict.fromkeys(found_qt))}) இதய துடிப்பை தீவிரமாக பாதிக்கலாம்.",
                    "te": f"గుండె లయ సమస్యల ప్రమాదం (QT Prolongation): మీ మందులలో ({', '.join(dict.fromkeys(found_qt))}) గుండె లయను దెబ్బతీసే అంశాలు ఉన్నాయి.",
                    "mr": f"हृदयाचे ठोके अनियमित होण्याचा धोका: तुमच्या औषधांमध्ये ({', '.join(dict.fromkeys(found_qt))}) हृदयाच्या ठोक्यांवर गंभीर परिणाम करणारे घटक आहेत."
                }.get(lang, "Multiple QT-prolonging medicines elevate arrhythmia risk.")

                table_rows.append(MultiInteractionTableRow(
                    id=f"DDI-{row_id_counter}",
                    medicines_involved=list(dict.fromkeys(found_qt)),
                    interaction_title="Additive Cardiac QT Prolongation Risk (3+ Drugs)",
                    severity="RED",
                    severity_label="High Risk (Arrhythmia)",
                    explanation=qt_expl,
                    clinical_mechanism="Additive blockade of cardiac hERG / IKr potassium channels delaying myocardial repolarization.",
                    clinical_consequences="Prolonged QTc interval (> 500 ms), syncope, polymorphic ventricular tachycardia (Torsades de Pointes), sudden cardiac arrest.",
                    recommended_action="Baseline ECG and serum electrolyte monitoring (potassium, magnesium) required. Consult prescribing physician.",
                    evidence_source="CredibleMeds QT Drugs Database / AHA Scientific Statement",
                    ml_predicted=False
                ))
                row_id_counter += 1

            # 3D. Additive CNS Depression: 2+ CNS Depressants
            cns_depressants = ["clonazepam", "alprazolam", "diazepam", "lorazepam", "pregabalin", "gabapentin", "tramadol", "pheniramine", "hydroxyzine", "promethazine", "zolpidem"]
            found_cns = [m["brand"] for m in resolved_meds if any(k in m["blob"] for k in cns_depressants)]
            if len(dict.fromkeys(found_cns)) >= 2:
                has_opioid = any(k in all_blobs for k in ["tramadol", "codeine", "morphine"])
                cns_sev = "RED" if has_opioid else "YELLOW"
                cns_expl = {
                    "en": f"ADDITIVE CNS DEPRESSION ALERT: Combining multiple central nervous system depressants ({', '.join(dict.fromkeys(found_cns))}) dramatically enhances sedation, respiratory depression, and psychomotor impairment.",
                    "kn": f"ತೀವ್ರ ನಿದ್ರಾಜನಕ ಮತ್ತು ನಿಶ್ಚೇಷ್ಟತೆ ಎಚ್ಚರಿಕೆ: ಕೇಂದ್ರ ನರಮಂಡಲವನ್ನು ಕುಗ್ಗಿಸುವ ಔಷಧಗಳನ್ನು ({', '.join(dict.fromkeys(found_cns))}) ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಂಡರೆ ತೀವ್ರ ತೂಕಡಿಕೆ, ಉಸಿರಾಟದ ನಿಧಾನತೆ ಮತ್ತು ಆಯಾಸ ಉಂಟಾಗಬಹುದು.",
                    "hi": f"अत्यधिक बेहोशी और श्वसन अवसाद चेतावनी: एक से अधिक केंद्रीय तंत्रिका तंत्र शामक दवाएं ({', '.join(dict.fromkeys(found_cns))}) लेने से अत्यधिक नींद, चक्कर और सांस लेने में कठिनाई हो सकती है।",
                    "ml": f"അമിത മയക്ക സാധ്യത: നാഡീവ്യൂഹത്തെ ബാധിക്കുന്ന ഒന്നിലധികം മരുന്നുകൾ ({', '.join(dict.fromkeys(found_cns))}) അമിത ഉറക്കത്തിനും ശ്വാസതടസ്സത്തിനും കാരണമാകും.",
                    "ta": f"அதிகப்படியான மயக்க எச்சரிக்கை: பல மயக்க மருந்துகளை ({', '.join(dict.fromkeys(found_cns))}) ஒன்றாக உட்கொள்வது மூச்சுத்திணறல் மற்றும் கடுமையான தூக்கத்தை ஏற்படுத்தும்.",
                    "te": f"అధిక మత్తు మరియు శ్వాస సమస్యల హెచ్చరిక: నాడీ వ్యవస్థపై ప్రభావం చూపే మందులు ({', '.join(dict.fromkeys(found_cns))}) కలిపి తీసుకుంటే తీవ్రమైన మత్తు మరియు శ్వాస మందగించడం జరుగుతుంది.",
                    "mr": f"प्रचंड गुंगी आणि श्वसन मंदावण्याचा धोका: मज्जासंस्थेवर परिणाम करणारी अनेक औषधे ({', '.join(dict.fromkeys(found_cns))}) एकत्र घेतल्यास तीव्र गुंगी आणि श्वसनाचा त्रास होऊ शकतो."
                }.get(lang, "Additive CNS depression causes profound sedation and respiratory depression.")

                table_rows.append(MultiInteractionTableRow(
                    id=f"DDI-{row_id_counter}",
                    medicines_involved=list(dict.fromkeys(found_cns)),
                    interaction_title="Additive Central Nervous System Depression (3+ Drugs)",
                    severity=cns_sev,
                    severity_label="High Risk (CNS/Respiratory)" if cns_sev == "RED" else "Caution (CNS Sedation)",
                    explanation=cns_expl,
                    clinical_mechanism="Synergistic potentiation of inhibitory GABA-ergic transmission and suppression of brainstem respiratory drive.",
                    clinical_consequences="Profound lethargy, respiratory depression, ataxia, accidental falls, cognitive clouding, coma.",
                    recommended_action="Avoid driving or operating machinery. Discuss lower dose titration with your physician.",
                    evidence_source="FDA Drug Safety Communications / CDC Prescribing Guidelines",
                    ml_predicted=False
                ))
                row_id_counter += 1

            # 3E. Additive Antithrombotic + NSAID Bleeding
            blood_thinners = [m["brand"] for m in resolved_meds if any(k in m["blob"] for k in ["warfarin", "clopidogrel", "aspirin", "apixaban", "rivaroxaban", "dabigatran", "ticagrelor"])]
            if len(dict.fromkeys(blood_thinners)) >= 2 and has_nsaid:
                bleed_expl = {
                    "en": "MULTIPLE ANTITHROMBOTIC + NSAID BLEEDING HAZARD: You are combining multiple blood thinners with an anti-inflammatory painkiller, drastically elevating gastrointestinal ulceration and life-threatening internal hemorrhage risk.",
                    "kn": "ರಕ್ತಸ್ರಾವದ ಗಂಭೀರ ಅಪಾಯ: ನೀವು ರಕ್ತ ತೆಳುಗೊಳಿಸುವ ಔಷಧಗಳೊಂದಿಗೆ ನೋವುನಿವಾರಕವನ್ನು ಸಂಯೋಜಿಸಿದ್ದೀರಿ. ಇದು ಜಠರದಲ್ಲಿ ರಕ್ತಸ್ರಾವ ಮತ್ತು ಅಲ್ಸರ್ ಅಪಾಯವನ್ನು ತೀವ್ರವಾಗಿ ಹೆಚ್ಚಿಸುತ್ತದೆ.",
                    "hi": "गंभीर आंतरिक रक्तस्राव का खतरा: आप रक्त पतला करने वाली दवाओं के साथ दर्द निवारक दवा ले रहे हैं, जिससे पेट में अल्सर और आंतरिक रक्तस्राव का खतरा बहुत बढ़ जाता है।",
                    "ml": "രക്തസ്രാവ സാധ്യത: ഒന്നിലധികം രക്തം നേർപ്പിക്കുന്ന മരുന്നുകളും വേദനസംഹാരിയും ഒരുമിച്ച് കഴിക്കുന്നത് ആമാശയത്തിൽ രക്തസ്രാവത്തിന് കാരണമാകും.",
                    "ta": "இரத்தப்போக்கு ஆபத்து: இரத்தம் மெலிதாக்கும் மருந்துகளுடன் வலி நிவாரணியை உட்கொள்வது குடல் புண் மற்றும் தீவிர இரத்தப்போக்கை உண்டாக்கும்.",
                    "te": "రక్తస్రావ ప్రమాదం: రక్తం పలుచబడే మందులతో పాటు పెయిన్‌కిల్లర్ వాడటం వల్ల కడుపులో అల్సర్లు మరియు తీవ్ర రక్తస్రావం జరిగే ప్రమాదం ఉంది.",
                    "mr": "रक्तस्रावाचा धोका: रक्त पातळ करणाऱ्या औषधांसोबत वेदनाशामक घेतल्यास पोटात अल्सर आणि अंतर्गत रक्तस्रावाचा मोठा धोका संभवतो."
                }.get(lang, "Multiple blood thinners + NSAID increases bleeding hazard.")

                table_rows.append(MultiInteractionTableRow(
                    id=f"DDI-{row_id_counter}",
                    medicines_involved=list(dict.fromkeys(blood_thinners)) + ["NSAID Painkiller"],
                    interaction_title="Additive Antithrombotic Hemorrhage Hazard (3+ Drugs)",
                    severity="RED",
                    severity_label="High Risk (Bleeding)",
                    explanation=bleed_expl,
                    clinical_mechanism="Dual platelet blockade and secondary coagulation pathway inhibition plus NSAID-induced gastric cyclooxygenase inhibition.",
                    clinical_consequences="Severe upper gastrointestinal hemorrhage, hematemesis, melena, hemorrhagic stroke.",
                    recommended_action="Avoid NSAIDs. Consult your prescribing physician or cardiologist before taking any OTC pain reliever.",
                    evidence_source="American College of Cardiology (ACC) Guidelines / CHEST",
                    ml_predicted=False
                ))
                row_id_counter += 1

        # 4. Drug-to-Disease Contraindications (Evaluated for all medicines)
        if req.health_profile and req.health_profile.medical_conditions:
            conds = [c.lower() for c in req.health_profile.medical_conditions]
            for m in resolved_meds:
                for cond in conds:
                    for d_rule in cls.DISEASE_CONTRAINDICATION_RULES:
                        if any(c in cond for c in d_rule["condition_keywords"]):
                            if any(d in m["blob"] for d in d_rule["drug_keywords"]):
                                table_rows.append(MultiInteractionTableRow(
                                    id=f"DDI-{row_id_counter}",
                                    medicines_involved=[m["brand"], cond.title()],
                                    interaction_title=f"Drug-Disease Contraindication ({cond.title()})",
                                    severity=d_rule["severity"],
                                    severity_label="High Risk (Contraindication)" if d_rule["severity"] == "RED" else "Caution (Contraindication)",
                                    explanation=f"'{m['brand']}' conflicts with your recorded condition '{cond.title()}': {d_rule['plain']}",
                                    clinical_mechanism=d_rule["mechanism"],
                                    clinical_consequences=d_rule["consequences"],
                                    recommended_action=d_rule["action"],
                                    evidence_source=d_rule["source"],
                                    ml_predicted=False
                                ))
                                row_id_counter += 1

        # 5. Drug-to-Allergy Conflicts (Evaluated for all medicines)
        if req.health_profile and req.health_profile.allergies:
            algs = [a.lower() for a in req.health_profile.allergies]
            for m in resolved_meds:
                for alg in algs:
                    for a_rule in cls.ALLERGY_CLASSES:
                        if any(k in alg for k in a_rule["allergy_terms"]):
                            if any(d in m["blob"] for d in a_rule["matching_drugs"]):
                                table_rows.append(MultiInteractionTableRow(
                                    id=f"DDI-{row_id_counter}",
                                    medicines_involved=[m["brand"], alg.title()],
                                    interaction_title=f"Documented Allergy Conflict ({alg.title()})",
                                    severity="RED",
                                    severity_label="High Risk (Allergy)",
                                    explanation=f"ALLERGY WARNING: '{m['brand']}' conflicts with your recorded allergy to '{alg.title()}': {a_rule['plain']}",
                                    clinical_mechanism=a_rule["mechanism"],
                                    clinical_consequences=a_rule["consequences"],
                                    recommended_action=a_rule["action"],
                                    evidence_source=a_rule["source"],
                                    ml_predicted=False
                                ))
                                row_id_counter += 1

        # 6. Metrics & Overall Status Calculation
        red_count = sum(1 for r in table_rows if r.severity == "RED")
        yellow_count = sum(1 for r in table_rows if r.severity == "YELLOW")
        grey_count = len(unidentified_meds)

        if red_count > 0:
            overall_status = "RED"
            overall_label = "RED – Serious Potential Interaction Identified"
            summary_headline = f"Serious Potential Interaction Detected ({red_count} High-Risk Finding{'s' if red_count > 1 else ''})"
        elif yellow_count > 0:
            if grey_count > 0:
                overall_status = "GREY"
                overall_label = "GREY – Compatibility Analysis Incomplete Due to Unidentified Medicine"
                summary_headline = f"Compatibility Incomplete ({grey_count} Unverified Medicine{'s' if grey_count > 1 else ''}; {yellow_count} Precaution{'s' if yellow_count > 1 else ''})"
            else:
                overall_status = "YELLOW"
                overall_label = "YELLOW – Caution Required (Professional Review Advised)"
                summary_headline = f"Caution Advised ({yellow_count} Precaution{'s' if yellow_count > 1 else ''} Identified)"
        elif grey_count > 0 or len(candidate_selections_needed) > 0:
            overall_status = "GREY"
            overall_label = "GREY – Compatibility Analysis Incomplete Due to Unidentified Medicine"
            summary_headline = f"Compatibility Analysis Incomplete ({grey_count} Unverified Medicine{'s' if grey_count > 1 else ''})"
        else:
            overall_status = "GREEN"
            if num_meds == 1:
                overall_label = "GREEN – Compatible with Your Recorded Health Profile"
                summary_headline = f"'{resolved_meds[0]['brand']}' is Compatible with Your Recorded Health Profile"
            else:
                overall_label = "GREEN – No Known Interaction Identified in Available Sources"
                summary_headline = "No Known Adverse Drug Interactions Identified in Available Sources"

        # 7. Localized Patient Explanations (What Does This Mean For You?)
        meds_names_str = ", ".join([m["brand"] for m in resolved_meds])

        if overall_status == "RED":
            what_means = {
                "en": f"You added {num_meds} medicine(s) ({meds_names_str}). Our clinical intelligence engine identified {red_count} potentially serious interaction(s). Taking these medicines together may cause adverse clinical side effects such as acute drops in blood pressure, kidney function changes, bleeding, or duplicate overdoses.",
                "kn": f"ನೀವು {num_meds} ಔಷಧಗಳನ್ನು ({meds_names_str}) ಸೇರಿಸಿದ್ದೀರಿ. ನಮ್ಮ ಕ್ಲಿನಿಕಲ್ ಎಂಜಿನ್ {red_count} ಗಂಭೀರ ಅಪಾಯಗಳನ್ನು ಗುರುತಿಸಿದೆ. ಈ ಔಷಧಗಳನ್ನು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳುವುದರಿಂದ ರಕ್ತದೊತ್ತಡದಲ್ಲಿ ತೀವ್ರ ಕುಸಿತ, ಕಿಡ್ನಿ ತೊಂದರೆ, ರಕ್ತಸ್ರಾವ ಅಥವಾ ಅಡ್ಡಪರಿಣಾಮಗಳು ಉಂಟಾಗಬಹುದು.",
                "hi": f"आपने {num_meds} दवाएं ({meds_names_str}) जोड़ी हैं। हमारे क्लीनिकल इंटेलिजेंस इंजन ने {red_count} गंभीर संभावित परस्पर प्रभाव पाए हैं। इन दवाओं को एक साथ लेने से ब्लड प्रेशर में अचानक गिरावट, गुर्दे पर प्रभाव, रक्तस्राव या ओवरडोज का खतरा हो सकता है।",
                "ml": f"നിങ്ങൾ നൽകിയ {num_meds} മരുന്നുകളിൽ ({meds_names_str}) {red_count} ഗുരുതരമായ പ്രശ്നങ്ങൾ കണ്ടെത്തി. ഇവ ഒരുമിച്ച് കഴിക്കുന്നത് രക്തസമ്മർദ്ദം പെട്ടെന്ന് കുറയാനോ വൃക്കകളെ ബാധിക്കാനോ കാരണമായേക്കാം.",
                "ta": f"நீங்கள் உள்ளிட்ட {num_meds} மருந்துகளில் ({meds_names_str}) {red_count} தீவிர சாத்தியமான எதிர்வினைகள் கண்டறியப்பட்டுள்ளன. இவற்றை ஒன்றாக உட்கொள்வது இரத்த அழுத்தக் குறைவு, சிறுநீரகப் பாதிப்பு அல்லது இரத்தப்போக்கு அபாயத்தை ஏற்படுத்தலாம்.",
                "te": f"మీరు జోడించిన {num_meds} మందులలో ({meds_names_str}) {red_count} తీవ్రమైన ప్రమాదాలు గుర్తించబడ్డాయి. వీటిని కలిపి తీసుకోవడం వల్ల రక్తపోటు తగ్గడం, కిడ్నీ సమస్యలు లేదా ఇతర దుష్ప్రభావాలు రావచ్చు.",
                "mr": f"तुम्ही जोडलेल्या {num_meds} औषधांमध्ये ({meds_names_str}) {red_count} गंभीर परस्पर परिणाम आढळले आहेत. ही औषधे एकत्र घेतल्यास रक्तदाब कमी होणे, किडनीवर परिणाम किंवा अंतर्गत रक्तस्रावाचा धोका वाढू शकतो."
            }.get(lang, f"Serious interactions detected across {num_meds} medicines. Review findings before co-administration.")

            why_interact = {
                "en": "These medicines share competing metabolic clearance pathways or produce synergistic cardiovascular/renal effects that compound their risks when taken simultaneously.",
                "kn": "ಈ ಔಷಧಗಳು ಪರಸ್ಪರ ರಕ್ತ ಪರಿಚಲನೆ ಮತ್ತು ಕಿಡ್ನಿಯ ಕಾರ್ಯನಿರ್ವಹಣೆಯ ಮೇಲೆ ತೀವ್ರವಾಗಿ ಪ್ರಭಾವ ಬೀರುತ್ತವೆ, ಇದು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಂಡಾಗ ಅಪಾಯವನ್ನು ದ್ವಿಗುಣಗೊಳಿಸುತ್ತದೆ.",
                "hi": "ये दवाएं शरीर के चयापचय और रक्त वाहिकाओं पर एक साथ प्रभाव डालती हैं, जिससे इनका संयुक्त असर खतरनाक स्तर तक बढ़ जाता है।",
                "ml": "ഈ മരുന്നുകൾ ഒരുമിച്ച് കഴിക്കുമ്പോൾ ശരീരത്തിലെ ആഗിരണത്തെയും വൃക്കകളുടെ പ്രവർത്തനത്തെയും പ്രതികൂലമായി ബാധിക്കുന്നു.",
                "ta": "இந்த மருந்துகள் இரத்த நாளங்கள் மற்றும் சிறுநீரகத்தின் மீது ஒரே நேரத்தில் அழுத்தம் கொடுத்து பக்கவிளைவுகளை அதிகரிக்கின்றன.",
                "te": "ఈ మందులు శరీరంలో ఒకే విధమైన వ్యవస్థలపై పనిచేయడం వల్ల వీటి మిశ్రమ ప్రభావం మరింత ప్రమాదకరంగా మారుతుంది.",
                "mr": "ही औषधे शरीराच्या चयापचय प्रक्रियेवर आणि रक्तवाहिन्यांवर एकाच वेळी परिणाम करून धोका वाढवतात."
            }.get(lang, "Metabolic or synergistic pharmacodynamic conflict.")

            what_happen = {
                "en": "You could experience sudden dizziness upon standing, weakness, fluid retention, unexpected bleeding, or worsening of kidney and heart parameters.",
                "kn": "ನೀವು ಎದ್ದು ನಿಂತಾಗ ತಲೆತಿರುಗುವಿಕೆ, ದೌರ್ಬಲ್ಯ, ಅನಿರೀಕ್ಷಿತ ರಕ್ತಸ್ರಾವ ಅಥವಾ ಕಿಡ್ನಿ ಮತ್ತು ಹೃದಯದ ನಿಯತಾಂಕಗಳಲ್ಲಿ ವ್ಯತ್ಯಾಸಗಳನ್ನು ಅನುಭವಿಸಬಹುದು.",
                "hi": "आपको खड़े होने पर चक्कर आना, अत्यधिक कमजोरी, अवांछित रक्तस्राव या गुर्दे और हृदय से संबंधित समस्याएं हो सकती हैं।",
                "ml": "തലകറക്കം, അമിത ക്ഷീണം, അപ്രതീക്ഷിത രക്തസ്രാവം അല്ലെങ്കിൽ രക്തസമ്മർദ്ദത്തിലെ വലിയ വ്യതിയാനങ്ങൾ ഉണ്ടായേക്കാം.",
                "ta": "திடீர் தலைசுற்றல், சோர்வு, எதிர்பாராத இரத்தப்போக்கு அல்லது இரத்த அழுத்தத்தில் தீவிர மாறுதல்களை நீங்கள் உணரலாம்.",
                "te": "మీకు నిలబడినప్పుడు తలతిరగడం, తీవ్రమైన బలహీనత, ఊహించని రక్తస్రావం లేదా కిడ్నీ పనితీరులో మార్పులు రావచ్చు.",
                "mr": "उभे राहिल्यावर चक्कर येणे, प्रचंड थकवा, रक्तस्राव किंवा रक्तदाबातील तीव्र चढउतार जाणवू शकतात."
            }.get(lang, "Dizziness, hypotension, bleeding, or renal strain.")

            how_conditions = {
                "en": "Your recorded medical conditions directly influence these risks, requiring careful clinical monitoring.",
                "kn": "ನಿಮ್ಮ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಗಳು ಈ ಅಪಾಯಗಳ ತೀವ್ರತೆಯನ್ನು ಮತ್ತಷ್ಟು ಹೆಚ್ಚಿಸುತ್ತವೆ.",
                "hi": "आपकी पहले से मौजूद स्वास्थ्य समस्याएं इस जोखिम को और अधिक बढ़ा देती हैं।",
                "ml": "നിങ്ങളുടെ നിലവിലെ രോഗങ്ങൾ ഈ അപകടസാധ്യത ഇരട്ടിയാക്കുന്നു.",
                "ta": "உங்கள் தற்போதைய நோய்கள் இந்த ஆபத்தை மேலும் அதிகரிக்கின்றன.",
                "te": "మీకున్న ఆరోగ్య సమస్యలు ఈ ప్రమాదాన్ని మరింత పెంచుతాయి.",
                "mr": "तुमचे जुने आजार या धोक्याची तीव्रता अधिक वाढवतात."
            }.get(lang, "Underlying conditions amplify clinical sensitivity.")

            action_guidance = {
                "en": "Speak with your doctor or pharmacist before taking these medicines together. Do NOT independently alter or discontinue your prescribed medicines. Bring this report to your consultation.",
                "kn": "ಈ ಔಷಧಗಳನ್ನು ಒಟ್ಟಿಗೆ ತೆಗೆದುಕೊಳ್ಳುವ ಮೊದಲು ನಿಮ್ಮ ವೈದ್ಯರು ಅಥವಾ ಫಾರ್ಮಸಿಸ್ಟ್ ಸಲಹೆ ಪಡೆಯಿರಿ. ನಿಮ್ಮ ಔಷಧಗಳನ್ನು ಸ್ವತಂತ್ರವಾಗಿ ನಿಲ್ಲಿಸಬೇಡಿ ಅಥವಾ ಬದಲಾಯಿಸಬೇಡಿ.",
                "hi": "इन दवाओं को एक साथ लेने से पहले अपने डॉक्टर या फार्मासिस्ट से परामर्श लें। अपनी निर्धारित दवाओं को स्वतंत्र रूप से बंद या परिवर्तित न करें।",
                "ml": "ഈ മരുന്നുകൾ ഒരുമിച്ച് കഴിക്കുന്നതിന് മുൻപ് ഡോക്ടറുടെയോ ഫಾರ್മസിസ്റ്റിൻ്റെയോ ഉപദേശം തേടുക. മരുന്നുകൾ സ്വയം നിർത്തരുത്.",
                "ta": "இந்த மருந்துகளை ஒன்றாக உட்கொள்வதற்கு முன் மருத்துவரிடம் ஆலோசனை பெறவும். பரிந்துரைக்கப்பட்ட மருந்துகளைத் தானாக நிறுத்த வேண்டாம்.",
                "te": "ఈ మందులను కలిపి తీసుకునే ముందు డాక్టర్ లేదా ఫార్మసిస్ట్‌ను సంప్రదించండి. మీ మందులను సొంతంగా ఆపవద్దు లేదా మార్చవద్దు.",
                "mr": "ही औषधे एकत्र घेण्यापूर्वी डॉक्टरांचा सल्ला नक्की घ्या. सुरू असलेली औषधे परस्पर बंद किंवा बदलू नका."
            }.get(lang, "Consult healthcare provider before co-administration.")

        elif overall_status == "YELLOW":
            what_means = {
                "en": f"You added {num_meds} medicine(s) ({meds_names_str}). Our clinical engine identified {yellow_count} precaution(s). Co-administration may require dose adjustments or staggered administration times.",
                "kn": f"ನೀವು {num_meds} ಔಷಧಗಳನ್ನು ಸೇರಿಸಿದ್ದೀರಿ. {yellow_count} ಮುನ್ನೆಚ್ಚರಿಕೆಗಳನ್ನು ಗುರುತಿಸಲಾಗಿದೆ. ಇವುಗಳ ನಡುವೆ ಸಮಯದ ಅಂತರ ಅಥವಾ ಪ್ರಮಾಣದ ಹೊಂದಾಣಿಕೆ ಅಗತ್ಯವಾಗಬಹುದು.",
                "hi": f"आपने {num_meds} दवाएं जोड़ी हैं। {yellow_count} सावधानियों की पहचान की गई है। इन्हें लेने के समय में अंतर रखना आवश्यक हो सकता है।",
                "ml": f"നിങ്ങൾ ചേർത്ത {num_meds} മരുന്നുകളിൽ {yellow_count} ജാഗ്രതാ നിർദ്ദേശങ്ങൾ കണ്ടെത്തി. ഇവ കഴിക്കുന്ന സമയത്തിൽ മാറ്റം വരുത്തേണ്ടി വന്നേക്കാം.",
                "ta": f"நீங்கள் உள்ளிட்ட {num_meds} மருந்துகளில் {yellow_count} முன்னெச்சரிக்கைகள் உள்ளன. இவற்றை உட்கொள்ளும் நேரத்தில் இடைவெளி தேவைப்படலாம்.",
                "te": f"మీరు జోడించిన {num_meds} మందులలో {yellow_count} జాగ్రత్తలు సూచించబడ్డాయి. వీటిని వేర్వేరు సమయాల్లో తీసుకోవాల్సి రావచ్చు.",
                "mr": f"तुम्ही जोडलेल्या {num_meds} औषधांमध्ये {yellow_count} सावधगिरीच्या सूचना आहेत. यांच्या वेळेत अंतर ठेवणे गरजेचे असू शकते."
            }.get(lang, "Precautions identified. Dose adjustments or separated timing recommended.")

            why_interact = "Mild to moderate competitive pharmacokinetics or metabolic clearance interactions."
            what_happen = "May reduce medication effectiveness or slightly increase mild side effects."
            how_conditions = "Requires routine observation of vitals (blood pressure and glucose)."
            action_guidance = "Review administration schedule with your pharmacist to optimize therapeutic benefit."

        elif overall_status == "GREY":
            unverified_str = ", ".join(unidentified_meds) if unidentified_meds else "Unspecified strength or formulation"
            what_means = {
                "en": f"Compatibility analysis could not be fully guaranteed because {len(unidentified_meds)} medicine(s) ({unverified_str}) require verification. In adherence to strict patient safety standards, unverified combinations cannot be classified as safe.",
                "kn": f"{len(unidentified_meds)} ಔಷಧಗಳು ({unverified_str}) ಅಧಿಕೃತ ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳಲ್ಲಿ ಪತ್ತೆಯಾಗದ ಕಾರಣ ಸಂಪೂರ್ಣ ಹೊಂದಾಣಿಕೆ ಪರಿಶೀಲನೆ ಪೂರ್ಣಗೊಂಡಿಲ್ಲ. ದಯವಿಟ್ಟು ಔಷಧದ ಹೆಸರನ್ನು ಮರುಪರಿಶೀಲಿಸಿ.",
                "hi": f"संगतता विश्लेषण पूरी तरह से पूरा नहीं हो सका क्योंकि {len(unidentified_meds)} दवाएं ({unverified_str}) सत्यापित संदर्भों में नहीं मिलीं। कृपया वर्तनी की जांच करें।",
                "ml": f"{len(unidentified_meds)} മരുന്നുകൾ സ്ഥിരീകരിക്കാൻ കഴിയാത്തതിനാൽ വിശകലനം അപൂർണ്ണമാണ്. മരുന്നിൻ്റെ പേര് പരിശോധിക്കുക.",
                "ta": f"{len(unidentified_meds)} மருந்துகள் ({unverified_str}) மருத்துவ அமைப்பில் காணப்படாததால் பகுப்பாய்வு முழுமையடையவில்லை. எழுத்துப்பிழையை சரிபார்க்கவும்.",
                "te": f"{len(unidentified_meds)} మందులు ({unverified_str}) ధృవీకరించబడనందున విశ్లేషణ అసంపూర్తిగా ఉంది. దయచేసి పేరును సరిచూసుకోండి.",
                "mr": f"{len(unidentified_meds)} औषधे ({unverified_str}) नोंदणीत आढळली नाहीत. कृपया औषधांचे नाव तपासा."
            }.get(lang, f"Compatibility analysis incomplete due to unverified medicine(s): {unverified_str}.")

            why_interact = "Missing pharmacopeial monograph prevents authoritative binding and metabolic analysis."
            what_happen = "Potential unidentified interactions cannot be ruled out without verified chemical identity."
            how_conditions = "Ensure your healthcare provider reviews your complete medication package."
            action_guidance = "Verify the exact brand name and active salt composition on the medicine package and re-enter."

        else:
            if num_meds == 1:
                what_means = {
                    "en": f"'{resolved_meds[0]['brand']}' ({resolved_meds[0]['generic']}) was evaluated against your recorded medical conditions and allergies. No contraindications or safety conflicts were identified. Note: At least two medicines are required for drug-drug interaction checking. If you take other medicines or supplements, add them to perform a complete multi-drug check.",
                    "kn": f"'{resolved_meds[0]['brand']}' ({resolved_meds[0]['generic']}) ಅನ್ನು ನಿಮ್ಮ ದಾಖಲಾದ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಗಳು ಮತ್ತು ಅಲರ್ಜಿಗಳ ವಿರುದ್ಧ ಪರಿಶೀಲಿಸಲಾಗಿದೆ. ಯಾವುದೇ ಅಡ್ಡಪರಿಣಾಮ ಅಥವಾ ವಿರೋಧಾಭಾಸಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಗಮನಿಸಿ: ಔಷಧ-ಔಷಧ ಸಂವಹನವನ್ನು ಪರೀಕ್ಷಿಸಲು ಕನಿಷ್ಠ ಎರಡು ಔಷಧಗಳು ಬೇಕಾಗುತ್ತವೆ.",
                    "hi": f"'{resolved_meds[0]['brand']}' ({resolved_meds[0]['generic']}) का आपकी दर्ज स्वास्थ्य स्थितियों और एलर्जी के साथ मूल्यांकन किया गया है। कोई प्रतिकूल प्रभाव या मतभेद नहीं पाया गया। ध्यान दें: दवा परस्पर प्रभाव की जांच के लिए कम से कम दो दवाओं की आवश्यकता होती है।",
                    "ml": f"'{resolved_meds[0]['brand']}' നിങ്ങളുടെ രേഖപ്പെടുത്തിയ ആരോഗ്യസ്ഥിതികളുമായും അലർജികളുമായും പൊരുത്തപ്പെടുന്നതാണ്. മരുന്നുകൾ തമ്മിലുള്ള പ്രതിപ്രവർത്തനം പരിശോധിക്കാൻ കുറഞ്ഞത് രണ്ട് മരുന്നുകൾ ആവശ്യമാണ്.",
                    "ta": f"'{resolved_meds[0]['brand']}' உங்கள் பதிவுசெய்யப்பட்ட உடல்நல நிலைமைகள் மற்றும் ஒவ்வாமைகளுடன் சரிபார்க்கப்பட்டது. எந்த முரண்பாடுகளும் இல்லை. மருந்து எதிர்வினைகளை சரிபார்க்க குறைந்தபட்சம் இரண்டு மருந்துகள் தேவை.",
                    "te": f"'{resolved_meds[0]['brand']}' మీ నమోదు చేయబడిన ఆరోగ్య సమస్యలు మరియు అలెర్జీలతో సరిపోలుతుంది. మందుల పరస్పర చర్యలను తనిఖీ చేయడానికి కనీసం రెండు మందులు అవసరం.",
                    "mr": f"'{resolved_meds[0]['brand']}' ची तुमच्या नोंदणीकृत वैद्यकीय परिस्थिती आणि ॲलर्जींशी सुसंगतता तपासली गेली आहे. कोणताही प्रतिकूल परिणाम आढळला नाही. औषध परस्पर परिणाम तपासण्यासाठी किमान दोन औषधांची आवश्यकता असते."
                }.get(lang, f"'{resolved_meds[0]['brand']}' is compatible with your recorded health profile.")

                why_interact = "Single medicine assessed against health profile. No drug-drug interactions possible with only one drug."
                what_happen = "This medicine appears compatible with your health profile when taken as prescribed."
                how_conditions = "No documented contraindications found for your recorded health conditions."
                action_guidance = "Take strictly as prescribed. If you take other prescription drugs, OTC medicines, or herbal supplements, add them to verify complete compatibility."
            else:
                what_means = {
                    "en": f"Based on available verified medical compendia, no documented adverse interactions were identified across your {num_meds} medicine(s) ({meds_names_str}).",
                    "kn": f"ಲಭ್ಯವಿರುವ ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳ ಪ್ರಕಾರ, ನೀವು ನಮೂದಿಸಿದ {num_meds} ಔಷಧಗಳಲ್ಲಿ ({meds_names_str}) ಯಾವುದೇ ಹಾನಿಕಾರಕ ಪರಸ್ಪರ ಪ್ರತಿಕ್ರಿಯೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ.",
                    "hi": f"सत्यापित चिकित्सीय संदर्भों के अनुसार, आपकी {num_meds} दवाओं ({meds_names_str}) के बीच कोई ज्ञात प्रतिकूल परस्पर प्रभाव नहीं मिला।",
                    "ml": f"ലഭ്യമായ വിവരങ്ങൾ പ്രകാരം നിങ്ങളുടെ {num_meds} മരുന്നുകൾക്കിടയിൽ ({meds_names_str}) പാർശ്വഫലങ്ങളൊന്നും കണ്ടെത്തിയില്ല.",
                    "ta": f"கிடைக்கக்கூடிய மருத்துவ ஆதாரங்களின்படி, உங்கள் {num_meds} மருந்துகளுக்கு இடையே ({meds_names_str}) முரண்பாடுகள் எதுவும் இல்லை.",
                    "te": f"లభ్యమైన వైద్య ఆధారాల ప్రకారం, మీ {num_meds} మందుల మధ్య ({meds_names_str}) ఎటువంటి హానికరమైన ప్రభావాలు కనుగొనబడలేదు.",
                    "mr": f"वैद्यकीय नोंदींनुसार, तुमच्या {num_meds} औषधांमध्ये ({meds_names_str}) कोणतेही प्रतिकूल परिणाम आढळलेले नाहीत."
                }.get(lang, "No documented interactions identified in verified sources.")

                why_interact = "No known pharmacological binding clashes identified in authoritative monographs."
                what_happen = "Combination appears compatible according to current clinical guidelines."
                how_conditions = "Standard dosages appropriate for patient profile; maintain regular checkups."
                action_guidance = "Continue taking as prescribed by your doctor. Always inform your care team if adding new supplements or OTC medicines."

        doctor_questions = [
            f"Are these {num_meds} medicines completely safe to take together on my daily schedule?",
            "Do I need to space out the times when I take each of these tablets?",
            "What specific warning symptoms should I report to your clinic?",
            "Are there safer therapeutic alternatives for any of the flagged medications?"
        ]

        action_bullets = [
            "Do NOT independently discontinue or alter prescribed dosages.",
            "Share this clinical compatibility summary with your doctor or clinical pharmacist.",
            "Schedule your daily medication times according to pharmacist instructions.",
            "Report any dizziness, stomach pain, or unusual weakness immediately."
        ]

        return MultiMedicineReportResponse(
            assessment_timestamp=now_str,
            patient_name=patient_name,
            total_medicines_analyzed=num_meds,
            overall_status=overall_status,
            overall_status_label=overall_label,
            summary_headline=summary_headline,
            language=lang,
            total_interactions_identified=len(table_rows),
            serious_potential_interactions=red_count,
            caution_warnings=yellow_count,
            safe_combinations=max(0, (num_meds * (num_meds - 1) // 2) - len(table_rows)) if num_meds >= 2 else 0,
            duplicate_medicines_count=duplicate_count,
            missing_information_count=grey_count,
            interaction_table=table_rows,
            what_does_this_mean=what_means,
            why_they_interact=why_interact,
            what_could_happen=what_happen,
            how_conditions_affect_risk=how_conditions,
            what_to_discuss_with_doctor=doctor_questions,
            action_guidance=action_guidance,
            action_bullets=action_bullets,
            missing_information=missing_info_list,
            unidentified_medicines=unidentified_meds,
            patient_conditions_evaluated=patient_conditions,
            allergies_evaluated=patient_allergies,
            medicines_analyzed=[m["item"] for m in resolved_meds],
            diagnostics_summary=diagnostics_summary,
            candidate_selections_needed=candidate_selections_needed,
            therapeutic_duplications_count=therapeutic_dup_count,
            disclaimer=disclaimer
        )
'''

def apply():
    with open(SERVICE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    marker = "    @classmethod\n    def _resolve_medicine_entry(cls, db, m):"
    idx = content.find(marker)
    if idx == -1:
        print("ERROR: marker not found!")
        return False

    prefix = content[:idx]
    updated = prefix + NEW_RESOLVER_AND_ANALYSIS.rstrip() + "\n"

    with open(SERVICE_FILE, "w", encoding="utf-8") as f:
        f.write(updated)

    print("Successfully updated patient_safety_service.py!")
    return True

if __name__ == "__main__":
    apply()
