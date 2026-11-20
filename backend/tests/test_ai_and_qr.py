import io
import pytest
import qrcode
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.services.rag_assistant_service import RAGAssistantService
from app.services.qr_service import MedicineQRService

client = TestClient(app)

# =====================================================================
# PART 1: AI ASSISTANT MULTI-DOMAIN INTELLIGENCE TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_general_ai_question_answered_directly():
    """Verify 'What is artificial intelligence?' answers the actual question, not website navigation."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_ai_direct_01",
            message="What is artificial intelligence?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "artificial intelligence" in resp_text or "machine learning" in resp_text
        assert "neural network" in resp_text or "learning" in resp_text
        # Must NOT be a canned website UI navigation guide!
        assert "click 'drug detection' in the sidebar" not in resp_text
        assert "step-by-step instructions:" not in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_human_heart_function_answered_directly():
    """Verify 'Explain the function of the human heart' describes cardiac physiology."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_heart_01",
            message="Explain the function of the human heart",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "heart" in resp_text
        assert "ventricle" in resp_text or "atrium" in resp_text or "circulation" in resp_text
        assert "oxygen" in resp_text or "pump" in resp_text
        assert "click 'nearby medical shops'" not in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_blood_pressure_mechanics_answered_directly():
    """Verify 'Why is blood pressure important?' explains hemodynamic mechanics."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_bp_01",
            message="Why is blood pressure important?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "systolic" in resp_text and "diastolic" in resp_text
        assert "mmhg" in resp_text or "arterial" in resp_text or "perfusion" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_virus_vs_bacteria_answered_directly():
    """Verify 'Difference between bacteria and viruses' explains biological differences and antibiotic specificity."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_vb_01",
            message="Difference between bacteria and viruses",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "bacteria" in resp_text and "virus" in resp_text
        assert "antibiotic" in resp_text
        assert "ineffective" in resp_text or "cannot" in resp_text or "cell" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_exercise_benefits_answered_directly():
    """Verify 'What are the benefits of regular exercise?' answers physical activity physiology."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_ex_01",
            message="What are the benefits of regular exercise?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "cardiovascular" in resp_text or "insulin" in resp_text or "heart" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_diabetes_pathophysiology_and_types():
    """Verify 'Explain diabetes' explains Type 1 vs Type 2, symptoms, and management."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_dia_01",
            message="Explain diabetes Type 1 vs Type 2",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "diabetes" in resp_text
        assert "type 1" in resp_text and "type 2" in resp_text
        assert "insulin" in resp_text
        assert "glucose" in resp_text or "hba1c" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_hypertension_staging_and_management():
    """Verify 'Explain hypertension' explains blood pressure staging and management."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_ht_01",
            message="Explain hypertension",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "hypertension" in resp_text or "blood pressure" in resp_text
        assert "140" in resp_text or "stage" in resp_text or "dash" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_cholesterol_ldl_vs_hdl():
    """Verify 'Difference between LDL and HDL cholesterol' contrasts bad vs good cholesterol."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_chol_01",
            message="Difference between LDL and HDL cholesterol",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "ldl" in resp_text and "hdl" in resp_text
        assert "bad" in resp_text or "arterial" in resp_text
        assert "good" in resp_text or "reverse" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_dehydration_signs_and_ors():
    """Verify 'Explain dehydration signs and treatment' explains ORS and fluid replacement."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_dh_01",
            message="Explain dehydration signs and treatment",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "dehydration" in resp_text
        assert "ors" in resp_text or "oral rehydration" in resp_text or "fluid" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_antibiotic_resistance_reasons():
    """Verify 'Why must antibiotics be finished?' explains antimicrobial resistance."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_amr_01",
            message="Why must antibiotics be finished?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "antibiotic" in resp_text
        assert "resistance" in resp_text or "resistant" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_why_medicines_taken_with_food():
    """Verify 'Why are some medicines taken with food?' explains gastric protection and absorption."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_food_01",
            message="Why are some medicines taken with food?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "gastric" in resp_text or "stomach" in resp_text or "nsaid" in resp_text or "absorption" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_paracetamol_monograph_and_safety():
    """Verify 'What are the side effects of Paracetamol?' details analgesia, ceiling dose, and liver toxicity."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_pcm_01",
            message="What are the side effects of Paracetamol?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "paracetamol" in resp_text or "acetaminophen" in resp_text
        assert "liver" in resp_text or "hepatic" in resp_text or "4,000" in resp_text or "overdose" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_losartan_and_amlodipine_interaction():
    """Verify 'Can I take Losartan with Amlodipine?' explains synergistic vasodilation and hypotension monitoring."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_ddi_01",
            message="Can I take Losartan with Amlodipine?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "losartan" in resp_text and "amlodipine" in resp_text
        assert "blood pressure" in resp_text or "antihypertensive" in resp_text
        assert "hypotension" in resp_text or "dizziness" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_triple_whammy_interaction():
    """Verify triple whammy interaction warning with NSAIDs, ACEi/ARB, and diuretics."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_tw_01",
            message="Can I take Ibuprofen with Losartan and a diuretic?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "triple whammy" in resp_text or "kidney" in resp_text or "aki" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_website_ordering_help_explicit():
    """Verify user asking explicitly 'How do I order medicines on PharmIntel?' receives the ordering guide."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_web_help_01",
            message="How do I order medicines on PharmIntel?",
            language="en"
        )
        resp_text = res["response"].lower()
        assert "online pharmacy" in resp_text
        assert "add to cart" in resp_text or "prescription" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_multi_turn_anaphora_resolution():
    """Verify follow-up question 'What are its symptoms?' resolves to diabetes from preceding turn."""
    db = SessionLocal()
    try:
        sess_id = "test_multi_turn_01"
        # Turn 1: Diabetes
        await RAGAssistantService.process_chat_message(
            db=db,
            session_id=sess_id,
            message="Explain diabetes",
            language="en"
        )
        # Turn 2: Follow-up using pronoun
        res2 = await RAGAssistantService.process_chat_message(
            db=db,
            session_id=sess_id,
            message="What are its symptoms?",
            language="en"
        )
        resp_text = res2["response"].lower()
        assert "diabetes" in resp_text or "polyuria" in resp_text or "thirst" in resp_text or "urination" in resp_text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_live_support_mode_honest_ai_persona():
    """Verify mode='live_support' identifies as PharmIntel AI Live Support Assistant, with NO fake human doctor."""
    db = SessionLocal()
    try:
        res = await RAGAssistantService.process_chat_message(
            db=db,
            session_id="test_live_supp_01",
            message="How do I check drug interactions?",
            language="en",
            mode="live_support"
        )
        resp_text = res["response"]
        assert "PharmIntel AI Live Support Assistant" in resp_text
        assert "Dr. Ananya Deshmukh" not in resp_text
        assert "Escalate to Pharmacist" in resp_text
    finally:
        db.close()


# =====================================================================
# PART 2: MEDICINE QR SCANNER TESTS
# =====================================================================

def test_qr_verify_by_brand_name():
    """Verify MedicineQRService matches a medicine when raw QR text is a brand name."""
    db = SessionLocal()
    try:
        res = MedicineQRService.verify_medicine_qr(db, "Dolo 650", source_type="camera_scan")
        assert res.is_verified_authentic is True
        assert res.medicine_name == "Dolo 650"
        assert res.generic_name == "Paracetamol"
        assert "CDSCO" in res.authenticity_badge or "Verified" in res.authenticity_badge
    finally:
        db.close()


def test_qr_verify_by_batch_number():
    """Verify MedicineQRService verifies an authentic batch code e.g. BT-101-1."""
    db = SessionLocal()
    try:
        res = MedicineQRService.verify_medicine_qr(db, "BT-101-1", source_type="camera_scan")
        assert res.is_verified_authentic is True
        assert res.batch_number == "BT-101-1"
        assert res.safety_information is not None
        assert res.packaging_metadata.tamper_seal_hash is not None
    finally:
        db.close()


def test_qr_scan_image_via_api():
    """Verify POST /api/qr/scan-image decodes an uploaded QR image via OpenCV and verifies the drug."""
    # Generate a real QR code in memory using qrcode library
    img = qrcode.make("Dolo 650")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/qr/scan-image",
        files={"file": ("dolo_test_qr.png", buf.getvalue(), "image/png")}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["is_verified_authentic"] is True
    assert data["medicine_name"] == "Dolo 650"
    assert data["generic_name"] == "Paracetamol"
    assert "safety_information" in data


def test_qr_scan_image_invalid_file_handling():
    """Verify POST /api/qr/scan-image gracefully handles an image without a QR code."""
    # Blank 100x100 white image
    from PIL import Image
    blank_img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    blank_img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/qr/scan-image",
        files={"file": ("blank.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "No readable" in detail or "Medicine identification is not sufficiently reliable" in detail
