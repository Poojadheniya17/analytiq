# backend/routers/simulator.py
# Analytiq — What-If Simulator Router

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import joblib

router = APIRouter()

BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")
)

class SimulatorConfigRequest(BaseModel):
    user_id:     int
    client_name: str

class PredictRequest(BaseModel):
    user_id:     int
    client_name: str
    features:    Dict[str, Any]

def get_path(user_id: int, client_name: str) -> str:
    return os.path.join(BASE_DATA, str(user_id), client_name.lower().replace(" ", "_"))

def detect_target(df: pd.DataFrame):
    known = ["churn", "churned", "target", "label", "class", "fraud", "is_fraud",
             "default", "attrition", "outcome", "converted", "exited", "left", "y"]
    for col in df.columns:
        if col.lower() in known:
            return col
    for col in reversed(df.columns.tolist()):
        if df[col].nunique() == 2:
            return col
    return None


@router.post("/config")
def get_simulator_config(req: SimulatorConfigRequest):
    """
    Return the feature configuration for the simulator:
    - Feature names, types, ranges, and options
    - A sample at-risk record to pre-populate
    - SHAP top features to prioritize which sliders to show
    """
    client_path  = get_path(req.user_id, req.client_name)
    model_path   = os.path.join(client_path, "trained_model.joblib")
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")
    at_risk_path = os.path.join(client_path, "at_risk.csv")
    full_results_path = os.path.join(client_path, "model_full_results.json")

    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="No trained model found. Train a model first.")
    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No cleaned data found.")

    df         = pd.read_csv(cleaned_path)
    target_col = detect_target(df)
    model      = joblib.load(model_path)

    # Drop target and ID columns
    feature_cols = [c for c in df.columns if c != target_col]
    id_cols      = [c for c in feature_cols if "id" in c.lower() and df[c].nunique() == len(df)]
    feature_cols = [c for c in feature_cols if c not in id_cols]

    # Get SHAP top features if available
    top_shap_features = []
    if os.path.exists(full_results_path):
        try:
            with open(full_results_path) as f:
                full = json.load(f)
            shap_info = full.get("shap", {})
            if shap_info.get("available") and shap_info.get("top_features"):
                top_shap_features = [f["feature"] for f in shap_info["top_features"]]
        except: pass

    # Sort features — SHAP top features first
    if top_shap_features:
        sorted_features = [f for f in top_shap_features if f in feature_cols]
        sorted_features += [f for f in feature_cols if f not in sorted_features]
        feature_cols = sorted_features[:15]  # max 15 features
    else:
        feature_cols = feature_cols[:15]

    # Build feature config
    features = []
    for col in feature_cols:
        col_data = df[col]
        n_unique = col_data.nunique()
        is_top   = col in top_shap_features[:5]

        if col_data.dtype == object or n_unique <= 10:
            # Categorical
            options = sorted([str(v) for v in col_data.dropna().unique().tolist()])
            features.append({
                "name":     col,
                "type":     "categorical",
                "options":  options,
                "default":  str(col_data.mode()[0]) if len(col_data.mode()) > 0 else options[0],
                "is_top":   is_top,
                "label":    col.replace("_", " ").title(),
            })
        else:
            # Numeric
            features.append({
                "name":    col,
                "type":    "numeric",
                "min":     round(float(col_data.min()), 2),
                "max":     round(float(col_data.max()), 2),
                "mean":    round(float(col_data.mean()), 2),
                "default": round(float(col_data.mean()), 2),
                "is_top":  is_top,
                "label":   col.replace("_", " ").title(),
            })

    # Get a high-risk sample record
    sample_record = {}
    if os.path.exists(at_risk_path):
        try:
            at_risk_df = pd.read_csv(at_risk_path)
            if len(at_risk_df) > 0:
                row = at_risk_df.iloc[0]
                for col in feature_cols:
                    if col in row.index:
                        val = row[col]
                        if pd.isna(val):
                            continue
                        sample_record[col] = str(val) if df[col].dtype == object or df[col].nunique() <= 10 else float(val)
        except: pass

    return {
        "features":      features,
        "target_col":    str(target_col) if target_col else "target",
        "sample_record": sample_record,
        "top_features":  top_shap_features[:5],
        "model_type":    "binary_classification",
    }


@router.post("/predict")
def predict_what_if(req: PredictRequest):
    """
    Run a what-if prediction with modified feature values.
    Returns churn probability and risk level.
    """
    client_path  = get_path(req.user_id, req.client_name)
    model_path   = os.path.join(client_path, "trained_model.joblib")
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")

    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="No trained model found.")

    df         = pd.read_csv(cleaned_path)
    target_col = detect_target(df)
    model      = joblib.load(model_path)

    # Prepare the feature row
    from sklearn.preprocessing import LabelEncoder
    df_processed = df.copy()

    # Drop target and ID cols
    feature_cols = [c for c in df.columns if c != target_col]
    id_cols      = [c for c in feature_cols if "id" in c.lower() and df[c].nunique() == len(df)]
    feature_cols = [c for c in feature_cols if c not in id_cols]

    # Encode categoricals using the same encoding as training
    le_map = {}
    for col in df_processed.select_dtypes(include="object").columns:
        le = LabelEncoder()
        df_processed[col] = le.fit_transform(df_processed[col].astype(str))
        le_map[col] = le

    # Build input row
    input_row = {}
    for col in feature_cols:
        if col in req.features:
            val = req.features[col]
            if col in le_map:
                try:
                    val = le_map[col].transform([str(val)])[0]
                except:
                    val = 0
            else:
                try:
                    val = float(val)
                except:
                    val = 0.0
        else:
            # Use mean for missing features
            val = float(df_processed[col].mean()) if col in df_processed.columns else 0.0
        input_row[col] = val

    # Get model feature names
    try:
        model_features = model.get_booster().feature_names if hasattr(model, "get_booster") else feature_cols
    except:
        model_features = feature_cols

    # Build DataFrame with correct feature order
    X_input = pd.DataFrame([input_row])
    for col in model_features:
        if col not in X_input.columns:
            X_input[col] = 0.0
    X_input = X_input[model_features]

    # Predict
    try:
        proba = model.predict_proba(X_input)[0]
        if len(proba) == 2:
            risk_pct = round(float(proba[1]) * 100, 2)
        else:
            risk_pct = round(float(proba.max()) * 100, 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # Risk level
    if risk_pct >= 70:
        risk_level = "high"
        risk_label = "High Risk"
        risk_color = "red"
        recommendation = "Immediate intervention required. Consider offering a contract upgrade or personalized retention offer."
    elif risk_pct >= 40:
        risk_level = "medium"
        risk_label = "Medium Risk"
        risk_color = "orange"
        recommendation = "Monitor closely. A targeted promotion or loyalty reward may reduce risk."
    else:
        risk_level = "low"
        risk_label = "Low Risk"
        risk_color = "green"
        recommendation = "Customer appears stable. Standard engagement is sufficient."

    return {
        "risk_probability": risk_pct,
        "risk_level":       risk_level,
        "risk_label":       risk_label,
        "risk_color":       risk_color,
        "recommendation":   recommendation,
    }
