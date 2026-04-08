# core/ml_model.py
# Analytiq — Smart ML Engine with Auto Problem Detection

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os, json, joblib

from sklearn.model_selection    import train_test_split
from sklearn.preprocessing      import LabelEncoder
from sklearn.metrics            import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, ConfusionMatrixDisplay, mean_squared_error,
    mean_absolute_error, r2_score, silhouette_score
)
from sklearn.linear_model       import LogisticRegression, LinearRegression
from sklearn.ensemble           import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster            import KMeans
from xgboost                    import XGBClassifier, XGBRegressor

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


# ══════════════════════════════════════════════════════════════
# STEP 1 — PROBLEM TYPE DETECTION
# ══════════════════════════════════════════════════════════════

def detect_problem_type(df: pd.DataFrame, target_col: str | None) -> dict:
    """
    Automatically detect what kind of ML problem this dataset represents.
    Returns problem type + confidence + reasoning.
    """
    # No target column → clustering
    if not target_col:
        has_date = any(
            pd.api.types.is_datetime64_any_dtype(df[c]) or "date" in c.lower() or "time" in c.lower()
            for c in df.columns
        )
        if has_date:
            return {"type": "time_series", "confidence": "medium", "reason": "Date/time column detected with no target — time series analysis"}
        return {"type": "clustering", "confidence": "medium", "reason": "No target column detected — using unsupervised clustering"}

    target = df[target_col]
    n_unique = target.nunique()
    is_numeric = pd.api.types.is_numeric_dtype(target)

    # Check for date column → time series
    has_date = any(
        "date" in c.lower() or "time" in c.lower() or "month" in c.lower() or "year" in c.lower()
        for c in df.columns if c != target_col
    )

    if n_unique == 2:
        return {"type": "binary_classification", "confidence": "high", "reason": f"Target '{target_col}' has exactly 2 unique values — binary classification"}

    if 2 < n_unique <= 15 and not is_numeric:
        return {"type": "multiclass_classification", "confidence": "high", "reason": f"Target '{target_col}' has {n_unique} categories — multiclass classification"}

    if 2 < n_unique <= 15 and is_numeric:
        return {"type": "multiclass_classification", "confidence": "medium", "reason": f"Target '{target_col}' has {n_unique} numeric classes — treating as multiclass"}

    if is_numeric and n_unique > 15:
        if has_date:
            return {"type": "time_series", "confidence": "high", "reason": f"Numeric target with date column detected — time series forecasting"}
        return {"type": "regression", "confidence": "high", "reason": f"Target '{target_col}' is continuous numeric — regression problem"}

    return {"type": "binary_classification", "confidence": "low", "reason": "Could not determine type clearly — defaulting to classification"}


def detect_target_column(df: pd.DataFrame) -> str | None:
    """Smart target column detection with multiple strategies."""
    # Strategy 1: Known names
    known = ["churn", "churned", "target", "label", "outcome", "attrition",
             "default", "fraud", "is_fraud", "converted", "purchased",
             "survived", "outcome", "response", "y"]
    for col in df.columns:
        if col.lower() in known:
            return col

    # Strategy 2: Columns starting with is_, has_, flag_
    for col in df.columns:
        if col.lower().startswith(("is_", "has_", "flag_", "will_", "did_")):
            if df[col].nunique() <= 10:
                return col

    # Strategy 3: Binary columns at the end of the dataframe
    for col in reversed(df.columns.tolist()):
        if df[col].nunique() == 2:
            return col

    return None


# ══════════════════════════════════════════════════════════════
# STEP 2 — UPLOAD VALIDATION
# ══════════════════════════════════════════════════════════════

