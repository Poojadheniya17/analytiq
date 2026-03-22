# pages/5_ask_ai.py
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth.auth import require_login
from core.nlp_engine import query as nlp_query

st.set_page_config(page_title="Analytiq · Ask AI", page_icon="◈", layout="wide")
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

st.markdown("<h1>Ask <em style='font-style:italic;color:#2563EB'>AI</em></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-family:DM Mono,monospace;font-size:11px;color:#9CA3AF;margin-top:-8px;margin-bottom:24px'>Plain English → SQL → Answer · {client['name']}</p>", unsafe_allow_html=True)

cleaned_path = f"{client_path}/cleaned_data.csv"
if not os.path.exists(cleaned_path):
    st.info("Please upload and clean your data first.")
    if st.button("Go to Upload"): st.switch_page("pages/2_upload.py")
    st.stop()

st.markdown("### Example Questions")
examples = [
    "What is the overall churn rate?",
    "Which category has the highest risk rate?",
    "What is the average monthly value for high vs low risk records?",
    "How many records have been active for more than 24 months?",
]
cols = st.columns(2)
for i, q in enumerate(examples):
    if cols[i % 2].button(q, key=f"ex_{i}"):
        st.session_state["nlp_q"] = q

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Your Question")
question = st.text_input(
    "Type any business question about your data:",
    value=st.session_state.get("nlp_q", ""),
    placeholder="e.g. Which segment has the most at-risk customers?"
)


if st.button("Run Query") and question:
    with st.spinner("Thinking..."):
        result = nlp_query(question, cleaned_path)
        st.session_state["nlp_result"] = result

# Always show result if it exists
if "nlp_result" in st.session_state and st.session_state["nlp_result"]:
    result = st.session_state["nlp_result"]
    if result["error"]:
        st.error(f"Query failed: {result['error']}")
    else:
        st.markdown("### Generated SQL")
        st.code(result["sql"], language="sql")
        st.markdown("### Query Results")
        st.dataframe(result["results"], width='stretch')
        st.markdown("<div style='background:#EFF6FF;border-left:3px solid #2563EB;padding:16px 20px;border-radius:0 8px 8px 0;margin-top:12px'><div style='font-family:DM Mono,monospace;font-size:9px;color:#2563EB;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px'>AI Answer</div><div style='font-size:14px;line-height:1.7'>" + result['answer'] + "</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
if st.button("Continue to Narrative →"):
    st.switch_page("pages/6_narrative.py")
