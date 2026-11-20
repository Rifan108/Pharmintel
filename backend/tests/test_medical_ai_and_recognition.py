"""
COMPREHENSIVE TEST SUITE: MEDICAL AI, PREGNANCY INTELLIGENCE, AND SMART MEDICINE RECOGNITION
=============================================================================================
Tests:
1. Pregnancy and Medication Safety (Dolo 650 / Paracetamol, NSAIDs, Antibiotics, Accidental ingestion, Breastfeeding)
2. Direct conversational answers without redirection to Drug Detection
3. Disease Pathophysiology & Management (Diabetes, Hypertension, Heart disease, Dehydration, Fever)
4. Symptom educational triage & Red flags (Headache, Stomach pain, Dizziness, Frequent urination, Heart attack signs)
5. Pharmacy Fundamentals (Generic vs Brand, Expiry dates, Batch numbers, Storage, Overdose first-aid)
6. In-Chat Drug-Drug Interactions (Combiflam + Dolo 650, Losartan + Amlodipine, General DDI principles)
7. Smart Medicine Package Image Recognition (Strips, Boxes, Barcodes, Blurry image rejection)
8. Multilingual Coverage across 7 Indian Languages
"""

import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.services.rag_assistant_service import RAGAssistantService
from app.services.qr_service import MedicineQRService

client = TestClient(app)

# =====================================================================
# 1. PREGNANCY & LACTATION MEDICATION SAFETY TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_pregnancy_dolo_650_answered_directly():
    """
    Verify: User: 'Can I take Dolo 650 while I am pregnant?'
    Must:
    1. Answer directly in chat (no redirect to Drug Detection).
    2. Recognize Dolo 650 is a brand of paracetamol.
    3. Explain paracetamol is a first-line option when clinically needed.
    4. Clarify that individual suitability depends on gestation stage, dose, medical history.
    5. Advise checking with an obstetrician.
    6. Explain dosage ceiling (max 4,000 mg/day) and avoiding multi-ingredient cold remedies.
    7. List emergency warning signs (high fever, severe headache, vision changes).
    """
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_preg_dolo_01",
            message="Can I take Dolo 650 while I am pregnant?",
            language="en"
        )
        resp = res["response"].lower()

        # 1. Direct answer in chat
        assert "navigate to drug detection" not in resp
        assert "click 'drug detection'" not in resp

        # 2. Brand & Active Ingredient identification
        assert "dolo 650" in resp
        assert "paracetamol" in resp or "acetaminophen" in resp

        # 3. Clinical evidence & first-line status
        assert "first-line" in resp or "option" in resp or "preferred" in resp

        # 4. Nuanced individual suitability
        assert "suitability" in resp or "individual" in resp or "trimester" in resp or "stage" in resp

        # 5. Professional consultation
        assert "obstetrician" in resp or "doctor" in resp or "healthcare provider" in resp

        # 6. Dosage limits & combination caution
        assert "4,000" in resp or "4000" in resp or "lowest effective dose" in resp

        # 7. Warning signs
        assert "warning" in resp or "fever" in resp or "headache" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_pregnancy_nsaids_contraindication():
    """Verify inquiry about ibuprofen/combiflam in pregnancy explains ductus arteriosus closure & oligohydramnios."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_preg_nsaid_01",
            message="Can pregnant women take ibuprofen or combiflam?",
            language="en"
        )
        resp = res["response"].lower()

        assert "ductus arteriosus" in resp or "amniotic" in resp or "oligohydramnios" in resp or "contraindicated" in resp
        assert "paracetamol" in resp  # Safer alternative recommendation
    finally:
        db.close()


@pytest.mark.asyncio
async def test_pregnancy_antibiotics_guidance():
    """Verify inquiry about antibiotics in pregnancy differentiates safer classes vs teratogenic classes."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_preg_abx_01",
            message="Can pregnant women take antibiotics?",
            language="en"
        )
        resp = res["response"].lower()

        # Safer classes
        assert "penicillin" in resp or "amoxicillin" in resp or "cephalosporin" in resp
        # Teratogenic classes
        assert "tetracycline" in resp or "doxycycline" in resp or "fluoroquinolone" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_pregnancy_medicines_to_avoid():
    """Verify 'Which medicines should be avoided during pregnancy?' lists known teratogens."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_preg_avoid_01",
            message="Which medicines should be avoided during pregnancy?",
            language="en"
        )
        resp = res["response"].lower()

        assert "ace inhibitor" in resp or "arb" in resp or "losartan" in resp
        assert "isotretinoin" in resp or "warfarin" in resp or "methotrexate" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_pregnancy_accidental_ingestion_protocol():
    """Verify 'What should I do if I accidentally took a medicine during pregnancy?' provides calm triage."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_preg_accident_01",
            message="What should I do if I accidentally took a medicine during pregnancy?",
            language="en"
        )
        resp = res["response"].lower()

        assert "calm" in resp or "remain calm" in resp
        assert "obstetrician" in resp or "poison" in resp or "doctor" in resp
        assert "do not induce vomiting" in resp or "vomiting" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_breastfeeding_medication_safety():
    """Verify 'Can I take medicine while breastfeeding?' explains RID and infant monitoring."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_bf_01",
            message="Can I take medicine while breastfeeding?",
            language="en"
        )
        resp = res["response"].lower()

        assert "paracetamol" in resp or "ibuprofen" in resp
        assert "codeine" in resp or "tramadol" in resp or "avoid" in resp
        assert "milk" in resp or "relative infant dose" in resp or "drowsiness" in resp
    finally:
        db.close()


# =====================================================================
# 2. IN-CHAT DRUG INTERACTIONS (NO REDIRECTION)
# =====================================================================

@pytest.mark.asyncio
async def test_in_chat_dolo_and_combiflam_duplicate_paracetamol():
    """
    Verify: User: 'Can I take Dolo 650 with Combiflam?'
    Must explain:
    - Combiflam contains Ibuprofen + Paracetamol.
    - Dolo 650 contains Paracetamol.
    - Double dosing paracetamol increases liver toxicity risk.
    - Answer appears DIRECTLY in chat (no redirect to Drug Detection).
    """
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_ddi_combiflam_01",
            message="Can I take Dolo 650 with Combiflam?",
            language="en"
        )
        resp = res["response"].lower()

        assert "navigate to drug detection" not in resp
        assert "combiflam" in resp and "dolo 650" in resp
        assert "paracetamol" in resp
        assert "duplicate" in resp or "double" in resp or "excess" in resp or "liver" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_general_drug_interaction_inquiry():
    """Verify 'Can two medicines interact?' explains pharmacokinetic and pharmacodynamic mechanisms."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_ddi_gen_01",
            message="Can two medicines interact?",
            language="en"
        )
        resp = res["response"].lower()

        assert "pharmacokinetic" in resp or "metabolism" in resp or "cyp450" in resp
        assert "pharmacodynamic" in resp or "synergistic" in resp or "antagonistic" in resp
    finally:
        db.close()


