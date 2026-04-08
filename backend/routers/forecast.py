# backend/routers/forecast.py
import sys, os, json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")
)

class ForecastRequest(BaseModel):
    user_id:     int
    client_name: str

def get_path(user_id: int, client_name: str) -> str:
    return os.path.join(BASE_DATA, str(user_id), client_name.lower().replace(" ", "_"))

def detect_target(df: pd.DataFrame) -> str | None:
    """Detect target column — extended list covering all common names."""
    known = [
        "churn", "churned", "target", "label", "class", "fraud", "is_fraud",
        "default", "attrition", "outcome", "converted", "purchased",
        "survived", "response", "y", "is_churn", "has_churned",
        "exited", "leave", "left"
    ]
    for col in df.columns:
        if col.lower() in known:
            return col
    # Prefix patterns
    for col in df.columns:
        if col.lower().startswith(("is_", "has_", "flag_", "will_", "did_")):
            if df[col].nunique() <= 10:
                return col
    # Last binary column
    for col in reversed(df.columns.tolist()):
        if df[col].nunique() == 2:
            return col
    return None

@router.post("/churn")
def forecast_churn(req: ForecastRequest):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")

    print(f"[Forecast] Looking for data at: {cleaned_path}")

    if not os.path.exists(cleaned_path):
        raise HTTPException(
            status_code=404,
            detail="No cleaned data found. Please upload and clean your data first."
        )

    df = pd.read_csv(cleaned_path)
    target_col = detect_target(df)

    print(f"[Forecast] Target column detected: {target_col}")

    if not target_col:
        raise HTTPException(
            status_code=400,
            detail="No target column detected. Make sure your dataset has a binary target column (e.g. churn, fraud, attrition, class)."
        )

    # Map target to numeric
    churn_map = {"Yes": 1, "No": 0, "True": 1, "False": 0,
                 "true": 1, "false": 0, 1: 1, 0: 0, "1": 1, "0": 0}
    df["_target"] = df[target_col].map(churn_map)
    if df["_target"].isna().all():
        df["_target"] = pd.to_numeric(df[target_col], errors="coerce")

    df["_target"] = df["_target"].fillna(0)
    churn_rate = float(df["_target"].mean())

    # Detect tenure/time column for trend
    tenure_col = None
    for col in df.columns:
        if col.lower() in ["tenure", "months", "age", "days", "duration", "period", "time"]:
            if pd.api.types.is_numeric_dtype(df[col]):
                tenure_col = col
                break

    # Build monthly trend
    if tenure_col:
        try:
            n_bins = min(12, df[tenure_col].nunique())
            df["_bucket"] = pd.cut(df[tenure_col], bins=n_bins, labels=False)
            trend_df = df.groupby("_bucket")["_target"].mean().reset_index()
            months = [
                {
                    "month": int(r["_bucket"]) + 1,
                    "churn_rate": round(float(r["_target"]) * 100, 2)
                }
                for _, r in trend_df.iterrows()
                if not pd.isna(r["_target"])
            ]
        except:
            months = _generate_synthetic_trend(churn_rate)
    else:
        months = _generate_synthetic_trend(churn_rate)

    # 3-month forecast using simple linear regression on last 3 points
    forecast = _generate_forecast(months, churn_rate)

    trend_direction = "increasing" if forecast and forecast[-1]["churn_rate"] > churn_rate * 100 else "decreasing"
    target_label    = target_col.replace("_", " ").title()

    return {
        "target_column":      target_col,
        "target_label":       target_label,
        "current_churn_rate": round(churn_rate * 100, 2),
        "trend":              months,
        "forecast":           forecast,
        "summary": (
            f"Current {target_label} rate is {round(churn_rate * 100, 1)}%. "
            f"The trend is {trend_direction} over the next 3 months. "
            f"Dataset contains {len(df):,} records with {int(df['_target'].sum())} positive cases."
        )
    }


def _generate_synthetic_trend(churn_rate: float) -> list:
    """Generate a synthetic 12-month trend when no tenure column exists."""
    np.random.seed(42)
    months = []
    base   = churn_rate * 100
    for i in range(1, 13):
        noise = np.random.uniform(-min(3, base * 0.2), min(3, base * 0.2))
        months.append({
            "month": i,
            "churn_rate": round(max(0, min(100, base + noise)), 2)
        })
    return months


def _generate_forecast(months: list, churn_rate: float) -> list:
    """Generate 3-month forecast from historical trend."""
    if not months:
        return []
    try:
        last_vals  = [m["churn_rate"] for m in months[-3:]]
        avg_change = (last_vals[-1] - last_vals[0]) / max(len(last_vals) - 1, 1)
        last_val   = months[-1]["churn_rate"]
        forecast   = []
        for i in range(1, 4):
            projected = round(max(0, min(100, last_val + avg_change * i)), 2)
            forecast.append({
                "month":      f"Month +{i}",
                "churn_rate": projected,
                "projected":  True
            })
        return forecast
    except:
        base = churn_rate * 100
        return [{"month": f"Month +{i}", "churn_rate": round(base, 2), "projected": True} for i in range(1, 4)]
