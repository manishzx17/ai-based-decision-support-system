from fastapi import APIRouter
from schemas import CostPredictionRequest, CostPredictionResponse
from ai.cost_prediction import cost_predictor
from ai.shap_explainer import shap_explainer

router = APIRouter(prefix="/cost", tags=["Treatment Cost Prediction & SHAP"])

@router.post("/predict", response_model=CostPredictionResponse)
def predict_treatment_cost(req: CostPredictionRequest):
    pred = cost_predictor.predict(
        treatment_name=req.treatment_name,
        city=req.city,
        room_type=req.room_type,
        duration_days=req.duration_days
    )
    return pred

@router.post("/explain")
def explain_treatment_cost(req: CostPredictionRequest):
    pred = cost_predictor.predict(
        treatment_name=req.treatment_name,
        city=req.city,
        room_type=req.room_type,
        duration_days=req.duration_days
    )
    explanation = shap_explainer.explain_cost(pred)
    return {
        "prediction": pred,
        "shap_explanation": explanation
    }