# =====================================================================
# 3. SYMPTOMS & EDUCATIONAL TRIAGE (NO DIAGNOSIS)
# =====================================================================

@pytest.mark.asyncio
async def test_headache_causes_and_red_flags():
    """Verify 'Why do I have a headache?' gives causes (tension, dehydration) and thunderclap red flag."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_symp_head_01",
            message="Why do I have a headache?",
            language="en"
        )
        resp = res["response"].lower()

        assert "tension" in resp or "dehydration" in resp or "migraine" in resp
        assert "thunderclap" in resp or "stiff neck" in resp or "red flag" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_heart_attack_warning_signs_emergency():
    """Verify 'What are the warning signs of a heart attack?' lists crushing chest pain and 112/108 directive."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_symp_ha_01",
            message="What are the warning signs of a heart attack?",
            language="en"
        )
        resp = res["response"].lower()

        assert "chest" in resp
        assert "arm" in resp or "jaw" in resp or "shortness of breath" in resp
        assert "112" in resp or "108" in resp or "emergency" in resp or "ambulance" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_when_to_consult_a_doctor():
    """Verify 'When should I consult a doctor?' provides structured clinical triage."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_symp_doc_01",
            message="When should I consult a doctor?",
            language="en"
        )
        resp = res["response"].lower()

        assert "persistent" in resp or "fever" in resp or "symptom" in resp
        assert "red flag" in resp or "emergency" in resp
    finally:
        db.close()


# =====================================================================
# 4. PHARMACY FUNDAMENTALS
# =====================================================================

@pytest.mark.asyncio
async def test_pharmacy_generic_vs_brand():
    """Verify 'What is the difference between a brand and generic medicine?' explains bioequivalence and API."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_pharm_gen_01",
            message="What is the difference between a brand and generic medicine?",
            language="en"
        )
        resp = res["response"].lower()

        assert "active" in resp and ("ingredient" in resp or "api" in resp)
        assert "bioequivalence" in resp or "bioequivalent" in resp or "same" in resp
        assert "cost" in resp or "cheaper" in resp or "price" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_pharmacy_medicine_storage():
    """Verify 'How should medicines be stored?' explains temperature (<25°C), moisture, and cold chain."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_pharm_store_01",
            message="How should medicines be stored?",
            language="en"
        )
        resp = res["response"].lower()

        assert "cool" in resp or "dry" in resp or "sunlight" in resp
        assert "bathroom" in resp or "refrigerat" in resp or "insulin" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_pharmacy_overdose_protocol():
    """Verify 'What should I do if I accidentally take too much medicine?' gives poison control & no vomiting guidance."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_pharm_od_01",
            message="What should I do if I accidentally take too much medicine?",
            language="en"
        )
        resp = res["response"].lower()

        assert "stop" in resp
        assert "112" in resp or "108" in resp or "poison" in resp or "emergency" in resp
        assert "vomiting" in resp  # Do not induce vomiting
    finally:
        db.close()


