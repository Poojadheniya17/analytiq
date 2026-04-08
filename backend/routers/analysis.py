# backend/routers/analysis.py
# Analytiq — Analysis Router (Phase 1 — Smart ML)

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd

from core.pipeline  import clean_data, profile_data, save_cleaned_data, save_profile
from core.insights  import (detect_target_column, generate_kpis, detect_anomalies,
                             generate_segment_insights, plot_insights, save_insights)
from core.ml_model  import (train_full_pipeline, detect_target_column as smart_detect,
                             detect_problem_type, validate_dataset, load_model, predict_at_risk)

router = APIRouter()

BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")
)

class ClientPath(BaseModel):
    user_id:     int
    client_name: str

class TrainRequest(BaseModel):
    user_id:     int
    client_name: str
    target_col:  str | None = None

def get_path(user_id: int, client_name: str) -> str:
    return os.path.join(BASE_DATA, str(user_id), client_name.lower().replace(" ", "_"))


@router.post("/clean")
def run_cleaning(req: ClientPath):
    client_path = get_path(req.user_id, req.client_name)
    raw_path    = os.path.join(client_path, "raw_data.csv")
    if not os.path.exists(raw_path):
        raise HTTPException(status_code=404, detail="No raw data found. Upload a CSV first.")

    df_raw     = pd.read_csv(raw_path)

    # Validate before cleaning
    validation = validate_dataset(df_raw)
    if not validation["passed"]:
        raise HTTPException(status_code=400, detail=" | ".join(validation["issues"]))

    df_cleaned = clean_data(df_raw)
    profile    = profile_data(df_cleaned)
    save_cleaned_data(df_cleaned, os.path.join(client_path, "cleaned_data.csv"))
    save_profile(profile, os.path.join(client_path, "data_profile.json"))

    # Auto-detect problem type
    target_col   = smart_detect(df_cleaned)
    problem_info = detect_problem_type(df_cleaned, target_col)

    return {
        "message":      "Data cleaned successfully",
        "rows":         df_cleaned.shape[0],
        "columns":      df_cleaned.shape[1],
        "profile":      profile,
        "preview":      df_cleaned.head(5).to_dict(orient="records"),
        "target_col":   target_col,
        "problem_type": problem_info,
        "validation":   validation,
    }


@router.post("/insights")
def run_insights(req: ClientPath):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")
    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No cleaned data found. Run cleaning first.")

    df         = pd.read_csv(cleaned_path)
    charts_dir = os.path.join(client_path, "charts")
    target_col = smart_detect(df)
    kpis       = generate_kpis(df, target_col)
    anomalies  = detect_anomalies(df)
    segments   = generate_segment_insights(df, target_col)
    plot_insights(df, target_col, charts_dir)
    save_insights(kpis, anomalies, segments, os.path.join(client_path, "insights.json"))

    return {
        "message":          "Insights generated",
        "target_column":    target_col,
        "kpis":             kpis,
        "anomalies":        anomalies,
        "segment_insights": segments,
        "charts":           [f for f in os.listdir(charts_dir) if f.endswith(".png")] if os.path.exists(charts_dir) else []
    }


@router.post("/train")
def run_training(req: TrainRequest):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")
    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No cleaned data found.")

    df = pd.read_csv(cleaned_path)

    # Use user-specified target or auto-detect
    target_col = req.target_col or smart_detect(df)

    print(f"\n🚀 Starting training for {req.client_name}")
    result = train_full_pipeline(df, target_col, client_path)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "message":           "Model trained successfully",
        "problem_type":      result.get("problem_type"),
        "problem_reason":    result.get("problem_reason"),
        "best_model":        result.get("best_model"),
        "target_column":     result.get("target_column"),
        "metrics":           result.get("metrics"),
        "automl_comparison": result.get("automl_comparison"),
        "shap":              result.get("shap"),
        "feature_count":     result.get("feature_count"),
        "training_rows":     result.get("training_rows"),
    }


@router.get("/status/{user_id}/{client_name}")
def get_status(user_id: int, client_name: str):
    client_path = get_path(user_id, client_name)

    metrics      = None
    full_results = None
    at_risk      = []
    charts       = []

    metrics_path      = os.path.join(client_path, "model_metrics.json")
    full_results_path = os.path.join(client_path, "model_full_results.json")
    at_risk_path      = os.path.join(client_path, "at_risk.csv")
    charts_dir        = os.path.join(client_path, "charts")

    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)

    if os.path.exists(full_results_path):
        with open(full_results_path) as f:
            full_results = json.load(f)

    if os.path.exists(at_risk_path):
        try:
            at_risk = pd.read_csv(at_risk_path).head(10).to_dict(orient="records")
        except: pass

    if os.path.exists(charts_dir):
        charts = [f for f in os.listdir(charts_dir) if f.endswith(".png")]

    insights = None
    insights_path = os.path.join(client_path, "insights.json")
    if os.path.exists(insights_path):
        with open(insights_path) as f:
            insights = json.load(f)

    return {
        "has_data":      os.path.exists(os.path.join(client_path, "cleaned_data.csv")),
        "has_insights":  os.path.exists(insights_path),
        "has_model":     os.path.exists(metrics_path),
        "has_narrative": os.path.exists(os.path.join(client_path, "narrative.txt")),
        "metrics":       metrics,
        "full_results":  full_results,
        "insights":      insights,
        "at_risk":       at_risk,
        "charts":        charts,
    }