def validate_dataset(df: pd.DataFrame) -> dict:
    """Validate dataset before processing. Returns issues and warnings."""
    issues   = []
    warnings = []
    passed   = True

    if len(df) < 50:
        issues.append(f"Dataset too small ({len(df)} rows). Minimum 50 rows required for reliable analysis.")
        passed = False

    if df.shape[1] < 2:
        issues.append("Dataset needs at least 2 columns.")
        passed = False

    if len(df) < 200:
        warnings.append(f"Small dataset ({len(df)} rows). Results may not be statistically reliable.")

    missing_pct = df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100
    if missing_pct > 50:
        issues.append(f"Too many missing values ({missing_pct:.1f}%). Please clean the data first.")
        passed = False
    elif missing_pct > 20:
        warnings.append(f"High missing value rate ({missing_pct:.1f}%). Consider reviewing data quality.")

    duplicate_pct = df.duplicated().sum() / len(df) * 100
    if duplicate_pct > 30:
        warnings.append(f"High duplicate rate ({duplicate_pct:.1f}%). Consider removing duplicates.")

    all_same = [col for col in df.columns if df[col].nunique() == 1]
    if all_same:
        warnings.append(f"Columns with no variation: {', '.join(all_same[:3])}. These won't help predictions.")

    return {"passed": passed, "issues": issues, "warnings": warnings,
            "rows": len(df), "columns": df.shape[1], "missing_pct": round(missing_pct, 2),
            "duplicate_pct": round(duplicate_pct, 2)}


# ══════════════════════════════════════════════════════════════
# STEP 3 — FEATURE PREPARATION
# ══════════════════════════════════════════════════════════════

def prepare_features(df: pd.DataFrame, target_col: str, problem_type: str = "binary_classification"):
    """Prepare features for ML training."""
    df = df.copy()

    # Map common binary targets
    if problem_type in ["binary_classification"]:
        churn_map = {"Yes": 1, "No": 0, "True": 1, "False": 0,
                     "true": 1, "false": 0, "1": 1, "0": 0, 1: 1, 0: 0}
        if df[target_col].dtype == object:
            df[target_col] = df[target_col].map(churn_map).fillna(df[target_col])

    # Drop ID columns
    id_cols = [c for c in df.columns if "id" in c.lower() and df[c].nunique() == len(df)]
    df.drop(columns=id_cols, inplace=True, errors="ignore")

    # Encode categoricals
    le = LabelEncoder()
    for col in df.select_dtypes(include="object").columns:
        if col != target_col:
            df[col] = le.fit_transform(df[col].astype(str))
    if df[target_col].dtype == object:
        df[target_col] = le.fit_transform(df[target_col].astype(str))

    X = df.drop(columns=[target_col])
    y = df[target_col]

    if problem_type in ["binary_classification", "multiclass_classification"]:
        y = y.astype(int)
    else:
        y = y.astype(float)

    return X, y


# ══════════════════════════════════════════════════════════════
# STEP 4 — AUTO ML (runs multiple models, picks best)
# ══════════════════════════════════════════════════════════════

