# pages/6_narrative.py
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth.auth import require_login
from core.narrative import generate_narrative

st.set_page_config(page_title="Analytiq · Narrative", page_icon="◈", layout="wide")
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

st.markdown("<h1>Executive <em style='font-style:italic;color:#2563EB'>Narrative</em></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-family:DM Mono,monospace;font-size:11px;color:#9CA3AF;margin-top:-8px;margin-bottom:24px'>AI-written consultant report · {client['name']}</p>", unsafe_allow_html=True)

insights_path  = f"{client_path}/insights.json"
metrics_path   = f"{client_path}/model_metrics.json"
narrative_path = f"{client_path}/narrative.txt"

if not os.path.exists(insights_path):
    st.info("Please run the Insights analysis first.")
    if st.button("Go to Insights"): st.switch_page("pages/3_insights.py")
    st.stop()

if os.path.exists(narrative_path):
    with open(narrative_path) as f:
        saved = f.read()

    st.markdown("<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:32px 36px;margin-bottom:20px'><div style='font-family:DM Mono,monospace;font-size:10px;color:#9CA3AF;letter-spacing:1px;text-transform:uppercase;margin-bottom:20px'>Executive Summary · " + client['name'] + " · " + client['domain'] + "</div><div style='font-size:15px;line-height:1.9;white-space:pre-wrap'>" + saved + "</div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Regenerate Narrative"):
            os.remove(narrative_path)
            st.rerun()
    with col2:
        if st.button("Continue to Export →"):
            st.switch_page("pages/7_export.py")
else:
    st.markdown("<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:16px 20px;margin-bottom:20px;font-family:DM Mono,monospace;font-size:11px;color:#1E40AF'>The AI will write a 4-5 paragraph executive summary in the style of a senior consultant — with specific numbers, segment insights, and actionable recommendations.</div>", unsafe_allow_html=True)

    if st.button("Generate Executive Narrative"):
        with st.spinner("Writing consultant report..."):
            narrative = generate_narrative(
                insights_path = insights_path,
                metrics_path  = metrics_path if os.path.exists(metrics_path) else None,
                client_name   = client["name"],
                domain        = client["domain"]
            )
            with open(narrative_path, "w") as f:
                f.write(narrative)
        st.rerun()
