import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Daily Work Report",
    layout="centered"
)

# --------------------------------------------------
# GOOGLE SERVICE ACCOUNT AUTH
# --------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

client = gspread.authorize(creds)

# --------------------------------------------------
# OPEN YOUR GOOGLE SHEET
# --------------------------------------------------
# 🔴 CHANGE THIS to your actual Google Sheet NAME
SHEET_NAME = "Work Report Master"

sheet = client.open(SHEET_NAME)

# --------------------------------------------------
# SIMPLE LOGIN (USERNAME ONLY)
# --------------------------------------------------
if "username" not in st.session_state:
    st.session_state.username = ""

st.title("📘 Daily Work Report System")

if not st.session_state.username:
    st.subheader("🔐 Login")
    username = st.text_input("Enter your name / username")

    if st.button("Login"):
        if username.strip():
            st.session_state.username = username.strip()
            st.rerun()
        else:
            st.warning("Please enter your name")

    st.stop()

st.success(f"Logged in as **{st.session_state.username}**")

# --------------------------------------------------
# DATA ENTRY FORM
# --------------------------------------------------
st.subheader("📝 Daily Work Entry")

with st.form("entry_form"):
    work_date = st.date_input("Date", date.today())
    school = st.text_input("School")
    work_done = st.text_area("Work Done")
    amendment = st.text_area("Amendment (if any)")
    distance = st.number_input(
        "Distance from Zonal Office (KM)",
        min_value=0.0,
        step=0.1
    )

    save = st.form_submit_button("💾 Save")

if save:
    month_tab = work_date.strftime("%Y-%m")

    # Get or create month worksheet
    try:
        ws = sheet.worksheet(month_tab)
    except:
        ws = sheet.add_worksheet(
            title=month_tab,
            rows=1000,
            cols=10
        )
        ws.append_row([
            "Date",
            "Username",
            "School",
            "Work Done",
            "Amendment",
            "Distance (KM)"
        ])

    # Append data row
    ws.append_row([
        work_date.strftime("%Y-%m-%d"),
        st.session_state.username,
        school,
        work_done,
        amendment,
        distance
    ])

    st.success("✅ Record added successfully")

# --------------------------------------------------
# MONTH PREVIEW (READ ONLY)
# --------------------------------------------------
st.markdown("---")
st.subheader("📊 This Month Preview")

current_month = date.today().strftime("%Y-%m")

try:
    ws = sheet.worksheet(current_month)
    data = ws.get_all_records()

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records yet for this month")

except:
    st.info("No sheet found for this month yet")

# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.username = ""
    st.rerun()
