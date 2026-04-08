# backend/routers/dashboard.py
# Analytiq — Interactive Dashboard Data Router

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import pandas as pd
import numpy as np

router = APIRouter()

BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")
)

class DashboardRequest(BaseModel):
    user_id:     int
    client_name: str

class FilteredRequest(BaseModel):
    user_id:     int
    client_name: str
    filters:     Dict[str, str] = {}

def get_path(user_id: int, client_name: str) -> str:
    return os.path.join(BASE_DATA, str(user_id), client_name.lower().replace(" ", "_"))

def detect_target(df: pd.DataFrame):
    known = ["churn", "churned", "target", "label", "class", "fraud", "is_fraud",
             "default", "attrition", "outcome", "converted", "exited", "left", "y"]
    for col in df.columns:
        if col.lower() in known:
            return col
    for col in df.columns:
        if col.lower().startswith(("is_", "has_", "flag_", "will_", "did_")):
            if df[col].nunique() <= 10:
                return col
    for col in reversed(df.columns.tolist()):
        if df[col].nunique() == 2:
            return col
    return None

def to_numeric_target(series: pd.Series) -> pd.Series:
    mapping = {"Yes": 1, "No": 0, "True": 1, "False": 0,
               "true": 1, "false": 0, "1": 1, "0": 0, 1: 1, 0: 0}
    mapped = series.map(mapping)
    if mapped.isna().all():
        mapped = pd.to_numeric(series, errors="coerce")
    return mapped.fillna(0).astype(int)


@router.post("/config")
def get_dashboard_config(req: DashboardRequest):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")

    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No cleaned data found. Run insights first.")

    df         = pd.read_csv(cleaned_path)
    target_col = detect_target(df)

    filter_cols = []
    for col in df.columns:
        if col == target_col:
            continue
        n_unique = df[col].nunique()
        if 2 <= n_unique <= 15:
            values = [str(v) for v in sorted(df[col].dropna().unique().tolist())]
            filter_cols.append({
                "column": str(col),
                "values": values,
                "type":   "categorical"
            })

    numeric_cols = [
        str(col) for col in df.select_dtypes(include=["float64", "int64"]).columns
        if col != target_col and df[col].nunique() > 10
    ]

    best_bar_col = None
    best_variance = 0
    if target_col:
        df["_target"] = to_numeric_target(df[target_col])
        for fc in filter_cols:
            col = fc["column"]
            try:
                rates    = df.groupby(col)["_target"].mean()
                variance = float(rates.var())
                if variance > best_variance:
                    best_variance = variance
                    best_bar_col  = col
            except:
                pass

    return {
        "target_col":   str(target_col) if target_col else None,
        "filter_cols":  filter_cols[:6],
        "numeric_cols": numeric_cols[:10],
        "best_bar_col": best_bar_col,
        "total_rows":   int(len(df)),
        "total_cols":   int(df.shape[1]),
    }


@router.post("/data")
def get_dashboard_data(req: DashboardRequest):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")

    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No cleaned data found.")

    df         = pd.read_csv(cleaned_path)
    target_col = detect_target(df)

    if not target_col:
        raise HTTPException(status_code=400, detail="No target column detected.")

    df["_target"] = to_numeric_target(df[target_col])
    return _build_dashboard_data(df, target_col)


@router.post("/filtered")
def get_filtered_data(req: FilteredRequest):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")

    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No cleaned data found.")

    df         = pd.read_csv(cleaned_path)
    target_col = detect_target(df)

    if not target_col:
        raise HTTPException(status_code=400, detail="No target column detected.")

    df["_target"] = to_numeric_target(df[target_col])

    # Apply filters
    for col, value in req.filters.items():
        if col in df.columns and value and value != "All":
            df = df[df[col].astype(str) == str(value)]

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="No data matches these filters. Try a different combination.")

    return _build_dashboard_data(df, target_col)


def _build_dashboard_data(df: pd.DataFrame, target_col: str) -> dict:
    total       = int(len(df))
    target_rate = round(float(df["_target"].mean() * 100), 2)
    total_pos   = int(df["_target"].sum())
    total_neg   = total - total_pos

    kpis = {
        "total_records":  total,
        "target_rate_%":  target_rate,
        "total_positive": total_pos,
        "total_negative": total_neg,
    }

    numeric_cols = [
        col for col in df.select_dtypes(include=["float64", "int64"]).columns
        if col not in ["_target"] and df[col].nunique() > 5
    ]
    for col in numeric_cols[:2]:
        kpis[f"avg_{col}"] = round(float(df[col].mean()), 2)

    # Bar charts
    bar_charts = []
    for col in df.columns:
        if col in ["_target", target_col]:
            continue
        n_unique = df[col].nunique()
        if 2 <= n_unique <= 12:
            try:
                grouped = df.groupby(col).agg(
                    count=("_target", "count"),
                    target_rate=("_target", "mean")
                ).reset_index()
                grouped["target_rate"] = (grouped["target_rate"] * 100).round(2)
                grouped[col] = grouped[col].astype(str)
                bar_charts.append({
                    "column": str(col),
                    "data": [
                        {
                            "name":        str(row[col]),
                            "target_rate": float(row["target_rate"]),
                            "count":       int(row["count"]),
                        }
                        for _, row in grouped.iterrows()
                    ]
                })
            except:
                pass
        if len(bar_charts) >= 4:
            break

    # Line chart
    line_chart = []
    for col in numeric_cols[:3]:
        try:
            n_bins = min(10, int(df[col].nunique()))
            df["_bucket"] = pd.cut(df[col], bins=n_bins, labels=False)
            line_df = df.groupby("_bucket").agg(
                count=("_target", "count"),
                target_rate=("_target", "mean"),
                avg_value=(col, "mean")
            ).reset_index().dropna()
            if len(line_df) >= 3:
                line_chart = [{
                    "column": str(col),
                    "data": [
                        {
                            "bucket":      int(r["_bucket"]),
                            "avg_value":   round(float(r["avg_value"]), 2),
                            "target_rate": round(float(r["target_rate"]) * 100, 2),
                            "count":       int(r["count"]),
                        }
                        for _, r in line_df.iterrows()
                    ]
                }]
                break
        except:
            pass

    return {
        "kpis":          kpis,
        "bar_charts":    bar_charts,
        "line_chart":    line_chart,
        "target_col":    str(target_col),
        "filtered_rows": total,
        "numeric_col_x": str(numeric_cols[0]) if len(numeric_cols) > 0 else None,
        "numeric_col_y": str(numeric_cols[1]) if len(numeric_cols) > 1 else None,
    }
