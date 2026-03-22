# pages/4_model.py
import streamlit as st
import pandas as pd
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth.auth import require_login
from core.ml_model import (prepare_features, train_model, evaluate_model,
                            plot_feature_importance, predict_at_risk)
from core.insights import detect_target_column
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="Analytiq · Model", page_icon="◈", layout="wide")
exec(open(os.path.join(os.path.dirname(__file__), "_shared_css.py")).read())

user = require_login()

if "active_client" not in st.session_state:
    st.switch_page("pages/1_workspace.py")
    st.stop()

client      = st.session_state.active_client
client_path = st.session_state.active_client_path

with st.sidebar:
    st.markdown("<div style='padding:8px 0 16px'><div style='font-family:Fraunces,serif;font-size:20px;font-weight:600'>Analytiq</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#9CA3AF;line-height:2;margin-bottom:12px'>CLIENT<br><span style='font-size:13px;font-family:DM Sans,sans-serif;font-weight:500'>{client['name']}</span></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("◈  Workspace"):      st.switch_page("pages/1_workspace.py")
    if st.button("↗  Upload & Clean"): st.switch_page("pages/2_upload.py")
    if st.button("◎  Insights"):       st.switch_page("pages/3_insights.py")
    if st.button("⬡  ML Model"):       st.switch_page("pages/4_model.py")
    if st.button("◌  Ask AI"):         st.switch_page("pages/5_ask_ai.py")
    if st.button("◻  Narrative"):      st.switch_page("pages/6_narrative.py")
    if st.button("↓  Export"):         st.switch_page("pages/7_export.py")
    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear(); st.switch_page("app.py")

st.markdown("<h1>ML <em style='font-style:italic;color:#2563EB'>Prediction Model</em></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-family:DM Mono,monospace;font-size:11px;color:#9CA3AF;margin-top:-8px;margin-bottom:24px'>XGBoost classifier · {client['name']} · {client['domain']}</p>", unsafe_allow_html=True)

cleaned_path = f"{client_path}/cleaned_data.csv"
if not os.path.exists(cleaned_path):
    st.info("Please upload and clean your data first.")
    if st.button("Go to Upload"): st.switch_page("pages/2_upload.py")
    st.stop()

df         = pd.read_csv(cleaned_path)
target_col = detect_target_column(df)

if not target_col:
    st.warning("Could not auto-detect a target column.")
    target_col = st.selectbox("Select your target column:", df.columns.tolist())
else:
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:11px;color:#6B7280;margin-bottom:16px;padding:10px 14px;background:#F7F8FA;border:1px solid #E2E8F0;border-radius:8px'>Target column detected · <span style='color:#2563EB;font-weight:500'>{target_col}</span></div>", unsafe_allow_html=True)

if st.button("Train XGBoost Model"):
    with st.spinner("Training model — this takes about 30 seconds..."):
        X, y = prepare_features(df, target_col)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        model      = train_model(Xtr, ytr)
        charts_dir = f"{client_path}/charts"
        metrics    = evaluate_model(model, Xte, yte, charts_dir)
        plot_feature_importance(model, X.columns.tolist(), charts_dir)
        predict_at_risk(model, X, df, f"{client_path}/at_risk.csv")
        with open(f"{client_path}/model_metrics.json", "w") as f:
            json.dump(metrics, f, indent=4)
    st.success("Model trained successfully.")
    st.rerun()

metrics_path = f"{client_path}/model_metrics.json"
if os.path.exists(metrics_path):
    with open(metrics_path) as f:
        m = json.load(f)

    st.markdown("### Model Performance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AUC-ROC",   m["auc_roc"])
    c2.metric("Precision", m["precision"])
    c3.metric("Recall",    m["recall"])
    c4.metric("F1-Score",  m["f1_score"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Performance Charts")
    charts_dir = f"{client_path}/charts"
    cols = st.columns(2)
    for i, chart in enumerate(["roc_curve.png", "confusion_matrix.png", "feature_importance.png"]):
        path = f"{charts_dir}/{chart}"
        if os.path.exists(path):
            cols[i % 2].image(path, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Top At-Risk Records")
    at_risk_path = f"{client_path}/at_risk.csv"
    if os.path.exists(at_risk_path):
        st.dataframe(pd.read_csv(at_risk_path).head(10), width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Continue to Ask AI →"):
        st.switch_page("pages/5_ask_ai.py")
else:
    st.info("Click 'Train XGBoost Model' to build your prediction model.")
