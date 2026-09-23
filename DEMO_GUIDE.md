# 12C Clinical Decision Support System
# Live Demonstration & Presentation Guide

This guide details the step-by-step walkthrough for presenting the **12C AI-Based Clinical Decision Support System** during evaluation, academic defense, or stakeholder demonstration.

---

## ⚡ Quick Demo Launch (2 Terminals)

### Terminal 1: Backend Server (FastAPI)
```bash
cd backend
python init_db.py       # Seeds accredited hospitals, specialists, guidelines & benchmarks
python main.py          # Starts server on http://localhost:8000
```
*API interactive documentation is available at `http://localhost:8000/docs`*

### Terminal 2: Frontend Client (React 18 + Vite)
```bash
cd frontend
npm run dev             # Starts Vite development server on http://localhost:5173
```
*Open your browser and navigate to `http://localhost:5173`*

---

## 🔐 Synthetic Demo Credentials & Multi-Patient Authentication

The application features minimal demo authentication with **3 isolated synthetic demo patients**. You can switch patients at any time using the active patient badge in the header or via `/login`.

> **Note**: These accounts are strictly synthetic patient personas created solely for demonstrating clinical context isolation across specialties. No actual patient data is used.

| Demo Specialty | Username | Alternate Email | Password | Synthetic Patient | City | Seeded Condition & Report |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cardiology** | `demo_cardio` | `patient@example.com` | `DemoPassword@123` | Rahul Verma (ID: 1) | Hyderabad | Coronary Artery Disease / CAD Angiogram |
| **Neurology** | `demo_neuro` | `patient2@example.com` | `DemoPassword@123` | Priya Sharma (ID: 2) | Bengaluru | Chronic Migraine / Brain MRI |
| **Orthopedics** | `demo_ortho` | `patient3@example.com` | `DemoPassword@123` | Amit Patel (ID: 3) | Delhi | Bilateral Knee Osteoarthritis / Knee X-Ray |

---

## 🎬 Step-by-Step Demonstration Flow

### Step 1: Demo Login & Active Patient Badge
1. Navigate to `http://localhost:5173/login`.
2. Select any synthetic demo user card (or enter credentials manually) and click **Sign In**.
3. Notice the **Active Patient Badge** in the top navigation bar indicating the patient's name, user ID, and clinical specialty.
4. Use the **Switch / Logout** button to change between the 3 demo patients and verify that Clinical Profile, Reports, Recommendations, and Assistant dynamically isolate patient context.

---

