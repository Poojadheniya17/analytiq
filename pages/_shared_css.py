import streamlit as st

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;1,300&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.main .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }

h1 { font-family: 'Fraunces', serif !important; font-weight: 300 !important; font-size: 28px !important; letter-spacing: -0.5px !important; }
h2 { font-family: 'Fraunces', serif !important; font-weight: 300 !important; font-size: 20px !important; }
h3 { font-family: 'DM Mono', monospace !important; font-size: 10px !important; color: #9CA3AF !important; letter-spacing: 1.2px !important; text-transform: uppercase !important; font-weight: 400 !important; }

section[data-testid="stSidebar"] { border-right: 1px solid #E2E8F0 !important; }
section[data-testid="stSidebar"] .stButton > button { background: transparent !important; color: #6B7280 !important; border: none !important; text-align: left !important; font-size: 13px !important; padding: 6px 10px !important; width: 100% !important; border-radius: 6px !important; box-shadow: none !important; }
section[data-testid="stSidebar"] .stButton > button:hover { background: #F7F8FA !important; color: #0F1117 !important; }

[data-testid="metric-container"] { border: 1px solid #E2E8F0 !important; border-radius: 10px !important; padding: 16px !important; }
[data-testid="metric-container"] label { font-family: 'DM Mono', monospace !important; font-size: 10px !important; letter-spacing: 0.8px !important; text-transform: uppercase !important; color: #9CA3AF !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-family: 'Fraunces', serif !important; font-size: 28px !important; font-weight: 600 !important; }

.stButton > button { border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; padding: 8px 20px !important; }

.stTextInput input { border-radius: 8px !important; font-size: 13px !important; }
.stSelectbox [data-baseweb="select"] { border-radius: 8px !important; }

.stTabs [data-baseweb="tab"] { font-family: 'DM Mono', monospace !important; font-size: 10px !important; letter-spacing: 0.8px !important; text-transform: uppercase !important; padding: 12px 20px !important; }

[data-testid="stDataFrame"] { border-radius: 10px !important; }
hr { border-color: #E2E8F0 !important; }
code { border-radius: 4px !important; font-family: 'DM Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)
