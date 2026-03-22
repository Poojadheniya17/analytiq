# core/pipeline.py
import pandas as pd
import numpy as np
import os
import json


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(" ", "_").str.replace(r"[^\w]", "_", regex=True))
    df = df.drop_duplicates()
    for col in df.columns:
        missing = df[col].isnull().sum()
        if missing > 0:
            if df[col].dtype in ["float64", "int64"]:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
    return df


def profile_data(df: pd.DataFrame) -> dict:
    profile = {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "column_types": {col: str(df[col].dtype) for col in df.columns},
        "missing_values": {},
        "numeric_summary": {},
        "categorical_summary": {}
    }
    for col in df.columns:
        missing = df[col].isnull().sum()
        if missing > 0:
            profile["missing_values"][col] = int(missing)
        if df[col].dtype in ["float64", "int64"]:
            profile["numeric_summary"][col] = {
                "mean":   round(float(df[col].mean()), 2),
                "median": round(float(df[col].median()), 2),
                "std":    round(float(df[col].std()), 2),
                "min":    round(float(df[col].min()), 2),
                "max":    round(float(df[col].max()), 2),
            }
        elif df[col].dtype == "object":
            profile["categorical_summary"][col] = {
                "unique_values": int(df[col].nunique()),
                "top_5": df[col].value_counts().head(5).to_dict()
            }
    return profile


def save_cleaned_data(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def save_profile(profile: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(profile, f, indent=4)
