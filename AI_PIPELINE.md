# AI Pipelines & Algorithms Guide - 12C Decision Support System

## 1. OCR Report Parsing Engine
Parses PDF, JPG, PNG medical report uploads using PyPDF and fallback image OCR into clean text streams.

## 2. ClinicalBERT / BioBERT Entity Extraction
Named Entity Recognition (NER) pipeline identifying 5 clinical entity types:
- `Disease`: e.g. Severe Double Vessel Disease, Meningioma, Osteoarthritis
- `Symptom`: e.g. Exertional Angina, Shortness of Breath, Dizziness
- `Procedure`: e.g. Percutaneous Coronary Intervention (PCI), Angiography, CABG
- `Medication`: e.g. Aspirin 75mg, Atorvastatin 40mg, Levetiracetam
- `BodyPart`: e.g. Left Anterior Descending (LAD) Artery, Right Parietal Region

## 3. Hybrid RAG Knowledge Pipeline
Combines TF-IDF / BM25 keyword relevance scoring with semantic vector similarity over verified medical guidelines, synthesized with Google Gemini API for grounded patient responses.

## 4. Multi-Criteria Hospital Recommendation Algorithm
$$\text{Score} = 0.30 \cdot S + 0.20 \cdot T + 0.15 \cdot D + 0.15 \cdot C + 0.10 \cdot R + 0.10 \cdot A$$
- $S$: Specialty Match
- $T$: Treatment & Facility Match
- $D$: Proximity & Distance Score
- $C$: Cost Score within Budget
- $R$: Patient Satisfaction Rating
- $A$: Bed & Doctor Availability

## 5. XGBoost Cost Prediction & SHAP
Predicts procedure cost ranges based on complexity, destination city economic tier, room type multiplier, and stay duration, paired with SHAP feature contribution breakdowns.

## 6. A* Spatial Pathfinding
Graph-based A* algorithm calculating optimal spatial routes and travel times between Airports, Railway Stations, Hotels, Hospitals, Pharmacies, and Emergency Units.
