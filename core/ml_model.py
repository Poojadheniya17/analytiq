# core/ml_model.py
# Analytiq — XGBoost Churn/Target Prediction

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os, json

from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import (classification_report, confusion_matrix,
                                      roc_auc_score, roc_curve, ConfusionMatrixDisplay)
from xgboost import XGBClassifier


def prepare_features(df: pd.DataFrame, target_col: str):
    df = df.copy()
    churn_map = {"Yes": 1, "No": 0, "True": 1, "False": 0, "true": 1, "false": 0}
    if df[target_col].dtype == object:
        df[target_col] = df[target_col].map(churn_map).fillna(df[target_col])

    id_cols = [c for c in df.columns if "id" in c.lower()]
    df.drop(columns=id_cols, inplace=True, errors="ignore")

    le = LabelEncoder()
    for col in df.select_dtypes(include="object").columns:
        df[col] = le.fit_transform(df[col].astype(str))

    X = df.drop(columns=[target_col])
    y = df[target_col].astype(int)
    return X, y


def train_model(X_train, y_train) -> XGBClassifier:
    model = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        eval_metric="logloss", random_state=42
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test, output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    auc    = round(roc_auc_score(y_test, y_proba), 4)
    report = classification_report(y_test, y_pred, output_dict=True)

    plt.style.use("seaborn-v0_8-whitegrid")

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color="#2563EB", lw=2.5, label=f"AUC = {auc}")
    ax.fill_between(fpr, tpr, alpha=0.08, color="#2563EB")
    ax.plot([0,1],[0,1],"--", color="#9CA3AF", lw=1)
    ax.set_title("ROC Curve", fontsize=13, fontweight="600", pad=15)
    ax.set_xlabel("False Positive Rate", fontsize=10)
    ax.set_ylabel("True Positive Rate", fontsize=10)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/roc_curve.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Confusion Matrix
    cm   = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Negative", "Positive"])
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Confusion Matrix", fontsize=13, fontweight="600", pad=15)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()

    return {
        "auc_roc":   auc,
        "precision": round(report["1"]["precision"], 4),
        "recall":    round(report["1"]["recall"], 4),
        "f1_score":  round(report["1"]["f1-score"], 4)
    }


def plot_feature_importance(model, feature_names: list, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    feat_df = pd.DataFrame({
        "feature":    feature_names,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False).head(15)

    fig, ax = plt.subplots(figsize=(9, 6))
    colors  = ["#2563EB" if i == 0 else "#93C5FD" for i in range(len(feat_df))]
    ax.barh(feat_df["feature"][::-1], feat_df["importance"][::-1], color=colors[::-1], edgecolor="white")
    ax.set_title("Top Feature Importances", fontsize=13, fontweight="600", pad=15)
    ax.set_xlabel("Importance Score", fontsize=10)
    ax.spines[['top','right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/feature_importance.png", dpi=150, bbox_inches="tight")
    plt.close()


def predict_at_risk(model, X, df_original: pd.DataFrame, output_path: str) -> pd.DataFrame:
    proba   = model.predict_proba(X)[:, 1]
    df_risk = df_original.copy()
    df_risk["risk_probability_%"] = (proba * 100).round(2)
    df_risk = df_risk.sort_values("risk_probability_%", ascending=False)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_risk.head(50).to_csv(output_path, index=False)
    return df_risk.head(10)
