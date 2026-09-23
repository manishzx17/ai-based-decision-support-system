# AI Based Decision Support System

An AI-powered healthcare decision-support platform that transforms unstructured medical reports into structured clinical information and combines patient context, biomedical NLP, retrieval-augmented generation, explainable machine learning, hospital recommendation, and medical travel services into a unified workflow.

> **Research Prototype / Academic Project**
>
> This system is designed for research and decision-support purposes. It does not provide medical diagnoses, prescriptions, emergency dispatch, guaranteed hospital availability, or binding treatment/cost estimates.

---

## Overview

Healthcare information is often distributed across medical reports, clinical records, treatment guidelines, hospital information, and patient-specific constraints.

The **AI Based Decision Support System** provides an integrated pipeline that:

1. Extracts information from medical reports using OCR and biomedical NER.
2. Builds a persistent clinical profile for the patient.
3. Retrieves relevant medical knowledge from a curated guideline knowledge base.
4. Generates evidence-grounded medical analysis with citations.
5. Ranks hospitals using transparent multi-criteria decision analysis.
6. Estimates inpatient length of stay and hospitalization cost using XGBoost.
7. Explains cost predictions using TreeSHAP.
8. Provides a patient-contextualized AI healthcare assistant with safety guardrails.
9. Supports medical travel planning through route, hotel, pharmacy, and emergency-service information.

---

# System Architecture

```text
                    ┌─────────────────────────────┐
                    │     Medical Report Input    │
                    │     PDF / PNG / JPG / WEBP  │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │ Medical Report Intelligence │
                    │                             │
                    │ OCR → Biomedical NER        │
                    │ → Structured Extraction     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      Clinical Profile       │
                    │                             │
                    │ Conditions / Symptoms       │
                    │ Medications / Tests         │
                    │ Procedures / History        │
                    └──────────────┬──────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
             ▼                     ▼                     ▼
┌────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ Medical Analysis   │  │ Personalized Hospital│  │ Cost & LOS Prediction │
│ / RAG              │  │ Recommendations      │  │                      │
│                    │  │                      │  │ XGBoost + TreeSHAP   │
│ FAISS + Embeddings │  │ Transparent MCDM     │  │                      │
│ + Local LLM        │  │ Ranking              │  │ LOS → Cost           │
└─────────┬──────────┘  └──────────┬───────────┘  └──────────┬───────────┘
          │                        │                         │
          └────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    AI Healthcare Assistant  │
                    │                             │
                    │ Patient Context + RAG       │
                    │ Multi-turn Conversation     │
                    │ Safety Guardrails            │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │ Medical Travel & Local      │
                    │ Connectivity                │
                    │                             │
                    │ Routes / Hotels / Pharmacies│
                    │ Emergency Services          │
                    └─────────────────────────────┘
