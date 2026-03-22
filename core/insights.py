# core/insights.py
# Analytiq — Auto Insight Engine

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json


def detect_target_column(df: pd.DataFrame) -> str | None:
    candidates = ["churn", "churned", "target", "label", "outcome", "attrition", "default", "fraud"]
    for col in df.columns:
        if col.lower() in candidates:
            return col
    return None


def generate_kpis(df: pd.DataFrame, target_col: str | None) -> dict:
    kpis = {}
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

    for keyword in ["charge", "revenue", "amount", "price", "value", "sales", "salary", "cost"]:
        for col in numeric_cols:
            if keyword in col:
                kpis[f"total_{col}"] = round(float(df[col].sum()), 2)
                kpis[f"avg_{col}"]   = round(float(df[col].mean()), 2)

    if target_col:
        churn_map = {"Yes": 1, "No": 0, "1": 1, "0": 0, 1: 1, 0: 0,
                     "True": 1, "False": 0, "true": 1, "false": 0}
        churn_series = df[target_col].map(churn_map)
        if churn_series.notna().any():
            kpis["target_rate_%"]   = round(float(churn_series.mean() * 100), 2)
            kpis["total_positive"]  = int(churn_series.sum())
            kpis["total_negative"]  = int((churn_series == 0).sum())

    kpis["total_records"] = len(df)
    kpis["total_features"] = df.shape[1]
    return kpis


def detect_anomalies(df: pd.DataFrame) -> list:
    anomalies = []
    for col in df.select_dtypes(include=["float64", "int64"]).columns:
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR     = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
        if len(outliers) > 0:
            anomalies.append({
                "column":        col,
                "outlier_count": len(outliers),
                "outlier_%":     round(len(outliers) / len(df) * 100, 2)
            })
    return anomalies


def generate_segment_insights(df: pd.DataFrame, target_col: str | None) -> list:
    insights = []
    if not target_col:
        return insights

    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    if target_col in cat_cols:
        cat_cols.remove(target_col)

    churn_map    = {"Yes": 1, "No": 0, "1": 1, "0": 0, 1: 1, 0: 0,
                    "True": 1, "False": 0, "true": 1, "false": 0}
    churn_series = df[target_col].map(churn_map)

    for col in cat_cols[:6]:
        if df[col].nunique() <= 15:
            segment = df.groupby(col).apply(
                lambda x: round(float(churn_series.loc[x.index].mean() * 100), 2)
            ).reset_index()
            segment.columns = [col, "churn_rate_%"]
            top = segment.sort_values("churn_rate_%", ascending=False).iloc[0]
            insights.append({
                "segment":               col,
                "highest_churn_value":   str(top[col]),
                "highest_churn_rate_%":  float(top["churn_rate_%"]),
                "full_breakdown":        segment.to_dict(orient="records")
            })
    return insights


def plot_insights(df: pd.DataFrame, target_col: str | None, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    colors = {"primary": "#2563EB", "danger": "#EF4444", "success": "#10B981", "warn": "#F59E0B"}

    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

    # 1. Target distribution
    if target_col:
        fig, ax = plt.subplots(figsize=(7, 4))
        counts = df[target_col].value_counts()
        bars = ax.bar(counts.index.astype(str), counts.values,
                      color=[colors["danger"], colors["success"]], width=0.5, edgecolor="white")
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                    f'{bar.get_height():,}', ha='center', va='bottom', fontsize=11, fontweight='500')
        ax.set_title(f"Target Distribution — {target_col.title()}", fontsize=13, fontweight="600", pad=15)
        ax.set_xlabel(""); ax.set_ylabel("Count", fontsize=10)
        ax.spines[['top','right']].set_visible(False)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/target_distribution.png", dpi=150, bbox_inches="tight")
        plt.close()

    # 2. Correlation heatmap
    if len(numeric_cols) >= 2:
        fig, ax = plt.subplots(figsize=(10, 7))
        corr = df[numeric_cols[:12]].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
                    cmap="RdYlBu_r", center=0, ax=ax,
                    linewidths=0.5, linecolor="#E2E8F0",
                    annot_kws={"size": 9})
        ax.set_title("Feature Correlation Matrix", fontsize=13, fontweight="600", pad=15)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/correlation_heatmap.png", dpi=150, bbox_inches="tight")
        plt.close()

    # 3. Numeric distributions
    for col in numeric_cols[:3]:
        if "charge" in col or "revenue" in col or "amount" in col or "salary" in col or "cost" in col:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.hist(df[col].dropna(), bins=40, color=colors["primary"], alpha=0.85, edgecolor="white")
            ax.axvline(df[col].mean(), color=colors["danger"], linewidth=2, linestyle="--",
                       label=f"Mean: {df[col].mean():.1f}")
            ax.set_title(f"Distribution — {col.replace('_',' ').title()}", fontsize=13, fontweight="600", pad=15)
            ax.set_xlabel(col.replace('_', ' ').title(), fontsize=10)
            ax.set_ylabel("Frequency", fontsize=10)
            ax.spines[['top','right']].set_visible(False)
            ax.legend(fontsize=10)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/{col}_distribution.png", dpi=150, bbox_inches="tight")
            plt.close()
            break


def save_insights(kpis: dict, anomalies: list, segments: list, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"kpis": kpis, "anomalies": anomalies, "segment_insights": segments}, f, indent=4)
