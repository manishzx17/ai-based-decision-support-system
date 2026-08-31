# System Architecture - 12C Medical Travel Decision Support System

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                          React 18 + TS Frontend                        │
│  (Tailwind CSS, Lucide Icons, React Router, Recharts Visualizations)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ REST API (JSON / Multipart)
┌──────────────────────────────────▼─────────────────────────────────────┐
│                          Python FastAPI Backend                        │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────┐ │
│ │  OCR Engine   │ │ Clinical BERT │ │  Hybrid RAG   │ │ Recommendation│ │
│ │  (Pdf/Image)  │ │ Entity Extract│ │ Vector+BM25   │ │ Score Engine │ │
│ └───────────────┘ └───────────────┘ └───────────────┘ └──────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────┐ │
│ │   XGBoost     │ │  SHAP Engine  │ │  A* Pathing   │ │  Gemini LLM  │ │
│ │ Cost Predict  │ │ Explainability│ │  Navigation   │ │ Translator   │ │
│ └───────────────┘ └───────────────┘ └───────────────┘ └──────────────┘ │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ SQLAlchemy ORM
┌──────────────────────────────────▼─────────────────────────────────────┐
│                   PostgreSQL / SQLite Database (Supabase)              │
│ (users, reports, entities, hospitals, doctors, costs, appointments...) │
└────────────────────────────────────────────────────────────────────────┘
```

## Data Isolation & Source Attribution
The platform maintains strict separation between data layers:
1. **AI-Generated Data**: Clearly marked with yellow disclaimer badges (e.g. Gemini RAG responses, symptom checker triage, ClinicalBERT entities).
2. **Verified Database Information**: Marked with green badges (e.g. Hospital accreditation, Doctor qualifications, Pharmacy inventory, Insurance TPA desks).
3. **External Real-Time API Data**: Marked with blue badges (e.g. A* Spatial Navigation maps, live traffic estimates).
4. **Emergency Services**: Marked with red badges (e.g. Direct EMRI 108 ambulance dispatch, casualty department phone numbers).
