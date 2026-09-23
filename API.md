# REST API Documentation - 12C Decision Support System

## Core Endpoints Summary

### Authentication & Profiles
- `POST /api/auth/register` - Create patient user account
- `POST /api/auth/login` - Sign in and receive JWT token
- `GET /api/auth/profile` - Fetch patient medical profile
- `PUT /api/auth/profile` - Update patient vitals, allergies, chronic conditions

### Medical Reports & OCR
- `POST /api/reports/upload` - Upload PDF/PNG/JPG medical report for OCR & Biomedical NER parsing
- `GET /api/reports/` - List user medical reports
- `GET /api/reports/{id}` - Fetch detailed report analysis & extracted entities

### Recommendations & Hospital Comparison
- `GET /api/recommend/hospitals` - Fetch weighted score hospital recommendations
- `GET /api/recommend/doctors` - Fetch doctor recommendations matched by specialty
- `POST /api/recommend/compare` - Compare up to 3 hospitals side-by-side with AI explanation

### Cost Prediction & SHAP
- `POST /api/cost/predict` - XGBoost treatment cost estimation (min, max, avg)
- `POST /api/cost/explain` - SHAP feature contribution breakdown

### Travel & Navigation
- `POST /api/travel/plan` - Generate multi-day medical travel itinerary
- `GET /api/travel/navigate` - A* spatial graph route calculation
- `GET /api/travel/accommodations` - Search nearby patient hotels

### Healthcare Services & AI Assistant
- `GET /api/services/pharmacies` - 24/7 pharmacies directory
- `GET /api/services/insurance` - Cashless insurance desk checklist
- `POST /api/services/symptoms` - AI symptom guidance & urgency classification
- `POST /api/services/translate` - Multilingual medical translator (Telugu, Hindi, Tamil, Kannada, Malayalam)
- `POST /api/services/chat` - RAG-grounded conversational AI Healthcare Assistant
- `GET /api/services/emergency` - 1-click emergency 108 trauma centers
