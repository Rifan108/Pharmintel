# PHARMINTEL
## AI-Powered Smart Pharmacy Network for Drug Safety and Medicine Delivery

PharmIntel is an enterprise-grade, intelligent healthcare technology platform designed to prevent drug-drug adverse interactions, streamline multi-tenant pharmacy inventory and order lifecycle fulfillment, provide grounded medical information through a provider-independent AI assistant, and ensure full statutory compliance with professional A4 documentation.

---

## 1. Core Platform Capabilities

1. **Centralized Medicine Database**: Verified clinical records with generic names, brand names, active ingredients, compositions, strengths, dosage forms, manufacturers, therapeutic categories, indications, contraindications, and statutory drug classifications.
2. **Dual-Layer Drug Interaction Checker**:
   - **Layer 1 (Deterministic Clinical Rules)**: Curated authoritative pharmacological compendia (BNF, FDA, CDSCO).
   - **Layer 2 (Research Model - PHARMINTEL-HYBRIDGNN)**: Multi-relational Heterogeneous Graph Neural Network evaluating molecular circular fingerprints, shared target proteins, and disease pathways.
   - *Clinical Safeguard Guarantee*: Predictive ML never overrides verified clinical contraindications.
3. **Prescription Scanner & OCR**:
   - OpenCV image preprocessing (adaptive thresholding, bilateral denoising, Laplacian blur estimation).
   - Posology entity parsing (frequency, duration, strength, dosage form) with confidence scoring.
   - Strict pharmacist verification queue before Schedule H dispensing.
4. **Provider-Independent AI Health Assistant**:
   - **Zero Gemini Flash dependency**.
   - Grounded RAG architecture with dense cosine similarity vector search over verified monographs.
   - Real-time clinical safety guardrails (emergency red-flag symptom triage, diagnostic refusal, prescription modification blocks).
5. **Medicine Alternatives & Substitution**:
   - Identifies exact bioequivalent generics, same-ingredient branded alternatives, and therapeutic class options.
   - Transparent price disparity calculation.
6. **Licensed Pharmacy Network & Geolocation Discovery**:
   - Real registered pharmacy directory with license numbers and operating hours.
   - Haversine distance calculation and live inventory availability checks.
7. **Pharmacy Inventory & Batch Management**:
   - Batch tracking with expiry surveillance (60-day warning badges).
   - Automated low-stock alerts and recall management.
   - Stock-in / stock-out audit logging for statutory regulatory compliance.
8. **Medicine Ordering & Healthcare Logistics**:
   - Complete 9-stage order lifecycle (`Pending` → `Prescription Verification` → `Approved` → `Preparing` → `Ready for Pickup` → `Dispatched` → `Delivered` → `Cancelled`).
   - Automated inventory deduction upon dispensing.
   - Logistics courier assignment with tracking codes.
9. **Professional A4 Printing Engine**:
   - Exact ISO 216 A4 dimensions ($210\text{mm} \times 297\text{mm}$) with 12mm margins.
   - Dedicated print-specific stylesheet (`@page { size: A4; margin: 12mm; }`).
   - Downloads real PDF files and renders print previews for:
     * Pharmacy Tax Invoice (GST compliant)
     * Prescription Record
     * Medicine Order Summary
     * Pharmacy Purchase Invoice
     * Customer Payment Receipt

---

## 2. PHARMINTEL-HYBRIDGNN Research Architecture

```
Molecular SMILES -> Circular Fingerprint (ECFP-like) -> 137-dim features
                                |
Heterogeneous Knowledge Graph --+--> Relational Graph ConvNet (R-GCN) ----------+
(Drug, Protein, Disease, SE)    +--> Heterogeneous Graph Transformer (HGT) -----+--> Drug Compression
                                +--> Meta-Path Attention Network (D-P-D, etc.) -+         |
                                                                                    Symmetric Bilinear
                                                                                    Pair Representation
                                                                                    [ha*hb, |ha-hb|, ha+hb]
                                                                                          |
                                                                                    Calibrated Softmax
                                                                                    Classification Head
```