def run_automl(X_train, X_test, y_train, y_test, problem_type: str, output_dir: str) -> dict:
    """
    Run multiple algorithms, evaluate all, return comparison + best model.
    """
    os.makedirs(output_dir, exist_ok=True)
    results    = {}
    best_model = None
    best_score = -999
    best_name  = ""

    # ── Binary Classification ──────────────────────────────
    if problem_type == "binary_classification":
        candidates = {
            "XGBoost":            XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, eval_metric="logloss", random_state=42),
            "Random Forest":      RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            "Logistic Regression":LogisticRegression(max_iter=1000, random_state=42),
        }
        for name, model in candidates.items():
            try:
                model.fit(X_train, y_train)
                y_proba = model.predict_proba(X_test)[:, 1]
                y_pred  = model.predict(X_test)
                auc     = round(roc_auc_score(y_test, y_proba), 4)
                report  = classification_report(y_test, y_pred, output_dict=True)
                results[name] = {
                    "auc_roc":   auc,
                    "precision": round(report["1"]["precision"], 4),
                    "recall":    round(report["1"]["recall"], 4),
                    "f1_score":  round(report["1"]["f1-score"], 4),
                    "accuracy":  round(report["accuracy"], 4),
                }
                if auc > best_score:
                    best_score = auc
                    best_model = model
                    best_name  = name
                print(f"  ✔ {name}: AUC={auc}")
            except Exception as e:
                print(f"  ✗ {name} failed: {e}")

    # ── Regression ────────────────────────────────────────
    elif problem_type == "regression":
        candidates = {
            "XGBoost Regressor":      XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42),
            "Random Forest Regressor":RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
            "Linear Regression":      LinearRegression(),
        }
        for name, model in candidates.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                rmse   = round(np.sqrt(mean_squared_error(y_test, y_pred)), 4)
                mae    = round(mean_absolute_error(y_test, y_pred), 4)
                r2     = round(r2_score(y_test, y_pred), 4)
                results[name] = {"rmse": rmse, "mae": mae, "r2_score": r2}
                score = r2  # higher is better
                if score > best_score:
                    best_score = score
                    best_model = model
                    best_name  = name
                print(f"  ✔ {name}: R²={r2}, RMSE={rmse}")
            except Exception as e:
                print(f"  ✗ {name} failed: {e}")

    # ── Multiclass Classification ─────────────────────────
    elif problem_type == "multiclass_classification":
        candidates = {
            "XGBoost":            XGBClassifier(n_estimators=200, eval_metric="mlogloss", random_state=42),
            "Random Forest":      RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            "Logistic Regression":LogisticRegression(max_iter=1000, random_state=42, multi_class="auto"),
        }
        for name, model in candidates.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                report = classification_report(y_test, y_pred, output_dict=True)
                f1     = round(report["macro avg"]["f1-score"], 4)
                acc    = round(report["accuracy"], 4)
                results[name] = {"f1_macro": f1, "accuracy": acc}
                if f1 > best_score:
                    best_score = f1
                    best_model = model
                    best_name  = name
                print(f"  ✔ {name}: F1={f1}, Acc={acc}")
            except Exception as e:
                print(f"  ✗ {name} failed: {e}")

    return {"results": results, "best_model": best_model, "best_name": best_name, "best_score": best_score}


# ══════════════════════════════════════════════════════════════
# STEP 5 — EVALUATION & CHARTS
# ══════════════════════════════════════════════════════════════

