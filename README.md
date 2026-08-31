# 12C – AI-Based Medical Travel Decision Support System

[![Python FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React TypeScript](https://img.shields.io/badge/React-18.2-61DAFB.svg?logo=react)](https://reactjs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38BDF8.svg?logo=tailwindcss)](https://tailwindcss.com)
[![Gemini LLM](https://img.shields.io/badge/Google-Gemini_1.5_Flash-4285F4.svg?logo=google)](https://ai.google.dev)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-111.svg)](https://xgboost.readthedocs.io)

## 📌 Project Overview
**12C – AI-Based Medical Travel Decision Support System** is an end-to-end intelligent platform built to assist patients traveling domestically or internationally for specialized medical treatment. The system ingests medical diagnostic reports, extracts clinical entities, retrieves verified medical guidelines via Hybrid RAG, scores accredited hospitals and doctors using a multi-criteria decision algorithm, estimates procedure costs with XGBoost, provides visual SHAP explainability, plans multi-day travel itineraries with A* spatial pathfinding, translates medical prescriptions into 6 languages, and provides 1-click 108 emergency assistance.

---

## 🚀 Key Architectural Features
1. **Medical Report OCR & ClinicalBERT NER**: Optical Character Recognition for PDF, JPG, and PNG reports with BioBERT/ClinicalBERT entity extraction (Diseases, Symptoms, Medications, Procedures, Body Parts).
2. **Hybrid Retrieval-Augmented Generation (RAG)**: Vector semantic embeddings + BM25 keyword matching grounded with Google Gemini API for medical report summarization and patient Q&A.
3. **Multi-Criteria Recommendation Scoring**:
   $$\text{Score} = 0.30 \times \text{SpecialtyMatch} + 0.20 \times \text{TreatmentMatch} + 0.15 \times \text{Distance} + 0.15 \times \text{Cost} + 0.10 \times \text{Rating} + 0.10 \times \text{Availability}$$
4. **XGBoost ML Treatment Cost Estimation**: Machine learning regression estimating minimum, maximum, and average procedure costs with SHAP feature driver explanations.
5. **A* Spatial Pathfinding Navigation**: Route planning and travel time estimation between Airports, Stations, Hotels, Hospitals, Pharmacies, and Trauma Centers.
6. **25 Fully Implemented Frontend Pages**: Complete modern, responsive web application built with React 18, TypeScript, Tailwind CSS, Lucide icons, and Recharts.

---

## 📂 Project Structure
```
project/
├── backend/
│   ├── ai/
│   │   ├── ocr_engine.py           # Medical report OCR engine
│   │   ├── clinical_bert.py        # ClinicalBERT / BioBERT entity extraction
│   │   ├── rag_engine.py           # Hybrid vector + BM25 RAG with Gemini LLM
│   │   ├── recommendation_engine.py# Multi-criteria hospital & doctor scoring
│   │   ├── cost_prediction.py      # XGBoost treatment cost predictor
│   │   ├── shap_explainer.py       # SHAP ML feature impact explainer
│   │   ├── astar_navigation.py     # A* spatial pathfinding navigation
│   │   └── translator.py           # Multilingual medical translator
│   ├── datasets/
│   │   └── seed_data.py            # Comprehensive medical travel demo dataset
│   ├── routes/
│   │   ├── auth.py                 # User authentication & patient profiles
│   │   ├── reports.py              # Medical report upload & OCR endpoints
│   │   ├── recommendations.py      # Hospital finder & side-by-side comparison
│   │   ├── cost.py                 # Treatment cost prediction & SHAP endpoints
│   │   ├── travel.py               # Medical travel itinerary & navigation
│   │   └── services.py             # Pharmacies, insurance, translation, emergency
│   ├── config.py                   # System configuration & environment settings
│   ├── database.py                 # SQLAlchemy database session & engine
│   ├── models.py                   # Relational ORM models (18 tables)
│   ├── schemas.py                  # Pydantic validation schemas
│   ├── init_db.py                  # Database initializer and seed script
│   ├── main.py                     # FastAPI server entry point
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable UI component library
│   │   ├── pages/                  # All 25 required application pages
│   │   ├── services/               # API fetch client
│   │   ├── App.tsx                 # React Router DOM configuration
│   │   └── index.css               # Tailwind CSS directives & glassmorphism
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── tests/
│   └── test_backend.py             # Backend AI unit test suite
├── ARCHITECTURE.md
├── API.md
├── DATABASE.md
└── AI_PIPELINE.md
```

---

## 🛠️ Quick Start Guide

### 1. Backend Setup (FastAPI)
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize database & seed demo data
python init_db.py

# Launch FastAPI backend server (Port 8000)
python main.py
```
*API Documentation will be live at `http://localhost:8000/docs`*

### 2. Frontend Setup (React + Vite + TypeScript)
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Launch Vite development server (Port 5173)
npm run dev
```
*Access the web app at `http://localhost:5173`*

### 3. Run Test Suite
```bash
python tests/test_backend.py
```

---

## ⚖️ Safety & Legal Disclaimer
12C provides AI-assisted clinical decision support, medical travel routing, and treatment cost estimations. All AI outputs are generated for informational assistance and must be verified by a qualified physician. Immediate life-threatening medical emergencies must dial **108** or proceed directly to an emergency department.