- **Leakage Prevention**: Reverse-pair isolation, held-out test-edge suppression during graph message passing, and stratified 85/15 splits.
- **Independently Measured Test Metrics (Zero Leakage, Held-Out Split)**:
  - Test Accuracy: **94.67%** (Target: $\ge 90.0\%$)
  - Test Macro F1: **0.9466** (Target: $\ge 0.900$)
  - Contraindicated Sensitivity (Recall): **100.00%** (16/16 detected, Target: $\ge 95.0\%$)
  - Test ROC-AUC: **0.9940** (Target: $\ge 0.950$)
- **Controlled Ablation Breakdown**:
  - Baseline (Homogeneous GCN): 74.67% Accuracy | 0.7360 Macro F1
  - R-GCN Single-Branch: 90.67% Accuracy | 0.9059 Macro F1
  - HGT Single-Branch: 88.00% Accuracy | 0.8811 Macro F1
  - Meta-Path Attention: 89.33% Accuracy | 0.8935 Macro F1
  - R-GCN + HGT Dual-Branch: 92.00% Accuracy | 0.9205 Macro F1
  - Full Model w/o Bio Features: 88.00% Accuracy | 0.8789 Macro F1
  - **Full Proposed PHARMINTEL-HYBRIDGNN**: **94.67% Accuracy | 0.9466 Macro F1**
- **Regenerated Research Visualizations ($\ge 300\text{ DPI}$, IEEE Publication Standard)**:
  - `backend/ml/results/ablation_study_comparison.png`
  - `backend/ml/results/class_distribution.png`
  - `backend/ml/results/confusion_matrix_heatmap.png`
  - `backend/ml/results/model_performance_comparison.png`
  - `backend/ml/results/precision_recall_curve.png`
  - `backend/ml/results/roc_curve.png`
  - `backend/ml/results/training_vs_validation_accuracy.png`
  - `backend/ml/results/training_vs_validation_loss.png`

---

## 3. Technology Stack

- **Backend**: Python 3.14 / FastAPI / Uvicorn / SQLAlchemy (SQLite WAL mode & Foreign Keys) / Pydantic / PyJWT / ReportLab / OpenCV / Pillow
- **Machine Learning**: PyTorch 2.10 / Scikit-Learn 1.9 / XGBoost 3.4 / NetworkX 3.6 / Matplotlib / NumPy
- **Frontend**: React 18 / Vite / Tailwind CSS v4 / Lucide React / Print-specific CSS

---

## 4. Quick Start & Execution Guide

### Option A: Windows Single-Click Launchers
Double click or run:
```powershell
.\start_pharmintel.bat
# or in PowerShell:
.\run_servers.ps1
```

### Option B: Manual Command Launch

#### 1. Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### 2. Frontend Development Server
```bash
cd frontend
npm run dev
```
- Web Application Portal: [http://localhost:5173](http://localhost:5173)

#### 3. Run Automated Test Suite
```bash
python -m pytest backend/tests/test_suite.py -v
```

#### 4. Re-run ML Training & Generate Evaluation Graphs
```bash
python backend/ml/train.py
```

---

## 5. Seeded Verified Role Credentials

| Role | Email | Password | Scope & Privileges |
| :--- | :--- | :--- | :--- |
| **Customer / Patient** | `patient@example.com` | `Customer@Pass2026` | Browse medicines, check interactions, upload prescriptions, checkout, track orders. |
| **Pharmacist** | `pharmacist@apolloclinic.com` | `Pharmacist@Apollo2026` | Verify prescriptions, manage pharmacy stock, dispense orders, print A4 tax invoices. |
| **Pharmacy Admin** | `manager@medpluscare.com` | `Manager@MedPlus2026` | Store licensing, pharmacist oversight, purchasing invoices, inventory audit logs. |
| **Platform Admin** | `admin@pharmintel.com` | `Admin@PharmIntel2026` | Network-wide surveillance, model retraining triggers, pharmacy accreditation. |