def evaluate_and_plot(model, X_test, y_test, problem_type: str, output_dir: str, feature_names: list) -> dict:
    """Generate evaluation metrics and charts based on problem type."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    metrics = {}

    if problem_type in ["binary_classification"]:
        y_pred  = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        report  = classification_report(y_test, y_pred, output_dict=True)
        metrics = {
            "auc_roc":   round(roc_auc_score(y_test, y_proba), 4),
            "precision": round(report["1"]["precision"], 4),
            "recall":    round(report["1"]["recall"], 4),
            "f1_score":  round(report["1"]["f1-score"], 4),
            "accuracy":  round(report["accuracy"], 4),
        }
        # ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(fpr, tpr, color="#2563EB", lw=2.5, label=f"AUC = {metrics['auc_roc']}")
        ax.fill_between(fpr, tpr, alpha=0.08, color="#2563EB")
        ax.plot([0,1],[0,1],"--", color="#9CA3AF", lw=1)
        ax.set_title("ROC Curve", fontsize=13, fontweight="600")
        ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
        ax.spines[['top','right']].set_visible(False)
        ax.legend(); plt.tight_layout()
        plt.savefig(f"{output_dir}/roc_curve.png", dpi=150, bbox_inches="tight"); plt.close()

        # Confusion Matrix
        cm   = confusion_matrix(y_test, y_pred)
        disp = ConfusionMatrixDisplay(cm, display_labels=["Negative","Positive"])
        fig, ax = plt.subplots(figsize=(6, 5))
        disp.plot(ax=ax, colorbar=False, cmap="Blues")
        ax.set_title("Confusion Matrix", fontsize=13, fontweight="600")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/confusion_matrix.png", dpi=150, bbox_inches="tight"); plt.close()

    elif problem_type == "regression":
        y_pred  = model.predict(X_test)
        metrics = {
            "rmse":    round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
            "mae":     round(float(mean_absolute_error(y_test, y_pred)), 4),
            "r2_score":round(float(r2_score(y_test, y_pred)), 4),
        }
        # Actual vs Predicted
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(y_test, y_pred, alpha=0.4, color="#2563EB", s=20)
        mn, mx = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
        ax.plot([mn, mx], [mn, mx], "r--", lw=1.5, label="Perfect prediction")
        ax.set_title("Actual vs Predicted", fontsize=13, fontweight="600")
        ax.set_xlabel("Actual"); ax.set_ylabel("Predicted")
        ax.spines[['top','right']].set_visible(False)
        ax.legend(); plt.tight_layout()
        plt.savefig(f"{output_dir}/actual_vs_predicted.png", dpi=150, bbox_inches="tight"); plt.close()

        # Residuals
        residuals = y_test - y_pred
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(residuals, bins=40, color="#2563EB", alpha=0.8, edgecolor="white")
        ax.axvline(0, color="red", linestyle="--", lw=1.5)
        ax.set_title("Residual Distribution", fontsize=13, fontweight="600")
        ax.set_xlabel("Residual"); ax.set_ylabel("Frequency")
        ax.spines[['top','right']].set_visible(False); plt.tight_layout()
        plt.savefig(f"{output_dir}/residuals.png", dpi=150, bbox_inches="tight"); plt.close()

    elif problem_type == "multiclass_classification":
        y_pred = model.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)
        metrics = {
            "f1_macro": round(report["macro avg"]["f1-score"], 4),
            "accuracy": round(report["accuracy"], 4),
            "f1_weighted": round(report["weighted avg"]["f1-score"], 4),
        }
        cm = confusion_matrix(y_test, y_pred)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title("Confusion Matrix", fontsize=13, fontweight="600")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/confusion_matrix.png", dpi=150, bbox_inches="tight"); plt.close()

    # Feature importance (works for tree-based models)
    try:
        if hasattr(model, "feature_importances_"):
            feat_df = pd.DataFrame({
                "feature":    feature_names,
                "importance": model.feature_importances_
            }).sort_values("importance", ascending=False).head(15)
            fig, ax = plt.subplots(figsize=(9, 6))
            ax.barh(feat_df["feature"][::-1], feat_df["importance"][::-1],
                    color=["#2563EB" if i == 0 else "#93C5FD" for i in range(len(feat_df))][::-1])
            ax.set_title("Top Feature Importances", fontsize=13, fontweight="600")
            ax.set_xlabel("Importance Score")
            ax.spines[['top','right']].set_visible(False); plt.tight_layout()
            plt.savefig(f"{output_dir}/feature_importance.png", dpi=150, bbox_inches="tight"); plt.close()
    except: pass

    return metrics


# ══════════════════════════════════════════════════════════════
# STEP 6 — SHAP EXPLAINABILITY
# ══════════════════════════════════════════════════════════════

def generate_shap_explanation(model, X_test, feature_names: list, output_dir: str, problem_type: str) -> dict:
    """Generate SHAP values for model explainability."""
    if not SHAP_AVAILABLE:
        return {"available": False, "reason": "SHAP not installed. Run: pip install shap"}

    os.makedirs(output_dir, exist_ok=True)
    try:
        X_sample = X_test.iloc[:min(200, len(X_test))]

        if hasattr(model, "feature_importances_"):
            explainer   = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            if isinstance(shap_values, list):
                shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            else:
                shap_vals = shap_values

            # Mean absolute SHAP per feature
            mean_shap = np.abs(shap_vals).mean(axis=0)
            shap_df   = pd.DataFrame({
                "feature": feature_names,
                "shap_importance": mean_shap
            }).sort_values("shap_importance", ascending=False).head(10)

            # SHAP bar chart
            fig, ax = plt.subplots(figsize=(9, 6))
            colors   = ["#EF4444" if v > shap_df["shap_importance"].median() else "#2563EB"
                        for v in shap_df["shap_importance"]]
            ax.barh(shap_df["feature"][::-1], shap_df["shap_importance"][::-1], color=colors[::-1])
            ax.set_title("SHAP Feature Importance — Why the Model Decides", fontsize=13, fontweight="600")
            ax.set_xlabel("Mean |SHAP Value| (impact on prediction)")
            ax.spines[['top','right']].set_visible(False); plt.tight_layout()
            plt.savefig(f"{output_dir}/shap_importance.png", dpi=150, bbox_inches="tight"); plt.close()

            top_features = shap_df.head(5).to_dict(orient="records")
            explanation  = f"The top driver is '{shap_df.iloc[0]['feature']}' with an average impact of {shap_df.iloc[0]['shap_importance']:.3f}. "
            explanation += f"Other key factors are: {', '.join(shap_df['feature'].iloc[1:4].tolist())}."

            return {"available": True, "top_features": top_features, "explanation": explanation}

    except Exception as e:
        return {"available": False, "reason": str(e)}

    return {"available": False, "reason": "SHAP not supported for this model type"}


# ══════════════════════════════════════════════════════════════
# STEP 7 — MODEL PERSISTENCE
# ══════════════════════════════════════════════════════════════

def save_model(model, output_dir: str) -> str:
    """Save trained model to disk."""
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "trained_model.joblib")
    joblib.dump(model, model_path)
    print(f"💾 Model saved to: {model_path}")
    return model_path


def load_model(model_dir: str):
    """Load saved model from disk."""
    model_path = os.path.join(model_dir, "trained_model.joblib")
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)


# ══════════════════════════════════════════════════════════════
# STEP 8 — AT-RISK PREDICTION (classification only)
# ══════════════════════════════════════════════════════════════

def predict_at_risk(model, X, df_original: pd.DataFrame, output_path: str, problem_type: str) -> pd.DataFrame:
    """Identify top at-risk records for classification problems."""
    if problem_type not in ["binary_classification", "multiclass_classification"]:
        return pd.DataFrame()
    try:
        proba   = model.predict_proba(X)
        if proba.shape[1] == 2:
            risk_scores = proba[:, 1]
        else:
            risk_scores = proba.max(axis=1)
        df_risk = df_original.copy()
        df_risk["risk_probability_%"] = (risk_scores * 100).round(2)
        df_risk = df_risk.sort_values("risk_probability_%", ascending=False)
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        df_risk.head(50).to_csv(output_path, index=False)
        return df_risk.head(10)
    except Exception as e:
        print(f"At-risk prediction failed: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════
# MAIN TRAINING PIPELINE
# ══════════════════════════════════════════════════════════════

def train_full_pipeline(df: pd.DataFrame, target_col: str | None, client_path: str) -> dict:
    """
    Complete ML pipeline:
    1. Detect problem type
    2. Validate dataset
    3. Prepare features
    4. Run AutoML
    5. Evaluate + plot
    6. SHAP explanation
    7. Save model
    8. Return full results
    """
    charts_dir = os.path.join(client_path, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    # Auto detect target if not provided
    if not target_col:
        target_col = detect_target_column(df)

    # Detect problem type
    problem_info = detect_problem_type(df, target_col)
    problem_type = problem_info["type"]
    print(f"\n🎯 Problem type: {problem_type} (confidence: {problem_info['confidence']})")
    print(f"   Reason: {problem_info['reason']}")

    # Validate
    validation = validate_dataset(df)
    if not validation["passed"]:
        return {"error": " | ".join(validation["issues"]), "validation": validation}

    # Handle clustering separately
    if problem_type == "clustering":
        return run_clustering(df, client_path, charts_dir)

    if not target_col:
        return {"error": "No target column found and clustering not applicable."}

    # Prepare features
    X, y = prepare_features(df, target_col, problem_type)
    stratify = y if problem_type in ["binary_classification", "multiclass_classification"] else None

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
    except:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # AutoML — run all candidates
    print("\n🤖 Running AutoML comparison...")
    automl_result = run_automl(X_train, X_test, y_train, y_test, problem_type, charts_dir)
    best_model    = automl_result["best_model"]
    best_name     = automl_result["best_name"]

    if not best_model:
        return {"error": "All models failed to train. Check your data."}

    print(f"\n🏆 Best model: {best_name}")

    # Evaluate best model
    metrics = evaluate_and_plot(best_model, X_test, y_test, problem_type, charts_dir, X.columns.tolist())

    # SHAP
    shap_result = generate_shap_explanation(best_model, X_test, X.columns.tolist(), charts_dir, problem_type)

    # Save model
    save_model(best_model, client_path)

    # At-risk prediction
    at_risk_path = os.path.join(client_path, "at_risk.csv")
    predict_at_risk(best_model, X, df, at_risk_path, problem_type)

    # Save full results
    results = {
        "problem_type":   problem_type,
        "problem_reason": problem_info["reason"],
        "best_model":     best_name,
        "target_column":  target_col,
        "metrics":        metrics,
        "automl_comparison": automl_result["results"],
        "shap":           shap_result,
        "validation":     validation,
        "feature_count":  X.shape[1],
        "training_rows":  len(X_train),
        "test_rows":      len(X_test),
    }

    model_path = os.path.join(client_path, "model_metrics.json")
    with open(model_path, "w") as f:
        json.dump({k: v for k, v in results.items() if k not in ["automl_comparison", "shap", "validation"]}, f, indent=4)

    full_results_path = os.path.join(client_path, "model_full_results.json")
    with open(full_results_path, "w") as f:
        json.dump(results, f, indent=4, default=str)

    print(f"\n✅ Pipeline complete. Best: {best_name} | Metrics: {metrics}")
    return results


def run_clustering(df: pd.DataFrame, client_path: str, charts_dir: str) -> dict:
    """Run K-Means clustering for unsupervised datasets."""
    numeric_df = df.select_dtypes(include=["float64", "int64"]).dropna()
    if numeric_df.shape[1] < 2:
        return {"error": "Need at least 2 numeric columns for clustering."}

    # Find optimal k using silhouette score
    best_k, best_score, best_model = 2, -1, None
    for k in range(2, min(8, len(df) // 10)):
        try:
            km    = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(numeric_df)
            score  = silhouette_score(numeric_df, labels)
            if score > best_score:
                best_score = score; best_k = k; best_model = km
        except: pass

    labels = best_model.fit_predict(numeric_df)
    df_clustered = df.copy()
    df_clustered["cluster"] = labels

    # Cluster profile
    profile = df_clustered.groupby("cluster")[numeric_df.columns.tolist()].mean().round(2)

    # Plot
    cols = numeric_df.columns[:2].tolist()
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(numeric_df[cols[0]], numeric_df[cols[1]], c=labels, cmap="tab10", alpha=0.6, s=20)
    ax.set_title(f"K-Means Clustering (k={best_k})", fontsize=13, fontweight="600")
    ax.set_xlabel(cols[0]); ax.set_ylabel(cols[1])
    plt.colorbar(scatter, ax=ax, label="Cluster")
    ax.spines[['top','right']].set_visible(False); plt.tight_layout()
    plt.savefig(f"{charts_dir}/clusters.png", dpi=150, bbox_inches="tight"); plt.close()

    output_path = os.path.join(client_path, "clusters.csv")
    df_clustered.to_csv(output_path, index=False)

    metrics = {"n_clusters": best_k, "silhouette_score": round(best_score, 4)}
    with open(os.path.join(client_path, "model_metrics.json"), "w") as f:
        json.dump({"problem_type": "clustering", "best_model": "K-Means", "metrics": metrics}, f, indent=4)

    return {
        "problem_type": "clustering",
        "best_model":   "K-Means",
        "metrics":      metrics,
        "n_clusters":   best_k,
        "cluster_profile": profile.to_dict(),
    }
