
import streamlit as st
from pages import overview, data_table, settings

st.set_page_config(page_title="Fleet Dashboard", layout="wide")

# Simple login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

def login_box():
    st.title("🔐 Fleet Dashboard Login")
    col1, col2 = st.columns([2,1])
    with col1:
        username = st.text_input("Username")
    with col2:
        password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "adminpass":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.experimental_rerun()
        elif username == "viewer" and password == "viewonly":
            st.session_state.logged_in = True
            st.session_state.role = "viewer"
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login_box()
    st.stop()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Data Table", "Settings"])

if page == "Overview":
    overview.render()
elif page == "Data Table":
    data_table.render()
elif page == "Settings":
    settings.render()
