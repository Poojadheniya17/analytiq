# pages/1_workspace.py
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth.auth import require_login, get_clients, add_client, delete_client

st.set_page_config(page_title="Analytiq · Workspace", page_icon="◈", layout="wide")
exec(open(os.path.join(os.path.dirname(__file__), "_shared_css.py")).read())

user = require_login()

with st.sidebar:
    st.markdown(f"""<div style='padding:8px 0 16px'><div style='font-family:Fraunces,serif;font-size:20px;font-weight:600;color:#0F1117'>Analytiq</div><div style='font-family:DM Mono,monospace;font-size:10px;color:#9CA3AF;letter-spacing:1px;margin-top:3px'>AI ANALYTICS PLATFORM</div></div><div style='font-family:DM Mono,monospace;font-size:11px;color:#6B7280;line-height:1.8;margin-bottom:16px'>Signed in as<br><span style='color:#0F1117;font-weight:500'>{user['username'].title()}</span></div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("### Navigation")
    if st.button("◈  Workspace"):      st.switch_page("pages/1_workspace.py")
    if st.button("↗  Upload & Clean"): st.switch_page("pages/2_upload.py")
    if st.button("◎  Insights"):       st.switch_page("pages/3_insights.py")
    if st.button("⬡  ML Model"):       st.switch_page("pages/4_model.py")
    if st.button("◌  Ask AI"):         st.switch_page("pages/5_ask_ai.py")
    if st.button("◻  Narrative"):      st.switch_page("pages/6_narrative.py")
    if st.button("↓  Export"):         st.switch_page("pages/7_export.py")
    st.divider()
    if st.button("Sign Out"):
        st.session_state.clear()
        st.switch_page("app.py")

st.markdown(f"<h1>Good to see you, <em style='font-style:italic;color:#2563EB'>{user['username'].title()}</em></h1>", unsafe_allow_html=True)
st.markdown("<p style='font-family:DM Mono,monospace;font-size:11px;color:#9CA3AF;margin-top:-8px;margin-bottom:24px'>Manage your client workspaces · Each client has isolated data and analyses</p>", unsafe_allow_html=True)

clients = get_clients(user["id"])

col1, col2, col3 = st.columns(3)
col1.metric("Total Clients", len(clients))
col2.metric("Active Analyses", len([c for c in clients if os.path.exists(f"data/users/{user['id']}/{c['name'].lower().replace(' ','_')}/cleaned_data.csv")]))
col3.metric("Account", user["username"].title())

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Add New Client")

with st.expander("+ New Client Workspace", expanded=len(clients) == 0):
    c1, c2 = st.columns(2)
    client_name   = c1.text_input("Client Name", placeholder="e.g. Acme Corp")
    client_domain = c2.selectbox("Industry Domain", [
        "Retail / E-commerce", "Telecom", "Healthcare", "Finance / Fintech",
        "Manufacturing", "HR / People Analytics", "Real Estate", "Other"
    ])
    if st.button("Create Workspace"):
        if not client_name:
            st.error("Please enter a client name.")
        else:
            success, msg = add_client(user["id"], client_name, client_domain)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

st.divider()
st.markdown("### Your Clients")

if not clients:
    st.info("No clients yet — create your first workspace above.")
else:
    for client in clients:
        safe_name   = client["name"].lower().replace(" ", "_")
        client_path = f"data/users/{user['id']}/{safe_name}"
        has_data    = os.path.exists(f"{client_path}/cleaned_data.csv")
        has_model   = os.path.exists(f"{client_path}/model_metrics.json")

        data_badge  = "<span style='background:#DCFCE7;color:#166534;font-size:10px;padding:3px 10px;border-radius:20px;font-family:DM Mono,monospace'>Data loaded</span>" if has_data else "<span style='background:#F1F5F9;color:#9CA3AF;font-size:10px;padding:3px 10px;border-radius:20px;font-family:DM Mono,monospace'>No data</span>"
        model_badge = "<span style='background:#DBEAFE;color:#1E40AF;font-size:10px;padding:3px 10px;border-radius:20px;font-family:DM Mono,monospace'>Model ready</span>" if has_model else ""

        st.markdown(f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;padding:16px 20px;margin-bottom:4px'><div style='display:flex;align-items:center;justify-content:space-between'><div><div style='font-size:15px;font-weight:500;color:#0F1117'>{client['name']}</div><div style='font-family:DM Mono,monospace;font-size:10px;color:#9CA3AF;margin-top:3px'>{client['domain']} · Created {client['created'][:10]}</div></div><div style='display:flex;gap:8px;align-items:center'>{data_badge} {model_badge}</div></div></div>", unsafe_allow_html=True)

        bc1, bc2, bc3 = st.columns([2, 2, 1])
        if bc1.button("Open Workspace →", key=f"open_{client['id']}"):
            st.session_state.active_client      = client
            st.session_state.active_client_path = client_path
            st.switch_page("pages/2_upload.py")
        if bc3.button("Delete", key=f"del_{client['id']}"):
            delete_client(client["id"], user["id"])
            st.rerun()