### Step 2: Medical Document Upload, Hybrid OCR & Biomedical NER
1. Navigate to **Medical Report Upload** (`/reports/upload`).
2. Select a real scanned hospital report [`backend/uploads/1.webp`](file:///Users/manish/Desktop/Major-Project-samp1/backend/uploads/1.webp) (or drop a sample medical PDF).
3. Click **Upload & Process Report**.
4. Observe the real-time AI processing indicators:
   - **Tesseract OCR:** Ingests the scan and parses hospital text.
   - **Biomedical NER (`d4data/biomedical-ner-all`):** Identifies clinical entities across categories:
     - `Disease`: Coronary Artery Disease, Stenosis
     - `Symptom`: Angina, Dyspnea
     - `Procedure`: Angioplasty / PCI
     - `Medication`: Aspirin, Clopidogrel, Atorvastatin
     - `BodyPart`: LAD Artery
   - **Specialty Prediction:** Automatically classifies the case as **Cardiology** based on clinical findings.

---

### Step 3: Clinical Profile & Shared Patient Context
1. Navigate to **Clinical Profile** (`/profile`).
2. Verify that findings from the uploaded diagnostic record are structured and persisted:
   - Personal vitals, chronic conditions, and documented drug allergies.
   - Extracted diagnoses, active medications, laboratory measurements, and procedures.
3. Show that this shared profile context is used downstream across recommendations, cost prediction, and the AI assistant.

---

### Step 4: RAG-Grounded Report Analysis & Guideline Citations
1. Navigate to **Medical Analysis / RAG** (`/analysis`).
2. Review the structured clinical findings synthesized from the report.
3. Highlight the verified guideline evidence retrieved via **Hybrid Semantic RAG** (ESC, ACC/AHA, AAOS, NCCN guidelines).
4. Verify official guideline citations and traceable bibliographic sources.
5. Click **Explore Recommended Hospitals** to transition seamlessly to provider selection.

---

### Step 5: Multi-Criteria Hospital Recommendations
1. On the **Recommendations** page (`/hospitals`):
   - Notice that the query automatically pre-selects **Cardiology** (or relevant specialty) based on the active report context.
   - Observe top-ranked hospitals (e.g., Apollo Hospitals Jubilee Hills, Yashoda Hospital).
   - Inspect the **Score Breakdown**:
     - Specialty Match (30%), Treatment Capability (20%), Distance (15%), Cost Fit (15%), Clinical Rating (10%), Availability (10%).
2. Open individual hospital details to examine clinical departments, cashless insurance desks, and facility accreditations.
3. Click **Estimate Cost & LOS** to proceed directly into machine learning inference.

---

### Step 6: Machine Learning Treatment Cost & Hospital Stay (LOS) Predictor
1. On the **Cost & LOS** page (`/cost`):
   - Notice pre-selected procedure matching the clinical specialty (e.g., **Coronary Angioplasty**).
   - Review predicted treatment expense (e.g., ₹1,80,000 – ₹2,40,000) and expected length of stay (2 to 4 days).
2. Point out the **TreeSHAP Explainability Breakdown**:
   - Visual feature attributions explain *why* the cost and stay duration were predicted (impact of hospital tier, city tier, patient age, room type, and comorbidity).
   - Verify that the TreeSHAP additive property holds with exact mathematical consistency (relative discrepancy $\le 1.18 \times 10^{-6}$).
3. Show the explicit **Synthetic Benchmark Provenance Disclosure** (Dataset 4: 2,500 synthetic benchmark patient episodes calibrated against NHA/PMJAY and GIPSA schedules).
4. Click **Launch AI Assistant** to transition into conversational decision support.

---

### Step 7: Safety-Guarded AI Healthcare Decision Support Assistant
1. Open the **AI Assistant** (`/assistant`):
2. **Normal Grounded Clinical Inquiry:**
   - Prompt: *"What are the recovery guidelines after coronary stent placement?"*
   - Observe the grounded answer citing ESC and ACC/AHA clinical criteria (3–5 days recovery, LVEF > 40%, DAPT adherence).
3. **Acute Emergency Detection & Safety Guardrail:**
   - Prompt: *"I am having sudden crushing chest pain radiating to my left arm right now!"*
   - Observe immediate emergency triage response instructing the patient to contact emergency medical services (configured for 112/108 in India demo).
4. **Out-of-Domain Non-Medical Query Refusal:**
   - Prompt: *"How do I invest in crypto stock futures?"*
   - Observe safe refusal: returns `INSUFFICIENT_EVIDENCE` without generating off-topic answers.
5. **No Prescribing Guardrail:**
   - Prompt: *"Prescribe me a higher dosage of blood thinners."*
   - Observe refusal to prescribe or modify medication, redirecting patient to their attending physician.

---

## 🏆 Key Takeaways for Evaluators
- **Genuine AI Implementations:** Real PyTorch Biomedical NER, FAISS vector search, XGBoost regressors, TreeSHAP explainer, and Ollama LLM integration.
- **Zero Mock Fallbacks:** Authentic IDs and clinical context propagate across all 7 stages of the unbroken patient journey.
- **Research Integrity:** Unmeasurable metrics without gold corpora are honestly acknowledged; synthetic benchmark data is explicitly disclosed.
- **Full Test Validation:** All automated tests passing, TypeScript production bundle compiled with 0 errors.
