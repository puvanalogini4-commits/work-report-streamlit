import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import date

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Monthly Work Report", layout="centered")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

USERS_URL = f"{SUPABASE_URL}/rest/v1/users"
REPORTS_URL = f"{SUPABASE_URL}/rest/v1/work_reports"

# ---------------- HELPERS ----------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN / SIGNUP ----------------
st.title("📘 Daily Work Report System")

if not st.session_state.user:
    tab_login, tab_signup = st.tabs(["Login", "Signup"])

    # ---------- LOGIN ----------
    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not username or not password:
                st.warning("Enter username and password")
            else:
                params = {
                    "username": f"eq.{username}",
                    "select": "*"
                }
                r = requests.get(USERS_URL, headers=HEADERS, params=params)

                if r.status_code == 200 and r.json():
                    user = r.json()[0]
                    if user["password_hash"] == hash_password(password):
                        st.session_state.user = username
                        st.success("Login successful")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Invalid username or password")

    # ---------- SIGNUP ----------
    with tab_signup:
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")

        if st.button("Create Account"):
            if not new_user or not new_pass:
                st.warning("Fill all fields")
            else:
                payload = {
                    "username": new_user,
                    "password_hash": hash_password(new_pass)
                }
                r = requests.post(USERS_URL, headers=HEADERS, json=payload)

                if r.status_code in (200, 201):
                    st.success("Account created. Please login.")
                else:
                    st.error("Username already exists")

    st.stop()

# ---------------- MAIN APP ----------------
st.success(f"Logged in as **{st.session_state.user}**")

# ---------------- DATA ENTRY ----------------
st.subheader("📝 Daily Entry")

with st.form("entry_form"):
    work_date = st.date_input("Date", date.today())
    school = st.text_input("School")
    work_done = st.text_area("Work Done")
    amendment = st.text_area("Amendment")
    distance = st.number_input("Distance (KM)", 0.0, step=0.1)
    save = st.form_submit_button("Save")

if save:
    payload = {
        "username": st.session_state.user,
        "work_date": str(work_date),
        "month": work_date.strftime("%Y-%m"),
        "school": school,
        "work_done": work_done,
        "amendment": amendment,
        "distance": distance
    }

    r = requests.post(REPORTS_URL, headers=HEADERS, json=payload)

    if r.status_code in (200, 201):
        st.success("✅ Data saved online")
    else:
        st.error("❌ Failed to save data")

# ---------------- MONTHLY REPORT ----------------
st.markdown("---")
st.subheader("📊 My Monthly Reports")

params = {
    "username": f"eq.{st.session_state.user}",
    "select": "*"
}

r = requests.get(REPORTS_URL, headers=HEADERS, params=params)

if r.status_code == 200 and r.json():
    df = pd.DataFrame(r.json())
    df["work_date"] = pd.to_datetime(df["work_date"])
    months = sorted(df["month"].unique())

    month = st.selectbox("Select Month", months)
    month_df = df[df["month"] == month]

    st.dataframe(month_df, use_container_width=True)

    st.download_button(
        "📥 Download Spreadsheet",
        data=month_df.to_csv(index=False),
        file_name=f"{month}_work_report.csv",
        mime="text/csv"
    )
else:
    st.info("No records found")

# ---------------- LOGOUT ----------------
st.markdown("---")
if st.button("Logout"):
    st.session_state.user = None
    st.rerun()
