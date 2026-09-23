# 12C – AI-Based Medical Travel Decision Support System

[![Python FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React TypeScript](https://img.shields.io/badge/React-18.2-61DAFB.svg?logo=react)](https://reactjs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38BDF8.svg?logo=tailwindcss)](https://tailwindcss.com)
[![BiomedicalNER](https://img.shields.io/badge/PyTorch-Biomedical_NER-EE4C2C.svg?logo=pytorch)](https://huggingface.co/d4data/biomedical-ner-all)
[![FAISS RAG](https://img.shields.io/badge/Vector-FAISS_Hybrid_RAG-blue.svg)](https://github.com/facebookresearch/faiss)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-111.svg)](https://xgboost.readthedocs.io)
[![TreeSHAP](https://img.shields.io/badge/Explainability-TreeSHAP-brightgreen.svg)](https://github.com/slundberg/shap)

## 📌 Project Overview
**12C** is an end-to-end intelligent clinical decision support system designed to assist patients traveling domestically or internationally for specialized medical care. The system ingests medical diagnostic reports, extracts clinical entities, grounds advice in verified clinical practice guidelines via Hybrid Semantic RAG, recommends accredited hospitals and specialists using multi-criteria optimization, predicts treatment costs and hospitalization duration with interpretable XGBoost/TreeSHAP models, calculates optimal transit routes with A* pathfinding, and delivers a safety-guarded AI healthcare assistant.

---

## 🏛️ Core Architectural Modules

1. **Medical Document Ingestion & Hybrid OCR (Phase 2)**:
   - Native digital stream extraction for text-based PDFs.
   - High-fidelity Tesseract OCR fallback for scanned reports and image files (PDF, PNG, JPG, WebP).
2. **Clinical Named Entity Recognition (NER) (Phase 2)**:
   - Pretrained `d4data/biomedical-ner-all` transformer model extracting 5 structured clinical classes: `Disease`, `Symptom`, `Procedure`, `Medication`, `BodyPart`, and `TestResult`.
   - Content-driven specialty prediction (Cardiology, Orthopedics, Oncology, Neurology, Gastroenterology, Nephrology) independent of file naming.
3. **Hybrid Semantic Retrieval-Augmented Generation (RAG) (Phases 3 & 7)**:
   - FAISS dense vector embeddings combined with BM25 lexical keyword matching over 18 curated international guidelines (ESC, ACC/AHA, AAOS, AANS, ASCO, NCCN).
   - Strict `INSUFFICIENT_EVIDENCE` refusal on out-of-domain queries and verifiable bibliographic citation grounding.
4. **Multi-Criteria Hospital & Doctor Recommendations (Phase 4)**:
   - Weighted multi-attribute decision scoring:
     $$\text{Score} = 0.30 \cdot S + 0.20 \cdot T + 0.15 \cdot D + 0.15 \cdot C + 0.10 \cdot R + 0.10 \cdot A$$
   - Balances Specialty Match ($S$), Treatment Capability ($T$), Patient Proximity ($D$), Budget/Insurance Fit ($C$), Clinical Rating ($R$), and Bed/Doctor Availability ($A$).
5. **Machine Learning Treatment Cost & Hospitalization Duration (LOS) (Phase 5)**:
   - Zero-leakage XGBoost regression for procedure cost ($R^2 = 0.9689$, $\text{MAE} = ₹24,307$) and Length of Stay ($R^2 = 0.8545$, $\text{MAE} = 0.716 \text{ days}$).
   - TreeSHAP feature-level attribution explaining the clinical and operational drivers behind predictions.
   - *Provenance Disclosure*: Calibrated on 2,500 synthetic benchmark patient episodes using National Health Authority (NHA/PMJAY) package tariffs and GIPSA schedules.
6. **A\* Spatial Navigation & Recovery Travel Planning (Phase 6)**:
   - Admissible heuristic pathfinding over an intra-city transit network connecting airports, railway junctions, hospitals, and pharmacies.
   - Content-based recovery accommodation ranking based on medical accessibility, elevator access, and hospital proximity.
7. **Clinical Safety Guardrails & Emergency Detection (Phase 7)**:
   - Deterministic acute emergency triage intercepting life-threatening conditions (angina, stroke, severe bleeding, syncope).
   - Direct emergency guidance advising users to contact local emergency services (configured with 112/108 for the India demo).
   - Mandatory medical disclaimer and prohibition against independent medication modification.
8. **Security & Patient Vault Isolation (Phase 8)**:
   - Cryptographically signed Bearer JWT authentication, bcrypt password hashing, and role-based access control.
   - Strict cross-patient isolation (HTTP 403 Forbidden) preventing Insecure Direct Object References (IDOR).
9. **Connected Supporting 12C Services (Phase 9)**:
   - Real-time pharmacy inventory finder, authenticated appointment scheduling, multilingual prescription translation (Hindi, Telugu, Tamil, Bengali, Marathi), and cashless insurance desk guidance.
10. **End-to-End Sequential Integration (Phase 10)**:
    - Coherent multi-stage patient journey passing dynamic IDs and clinical context across all modules.
11. **Quantitative Research Validation & Evaluation (Phase 11)**:
    - Transparent benchmark evaluation across 7 dimensions mapped to 6 research gaps and 6 project objectives.

---

## 📂 Project Directory Structure

```text
Major-Project-samp1/
├── backend/
│   ├── ai/
│   │   ├── ocr_engine.py             # Hybrid PDF & Tesseract OCR engine
│   │   ├── clinical_bert.py          # Biomedical NER clinical entity extractor
│   │   ├── rag_engine.py             # Hybrid FAISS vector + BM25 RAG engine
│   │   ├── recommendation_engine.py  # Multi-criteria decision scoring algorithm
│   │   ├── cost_prediction.py        # XGBoost cost & LOS inference pipeline
│   │   ├── shap_explainer.py         # TreeSHAP feature contribution explainer
│   │   ├── astar_navigation.py       # A* spatial graph navigation engine
│   │   ├── healthcare_assistant.py   # RAG-grounded conversational safety assistant
│   │   ├── translator.py             # Multilingual medical translation module
│   │   ├── evaluation.py             # Phase 11 research evaluation engine
│   │   └── ml_models/                # Persisted models, metrics & reports
│   ├── datasets/
│   │   ├── cost_training_data.py     # NHA/PMJAY calibrated synthetic cost dataset
│   │   ├── providers_data.py         # 55+ accredited hospitals & specialist registry
│   │   └── seed_data.py              # Relational database seed records
│   ├── routes/                       # FastAPI modular API routers
│   ├── main.py                       # FastAPI application entry point
│   ├── database.py                   # SQLAlchemy engine & session manager
│   ├── models.py                     # Relational ORM models (18 tables)
│   ├── schemas.py                    # Pydantic validation schemas
│   └── security.py                   # JWT security & vault authorization
├── frontend/
│   ├── src/
│   │   ├── components/               # UI components, navigation & banners
│   │   ├── pages/                    # 25 full-featured React application pages
│   │   └── services/api.ts           # Authenticated API fetch client
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── tests/                            # 102 comprehensive pytest test cases
│   ├── test_phase2_ocr_ner.py
│   ├── test_phase3_rag.py
│   ├── test_phase4_recommendations.py
│   ├── test_phase5_cost_prediction.py
│   ├── test_phase6_travel_planner.py
│   ├── test_phase7_healthcare_assistant.py
│   ├── test_phase8_security_records.py
│   ├── test_phase9_supporting_features.py
│   ├── test_phase10_e2e_integration.py
│   └── test_phase11_evaluation.py
├── EVALUATION_REPORT.md              # Research metrics and gap mapping
├── FINAL_PROJECT_REPORT.md           # Formal project technical summary
├── DEMO_GUIDE.md                     # Step-by-step presentation & demo walkthrough
└── README.md
```

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm
- Tesseract OCR (`brew install tesseract` on macOS or `apt-get install tesseract-ocr` on Linux)

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize database schema and seed benchmark data
python init_db.py

# Launch FastAPI backend server (Port 8000)
python main.py
```
*API documentation is live at `http://localhost:8000/docs`*

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Launch development server (Port 5173)
npm run dev
```
*Web application runs at `http://localhost:5173`*

### 3. Production Build
```bash
cd frontend
npm run build
```

### 4. Synthetic Demo Accounts (Multi-Patient Isolation)
The system supports minimal demo authentication to showcase context isolation between distinct clinical specialties. Accounts can be switched instantly via `/login` or the top navigation bar badge:

| Specialty | Username | Alternate Email | Password | Synthetic Patient | Clinical Focus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cardiology** | `demo_cardio` | `patient@example.com` | `DemoPassword@123` | Rahul Verma (ID: 1) | Coronary Artery Disease / Angiogram |
| **Neurology** | `demo_neuro` | `patient2@example.com` | `DemoPassword@123` | Priya Sharma (ID: 2) | Chronic Migraine / Brain MRI |
| **Orthopedics** | `demo_ortho` | `patient3@example.com` | `DemoPassword@123` | Amit Patel (ID: 3) | Bilateral Knee Osteoarthritis / X-Ray |

> *All accounts are synthetic demonstration personas with distinct diagnostic profiles, uploaded reports, and clinical recommendations.*

---

## 🧪 Testing & Research Validation

Run the complete regression test suite (102 tests across Phases 1–11):
```bash
python3 -m pytest -v
```

Run only the Phase 10 End-to-End Sequential Workflow Integration test:
```bash
python3 -m pytest tests/test_phase10_e2e_integration.py -v
```

Run the Phase 11 Evaluation & Research Validation Engine:
```bash
python3 backend/ai/evaluation.py
python3 -m pytest tests/test_phase11_evaluation.py -v
```

---

## ⚖️ Clinical Safety & Emergency Advisory Notice
12C is strictly an AI-assisted clinical decision support system designed for informational guidance. It does not provide formal medical diagnoses, prescription alterations, or emergency clearances. For acute, life-threatening symptoms (e.g. crushing chest pain, sudden paralysis, severe dyspnea), patients must immediately contact local emergency medical services (configured for 112/108 in the India demo) or proceed to the nearest emergency trauma department.
