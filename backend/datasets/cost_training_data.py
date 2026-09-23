"""
Cost and Hospitalization Duration Training Dataset for 12C Decision Support System.

DATASET DISCLOSURE:
The 2,500 patient episodes in this dataset are SYNTHETIC BENCHMARK DATA generated for this project,
calibrated using publicly available National Health Authority (NHA / PMJAY) standard package tariffs
and General Insurance Public Sector Association (GIPSA) schedule of charges.
They are NOT real patient records and must not be represented as actual patient health records.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

TREATMENT_SPECS = {
    "Coronary Angioplasty": {
        "specialty": "Cardiology",
        "base_cost": 210000.0,
        "cost_std": 25000.0,
        "base_los": 2.5,
        "los_std": 0.6
    },
    "CABG": {
        "specialty": "Cardiothoracic Surgery",
        "base_cost": 390000.0,
        "cost_std": 40000.0,
        "base_los": 8.0,
        "los_std": 1.4
    },
    "Total Knee Replacement": {
        "specialty": "Orthopedics",
        "base_cost": 250000.0,
        "cost_std": 30000.0,
        "base_los": 4.5,
        "los_std": 0.9
    },
    "Craniotomy": {
        "specialty": "Neurosurgery",
        "base_cost": 430000.0,
        "cost_std": 45000.0,
        "base_los": 7.5,
        "los_std": 1.5
    },
    "Chemotherapy Cycle": {
        "specialty": "Oncology",
        "base_cost": 95000.0,
        "cost_std": 15000.0,
        "base_los": 1.8,
        "los_std": 0.5
    },
    "Laparoscopic Cholecystectomy": {
        "specialty": "Gastroenterology",
        "base_cost": 90000.0,
        "cost_std": 12000.0,
        "base_los": 2.0,
        "los_std": 0.4
    },
    "Appendectomy": {
        "specialty": "General Surgery",
        "base_cost": 70000.0,
        "cost_std": 10000.0,
        "base_los": 2.2,
        "los_std": 0.5
    },
    "Nephrectomy": {
        "specialty": "Urology",
        "base_cost": 280000.0,
        "cost_std": 35000.0,
        "base_los": 5.0,
        "los_std": 1.0
    }
}

CITY_FACTORS = {
    "Mumbai": 1.22,
    "Delhi": 1.18,
    "Bengaluru": 1.10,
    "Hyderabad": 1.00,
    "Chennai": 0.96,
    "Kolkata": 0.92
}

ROOM_FACTORS = {
    "General Ward": 0.78,
    "Semi-Private AC": 0.92,
    "Private AC Deluxe": 1.00,
    "Super Deluxe Suite": 1.32
}

DATASET_PROVENANCE: Dict[str, Any] = {
    "data_source": "NHA / PMJAY Package Tariffs & GIPSA General Insurance Schedules",
    "is_benchmark": True,
    "sample_size": 2500,
    "curated_procedures": list(TREATMENT_SPECS.keys()),
    "curated_cities": list(CITY_FACTORS.keys()),
    "curated_room_types": list(ROOM_FACTORS.keys()),
    "provenance_notes": "Synthesized benchmark dataset calibrated against published Indian healthcare tariffs and clinical LOS pathways for reproducible ML training."
}

def generate_cost_and_los_dataset(n_samples: int = 2500, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a reproducible dataset of patient procedure episodes with NO target leakage.
    - LOS Model features: strictly pre-operative baseline patient, clinical, and facility attributes.
    - Cost Model features: pre-operative attributes + planned hospitalization duration.
    """
    np.random.seed(random_seed)

    treatments = list(TREATMENT_SPECS.keys())
    cities = list(CITY_FACTORS.keys())
    rooms = list(ROOM_FACTORS.keys())
    insurance_types = ["Cashless Empanelled", "Third Party Reimbursement", "Self-Pay"]
    hospital_tiers = ["Tier 1 Apex/Metro", "Tier 2 Tertiary"]

    records = []

    for i in range(n_samples):
        # 1. Demographics & Comorbidities
        age = int(np.random.normal(54, 14))
        age = max(20, min(85, age))
        gender = np.random.choice(["Male", "Female"], p=[0.55, 0.45])

        # Comorbidities increase with age
        p_dm = min(0.15 + (age / 180.0), 0.50)
        p_htn = min(0.20 + (age / 150.0), 0.60)
        p_cad = min(0.10 + (age / 200.0), 0.45)

        has_dm = 1 if np.random.rand() < p_dm else 0
        has_htn = 1 if np.random.rand() < p_htn else 0
        has_cad = 1 if np.random.rand() < p_cad else 0
        comorbidity_count = has_dm + has_htn + has_cad

        # 2. Procedure & Specialty
        t_name = np.random.choice(treatments)
        t_info = TREATMENT_SPECS[t_name]
        specialty = t_info["specialty"]

        # 3. Location & Facility
        city = np.random.choice(cities)
        city_factor = CITY_FACTORS[city]

        room_type = np.random.choice(rooms, p=[0.20, 0.35, 0.35, 0.10])
        room_factor = ROOM_FACTORS[room_type]

        h_tier = np.random.choice(hospital_tiers, p=[0.60, 0.40])
        tier_factor = 1.08 if h_tier == "Tier 1 Apex/Metro" else 0.94

        insurance = np.random.choice(insurance_types, p=[0.50, 0.30, 0.20])

        # 4. Length of Stay (LOS in days) Target Generation
        # Clinical base LOS + comorbidity prolongation + age factor + random residual
        age_los_effect = max(0.0, (age - 50) * 0.03)
        comorb_los_effect = comorbidity_count * 0.45
        los_noise = np.random.normal(0, t_info["los_std"])
        
        # Realized/Actual LOS (Target for Model 2)
        realized_los = t_info["base_los"] + age_los_effect + comorb_los_effect + los_noise
        realized_los = round(float(np.clip(realized_los, 1.0, 18.0)), 1)

        # Pre-operative Planned LOS (Baseline expectation prior to hospital admission)
        planned_los = round(float(np.clip(t_info["base_los"] + (comorbidity_count * 0.3), 1.0, 16.0)), 1)

        # 5. Treatment Cost (INR) Target Generation (Target for Model 1)
        # Driven by surgical base complexity, city economic index, room category, hospital tier, and planned duration
        age_cost_factor = 1.0 + max(0.0, (age - 50) * 0.003)
        comorb_cost_factor = 1.0 + (comorbidity_count * 0.05)
        # Consumables and nursing fees scale with stay
        los_cost_component = planned_los * 7500.0 * room_factor
        cost_noise = np.random.normal(0, t_info["cost_std"])

        base_proc_cost = (t_info["base_cost"] * city_factor * room_factor * tier_factor * age_cost_factor * comorb_cost_factor)
        total_cost = base_proc_cost + los_cost_component + cost_noise
        total_cost = round(float(np.clip(total_cost, 40000.0, 1500000.0)), -2)

        records.append({
            "patient_id": i + 1,
            "age": age,
            "gender": gender,
            "has_diabetes": has_dm,
            "has_hypertension": has_htn,
            "has_cardiac_history": has_cad,
            "comorbidity_count": comorbidity_count,
            "treatment_name": t_name,
            "specialty": specialty,
            "city": city,
            "hospital_tier": h_tier,
            "room_type": room_type,
            "insurance_type": insurance,
            "planned_los_days": planned_los,
            "hospitalization_los_days": realized_los,
            "treatment_cost_inr": total_cost
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    df = generate_cost_and_los_dataset(2500)
    print(f"Generated benchmark dataset: {len(df)} rows, columns: {list(df.columns)}")
    print(df.head(2))
