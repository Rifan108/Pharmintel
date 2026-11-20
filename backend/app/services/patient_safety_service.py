import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.medicine import Medicine, DrugInteraction
from app.models.patient_safety import (
    PatientHealthProfile, PatientCurrentMedication, PatientSafetyAssessmentRecord
)
from app.schemas.interaction import (
    HealthProfileInput, CurrentMedicationInput, ProposedMedicineInput,
    CheckRegimenCompatibilityRequest, InteractionFindingDetail,
    PersonalizedExplanation, FindingsCount, PatientSummarySchema,
    CompatibilityReportResponse, MultiMedicineCheckRequest,
    MultiMedicineReportResponse, MultiInteractionTableRow,
    MultiMedicineItem
)
from app.services.ddi_layer1_service import DDILayer1Service
from app.services.ddi_layer2_service import DDILayer2Service
from app.services.medicine_intelligence_service import MedicineIntelligenceService, DIAGNOSTIC_CODES

KNOWLEDGE_BASE_VERSION = "CDSCO/BNF-2026.1-GNN-v2"

class PatientSafetyIntelligenceService:
    """
    Patient-Specific Multi-Drug Safety Intelligence Engine.
    Executes whole-regimen clinical compatibility analysis across 6 dimensions:
    1. Drug-to-Drug Interaction (Curated BNF/FDA Layer 1 + GNN Layer 2)
    2. Drug-to-Disease Interaction (Clinical Contraindication Engine)
    3. Drug-to-Allergy Detection
    4. Duplicate Medicine & Active Ingredient Detection
    5. Multiple Medicine Regimen Risk (e.g. Triple Whammy, Additive Bleeding/Sedation)
    6. Patient-Specific Factors (Age, Renal/Hepatic Impairment)
    """

    # Clinical Drug-to-Disease rules
    DISEASE_CONTRAINDICATION_RULES = [
        # Diabetes
        {
            "condition_keywords": ["diabetes", "type 1 diabetes", "type 2 diabetes", "t2d", "t1d"],
            "drug_keywords": ["prednisolone", "dexamethasone", "hydrocortisone", "betamethasone", "methylprednisolone", "deflazacort"],
            "severity": "RED",
            "headline": "Corticosteroid-Induced Severe Hyperglycemia Alert",
            "plain": "Corticosteroids cause significant elevations in blood glucose by increasing insulin resistance. In patients with diabetes, this can trigger severe hyperglycemia (dangerously high blood sugar) requiring emergency insulin adjustment.",
            "mechanism": "Glucocorticoids stimulate hepatic gluconeogenesis and decrease peripheral glucose uptake in skeletal muscle and adipose tissue.",
            "consequences": "Marked worsening of glycemic control, diabetic ketoacidosis or hyperosmolar hyperglycemic state.",
            "action": "Do not start systemic steroids without consulting your prescribing diabetologist or endocrinologist. Frequent blood glucose monitoring is mandatory.",
            "source": "American Diabetes Association (ADA) Clinical Guidelines / BNF 86",
            "source_date": "2026-02-15"
        },
        {
            "condition_keywords": ["diabetes", "type 1 diabetes", "type 2 diabetes"],
            "drug_keywords": ["propranolol", "atenolol", "metoprolol", "carvedilol", "bisoprolol"],
            "severity": "YELLOW",
            "headline": "Beta-Blocker Masking of Hypoglycemia Warning",
            "plain": "Beta-blockers can conceal the classic early warning symptoms of dangerously low blood sugar (hypoglycemia)—such as shakiness, sweating, and rapid heartbeat.",
            "mechanism": "Non-cardioselective beta-adrenergic antagonism prevents sympathoadrenal reflex tachycardia and tremor during hypoglycemic episodes.",
            "consequences": "Delayed patient perception of neuroglycopenia, increasing risk of sudden hypoglycemic collapse.",
            "action": "Discuss with your doctor. Diaphoresis (sweating) usually remains unmasked, but frequent capillary blood glucose checking is advised.",
            "source": "British National Formulary (BNF 86)",
            "source_date": "2026-01-20"
        },
        # Heart Disease / Heart Failure
        {
            "condition_keywords": ["heart disease", "heart failure", "chf", "congestive heart failure", "cad", "coronary"],
            "drug_keywords": ["ibuprofen", "diclofenac", "naproxen", "etoricoxib", "celecoxib", "piroxicam", "indomethacin"],
            "severity": "RED",
            "headline": "NSAID Cardiovascular & Heart Failure Exacerbation Hazard",
            "plain": "Anti-inflammatory pain medicines (NSAIDs) cause fluid and salt retention and increase blood clotting tendency, significantly worsening heart failure and raising heart attack risk.",
            "mechanism": "Inhibition of renal COX-2 decreases vasodilatory prostaglandins (PGE2, PGI2), causing renal vasoconstriction, systemic vascular resistance increase, and blunting of diuretic/ACEi effects.",
            "consequences": "Acute decompensated heart failure, pulmonary edema, myocardial infarction, and cardiovascular hospitalization.",
            "action": "Avoid NSAIDs in heart failure. Paracetamol is generally the safer alternative for mild to moderate pain; consult your cardiologist before taking any pain reliever.",
            "source": "European Society of Cardiology (ESC) Heart Failure Guidelines / FDA Black Box",
            "source_date": "2026-03-01"
        },
        # High Blood Pressure / Hypertension
        {
            "condition_keywords": ["high blood pressure", "hypertension", "htn"],
            "drug_keywords": ["pseudoephedrine", "phenylephrine", "oxymetazoline"],
            "severity": "YELLOW",
            "headline": "Sympathomimetic Decongestant Blood Pressure Elevation",
            "plain": "Oral decongestants stimulate blood vessel constriction and can cause sharp spikes in blood pressure, opposing your blood pressure medications.",
            "mechanism": "Direct and indirect alpha-1 adrenergic receptor stimulation causes peripheral arteriolar vasoconstriction.",
            "consequences": "Hypertensive urgency or blunted response to antihypertensive regimen.",
            "action": "Use saline nasal sprays or consult your pharmacist for non-sympathomimetic alternatives for nasal congestion.",
            "source": "AHA/ACC Hypertension Clinical Compendium",
            "source_date": "2026-01-10"
        },
        {
            "condition_keywords": ["high blood pressure", "hypertension"],
            "drug_keywords": ["ibuprofen", "diclofenac", "naproxen", "etoricoxib"],
            "severity": "YELLOW",
            "headline": "NSAID Antagonism of Antihypertensive Therapy",
            "plain": "Regular use of NSAID painkillers elevates average blood pressure by 3 to 6 mmHg and blunts the effectiveness of ACE inhibitors, ARBs, and beta-blockers.",
            "mechanism": "Inhibition of renal prostaglandins reduces natriuresis and promotes salt and water retention.",
            "consequences": "Loss of blood pressure control and increased vascular resistance.",
            "action": "Limit NSAID use to lowest dose for shortest possible duration; monitor blood pressure closely.",
            "source": "Joint National Committee (JNC-8) / BNF",
            "source_date": "2026-02-01"
        },
        # Kidney Disease / Renal Impairment
        {
            "condition_keywords": ["kidney disease", "renal disease", "ckd", "renal failure", "impaired renal"],
            "drug_keywords": ["metformin"],
            "severity": "RED",
            "headline": "Metformin-Associated Lactic Acidosis Risk in Renal Impairment",
            "plain": "Metformin is eliminated almost exclusively by the kidneys. In kidney disease, metformin accumulates in the body, which can trigger lactic acidosis—a dangerous buildup of acid in the bloodstream.",
            "mechanism": "Accumulation of metformin inhibits mitochondrial respiratory chain complex I, driving anaerobic metabolism and systemic lactate overproduction.",
            "consequences": "Lactic acidosis (hypothermia, hypotension, resistant bradyarrhythmias, metabolic acidosis) with high mortality.",
            "action": "Contraindicated if eGFR is below 30 mL/min/1.73m²; dose reduction required if eGFR is between 30-45. Confirm renal function test (serum creatinine / eGFR) with your doctor.",
            "source": "FDA Safety Alert / CDSCO Drug Safety Gazette",
            "source_date": "2026-02-28"
        },
        {
            "condition_keywords": ["kidney disease", "renal disease", "ckd", "renal impairment"],
            "drug_keywords": ["ibuprofen", "diclofenac", "naproxen", "piroxicam", "ketorolac", "mefenamic"],
            "severity": "RED",
            "headline": "NSAID Hemodynamic Acute Kidney Injury Hazard",
            "plain": "In compromised kidneys, blood flow relies heavily on prostaglandins. NSAIDs shut off these protective prostaglandins, precipitating sudden kidney failure.",
            "mechanism": "Selective inhibition of cyclooxygenase blocks renal vasodilating prostaglandins (PGI2, PGE2), triggering afferent arteriolar constriction and drop in glomerular filtration rate (GFR).",
            "consequences": "Acute kidney injury (AKI), fluid overload, severe hyperkalemia.",
            "action": "Strictly avoid NSAIDs. Consult your nephrologist or physician for renal-safe analgesics.",
            "source": "KDIGO Clinical Practice Guideline for Acute Kidney Injury",
            "source_date": "2026-01-15"
        },
        # Asthma
        {
            "condition_keywords": ["asthma", "bronchial asthma", "reactive airway"],
            "drug_keywords": ["propranolol", "timolol", "carvedilol", "labetalol", "sotalol", "nadolol"],
            "severity": "RED",
            "headline": "Non-Selective Beta-Blocker Life-Threatening Bronchospasm Hazard",
            "plain": "Non-selective beta-blockers block beta-2 receptors in lung airways, causing severe bronchospasm (narrowing of air passages) that can trigger a fatal asthma attack.",
            "mechanism": "Blockade of bronchial smooth muscle beta-2 adrenergic receptors prevents bronchodilation and induces bronchoconstriction.",
            "consequences": "Severe refractory bronchospasm, acute respiratory distress, status asthmaticus.",
            "action": "Non-selective beta-blockers are strictly contraindicated in patients with asthma. Inform your doctor immediately to select asthma-safe cardiovascular alternatives.",
            "source": "Global Initiative for Asthma (GINA) / BNF 86",
            "source_date": "2026-02-10"
        },
        {
            "condition_keywords": ["asthma"],
            "drug_keywords": ["aspirin", "ibuprofen", "diclofenac", "naproxen"],
            "severity": "YELLOW",
            "headline": "Aspirin-Exacerbated Respiratory Disease (AERD) Precaution",
            "plain": "In up to 15% of patients with asthma, aspirin and other NSAID painkillers trigger acute asthma attacks and severe nasal congestion.",
            "mechanism": "Inhibition of COX-1 shunts arachidonic acid metabolism to the 5-lipoxygenase pathway, leading to massive overproduction of cysteinyl leukotrienes.",
            "consequences": "Sudden wheezing, bronchospasm, and rhinorrhea within 30-120 minutes of ingestion.",
            "action": "If you have never tolerated NSAIDs or have nasal polyps, exercise extreme caution and consult your doctor before taking aspirin or ibuprofen.",
            "source": "GINA Clinical Guidelines / American Academy of Allergy, Asthma & Immunology (AAAAI)",
            "source_date": "2026-01-25"
        },
        # Liver Disease
        {
            "condition_keywords": ["liver disease", "cirrhosis", "hepatitis", "hepatic impairment"],
            "drug_keywords": ["paracetamol", "acetaminophen"],
            "severity": "YELLOW",
            "headline": "Hepatotoxicity Risk in Pre-Existing Liver Impairment",
            "plain": "In liver disease, the liver's ability to safely process paracetamol is reduced. Dosages above 2 grams (2,000 mg) per day can lead to dangerous toxic metabolite accumulation.",
            "mechanism": "Depleted hepatic glutathione reserves allow reactive intermediate NAPQI to bind cellular proteins, accelerating hepatocyte necrosis.",
            "consequences": "Exacerbation of hepatic encephalopathy or liver injury.",
            "action": "Maximum daily dose should strictly not exceed 2,000 mg (four 500mg tablets) in 24 hours. Avoid alcohol completely.",
            "source": "American Association for the Study of Liver Diseases (AASLD)",
            "source_date": "2026-02-18"
        },
        {
            "condition_keywords": ["liver disease", "active liver disease", "cirrhosis"],
            "drug_keywords": ["atorvastatin", "simvastatin", "rosuvastatin"],
            "severity": "YELLOW",
            "headline": "Statin Hepatic Clearance & Enzyme Elevation Caution",
            "plain": "Statins undergo extensive hepatic metabolism. In active or decompensated liver disease, statin blood levels can rise, increasing risks of muscle toxicity and liver enzyme spikes.",
            "mechanism": "Impaired CYP3A4/2C9 metabolism and biliary excretion leading to elevated systemic statin exposure.",
            "consequences": "Serum transaminase elevations, increased risk of statin-induced myopathy/rhabdomyolysis.",
            "action": "Baseline and follow-up liver function tests (LFTs) required. Consult your hepatologist or physician.",
            "source": "BNF 86 / FDA Drug Safety Communication",
            "source_date": "2026-01-30"
        }
    ]

    # Drug-to-Allergy Classes
    ALLERGY_CLASSES = [
        {
            "allergy_terms": ["penicillin", "amoxicillin", "ampicillin", "augmentin", "beta-lactam"],
            "matching_drugs": ["amoxicillin", "ampicillin", "penicillin", "piperacillin", "cloxacillin", "augmentin", "cephalexin", "cefuroxime", "ceftriaxone", "cefixime"],
            "severity": "RED",
            "headline": "Documented Beta-Lactam / Penicillin Allergy Conflict",
            "plain": "You have recorded a Penicillin allergy. The proposed medicine belongs to the penicillin / beta-lactam class and carries a high risk of triggering an immediate allergic reaction, skin eruption, or life-threatening anaphylaxis.",
            "mechanism": "IgE-mediated Type I hypersensitivity against penicilloyl major determinants or beta-lactam core structures.",
            "consequences": "Urticaria, angioedema, bronchospasm, anaphylactic shock.",
            "action": "Do NOT take this medicine. Inform your doctor or pharmacist of your penicillin allergy to receive a safe non-beta-lactam antibiotic (such as a macrolide or fluoroquinolone).",
            "source": "World Allergy Organization (WAO) Guidelines",
            "source_date": "2026-02-01"
        },
        {
            "allergy_terms": ["sulfa", "sulfonamide", "septra", "bactrim"],
            "matching_drugs": ["sulfamethoxazole", "celecoxib", "furosemide", "hydrochlorothiazide", "glimepiride", "gliclazide"],
            "severity": "RED",
            "headline": "Documented Sulfonamide (Sulfa) Allergy Conflict",
            "plain": "You have recorded a Sulfa allergy. This proposed medicine contains a sulfonamide structure, which can cause severe skin rashes or allergic reactions.",
            "mechanism": "Immunological cross-reactivity or hapten formation linked to the sulfonamide moiety.",
            "consequences": "Erythema multiforme, Stevens-Johnson syndrome (SJS), fever, toxic epidermal necrolysis.",
            "action": "Avoid this medication. Review your complete allergy history with your pharmacist before dispensing.",
            "source": "CDSCO / FDA Safety Alerts",
            "source_date": "2026-01-18"
        },
        {
            "allergy_terms": ["aspirin", "nsaid", "ibuprofen", "brufen"],
            "matching_drugs": ["aspirin", "ibuprofen", "diclofenac", "naproxen", "etoricoxib", "mefenamic", "piroxicam", "ketorolac"],
            "severity": "RED",
            "headline": "Documented NSAID / Aspirin Hypersensitivity Conflict",
            "plain": "You have recorded an allergy to Aspirin or NSAIDs. The proposed medicine is an NSAID and will cross-react with your documented allergy.",
            "mechanism": "COX-1 inhibition leading to leukotriene release or IgE-mediated allergy.",
            "consequences": "Facial swelling, hives, asthma attack, or anaphylaxis.",
            "action": "Do NOT take this medicine. Consult your doctor for an allergy-safe pain alternative.",
            "source": "AAAAI Practice Parameters",
            "source_date": "2026-02-12"
        }
    ]

    @classmethod
    def _normalize(cls, text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", text).lower()

    @classmethod
    def _text_contains_any(cls, target_text: str, keywords: List[str]) -> bool:
        t_low = target_text.lower()
        return any(k.lower() in t_low for k in keywords)

    @classmethod
    def analyze_regimen_compatibility(
        cls,
        db: Session,
        req: CheckRegimenCompatibilityRequest,
        user_id: Optional[int] = None
    ) -> CompatibilityReportResponse:
        now_dt = datetime.utcnow()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        patient_name = req.patient_name or (req.health_profile.patient_name if req.health_profile else None)

        findings: List[InteractionFindingDetail] = []
        finding_counter = 1

        # 1. Resolve proposed medicine metadata
        prop = req.proposed_medicine
        prop_med_db: Optional[Medicine] = None
        if prop.medicine_id:
            prop_med_db = db.query(Medicine).filter(Medicine.id == prop.medicine_id).first()
        elif prop.medicine_name:
            prop_med_db = db.query(Medicine).filter(
                or_(
                    Medicine.brand_name.ilike(f"%{prop.medicine_name}%"),
                    Medicine.generic_name.ilike(f"%{prop.medicine_name}%")
                )
            ).first()

            if not prop_med_db:
                res_intel = MedicineIntelligenceService.resolve_medicine(db, prop.medicine_name)
                if res_intel.get("medicine"):
                    prop_med_db = res_intel["medicine"]

        # Fill in metadata from DB if found
        prop_brand = prop.brand_name or (prop_med_db.brand_name if prop_med_db else prop.medicine_name)
        prop_generic = prop.generic_name or (prop_med_db.generic_name if prop_med_db else prop.medicine_name)
        prop_ingredients = prop.active_ingredients or (prop_med_db.active_ingredients if prop_med_db else prop_generic)
        prop_strength = prop.strength or (prop_med_db.strength if prop_med_db else "Unspecified")
        prop_manufacturer = prop.manufacturer or (prop_med_db.manufacturer if prop_med_db else "Unspecified")

        # Prepare normalized proposed drug string
        prop_search_blob = f"{prop_brand} {prop_generic} {prop_ingredients}".lower()

        # 2. Check for DUPLICATE MEDICINES (same active ingredient)
        for exist_med in req.existing_medicines:
            exist_brand = exist_med.brand_name or exist_med.medicine_name
            exist_generic = exist_med.generic_name or exist_med.medicine_name
            exist_ingredients = exist_med.active_ingredients or exist_generic

            # Check matching generic tokens
            prop_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", prop_generic.lower() + " " + prop_ingredients.lower()))
            exist_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", exist_generic.lower() + " " + exist_ingredients.lower()))
            
            # Filter common fillers
            filler_words = {"tablet", "capsule", "hydrochloride", "sodium", "potassium", "sustained", "release", "extended", "syrup"}
            prop_tokens -= filler_words
            exist_tokens -= filler_words

            overlap = prop_tokens & exist_tokens
            if overlap:
                matched_ingredient = list(overlap)[0].capitalize()
                findings.append(InteractionFindingDetail(
                    id=f"FINDING-{finding_counter}",
                    finding_type="DUPLICATE_MEDICINE",
                    severity="RED",
                    severity_label="Serious Risk (Duplicate Ingredient)",
                    headline=f"Duplicate Active Ingredient Hazard: {matched_ingredient}",
                    medicines_involved=[prop_brand, exist_brand],
                    plain_language_explanation=(
                        f"DUPLICATE INGREDIENT WARNING: The proposed medicine '{prop_brand}' contains '{matched_ingredient}', "
                        f"which is identical to the active chemical in your current medicine '{exist_brand}'. "
                        f"Taking both medicines at the same time could result in an accidental double dose and toxic overdose."
                    ),
                    clinical_mechanism=f"Therapeutic duplication: simultaneous intake of identical pharmacophore ({matched_ingredient}).",
                    clinical_consequences="Significant risk of dosage-dependent adverse toxicity, organ overload, and acute side effects.",
                    recommended_action=f"Do NOT take '{prop_brand}' alongside '{exist_brand}' without strict pharmacist verification of intended dosage.",
                    evidence_source="CDSCO / WHO Safe Medication Practice Guidelines",
                    source_update_date="2026-03-01",
                    ml_predicted=False
                ))
                finding_counter += 1

        # 3. Check DRUG-TO-ALLERGY CONFLICTS
        patient_allergies = req.health_profile.allergies
        for allergy_item in patient_allergies:
            a_clean = allergy_item.lower()
            for a_rule in cls.ALLERGY_CLASSES:
                if any(k in a_clean for k in a_rule["allergy_terms"]):
                    # Patient has this allergy class! Does proposed drug match?
                    if any(d in prop_search_blob for d in a_rule["matching_drugs"]):
                        findings.append(InteractionFindingDetail(
                            id=f"FINDING-{finding_counter}",
                            finding_type="DRUG_TO_ALLERGY",
                            severity="RED",
                            severity_label="Serious Risk (Allergy Conflict)",
                            headline=a_rule["headline"],
                            medicines_involved=[prop_brand],
                            allergy_involved=allergy_item,
                            plain_language_explanation=a_rule["plain"],
                            clinical_mechanism=a_rule["mechanism"],
                            clinical_consequences=a_rule["consequences"],
                            recommended_action=a_rule["action"],
                            evidence_source=a_rule["source"],
                            source_update_date=a_rule["source_date"],
                            ml_predicted=False
                        ))
                        finding_counter += 1

        # 4. Check DRUG-TO-DISEASE CONTRAINDICATIONS
        patient_conditions = req.health_profile.medical_conditions
        for condition in patient_conditions:
            cond_low = condition.lower()
            for d_rule in cls.DISEASE_CONTRAINDICATION_RULES:
                if any(c in cond_low for c in d_rule["condition_keywords"]):
                    # Patient has this condition! Does proposed drug match?
                    if any(d in prop_search_blob for d in d_rule["drug_keywords"]):
                        findings.append(InteractionFindingDetail(
                            id=f"FINDING-{finding_counter}",
                            finding_type="DRUG_TO_DISEASE",
                            severity=d_rule["severity"],
                            severity_label="Serious Risk (Contraindication)" if d_rule["severity"] == "RED" else "Caution Required",
                            headline=d_rule["headline"],
                            medicines_involved=[prop_brand],
                            medical_condition_involved=condition,
                            plain_language_explanation=d_rule["plain"],
                            clinical_mechanism=d_rule["mechanism"],
                            clinical_consequences=d_rule["consequences"],
                            recommended_action=d_rule["action"],
                            evidence_source=d_rule["source"],
                            source_update_date=d_rule["source_date"],
                            ml_predicted=False
                        ))
                        finding_counter += 1

        # 5. Check PAIRWISE DRUG-TO-DRUG INTERACTIONS (Proposed vs Each Existing)
        for exist_med in req.existing_medicines:
            exist_brand = exist_med.brand_name or exist_med.medicine_name
            exist_generic = exist_med.generic_name or exist_med.medicine_name

            # Layer 1 Curated Check
            rule_detail = DDILayer1Service.check_pair(db, prop_generic, exist_generic)
            if not rule_detail:
                # Also try matching brand names in case generic was omitted
                rule_detail = DDILayer1Service.check_pair(db, prop_brand, exist_brand)

            if rule_detail:
                # Severity mapping
                sev = "RED" if rule_detail.severity in ["Contraindicated", "Major"] else "YELLOW"
                sev_label = "Serious Risk (Contraindicated)" if rule_detail.severity == "Contraindicated" else (
                    "Major Clinical Interaction" if rule_detail.severity == "Major" else "Moderate Precaution"
                )

                # Patient-friendly translation
                plain_exp = (
                    f"POTENTIAL INTERACTION: Taking '{prop_brand}' together with your current medicine '{exist_brand}' "
                    f"({exist_generic}) may lead to adverse effects. "
                    f"Clinically documented concern: {rule_detail.clinical_consequences}."
                )

                findings.append(InteractionFindingDetail(
                    id=f"FINDING-{finding_counter}",
                    finding_type="DRUG_TO_DRUG",
                    severity=sev,
                    severity_label=sev_label,
                    headline=f"Interaction: {prop_brand} + {exist_brand} ({rule_detail.severity})",
                    medicines_involved=[prop_brand, exist_brand],
                    plain_language_explanation=plain_exp,
                    clinical_mechanism=rule_detail.mechanism,
                    clinical_consequences=rule_detail.clinical_consequences,
                    recommended_action=(
                        "Speak with your doctor or pharmacist before starting this medicine. "
                        "Do not independently discontinue your existing prescribed medicine."
                    ),
                    evidence_source=rule_detail.source,
                    source_update_date=rule_detail.last_verified_date,
                    ml_predicted=False
                ))
                finding_counter += 1
            elif req.enable_ml_prediction and prop_med_db:
                # Layer 2 Hybrid GNN check if existing medicine is also in DB
                exist_med_db = None
                if exist_med.medicine_id:
                    exist_med_db = db.query(Medicine).filter(Medicine.id == exist_med.medicine_id).first()
                elif exist_med.medicine_name:
                    exist_med_db = db.query(Medicine).filter(
                        or_(Medicine.brand_name.ilike(f"%{exist_med.medicine_name}%"), Medicine.generic_name.ilike(f"%{exist_med.medicine_name}%"))
                    ).first()

                if exist_med_db:
                    try:
                        gnn_pred = DDILayer2Service.predict_pair_ml(db, prop_med_db, exist_med_db)
                        if gnn_pred and gnn_pred["severity"] in ["Contraindicated", "Major"] and gnn_pred["confidence"] > 0.65:
                            findings.append(InteractionFindingDetail(
                                id=f"FINDING-{finding_counter}",
                                finding_type="DRUG_TO_DRUG",
                                severity="YELLOW",
                                severity_label="Experimental Model Warning (GNN Prediction)",
                                headline=f"Experimental Prediction: {prop_brand} + {exist_brand} ({gnn_pred['severity']})",
                                medicines_involved=[prop_brand, exist_brand],
                                plain_language_explanation=(
                                    f"EXPERIMENTAL WARNING: The PHARMINTEL-HYBRIDGNN research model predicts a potential "
                                    f"{gnn_pred['severity'].lower()} interaction between '{prop_brand}' and '{exist_brand}' "
                                    f"(Model Confidence: {(gnn_pred['confidence']*100):.1f}%). "
                                    "Note: This is an automated machine-learning prediction and has not yet been verified by authoritative clinical rules."
                                ),
                                clinical_mechanism=gnn_pred.get("mechanism") or "Predicted high-dimensional topological structural feature clash in biological graph network.",
                                clinical_consequences=gnn_pred.get("clinical_consequences") or "Potential pharmacodynamic or metabolic competition.",
                                recommended_action="Consult a pharmacist to review this potential interaction prior to co-administration.",
                                evidence_source="PHARMINTEL-HYBRIDGNN (Heterogeneous Graph Transformer & R-GCN)",
                                source_update_date="2026-03-20",
                                ml_predicted=True,
                                ml_confidence=gnn_pred["confidence"]
                            ))
                            finding_counter += 1
                    except Exception as e:
                        print(f"GNN pair evaluation error: {e}")

        # 6. MULTIPLE MEDICINE REGIMEN RISKS (Regimen-Level Analysis)
        all_meds_text = (prop_search_blob + " " + " ".join([
            f"{m.medicine_name} {m.brand_name or ''} {m.generic_name or ''} {m.active_ingredients or ''}".lower()
            for m in req.existing_medicines
        ])).lower()

        # 6A. Triple Whammy: ACEi/ARB + Diuretic + NSAID
        has_ace_arb = any(k in all_meds_text for k in ["ramipril", "enalapril", "lisinopril", "telmisartan", "losartan", "valsartan", "olmesartan"])
        has_diuretic = any(k in all_meds_text for k in ["hydrochlorothiazide", "furosemide", "torsemide", "chlorthalidone", "indapamide", "spironolactone"])
        has_nsaid = any(k in all_meds_text for k in ["ibuprofen", "diclofenac", "naproxen", "piroxicam", "etoricoxib", "celecoxib", "mefenamic"])

        if has_ace_arb and has_diuretic and has_nsaid:
            findings.append(InteractionFindingDetail(
                id=f"FINDING-{finding_counter}",
                finding_type="MULTIPLE_REGIMEN_RISK",
                severity="RED",
                severity_label="Serious Risk (Triple Whammy Regimen)",
                headline="Triple Whammy: Acute Kidney Failure Regimen Hazard",
                medicines_involved=[m.medicine_name for m in req.existing_medicines] + [prop_brand],
                plain_language_explanation=(
                    "CRITICAL REGIMEN ALERT (THE TRIPLE WHAMMY): Your complete medication combination includes a blood pressure medicine "
                    "(ACE inhibitor or ARB), a water pill (diuretic), and an anti-inflammatory painkiller (NSAID). "
                    "When taken together, this specific trio cuts off blood flow to the kidneys, causing acute renal failure."
                ),
                clinical_mechanism=(
                    "Triple hemodynamic insult: Diuretic depletes intravascular volume; NSAID constricts afferent renal arteriole; "
                    "ACEi/ARB prevents efferent renal arteriolar vasoconstriction, causing catastrophic drop in intraglomerular hydrostatic pressure."
                ),
                clinical_consequences="Severe acute kidney injury (AKI), oliguria, fluid overload, and hyperkalemic emergency.",
                recommended_action="Do NOT take this combination. Contact your doctor immediately to select a kidney-safe painkiller such as paracetamol.",
                evidence_source="Australian Prescriber / British Medical Journal (BMJ) Clinical Evidence",
                source_update_date="2026-02-15",
                ml_predicted=False
            ))
            finding_counter += 1

        # 6B. Additive Bleeding Risk: 2 or more antiplatelets/anticoagulants + NSAID
        blood_thinners = [k for k in ["warfarin", "aspirin", "clopidogrel", "apixaban", "rivaroxaban", "dabigatran", "ticagrelor", "heparin"] if k in all_meds_text]
        if len(blood_thinners) >= 2 and has_nsaid:
            findings.append(InteractionFindingDetail(
                id=f"FINDING-{finding_counter}",
                finding_type="MULTIPLE_REGIMEN_RISK",
                severity="RED",
                severity_label="Serious Risk (Additive Bleeding)",
                headline="Multiple Antithrombotic + NSAID Severe Bleeding Hazard",
                medicines_involved=blood_thinners + ["NSAID Painkiller"],
                plain_language_explanation=(
                    "HIGH BLEEDING RISK: You are taking multiple medications that prevent blood clotting alongside an anti-inflammatory pain reliever. "
                    "This combination dramatically raises the risk of severe stomach ulcers, gastrointestinal bleeding, and bruising."
                ),
                clinical_mechanism="Additive inhibition of primary platelet aggregation and secondary coagulation cascade combined with NSAID-induced gastric mucosal barrier depletion.",
                clinical_consequences="Major upper gastrointestinal bleeding, hematemesis, melena, or hemorrhagic stroke.",
                recommended_action="Avoid NSAIDs. Consult your prescribing physician or cardiologist before starting any new painkiller.",
                evidence_source="American College of Cardiology (ACC) / CHEST Guidelines",
                source_update_date="2026-01-25",
                ml_predicted=False
            ))
            finding_counter += 1

        # 7. PATIENT-SPECIFIC ORGAN & AGE RISK ASSESSMENT
        if req.health_profile.age and req.health_profile.age >= 65:
            # Check high-risk geriatric drugs (Beers criteria)
            geriatric_high_risk = ["chlorpheniramine", "hydroxyzine", "promethazine", "diazepam", "lorazepam", "alprazolam", "indomethacin"]
            if any(k in prop_search_blob for k in geriatric_high_risk):
                findings.append(InteractionFindingDetail(
                    id=f"FINDING-{finding_counter}",
                    finding_type="PATIENT_SPECIFIC_RISK",
                    severity="YELLOW",
                    severity_label="Caution Required (Geriatric Sensitivity)",
                    headline="Age-Related Caution: Potentially Inappropriate Medication",
                    medicines_involved=[prop_brand],
                    plain_language_explanation=(
                        f"In adults aged 65 and older, '{prop_brand}' carries elevated risks of profound dizziness, confusion, falls, "
                        "and prolonged sedation due to reduced physiological clearance."
                    ),
                    clinical_mechanism="Age-related declines in hepatic cytochrome P450 activity, renal clearance, and blood-brain barrier permeability.",
                    clinical_consequences="Postural hypotension, falls, cognitive clouding, anticholinergic toxicity.",
                    recommended_action="Discuss starting with a lower geriatric dose or alternative agent with your doctor.",
                    evidence_source="American Geriatrics Society (AGS) Beers Criteria® 2023 Update",
                    source_update_date="2026-01-10",
                    ml_predicted=False
                ))
                finding_counter += 1

        # 8. DETERMINE OVERALL STATUS
        serious_red_count = sum(1 for f in findings if f.severity == "RED")
        caution_yellow_count = sum(1 for f in findings if f.severity == "YELLOW")
        info_green_count = sum(1 for f in findings if f.severity == "GREEN")

        # Check if essential information is missing (GREY condition)
        is_missing_info = (
            not prop_generic or prop_generic == "Unspecified" or
            ("kidney" in " ".join(req.health_profile.medical_conditions).lower() and req.health_profile.kidney_function == "Unknown")
        )

        if serious_red_count > 0:
            overall_status = "RED"
            overall_label = "RED – Serious Potential Interaction Identified"
            headline = f"Potential Serious Safety Concern Detected ({serious_red_count} High-Risk Finding{'s' if serious_red_count > 1 else ''})"
            should_take = "RED – Serious Potential Safety Concern: Do NOT start this medicine without consulting your doctor or pharmacist."
        elif caution_yellow_count > 0:
            overall_status = "YELLOW"
            overall_label = "YELLOW – Caution Required (Professional Review Advised)"
            headline = f"Moderate Safety Concerns or Precautionary Flags Identified ({caution_yellow_count} Precaution{'s' if caution_yellow_count > 1 else ''})"
            should_take = "YELLOW – Professional Advice Recommended: Review with your doctor or pharmacist before starting."
        elif is_missing_info:
            overall_status = "GREY"
            overall_label = "GREY – Insufficient Clinical Information to Guarantee Safety"
            headline = "Compatibility Analysis Incomplete Due to Missing Clinical Parameters"
            should_take = "GREY – Unable to Determine: System lacks essential verified information to determine suitability."
        else:
            overall_status = "GREEN"
            overall_label = "GREEN – No Known Interaction Identified in Verified Sources"
            headline = "No Documented Contraindications or Adverse Interactions Found"
            should_take = "GREEN – No Known Interaction Identified: Verified sources do not list documented conflicts, but doctor/pharmacist confirmation is still required."

        # 9. CONSTRUCT PERSONALIZED EXPLANATION & ACTION GUIDANCE
        # Personalized paragraph citing their actual medical conditions and current medicines
        cond_str = ", ".join(patient_conditions) if patient_conditions else "no pre-existing medical conditions"
        meds_str = ", ".join([m.medicine_name for m in req.existing_medicines]) if req.existing_medicines else "no active medications"

        if overall_status == "RED":
            what_means = (
                f"You have recorded medical conditions ({cond_str}) and currently take {len(req.existing_medicines)} medicine(s) ({meds_str}). "
                f"Our clinical safety intelligence engine identified {serious_red_count} potentially serious conflict(s) with the proposed medicine '{prop_brand}'. "
                f"Taking this medicine alongside your existing regimen could produce adverse clinical consequences or worsen your underlying health conditions. "
                "Do NOT start this medicine independently. Do NOT stop taking your currently prescribed medicines."
            )
            why_applies = (
                f"This result applies specifically to you because the pharmacological properties of '{prop_brand}' interact with your "
                f"recorded health profile. Review the detailed findings below to see which of your existing medicines or conditions are directly involved."
            )
            actions = [
                f"Do not take '{prop_brand}' until you have reviewed these findings with your doctor or pharmacist.",
                "Do not discontinue or modify any of your existing prescribed medicines without professional guidance.",
                "Bring this printed safety report or share the digital assessment with your prescribing physician.",
                "If this medicine was newly prescribed, contact your pharmacy to verify whether a safer alternative is available."
            ]
            questions = [
                f"Is '{prop_brand}' safe for me given my diagnosis of {cond_str}?",
                f"Does '{prop_brand}' interact dangerously with my current medication '{req.existing_medicines[0].medicine_name if req.existing_medicines else 'regimen'}'?",
                "Is there an alternative medicine for my symptoms that does not carry these documented risks?",
                "What specific symptoms should I watch out for if I must take this treatment?"
            ]
        elif overall_status == "YELLOW":
            what_means = (
                f"You have recorded {cond_str} and are currently taking {len(req.existing_medicines)} medicine(s) ({meds_str}). "
                f"Our clinical engine identified {caution_yellow_count} precaution(s) regarding '{prop_brand}'. "
                "While not strictly contraindicated, co-administration may require dosage adjustments, separation of dosing times, "
                "or clinical monitoring by your healthcare team."
            )
            why_applies = (
                f"This caution matters for your treatment because '{prop_brand}' may increase the risk of side effects or reduce the "
                f"efficacy of your existing medicines ({meds_str})."
            )
            actions = [
                f"Consult your pharmacist or doctor before starting '{prop_brand}'.",
                "Discuss whether monitoring (such as blood pressure checks or blood tests) is required.",
                "Never alter the dosage of your current medications without medical supervision."
            ]
            questions = [
                f"Do I need to adjust the timing between taking '{prop_brand}' and my other medicines?",
                "Should my kidney, liver, or blood sugar levels be monitored while taking this?",
                "What mild or moderate side effects should prompt me to contact you?"
            ]
        elif overall_status == "GREY":
            what_means = (
                f"We could not verify all necessary clinical parameters for '{prop_brand}'. "
                "PharmIntel strictly adheres to healthcare safety standards: we never classify unknown or unverified combinations as safe."
            )
            why_applies = "Accurate clinical decision-support requires complete active ingredient data and verified medical history."
            actions = [
                "Ask a licensed pharmacist to review the physical packaging and active ingredients.",
                "Update your patient profile with complete dosage and organ function details if available."
            ]
            questions = [
                f"What are the active chemical ingredients in '{prop_brand}'?",
                f"Is '{prop_brand}' compatible with my existing treatment ({meds_str})?"
            ]
        else:
            what_means = (
                f"Based on your recorded health conditions ({cond_str}) and your current medication list ({meds_str}), "
                f"our verified clinical knowledge bases did not identify documented interactions with '{prop_brand}'. "
                "Please note: A clean interaction check does not guarantee complete individual tolerance or absence of unknown side effects."
            )
            why_applies = (
                f"No documented pharmacokinetic or pharmacodynamic clashes were found between '{prop_brand}' and your current regimen."
            )
            actions = [
                f"Follow the dosage instructions provided by your doctor or on the medicine label.",
                "Take with appropriate meals or fluids as directed in the product monograph.",
                "If you experience unexpected symptoms, contact your doctor or local pharmacy immediately."
            ]
            questions = [
                f"What is the recommended daily dosage and duration for '{prop_brand}'?",
                "Should this medicine be taken with food or on an empty stomach?"
            ]

        missing_info_list = []
        if not req.health_profile.kidney_function or req.health_profile.kidney_function == "Unknown":
            missing_info_list.append("Kidney function status (eGFR / serum creatinine) is not recorded.")
        if not req.health_profile.age:
            missing_info_list.append("Patient age is unrecorded (important for geriatric dosing assessment).")
        if not prop_ingredients:
            missing_info_list.append("Exact active chemical ingredients for proposed medicine could not be retrieved from database.")

        personalized_guidance = PersonalizedExplanation(
            should_take_assessment=should_take,
            what_this_means_for_you=what_means,
            why_this_applies_to_you=why_applies,
            action_summary=actions,
            questions_for_doctor=questions,
            missing_information=missing_info_list
        )

        counts = FindingsCount(
            total=len(findings),
            serious_red=serious_red_count,
            caution_yellow=caution_yellow_count,
            info_green=info_green_count,
            insufficient_grey=1 if overall_status == "GREY" else 0
        )

        disclaimer = (
            "MANDATORY CLINICAL SAFETY NOTICE: PharmIntel Drug Detection is an advanced clinical decision-support system "
            "designed to assist patients and healthcare professionals. It does not constitute medical advice, diagnosis, or an independent "
            "prescription. Never discontinue, start, or alter the dosage of any prescribed medicine without the explicit evaluation "
            "of a qualified physician or licensed pharmacist."
        )

        # 10. Persist Assessment Record if user is logged in
        assessment_record_id = None
        if user_id:
            try:
                rec = PatientSafetyAssessmentRecord(
                    user_id=user_id,
                    assessment_date=now_str,
                    proposed_medicine_name=prop_brand,
                    proposed_medicine_id=prop.medicine_id,
                    patient_name=patient_name,
                    overall_status=overall_status,
                    summary_headline=headline,
                    patient_conditions_json=json.dumps(patient_conditions),
                    patient_allergies_json=json.dumps(patient_allergies),
                    existing_medicines_json=json.dumps([m.dict() for m in req.existing_medicines]),
                    findings_json=json.dumps([f.dict() for f in findings]),
                    personalized_explanation_json=json.dumps(personalized_guidance.dict()),
                    knowledge_base_version=KNOWLEDGE_BASE_VERSION,
                    created_at=now_dt
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                assessment_record_id = rec.id

                # Save profile if requested
                if req.save_profile:
                    cls.save_patient_profile(db, user_id, req.health_profile, req.existing_medicines)

            except Exception as e:
                print(f"Error persisting assessment history: {e}")
                db.rollback()

        return CompatibilityReportResponse(
            assessment_id=assessment_record_id,
            assessment_timestamp=now_str,
            patient_name=patient_name,
            overall_status=overall_status,
            overall_status_label=overall_label,
            summary_headline=headline,
            patient_summary=PatientSummarySchema(
                patient_name=patient_name,
                medical_conditions=patient_conditions,
                known_allergies=patient_allergies,
                age=req.health_profile.age,
                gender=req.health_profile.gender,
                kidney_function=req.health_profile.kidney_function,
                liver_function=req.health_profile.liver_function
            ),
            proposed_medicine=prop,
            existing_medicines_analysed=req.existing_medicines,
            findings=findings,
            findings_count=counts,
            personalized_guidance=personalized_guidance,
            knowledge_base_version=KNOWLEDGE_BASE_VERSION,
            disclaimer=disclaimer
        )

    @classmethod
    def save_patient_profile(
        cls,
        db: Session,
        user_id: int,
        health_profile: HealthProfileInput,
        existing_medicines: List[CurrentMedicationInput]
    ):
        prof = db.query(PatientHealthProfile).filter(PatientHealthProfile.user_id == user_id).first()
        if not prof:
            prof = PatientHealthProfile(user_id=user_id)
            db.add(prof)

        if getattr(health_profile, "patient_name", None):
            prof.patient_name = health_profile.patient_name.strip()
        prof.medical_conditions_json = json.dumps(health_profile.medical_conditions)
        prof.allergies_json = json.dumps(health_profile.allergies)
        prof.age = health_profile.age
        prof.gender = health_profile.gender
        prof.kidney_function = health_profile.kidney_function
        prof.liver_function = health_profile.liver_function
        prof.updated_at = datetime.utcnow()

        # Update current medications
        # Deactivate old ones and insert current
        db.query(PatientCurrentMedication).filter(PatientCurrentMedication.user_id == user_id).delete()

        for m in existing_medicines:
            med_entry = PatientCurrentMedication(
                user_id=user_id,
                medicine_id=m.medicine_id,
                medicine_name=m.medicine_name,
                brand_name=m.brand_name or m.medicine_name,
                generic_name=m.generic_name,
                active_ingredients=m.active_ingredients,
                strength=m.strength,
                dosage=m.dosage,
                frequency=m.frequency,
                administration_route=m.administration_route or "Oral",
                timing=m.timing,
                start_date=m.start_date,
                is_active=True
            )
            db.add(med_entry)

        db.commit()

    @classmethod
    def get_patient_profile(cls, db: Session, user_id: int) -> Dict[str, Any]:
        prof = db.query(PatientHealthProfile).filter(PatientHealthProfile.user_id == user_id).first()
        meds = db.query(PatientCurrentMedication).filter(
            PatientCurrentMedication.user_id == user_id,
            PatientCurrentMedication.is_active == True
        ).all()

        conditions = json.loads(prof.medical_conditions_json) if prof and prof.medical_conditions_json else []
        allergies = json.loads(prof.allergies_json) if prof and prof.allergies_json else []

        med_list = [
            {
                "id": m.id,
                "medicine_id": m.medicine_id,
                "medicine_name": m.medicine_name,
                "brand_name": m.brand_name,
                "generic_name": m.generic_name,
                "active_ingredients": m.active_ingredients,
                "strength": m.strength,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "administration_route": m.administration_route,
                "timing": m.timing,
                "start_date": m.start_date
            }
            for m in meds
        ]

        return {
            "health_profile": {
                "patient_name": prof.patient_name if prof else None,
                "medical_conditions": conditions,
                "allergies": allergies,
                "age": prof.age if prof else None,
                "gender": prof.gender if prof else None,
                "kidney_function": prof.kidney_function if prof else "Normal",
                "liver_function": prof.liver_function if prof else "Normal"
            },
            "existing_medicines": med_list
        }

    @classmethod
    def get_assessment_history(cls, db: Session, user_id: int) -> List[Dict[str, Any]]:
        records = db.query(PatientSafetyAssessmentRecord).filter(
            PatientSafetyAssessmentRecord.user_id == user_id
        ).order_by(PatientSafetyAssessmentRecord.created_at.desc()).limit(20).all()

        output = []
        for r in records:
            meds = json.loads(r.existing_medicines_json) if r.existing_medicines_json else []
            findings = json.loads(r.findings_json) if r.findings_json else []
            output.append({
                "id": r.id,
                "patient_name": r.patient_name or "Patient name not provided",
                "assessment_date": r.assessment_date,
                "proposed_medicine_name": r.proposed_medicine_name,
                "overall_status": r.overall_status,
                "summary_headline": r.summary_headline,
                "medicines_count": len(meds),
                "warnings_count": len(findings),
                "knowledge_base_version": r.knowledge_base_version
            })
        return output

    THERAPEUTIC_CLASSES = {
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

        brand = getattr(m, "brand_name", None) or getattr(m, "medicine_name", None) or (best_med.brand_name if best_med else raw_name)
        generic = (best_med.generic_name if best_med else None) or getattr(m, "generic_name", None) or raw_name
        ingredients = (best_med.active_ingredients if best_med else None) or getattr(m, "active_ingredients", None) or generic
        strength = (best_med.strength if best_med else None) or getattr(m, "strength", None) or "Standard"

        substances = res.get("active_substances") or []
        if not substances and ingredients:
            substances = [s.strip() for s in re.split(r"[\+/&,;]|and", ingredients) if s.strip()]
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
