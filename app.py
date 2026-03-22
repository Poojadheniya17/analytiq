# ============================================================
# app.py
# Analytiq — Main Entry Point with Login / Signup
# ============================================================

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth.auth import init_db, login, signup

st.set_page_config(
    page_title="Analytiq",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Init database ─────────────────────────────────────────────
init_db()

# ── Light Theme CSS ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #F7F8FA !important;
    color: #0F1117 !important;
}
.main .block-container {
    background: #F7F8FA !important;
    max-width: 480px !important;
    padding: 3rem 2rem !important;
}
h1 { font-family: 'Fraunces', serif !important; font-weight: 600 !important; font-size: 32px !important; color: #0F1117 !important; letter-spacing: -0.8px !important; }
h3 { font-family: 'DM Mono', monospace !important; font-size: 11px !important; color: #6B7280 !important; letter-spacing: 1px !important; text-transform: uppercase !important; font-weight: 400 !important; }
p  { color: #6B7280 !important; font-size: 14px !important; }

.stTextInput input {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    color: #0F1117 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}
.stTextInput input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
.stTextInput label {
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    color: #6B7280 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}
.stButton > button {
    background: #0F1117 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 10px 24px !important;
    width: 100% !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #E2E8F0 !important;
    gap: 0 !important;
    margin-bottom: 24px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7280 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #0F1117 !important;
    border-bottom: 2px solid #2563EB !important;
}
.stSuccess { background: rgba(16,185,129,0.08) !important; border: 1px solid rgba(16,185,129,0.2) !important; color: #065F46 !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 12px !important; }
.stError   { background: rgba(239,68,68,0.08)  !important; border: 1px solid rgba(239,68,68,0.2)  !important; color: #991B1B !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 12px !important; }
.stInfo    { background: rgba(37,99,235,0.06)   !important; border: 1px solid rgba(37,99,235,0.15) !important; color: #1E40AF !important; border-radius: 8px !important; font-family: 'DM Mono', monospace !important; font-size: 12px !important; }
section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Already logged in → redirect ─────────────────────────────
if "user" in st.session_state and st.session_state.user:
    st.switch_page("pages/1_workspace.py")

# ── Logo ──────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 2rem 0 1.5rem'>
    <div style='font-family:Fraunces,serif; font-size:42px; font-weight:600; color:#0F1117; letter-spacing:-1px'>Analytiq</div>
    <div style='font-family:DM Mono,monospace; font-size:11px; color:#9CA3AF; letter-spacing:1.5px; margin-top:6px'>AI-POWERED ANALYTICS PLATFORM</div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Sign In", "Create Account"])

# ── LOGIN ─────────────────────────────────────────────────────
with tab1:
    username_in = st.text_input("Username", key="login_user", placeholder="yourname")
    password_in = st.text_input("Password", key="login_pass", placeholder="••••••••", type="password")

    stay = st.checkbox("Stay signed in on this device", value=True)

    if st.button("Sign In", key="btn_login"):
        if not username_in or not password_in:
            st.error("Please fill in all fields.")
        else:
            success, msg, user_data = login(username_in, password_in)
            if success:
                st.session_state.user       = user_data
                st.session_state.stay_login = stay
                st.success(f"Welcome back, {user_data['username'].title()}!")
                st.switch_page("pages/1_workspace.py")
            else:
                st.error(msg)

# ── SIGNUP ────────────────────────────────────────────────────
with tab2:
    new_user  = st.text_input("Username",  key="su_user",  placeholder="yourname")
    new_email = st.text_input("Email",     key="su_email", placeholder="you@company.com")
    new_pass  = st.text_input("Password",  key="su_pass",  placeholder="Min. 6 characters", type="password")
    new_pass2 = st.text_input("Confirm Password", key="su_pass2", placeholder="Repeat password", type="password")

    if st.button("Create Account", key="btn_signup"):
        if not all([new_user, new_email, new_pass, new_pass2]):
            st.error("Please fill in all fields.")
        elif new_pass != new_pass2:
            st.error("Passwords do not match.")
        else:
            success, msg = signup(new_user, new_email, new_pass)
            if success:
                st.success(msg + " Please sign in.")
            else:
                st.error(msg)

# ── Footer ────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; margin-top:3rem; font-family:DM Mono,monospace; font-size:10px; color:#D1D5DB'>
    Analytiq · Built for Bold Analytics
</div>
""", unsafe_allow_html=True)
