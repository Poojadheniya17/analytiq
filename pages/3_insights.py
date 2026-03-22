# pages/3_insights.py
import streamlit as st
import pandas as pd
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth.auth import require_login
from core.insights import (detect_target_column, generate_kpis, detect_anomalies,
                            generate_segment_insights, plot_insights, save_insights)

st.set_page_config(page_title="Analytiq · Insights", page_icon="◈", layout="wide")
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

st.markdown("<h1>Business <em style='font-style:italic;color:#2563EB'>Insights</em></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-family:DM Mono,monospace;font-size:11px;color:#9CA3AF;margin-top:-8px;margin-bottom:24px'>Auto-generated analysis · {client['name']} · {client['domain']}</p>", unsafe_allow_html=True)

cleaned_path = f"{client_path}/cleaned_data.csv"
if not os.path.exists(cleaned_path):
    st.info("No data found. Please upload a dataset first.")
    if st.button("Go to Upload"): st.switch_page("pages/2_upload.py")
    st.stop()

df = pd.read_csv(cleaned_path)

if st.button("Generate Insights"):
    with st.spinner("Analyzing your data..."):
        charts_dir = f"{client_path}/charts"
        target_col = detect_target_column(df)
        kpis       = generate_kpis(df, target_col)
        anomalies  = detect_anomalies(df)
        segments   = generate_segment_insights(df, target_col)
        plot_insights(df, target_col, charts_dir)
        save_insights(kpis, anomalies, segments, f"{client_path}/insights.json")
    st.success("Insights generated successfully.")
    st.rerun()

insights_path = f"{client_path}/insights.json"
if os.path.exists(insights_path):
    with open(insights_path) as f:
        ins = json.load(f)

    st.markdown("### Key Performance Indicators")
    kpi_items = list(ins["kpis"].items())
    cols = st.columns(min(4, len(kpi_items)))
    for i, (k, v) in enumerate(kpi_items):
        cols[i % 4].metric(k.replace("_", " ").upper(), f"{v:,}" if isinstance(v, (int, float)) else v)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Anomaly Detection")
    if ins["anomalies"]:
        st.dataframe(pd.DataFrame(ins["anomalies"]), width='stretch')
    else:
        st.success("No significant anomalies detected.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Segment Breakdown")
    for seg in ins["segment_insights"]:
        with st.expander(f"{seg['segment'].replace('_',' ').upper()}  ·  Highest: {seg['highest_churn_value']} ({seg['highest_churn_rate_%']}%)"):
            st.dataframe(pd.DataFrame(seg["full_breakdown"]), width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Visual Insights")
    charts_dir = f"{client_path}/charts"
    if os.path.exists(charts_dir):
        charts = [f for f in os.listdir(charts_dir) if f.endswith(".png")]
        cols   = st.columns(2)
        for i, c in enumerate(charts):
            cols[i % 2].image(f"{charts_dir}/{c}", width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Continue to ML Model →"):
        st.switch_page("pages/4_model.py")
else:
    st.info("Click 'Generate Insights' to analyse this client's data.")
