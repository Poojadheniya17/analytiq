# pages/2_upload.py
import streamlit as st
import pandas as pd
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth.auth import require_login
from core.pipeline import clean_data, profile_data, save_cleaned_data, save_profile

st.set_page_config(page_title="Analytiq · Upload", page_icon="◈", layout="wide")
exec(open(os.path.join(os.path.dirname(__file__), "_shared_css.py")).read())

user = require_login()

if "active_client" not in st.session_state:
    st.switch_page("pages/1_workspace.py")
    st.stop()

client      = st.session_state.active_client
client_path = st.session_state.active_client_path
os.makedirs(client_path, exist_ok=True)

with st.sidebar:
    st.markdown("<div style='padding:8px 0 16px'><div style='font-family:Fraunces,serif;font-size:20px;font-weight:600'>Analytiq</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#9CA3AF;line-height:2;margin-bottom:12px'>CLIENT<br><span style='font-size:13px;font-family:DM Sans,sans-serif;font-weight:500'>{client['name']}</span><br><span style='color:#6B7280'>{client['domain']}</span></div>", unsafe_allow_html=True)
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

st.markdown("<h1>Upload & <em style='font-style:italic;color:#2563EB'>Clean</em></h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-family:DM Mono,monospace;font-size:11px;color:#9CA3AF;margin-top:-8px;margin-bottom:24px'>Client · {client['name']} · {client['domain']}</p>", unsafe_allow_html=True)

st.markdown("### Upload Dataset")
uploaded = st.file_uploader("Drop any CSV file — works with any domain or industry", type=["csv"])

if uploaded:
    raw_path = f"{client_path}/raw_data.csv"
    with open(raw_path, "wb") as f:
        f.write(uploaded.read())

    df_raw = pd.read_csv(raw_path)
    st.markdown("### Raw Data Preview")
    st.dataframe(df_raw.head(10), width='stretch')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows",           f"{df_raw.shape[0]:,}")
    c2.metric("Columns",        df_raw.shape[1])
    c3.metric("Missing Values", int(df_raw.isnull().sum().sum()))
    c4.metric("Duplicates",     int(df_raw.duplicated().sum()))

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Run Cleaning Pipeline"):
        with st.spinner("Cleaning data..."):
            df_cleaned = clean_data(df_raw)
            profile    = profile_data(df_cleaned)
            save_cleaned_data(df_cleaned, f"{client_path}/cleaned_data.csv")
            save_profile(profile, f"{client_path}/data_profile.json")
        st.success("Data cleaned and saved to your client workspace.")
        st.markdown("### Cleaned Preview")
        st.dataframe(df_cleaned.head(10), width='stretch')
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Numeric Summary")
            st.json(profile["numeric_summary"])
        with c2:
            st.markdown("### Categorical Summary")
            st.json(profile["categorical_summary"])
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Continue to Insights →"):
            st.switch_page("pages/3_insights.py")

elif os.path.exists(f"{client_path}/cleaned_data.csv"):
    st.info("This client already has a dataset loaded.")
    df = pd.read_csv(f"{client_path}/cleaned_data.csv")
    st.dataframe(df.head(10), width='stretch')
    c1, c2 = st.columns(2)
    c1.metric("Rows",    f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Replace with New Dataset"):
            os.remove(f"{client_path}/cleaned_data.csv")
            st.rerun()
    with col2:
        if st.button("Continue to Insights →"):
            st.switch_page("pages/3_insights.py")