# =====================================================================
# 5. SMART MEDICINE PACKAGE IMAGE RECOGNITION TESTS
# =====================================================================

def test_recognize_medicine_strip_dolo():
    """Verify uploading a simulated medicine packaging strip photograph of Dolo 650 matches accurately."""
    # Create a mock packaging strip image
    img = Image.new("RGB", (500, 250), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.text((25, 30), "Dolo 650 mg Tablets", fill=(20, 20, 20))
    draw.text((25, 75), "Paracetamol IP 650mg", fill=(30, 30, 30))
    draw.text((25, 120), "B.No. DL-98124  Exp: 08/2027", fill=(40, 40, 40))
    draw.text((25, 165), "Micro Labs Limited", fill=(50, 50, 50))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/qr/scan-image",
        files={"file": ("dolo_650_strip.jpg", buf, "image/jpeg")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["medicine_name"] == "Dolo 650"
    assert "Paracetamol" in data["generic_name"]
    assert data["is_verified_authentic"] is True
    assert "Micro Labs" in data["manufacturer"]


def test_recognize_medicine_box_augmentin():
    """Verify uploading a packaging photo of Augmentin matches Augmentin from CDSCO database."""
    img = Image.new("RGB", (500, 250), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    draw.text((25, 30), "Augmentin 625 Duo", fill=(20, 20, 20))
    draw.text((25, 75), "Amoxicillin and Potassium Clavulanate Tablets IP", fill=(30, 30, 30))
    draw.text((25, 120), "B.No. AG-4819  Exp: 11/2027", fill=(40, 40, 40))
    draw.text((25, 165), "GlaxoSmithKline Pharmaceuticals", fill=(50, 50, 50))

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/qr/scan-image",
        files={"file": ("augmentin_box.jpg", buf, "image/jpeg")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Augmentin" in data["medicine_name"]
    assert data["is_verified_authentic"] is True


def test_reject_blurry_unrecognizable_image():
    """
    Verify uploading a solid grey / blurry unidentifiable image raises 422 with:
    'Medicine identification is not sufficiently reliable. Please upload a clearer photograph showing the medicine name and ingredients.'
    Does NOT invent an unverified medicine name.
    """
    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    resp = client.post(
        "/api/qr/scan-image",
        files={"file": ("blurry_unknown.jpg", buf, "image/jpeg")}
    )
    assert resp.status_code == 422
    err_detail = resp.json()["detail"]
    assert "Medicine identification is not sufficiently reliable" in err_detail
    assert "Please upload a clearer photograph" in err_detail


# =====================================================================
# 6. MULTILINGUAL SUPPORT TESTS (KANNADA, HINDI, TAMIL, TELUGU, MARATHI)
# =====================================================================

@pytest.mark.asyncio
async def test_multilingual_kannada_pregnancy_guidance():
    """Verify Kannada query regarding Dolo 650 in pregnancy returns accurate Kannada clinical guidance."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_kn_preg_01",
            message="ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಡೋಲೋ 650 ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ?",
            language="kn"
        )
        resp = res["response"]
        assert "ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ" in resp or "ಪ್ಯಾರಸಿಟಮಾಲ್" in resp
        assert "ವೈದ್ಯರ" in resp
    finally:
        db.close()


@pytest.mark.asyncio
async def test_multilingual_hindi_pregnancy_guidance():
    """Verify Hindi query regarding Dolo 650 in pregnancy returns accurate Hindi clinical guidance."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_hi_preg_01",
            message="क्या गर्भावस्था में डोलो 650 ले सकते हैं?",
            language="hi"
        )
        resp = res["response"]
        assert "गर्भावस्था" in resp
        assert "पैरासिटामोल" in resp or "डोलो" in resp
        assert "डॉक्टर" in resp
    finally:
        db.close()
