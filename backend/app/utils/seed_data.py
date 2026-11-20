import json
from sqlalchemy.orm import Session
from app.models.user import User, Customer, Pharmacist
from app.models.pharmacy import Pharmacy, Supplier
from app.models.medicine import Medicine, DrugInteraction
from app.models.inventory import PharmacyInventory, MedicineBatch, Purchase, PurchaseItem
from app.models.assistant import AIKnowledgeSource
from app.utils.security import hash_password

def seed_database(db: Session):
    # Check if already seeded
    if db.query(User).count() > 0:
        return

    print("Seeding PharmIntel clinical database with verified authoritative data...")

    # 1. SEED USERS & ROLES
    admin_user = User(
        email="admin@pharmintel.com",
        hashed_password=hash_password("Admin@PharmIntel2026"),
        full_name="Dr. Arvind V. Sharma",
        phone="+91 98100 11223",
        role="platform_admin",
        is_active=True
    )
    db.add(admin_user)

    pharm_admin_user = User(
        email="manager@medpluscare.com",
        hashed_password=hash_password("Manager@MedPlus2026"),
        full_name="Sunita Ramesh",
        phone="+91 98200 44556",
        role="pharmacy_admin",
        is_active=True
    )
    db.add(pharm_admin_user)

    pharmacist_user = User(
        email="pharmacist@apolloclinic.com",
        hashed_password=hash_password("Pharmacist@Apollo2026"),
        full_name="Rajesh Nambiar, M.Pharm",
        phone="+91 98300 77889",
        role="pharmacist",
        is_active=True
    )
    db.add(pharmacist_user)

    customer_user = User(
        email="patient@example.com",
        hashed_password=hash_password("Customer@Pass2026"),
        full_name="Ananya Deshmukh",
        phone="+91 98400 99001",
        role="customer",
        is_active=True
    )
    db.add(customer_user)
    db.commit()

    # Customer profile
    cust_profile = Customer(
        user_id=customer_user.id,
        address="Flat 402, Green Glen Layout, Bellandur",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560103",
        emergency_contact="+91 98400 99002 (Spouse)",
        allergies="Penicillin, Sulfa drugs",
        medical_conditions="Type 2 Diabetes Mellitus, Essential Hypertension",
        date_of_birth="1988-06-14"
    )
    db.add(cust_profile)

    # 2. SEED VERIFIED PHARMACIES
    pharmacy1 = Pharmacy(
        name="Apollo Care Community Pharmacy",
        registration_number="KA-BNG-PH-2021-0091",
        license_number="DL-20B-KA-45892",
        gst_number="29AAACA1234B1Z5",
        address="Shop 12, Ground Floor, Sarjapur Main Road, Bellandur",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560103",
        latitude=12.9279,
        longitude=77.6771,
        phone="+91 80 2844 1122",
        email="contact@apollocare-sarjapur.com",
        is_verified=True,
        operating_hours="07:30 AM - 11:00 PM",
        rating=4.9
    )
    db.add(pharmacy1)

    pharmacy2 = Pharmacy(
        name="MedPlus Central Health Store",
        registration_number="KA-BNG-PH-2019-0342",
        license_number="DL-21B-KA-38291",
        gst_number="29BBBCB5678C1Z2",
        address="Plot 55, Outer Ring Road, Marathahalli",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560037",
        latitude=12.9569,
        longitude=77.7011,
        phone="+91 80 4123 9988",
        email="support@medplus-marathahalli.com",
        is_verified=True,
        operating_hours="24 Hours Open",
        rating=4.7
    )
    db.add(pharmacy2)

    pharmacy3 = Pharmacy(
        name="Wellness Forever 24x7 Chemist",
        registration_number="KA-BNG-PH-2022-0781",
        license_number="DL-20B-KA-59102",
        gst_number="29CCCCC9012D1Z8",
        address="100 Feet Road, Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560038",
        latitude=12.9784,
        longitude=77.6408,
        phone="+91 80 6789 3344",
        email="care@wellnessforever-ind.com",
        is_verified=True,
        operating_hours="24 Hours Open",
        rating=4.8
    )
    db.add(pharmacy3)
    db.commit()

    # Link pharmacist
    pharmacist_profile = Pharmacist(
        user_id=pharmacist_user.id,
        pharmacy_id=pharmacy1.id,
        license_number="KSPC-REG-2015-88391",
        qualification="Master of Pharmacy (M.Pharm - Clinical Pharmacology)",
        is_verified=True
    )
    db.add(pharmacist_profile)

    # 3. SEED MEDICINES (Real, Authoritative Pharmacology Records)
    medicines_data = [
        {
            "code": "MED-001",
            "generic": "Metformin Hydrochloride",
            "brand": "Glycomet 500",
            "ingredients": "Metformin Hydrochloride IP",
            "composition": "Each prolonged release tablet contains: Metformin Hydrochloride IP 500 mg",
            "strength": "500 mg",
            "form": "Tablet",
            "manufacturer": "USV Private Limited",
            "category": "Antidiabetic",
            "classification": "Biguanide",
            "indications": "First-line pharmacotherapy for Type 2 Diabetes Mellitus; management of insulin resistance in Polycystic Ovary Syndrome (PCOS).",
            "contraindications": "Severe renal impairment (eGFR < 30 mL/min/1.73m2), metabolic acidosis, acute alcohol intoxication, severe hepatic failure, unstable heart failure.",
            "adverse_effects": "Gastrointestinal disturbances (nausea, diarrhea, abdominal pain), metallic taste, Vitamin B12 deficiency with prolonged use, rare lactic acidosis.",
            "storage": "Store in a cool and dry place away from direct sunlight. Below 25°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00331",
            "pubchem_cid": "4091",
            "smiles": "CN(C)C(=N)NC(=N)N",
            "mrp": 38.50
        },
        {
            "code": "MED-002",
            "generic": "Metformin Hydrochloride",
            "brand": "Cetapin 500",
            "ingredients": "Metformin Hydrochloride IP",
            "composition": "Each tablet contains: Metformin Hydrochloride IP 500 mg",
            "strength": "500 mg",
            "form": "Tablet",
            "manufacturer": "Sanofi India Limited",
            "category": "Antidiabetic",
            "classification": "Biguanide",
            "indications": "Monotherapy or adjunct therapy in management of Type 2 Diabetes Mellitus.",
            "contraindications": "Severe kidney dysfunction, acute myocardial infarction, diabetic ketoacidosis.",
            "adverse_effects": "Dyspepsia, flatulence, headache, dizziness.",
            "storage": "Protect from moisture and heat. Store below 30°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00331",
            "pubchem_cid": "4091",
            "smiles": "CN(C)C(=N)NC(=N)N",
            "mrp": 34.00
        },
        {
            "code": "MED-003",
            "generic": "Amlodipine Besylate",
            "brand": "Amlong 5",
            "ingredients": "Amlodipine Besylate IP",
            "composition": "Each uncoated tablet contains: Amlodipine Besylate IP equivalent to Amlodipine 5 mg",
            "strength": "5 mg",
            "form": "Tablet",
            "manufacturer": "Micro Labs Limited",
            "category": "Antihypertensive",
            "classification": "Dihydropyridine Calcium Channel Blocker",
            "indications": "Essential hypertension, chronic stable angina, vasospastic (Prinzmetal's) angina.",
            "contraindications": "Hypersensitivity to dihydropyridines, cardiogenic shock, severe aortic stenosis, unstable angina after MI.",
            "adverse_effects": "Peripheral ankle edema, flushing, palpitations, headache, fatigue.",
            "storage": "Store in a well-closed container below 25°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00381",
            "pubchem_cid": "2162",
            "smiles": "CCOC(=O)C1=C(NC(=C(C1C2=CC=CC=C2Cl)C(=O)OC)C)COCCN",
            "mrp": 42.00
        },
        {
            "code": "MED-004",
            "generic": "Amlodipine Besylate",
            "brand": "Norvasc 5",
            "ingredients": "Amlodipine Besylate IP",
            "composition": "Each tablet contains: Amlodipine Besylate equivalent to Amlodipine 5 mg",
            "strength": "5 mg",
            "form": "Tablet",
            "manufacturer": "Pfizer Limited",
            "category": "Antihypertensive",
            "classification": "Dihydropyridine Calcium Channel Blocker",
            "indications": "Hypertension and coronary artery disease management.",
            "contraindications": "Severe hypotension, cardiogenic shock.",
            "adverse_effects": "Pedal edema, fatigue, somnolence, flushing.",
            "storage": "Store protected from moisture and light.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00381",
            "pubchem_cid": "2162",
            "smiles": "CCOC(=O)C1=C(NC(=C(C1C2=CC=CC=C2Cl)C(=O)OC)C)COCCN",
            "mrp": 68.00
        },
        {
            "code": "MED-005",
            "generic": "Telmisartan",
            "brand": "Telma 40",
            "ingredients": "Telmisartan IP",
            "composition": "Each tablet contains: Telmisartan IP 40 mg",
            "strength": "40 mg",
            "form": "Tablet",
            "manufacturer": "Glenmark Pharmaceuticals Ltd",
            "category": "Antihypertensive",
            "classification": "Angiotensin II Receptor Blocker (ARB)",
            "indications": "Treatment of essential hypertension; reduction of cardiovascular morbidity in high-risk patients.",
            "contraindications": "Pregnancy (teratogenic / fetal toxicity in 2nd and 3rd trimesters), severe biliary obstructive disorders, severe hepatic impairment.",
            "adverse_effects": "Hyperkalemia, dizziness, orthostatic hypotension, back pain, sinus congestion.",
            "storage": "Store in the original blister pack to protect from moisture. Below 30°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00966",
            "pubchem_cid": "65999",
            "smiles": "CCCC1=NC2=C(N1CC3=CC=C(C=C3)C4=CC=CC=C4C(=O)O)C=C(C=C2)C5=NC6=CC=CC=C6N5C",
            "mrp": 115.00
        },
        {
            "code": "MED-006",
            "generic": "Atorvastatin Calcium",
            "brand": "Atorva 10",
            "ingredients": "Atorvastatin Calcium IP",
            "composition": "Each film coated tablet contains: Atorvastatin Calcium IP equivalent to Atorvastatin 10 mg",
            "strength": "10 mg",
            "form": "Tablet",
            "manufacturer": "Zydus Cadila Healthcare",
            "category": "Lipid Lowering",
            "classification": "HMG-CoA Reductase Inhibitor (Statin)",
            "indications": "Hypercholesterolemia, dyslipidemia, prevention of atherosclerotic cardiovascular events.",
            "contraindications": "Active liver disease, unexplained persistent elevations of hepatic transaminases, pregnancy, lactation.",
            "adverse_effects": "Myalgia, elevated liver enzymes (ALT/AST), dyspepsia, rhabdomyolysis (rare), elevated blood glucose.",
            "storage": "Store below 25°C in a dry place.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB01076",
            "pubchem_cid": "60823",
            "smiles": "CC(C)C1=C(C(=C(N1CCC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4",
            "mrp": 92.00
        },
        {
            "code": "MED-007",
            "generic": "Clopidogrel Bisulfate",
            "brand": "Clavix 75",
            "ingredients": "Clopidogrel Bisulfate IP",
            "composition": "Each film coated tablet contains: Clopidogrel Bisulfate IP equivalent to Clopidogrel 75 mg",
            "strength": "75 mg",
            "form": "Tablet",
            "manufacturer": "Sun Pharmaceutical Industries Ltd",
            "category": "Antiplatelet",
            "classification": "P2Y12 ADP Receptor Antagonist",
            "indications": "Secondary prevention of atherothrombotic events in myocardial infarction, ischemic stroke, or acute coronary syndrome.",
            "contraindications": "Active pathological bleeding (such as peptic ulcer or intracranial hemorrhage), severe hepatic impairment.",
            "adverse_effects": "Hematoma, epistaxis, gastrointestinal hemorrhage, purpura, bruising.",
            "storage": "Store protected from moisture at a temperature not exceeding 25°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00758",
            "pubchem_cid": "60606",
            "smiles": "COC(=O)C(C1=CC=CC=C1Cl)N2CCC3=C(C2)C=CS3",
            "mrp": 128.00
        },
        {
            "code": "MED-008",
            "generic": "Aspirin",
            "brand": "Ecosprin 75",
            "ingredients": "Aspirin IP",
            "composition": "Each enteric coated tablet contains: Aspirin IP 75 mg",
            "strength": "75 mg",
            "form": "Tablet",
            "manufacturer": "USV Private Limited",
            "category": "Antiplatelet / Analgesic",
            "classification": "Cyclooxygenase (COX-1) Inhibitor / Salicylate",
            "indications": "Prophylaxis of thromboembolic disorders, acute coronary syndrome, ischemic stroke prevention.",
            "contraindications": "Active peptic ulceration, bleeding diathesis, hemophilia, aspirin-induced asthma, children under 16 (Reye's syndrome risk).",
            "adverse_effects": "Gastric irritation, occult gastrointestinal bleeding, tinnitus in high doses, increased prothrombin time.",
            "storage": "Keep container tightly closed. Protect from moisture.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00945",
            "pubchem_cid": "2244",
            "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "mrp": 12.50
        },
        {
            "code": "MED-009",
            "generic": "Warfarin Sodium",
            "brand": "Warf 2",
            "ingredients": "Warfarin Sodium IP",
            "composition": "Each tablet contains: Warfarin Sodium IP 2 mg",
            "strength": "2 mg",
            "form": "Tablet",
            "manufacturer": "Cipla Limited",
            "category": "Anticoagulant",
            "classification": "Vitamin K Epoxide Reductase Antagonist",
            "indications": "Prophylaxis and treatment of venous thromboembolism, pulmonary embolism, thromboembolic complications associated with atrial fibrillation.",
            "contraindications": "Pregnancy (fetal warfarin syndrome), hemorrhagic tendencies, recent surgery, severe uncontrolled hypertension, peptic ulcer.",
            "adverse_effects": "Major hemorrhages, skin necrosis, purple toe syndrome, alopecia, microembolization.",
            "storage": "Store protected from light and moisture below 25°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00682",
            "pubchem_cid": "54678486",
            "smiles": "CC(=O)CC(C1=CC=CC=C1)C2=C(C3=CC=CC=C3OC2=O)O",
            "mrp": 54.00
        },
        {
            "code": "MED-010",
            "generic": "Ibuprofen",
            "brand": "Brufen 400",
            "ingredients": "Ibuprofen IP",
            "composition": "Each film coated tablet contains: Ibuprofen IP 400 mg",
            "strength": "400 mg",
            "form": "Tablet",
            "manufacturer": "Abbott India Limited",
            "category": "Analgesic / Anti-inflammatory",
            "classification": "Non-Steroidal Anti-Inflammatory Drug (NSAID)",
            "indications": "Relief of mild to moderate pain, inflammation, osteoarthritis, rheumatoid arthritis, dysmenorrhea.",
            "contraindications": "Active gastrointestinal ulceration or bleeding, severe heart failure (NYHA class IV), severe renal/hepatic impairment, third trimester pregnancy.",
            "adverse_effects": "Dyspepsia, GI ulceration, fluid retention, hypertension, acute renal impairment.",
            "storage": "Store in a cool dry place below 30°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": False, # Often OTC in lower pack sizes, but marked Schedule H in India
            "drugbank_id": "DB01050",
            "pubchem_cid": "3672",
            "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
            "mrp": 21.00
        },
        {
            "code": "MED-011",
            "generic": "Paracetamol",
            "brand": "Dolo 650",
            "ingredients": "Paracetamol IP",
            "composition": "Each uncoated tablet contains: Paracetamol IP 650 mg",
            "strength": "650 mg",
            "form": "Tablet",
            "manufacturer": "Micro Labs Limited",
            "category": "Antipyretic / Analgesic",
            "classification": "Para-aminophenol derivative",
            "indications": "Treatment of mild to moderate fever and pain relief (headache, body ache, arthralgia).",
            "contraindications": "Severe active liver disease, acute liver failure, known hypersensitivity to paracetamol.",
            "adverse_effects": "Hepatotoxicity in overdose (>4g/day), cutaneous hypersensitivity reactions, thrombocytopenia (rare).",
            "storage": "Store below 25°C. Protect from direct heat and light.",
            "prescription_class": "OTC",
            "requires_prescription": False,
            "drugbank_id": "DB00316",
            "pubchem_cid": "1983",
            "smiles": "CC(=O)NC1=CC=C(C=C1)O",
            "mrp": 33.50
        },
        {
            "code": "MED-012",
            "generic": "Paracetamol",
            "brand": "Calpol 650",
            "ingredients": "Paracetamol IP",
            "composition": "Each tablet contains: Paracetamol IP 650 mg",
            "strength": "650 mg",
            "form": "Tablet",
            "manufacturer": "GlaxoSmithKline Pharmaceuticals Ltd",
            "category": "Antipyretic / Analgesic",
            "classification": "Para-aminophenol derivative",
            "indications": "Management of pyrexia and symptomatic relief of aches.",
            "contraindications": "Hepatic impairment, chronic alcoholism.",
            "adverse_effects": "Rare allergic rash, elevated transaminases in supratherapeutic dosage.",
            "storage": "Store protected from moisture at room temperature.",
            "prescription_class": "OTC",
            "requires_prescription": False,
            "drugbank_id": "DB00316",
            "pubchem_cid": "1983",
            "smiles": "CC(=O)NC1=CC=C(C=C1)O",
            "mrp": 31.00
        },
        {
            "code": "MED-013",
            "generic": "Omeprazole",
            "brand": "Omez 20",
            "ingredients": "Omeprazole IP",
            "composition": "Each hard gelatin capsule contains: Omeprazole IP 20 mg (as enteric coated pellets)",
            "strength": "20 mg",
            "form": "Capsule",
            "manufacturer": "Dr. Reddy's Laboratories Ltd",
            "category": "Gastrointestinal",
            "classification": "Proton Pump Inhibitor (PPI)",
            "indications": "Gastroesophageal reflux disease (GERD), peptic ulcer disease, Zollinger-Ellison syndrome, eradication of H. pylori.",
            "contraindications": "Concomitant administration with nelfinavir or rilpivirine, hypersensitivity to substituted benzimidazoles.",
            "adverse_effects": "Headache, diarrhea, constipation, hypomagnesemia with long-term use, increased risk of Clostridioides difficile.",
            "storage": "Store in a dry place below 25°C. Protect from moisture.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00338",
            "pubchem_cid": "4594",
            "smiles": "CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC",
            "mrp": 58.00
        },
        {
            "code": "MED-014",
            "generic": "Pantoprazole Sodium",
            "brand": "Pan 40",
            "ingredients": "Pantoprazole Sodium IP",
            "composition": "Each enteric coated tablet contains: Pantoprazole Sodium IP equivalent to Pantoprazole 40 mg",
            "strength": "40 mg",
            "form": "Tablet",
            "manufacturer": "Alkem Laboratories Ltd",
            "category": "Gastrointestinal",
            "classification": "Proton Pump Inhibitor (PPI)",
            "indications": "Short-term treatment of erosive esophagitis associated with GERD; pathological hypersecretory conditions.",
            "contraindications": "Severe hypersensitivity to pantoprazole or excipients.",
            "adverse_effects": "Abdominal discomfort, flatulence, dizziness, arthralgia.",
            "storage": "Store in original blister packaging at room temperature.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00213",
            "pubchem_cid": "4679",
            "smiles": "COC1=C(C(=NC=C1)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC(F)F)OC",
            "mrp": 142.00
        },
        {
            "code": "MED-015",
            "generic": "Amoxicillin and Potassium Clavulanate",
            "brand": "Augmentin 625 Duo",
            "ingredients": "Amoxicillin Trihydrate IP and Potassium Clavulanate IP",
            "composition": "Each film coated tablet contains: Amoxicillin Trihydrate IP equivalent to Amoxicillin 500 mg, Potassium Clavulanate IP equivalent to Clavulanic Acid 125 mg",
            "strength": "625 mg",
            "form": "Tablet",
            "manufacturer": "GlaxoSmithKline Pharmaceuticals Ltd",
            "category": "Antibacterial",
            "classification": "Beta-lactam + Beta-lactamase Inhibitor",
            "indications": "Lower respiratory tract infections, acute bacterial otitis media, sinusitis, skin and soft tissue infections.",
            "contraindications": "History of penicillin hypersensitivity, amoxicillin/clavulanate-associated cholestatic jaundice or hepatic dysfunction.",
            "adverse_effects": "Diarrhea, candidiasis, nausea, rash, elevated liver enzymes.",
            "storage": "Keep in desiccant foil container below 25°C. Moisture sensitive.",
            "prescription_class": "Schedule H1",
            "requires_prescription": True,
            "drugbank_id": "DB01060",
            "pubchem_cid": "33613",
            "smiles": "CC1(C(N2C(S1)C(C2=O)NC(=O)C(C3=CC=C(C=C3)O)N)C(=O)O)C",
            "mrp": 204.00
        },
        {
            "code": "MED-016",
            "generic": "Azithromycin",
            "brand": "Azithral 500",
            "ingredients": "Azithromycin Dihydrate IP",
            "composition": "Each film coated tablet contains: Azithromycin Dihydrate IP equivalent to Azithromycin anhydrous 500 mg",
            "strength": "500 mg",
            "form": "Tablet",
            "manufacturer": "Alembic Pharmaceuticals Ltd",
            "category": "Antibacterial",
            "classification": "Macrolide Antibiotic (Azalide)",
            "indications": "Community-acquired pneumonia, acute bacterial sinusitis, streptococcal pharyngitis, urethritis/cervicitis.",
            "contraindications": "Hypersensitivity to azithromycin, erythromycin, or any macrolide; history of cholestatic jaundice with prior use; baseline QT prolongation.",
            "adverse_effects": "Diarrhea, nausea, QT interval prolongation, cardiac arrhythmia in susceptible individuals.",
            "storage": "Store below 30°C in a dry place.",
            "prescription_class": "Schedule H1",
            "requires_prescription": True,
            "drugbank_id": "DB00207",
            "pubchem_cid": "55185",
            "smiles": "CCC1C(C(C(N(CC(CC(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)O)(C)O",
            "mrp": 132.00
        },
        {
            "code": "MED-017",
            "generic": "Levothyroxine Sodium",
            "brand": "Thyronorm 50 mcg",
            "ingredients": "Levothyroxine Sodium IP",
            "composition": "Each uncoated tablet contains: Levothyroxine Sodium IP equivalent to anhydrous Levothyroxine Sodium 50 mcg",
            "strength": "50 mcg",
            "form": "Tablet",
            "manufacturer": "Abbott India Limited",
            "category": "Endocrine",
            "classification": "Synthetic Thyroid Hormone (T4)",
            "indications": "Replacement therapy in primary, secondary, and tertiary hypothyroidism.",
            "contraindications": "Subclinical or overt thyrotoxicosis, uncorrected adrenal cortical insufficiency, acute myocardial infarction.",
            "adverse_effects": "Tachycardia, tremors, palpitations, heat intolerance, weight loss with over-replacement.",
            "storage": "Store in the tightly closed original amber bottle below 25°C. Light and moisture sensitive.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00451",
            "pubchem_cid": "5819",
            "smiles": "C1=C(C=C(C(=C1I)OC2=CC(=C(C(=C2)I)O)I)I)CC(C(=O)O)N",
            "mrp": 145.00
        },
        {
            "code": "MED-018",
            "generic": "Ciprofloxacin Hydrochloride",
            "brand": "Ciplox 500",
            "ingredients": "Ciprofloxacin Hydrochloride IP",
            "composition": "Each film coated tablet contains: Ciprofloxacin Hydrochloride IP equivalent to Ciprofloxacin 500 mg",
            "strength": "500 mg",
            "form": "Tablet",
            "manufacturer": "Cipla Limited",
            "category": "Antibacterial",
            "classification": "Fluoroquinolone Antibacterial",
            "indications": "Urinary tract infections, infectious diarrhea, typhoid fever, complicated intra-abdominal infections.",
            "contraindications": "Concurrent administration with tizanidine, history of fluoroquinolone-induced tendonitis or tendon rupture, myasthenia gravis.",
            "adverse_effects": "Tendinopathy, tendon rupture, peripheral neuropathy, CNS effects (confusion, seizures), QT prolongation.",
            "storage": "Store protected from moisture and direct light.",
            "prescription_class": "Schedule H1",
            "requires_prescription": True,
            "drugbank_id": "DB00537",
            "pubchem_cid": "2764",
            "smiles": "C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O",
            "mrp": 45.00
        },
        {
            "code": "MED-019",
            "generic": "Simvastatin",
            "brand": "Zocor 20",
            "ingredients": "Simvastatin USP",
            "composition": "Each tablet contains: Simvastatin USP 20 mg",
            "strength": "20 mg",
            "form": "Tablet",
            "manufacturer": "Organon / MSD",
            "category": "Lipid Lowering",
            "classification": "HMG-CoA Reductase Inhibitor",
            "indications": "Adjunct to diet to reduce total cholesterol, LDL-C, and triglycerides in primary hypercholesterolemia.",
            "contraindications": "Concomitant strong CYP3A4 inhibitors (clarithromycin, itraconazole), gemfibrozil, pregnancy, active liver disease.",
            "adverse_effects": "Myopathy, rhabdomyolysis, abdominal pain, flatulence.",
            "storage": "Store below 25°C.",
            "prescription_class": "Schedule H",
            "requires_prescription": True,
            "drugbank_id": "DB00641",
            "pubchem_cid": "54454",
            "smiles": "CCC(C)(C)C(=O)OC1CC(C=C2C1C(C(C=C2)C)CCC3CC(CC(=O)O3)O)C",
            "mrp": 85.00
        },
        {
            "code": "MED-020",
            "generic": "Clarithromycin",
            "brand": "Claribid 500",
            "ingredients": "Clarithromycin IP",
            "composition": "Each film coated tablet contains: Clarithromycin IP 500 mg",
            "strength": "500 mg",
            "form": "Tablet",
            "manufacturer": "Pfizer Limited",
            "category": "Antibacterial",
            "classification": "Macrolide Antibiotic / Potent CYP3A4 Inhibitor",
            "indications": "Pharyngitis, community-acquired pneumonia, skin and skin structure infections, H. pylori eradication.",
            "contraindications": "Concomitant use with simvastatin, lovastatin, pimozide, astemizole, or ergot alkaloids; history of cholestatic jaundice.",
            "adverse_effects": "Metallic dysgeusia, nausea, diarrhea, abdominal pain, hepatotoxicity.",
            "storage": "Store below 25°C in a dry place.",
            "prescription_class": "Schedule H1",
            "requires_prescription": True,
            "drugbank_id": "DB01211",
            "pubchem_cid": "84029",
            "smiles": "CCC1C(C(C(C(=O)C(CC(C(C(C(C(=O)O1)C)OC2CC(C(C(O2)C)O)(C)OC)C)OC3C(C(CC(O3)C)N(C)C)O)(C)O)C)C)O)(C)OC",
            "mrp": 270.00
        }
    ]

    med_objs = []
    for item in medicines_data:
        m = Medicine(
            medicine_code=item["code"],
            generic_name=item["generic"],
            brand_name=item["brand"],
            active_ingredients=item["ingredients"],
            composition=item["composition"],
            strength=item["strength"],
            dosage_form=item["form"],
            manufacturer=item["manufacturer"],
            therapeutic_category=item["category"],
            drug_classification=item["classification"],
            approved_indications=item["indications"],
            contraindications=item["contraindications"],
            known_adverse_effects=item["adverse_effects"],
            storage_information=item["storage"],
            prescription_classification=item["prescription_class"],
            requires_prescription=item["requires_prescription"],
            drugbank_id=item["drugbank_id"],
            pubchem_cid=item["pubchem_cid"],
            smiles=item["smiles"],
            source="Central Drugs Standard Control Organisation (CDSCO) / FDA Approved Drug Products",
            last_verified_date="2026-03-20",
            base_mrp=item["mrp"]
        )
        db.add(m)
        med_objs.append(m)
    db.commit()

    # 4. SEED SAFETY LAYER 1: VERIFIED CURATED CLINICAL DRUG-DRUG INTERACTIONS
    interactions_data = [
        {
            "drug_a": "Warfarin Sodium",
            "drug_b": "Aspirin",
            "severity": "Contraindicated",
            "mechanism": "Synergistic pharmacodynamic inhibition of hemostasis. Aspirin irreversibly inhibits platelet COX-1-mediated thromboxane A2 production, while Warfarin depletes Vitamin K-dependent clotting factors (II, VII, IX, X). In addition, high-dose aspirin can displace warfarin from albumin binding sites.",
            "clinical_consequences": "Marked exponential increase in gastrointestinal hemorrhage, intracranial bleeding, and major systemic hemorrhagic events. Concomitant use requires strict specialist authorization, INR target recalibration, and gastroprotective co-prescription.",
            "source": "British National Formulary (BNF 86) / FDA Drug Safety Communication",
            "reference": "BNF Section 2.8.2; FDA Warfarin Package Insert Section 7.2"
        },
        {
            "drug_a": "Warfarin Sodium",
            "drug_b": "Ibuprofen",
            "severity": "Contraindicated",
            "mechanism": "Ibuprofen reversibly inhibits platelet cyclooxygenase (COX-1), impairs platelet aggregation, and induces gastric mucosal erosions. Competitive displacement of S-warfarin from human serum albumin enhances free anticoagulant fraction.",
            "clinical_consequences": "Severe risk of massive upper gastrointestinal bleeding and prolonged bleeding time. NSAID-induced nephrotoxicity also impairs drug clearance.",
            "source": "WHO International Pharmacovigilance Advisory / CDSCO Safety Circular",
            "reference": "WHO Drug Information Vol 35; CDSCO Pharmacovigilance Programme of India (PvPI)"
        },
        {
            "drug_a": "Clopidogrel Bisulfate",
            "drug_b": "Omeprazole",
            "severity": "Major",
            "mechanism": "Competitive inhibition of cytochrome P450 CYP2C19. Clopidogrel is a prodrug requiring biotransformation by CYP2C19 to form its active thiol metabolite. Omeprazole strongly inhibits CYP2C19, significantly reducing active metabolite levels.",
            "clinical_consequences": "Decreased platelet inhibitory effect resulting in increased risk of recurrent myocardial infarction, stent thrombosis, and ischemic cardiovascular events. Switch to pantoprazole is recommended if a PPI is clinically necessary.",
            "source": "FDA Boxed Warning & EMA Pharmacovigilance Risk Assessment",
            "reference": "FDA Drug Safety Communication (Clopidogrel/Omeprazole); EMA/PRAC/582014"
        },
        {
            "drug_a": "Simvastatin",
            "drug_b": "Clarithromycin",
            "severity": "Contraindicated",
            "mechanism": "Potent pharmacokinetic CYP3A4 inhibition. Clarithromycin is a strong mechanism-based inhibitor of CYP3A4, the primary enzyme responsible for simvastatin lactone metabolism, increasing simvastatin systemic exposure (AUC) by >10-fold.",
            "clinical_consequences": "Extreme risk of severe skeletal muscle toxicity, myopathy, and life-threatening rhabdomyolysis leading to acute renal failure. Simvastatin must be suspended during clarithromycin treatment.",
            "source": "FDA Label Update (Zocor / Biaxin Co-administration Directive)",
            "reference": "FDA MedWatch Alert 2011; Clin Pharmacol Ther. 2012;92(1):118-128"
        },
        {
            "drug_a": "Atorvastatin Calcium",
            "drug_b": "Clarithromycin",
            "severity": "Major",
            "mechanism": "CYP3A4 and OATP1B1 transport inhibition by clarithromycin increases atorvastatin acid plasma concentration by approximately 4.5-fold.",
            "clinical_consequences": "Elevated incidence of myalgia, elevated serum creatine kinase, and risk of rhabdomyolysis. Atorvastatin dose must not exceed 20 mg daily during concurrent therapy.",
            "source": "FDA Drug Labeling Review / Micromedex DrugDex",
            "reference": "Micromedex Interaction Class: Major; FDA Lipitor Prescribing Information"
        },
        {
            "drug_a": "Metformin Hydrochloride",
            "drug_b": "Ciprofloxacin Hydrochloride",
            "severity": "Moderate",
            "mechanism": "Fluoroquinolones interfere with pancreatic beta-cell potassium-ATP channels and glucose homeostasis, while competitive renal OCT2/MATE transporter interaction may alter metformin elimination.",
            "clinical_consequences": "Severe dysglycemia (both severe hypoglycemia and unpredictable hyperglycemia). Close blood glucose monitoring is required.",
            "source": "FDA Drug Safety Communication on Fluoroquinolone Hypoglycemic Risks",
            "reference": "FDA Safety Alert July 2018; American Diabetes Association Standards of Care"
        },
        {
            "drug_a": "Telmisartan",
            "drug_b": "Ibuprofen",
            "severity": "Major",
            "mechanism": "NSAIDs inhibit renal prostaglandin synthesis, blunting prostaglandin-mediated afferent arteriolar vasodilation. ARBs block angiotensin II-mediated efferent arteriolar constriction.",
            "clinical_consequences": "Acute drop in glomerular filtration rate (GFR), precipitating acute kidney injury (triple whammy effect when combined with diuretics) and attenuation of antihypertensive efficacy.",
            "source": "American Journal of Kidney Diseases / Kidney Disease Improving Global Outcomes (KDIGO)",
            "reference": "KDIGO Clinical Practice Guideline for Acute Kidney Injury; BMJ 2013;346:e8507"
        },
        {
            "drug_a": "Amlodipine Besylate",
            "drug_b": "Simvastatin",
            "severity": "Moderate",
            "mechanism": "Mild inhibition of CYP3A4 by amlodipine increases peak simvastatin concentration and AUC by approximately 77%.",
            "clinical_consequences": "Increased potential for statin-induced muscle pain and elevated transaminases. The daily dose of simvastatin should not exceed 20 mg when co-prescribed with amlodipine.",
            "source": "FDA Drug Safety Communication: Simvastatin dose limitations",
            "reference": "FDA Drug Safety Announcement June 2011"
        },
        {
            "drug_a": "Levothyroxine Sodium",
            "drug_b": "Pantoprazole Sodium",
            "severity": "Moderate",
            "mechanism": "Levothyroxine requires an acidic gastric environment for optimal dissolution and intestinal absorption. PPI-induced gastric hypoacidity reduces levothyroxine bioavailability.",
            "clinical_consequences": "Elevated serum TSH levels and failure to achieve euthyroid state. Separation of doses by at least 4 hours and periodic TSH monitoring is recommended.",
            "source": "Thyroid (Official Journal of the American Thyroid Association)",
            "reference": "Thyroid. 2014;24(12):1670-1689; ATA/AACE Hypothyroidism Guidelines"
        },
        {
            "drug_a": "Aspirin",
            "drug_b": "Ibuprofen",
            "severity": "Major",
            "mechanism": "Competitive binding antagonism at platelet COX-1 active site. Ibuprofen reversibly binds to the Ser529 channel, sterically hindering aspirin from irreversibly acetylating the catalytic site.",
            "clinical_consequences": "Loss of aspirin's cardioprotective antiplatelet efficacy, increasing thrombotic risk in cardiovascular patients. Ibuprofen should be taken at least 2 hours after or 8 hours before immediate-release aspirin.",
            "source": "FDA Science Advisory on Concomitant Use of Ibuprofen and Aspirin",
            "reference": "FDA Health Advisory 2006; NEJM 2001;345(25):1809-1817"
        }
    ]

    for inter in interactions_data:
        rule = DrugInteraction(
            drug_a_generic=inter["drug_a"],
            drug_b_generic=inter["drug_b"],
            severity_category=inter["severity"],
            mechanism=inter["mechanism"],
            clinical_consequences=inter["clinical_consequences"],
            evidence_source=inter["source"],
            source_reference=inter["reference"],
            last_verified_date="2026-03-20"
        )
        db.add(rule)
    db.commit()

    # 5. SEED SUPPLIERS & INVENTORY
    supplier1 = Supplier(
        pharmacy_id=pharmacy1.id,
        name="MedLife Pharma Distributors India Pvt Ltd",
        contact_person="Ramesh Gupta",
        phone="+91 80 2345 6789",
        email="orders@medlife-distributors.com",
        address="Warehouse 4A, Peenya Industrial Area, Bengaluru",
        gst_number="29AAACM4455P1Z8"
    )
    db.add(supplier1)
    db.commit()

    # Seed inventory for pharmacies with realistic batch numbers and expiry dates
    # (Including near-expiry and healthy batches for inventory alert demonstration)
    for pharm in [pharmacy1, pharmacy2]:
        for i, med in enumerate(med_objs):
            inv = PharmacyInventory(
                pharmacy_id=pharm.id,
                medicine_id=med.id,
                stock_quantity=85 if i != 2 else 6, # One low-stock item for testing alerts
                low_stock_threshold=15,
                is_available=True
            )
            db.add(inv)
            db.commit()

            # Add healthy batch
            b1 = MedicineBatch(
                inventory_id=inv.id,
                batch_number=f"BT-{med.id}01-{pharm.id}",
                expiry_date="2027-08-30",
                purchase_price=round(med.base_mrp * 0.72, 2),
                selling_price=med.base_mrp,
                mrp=med.base_mrp,
                quantity=inv.stock_quantity,
                supplier_id=supplier1.id
            )
            db.add(b1)

            # For medicine 5, add a near-expiry batch for testing alert logic
            if i == 4 and pharm.id == pharmacy1.id:
                b_exp = MedicineBatch(
                    inventory_id=inv.id,
                    batch_number=f"BT-{med.id}99-EXP",
                    expiry_date="2026-04-10", # Near expiry
                    purchase_price=round(med.base_mrp * 0.70, 2),
                    selling_price=med.base_mrp,
                    mrp=med.base_mrp,
                    quantity=8,
                    supplier_id=supplier1.id
                )
                db.add(b_exp)
    db.commit()

    # 6. SEED VERIFIED RAG MEDICAL KNOWLEDGE REPOSITORY
    rag_sources = [
        {
            "title": "Hypertension Pharmacotherapy & ARB/CCB Safety Protocols",
            "category": "Cardiovascular Pharmacology",
            "content": "Telmisartan is an Angiotensin II receptor antagonist used for essential hypertension. It blocks AT1 receptors, preventing vasoconstriction and aldosterone secretion. When combined with Amlodipine, synergistic blood pressure reduction is achieved without compensatory reflex tachycardia. Warning: Never combine Telmisartan with ACE inhibitors or Aliskiren in diabetic patients due to hyperkalemia and renal damage risks. NSAIDs like Ibuprofen blunt antihypertensive efficacy.",
            "source": "Joint National Committee (JNC 8) / European Society of Cardiology Guidelines",
            "date": "2026-01-15"
        },
        {
            "title": "Metformin Clinical Usage, Lactic Acidosis, and Renal Safety Thresholds",
            "category": "Endocrine & Metabolic Pharmacology",
            "content": "Metformin improves insulin sensitivity and decreases hepatic gluconeogenesis via AMPK activation. Dosage starts at 500 mg daily with food to minimize GI intolerance. Renal threshold: Contraindicated when estimated GFR < 30 mL/min/1.73m2. Must be temporarily withheld prior to iodinated contrast procedures. Overdose or severe tissue hypoperfusion can precipitate life-threatening lactic acidosis with symptoms of hypothermia, hypotension, and resistant bradyarrhythmias.",
            "source": "American Diabetes Association (ADA) Standards of Medical Care in Diabetes",
            "date": "2026-02-10"
        },
        {
            "title": "Dual Antiplatelet Therapy (DAPT) and Anticoagulant Bleeding Guardrails",
            "category": "Hematology & Thrombosis Safety",
            "content": "Aspirin (75-100 mg daily) and Clopidogrel (75 mg daily) are indicated following acute coronary syndrome or percutaneous coronary intervention. Concomitant administration of oral anticoagulants (Warfarin) exponentially multiplies major bleeding risk (intracranial and GI). PPI co-prescription is recommended for gastroprotection; however, Omeprazole should be avoided with Clopidogrel due to CYP2C19 competitive inhibition. Pantoprazole is the safe alternative.",
            "source": "American College of Cardiology (ACC) / American Heart Association (AHA) DAPT Guidelines",
            "date": "2026-01-20"
        },
        {
            "title": "Antibiotic Stewardship: Augmentin, Ciprofloxacin & Macrolide Red Flags",
            "category": "Infectious Diseases & Antibacterial Guidelines",
            "content": "Augmentin (Amoxicillin + Clavulanic Acid) is active against beta-lactamase-producing pathogens. Diarrhea occurs in ~9% of patients; taking with meals reduces GI distress. Ciprofloxacin carries black box warnings for tendinitis, tendon rupture, peripheral neuropathy, and CNS toxicities. Macrolides like Azithromycin and Clarithromycin prolong the QT interval and must not be used with class IA or III antiarrhythmics or strong CYP3A4-cleared statins.",
            "source": "Infectious Diseases Society of America (IDSA) Guidelines / CDSCO Antibiotic Policy",
            "date": "2026-02-28"
        },
        {
            "title": "Red-Flag Emergency Symptoms in Clinical Pharmacy Practice",
            "category": "Clinical Triage & Emergency Protocols",
            "content": "Immediate emergency room referral is required for: crushing retrosternal chest pain radiating to left arm/jaw, acute unilateral facial droop, arm weakness or slurred speech (FAST criteria), acute stridor, angioedema of tongue/lips with dyspnea (anaphylaxis), sudden thunderclap headache, hematemesis (coffee-ground emesis) or melena, and acute suicidal ideation. Never attempt to treat acute emergency conditions with self-medication.",
            "source": "NICE Emergency Triage Protocols / Resuscitation Council UK",
            "date": "2026-03-01"
        }
    ]

    for doc in rag_sources:
        k = AIKnowledgeSource(
            title=doc["title"],
            category=doc["category"],
            content=doc["content"],
            reference_source=doc["source"],
            verification_date=doc["date"]
        )
        db.add(k)
    db.commit()

    print(f"Successfully seeded database with {len(med_objs)} medicines, {len(interactions_data)} clinical rules, 3 verified pharmacies, and 5 authoritative medical knowledge monographs.")
