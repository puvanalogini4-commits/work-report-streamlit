import streamlit as st
import pandas as pd
from datetime import date
import os
import hashlib

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Monthly Work Report", layout="centered")

DATA_DIR = "data"
USERS_FILE = "users.csv"

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- USER DB ----------------
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["username", "password"]).to_csv(USERS_FILE, index=False)

users_df = pd.read_csv(USERS_FILE)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = ""

# ---------------- LOGIN / SIGNUP ----------------
st.title("📘 Daily Work Report System")

if not st.session_state.user:
    tab1, tab2 = st.tabs(["Login", "Signup"])

    # ---------- LOGIN ----------
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            hashed = hash_password(password)
            match = users_df[
                (users_df["username"] == username) &
                (users_df["password"] == hashed)
            ]

            if not match.empty:
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    # ---------- SIGNUP ----------
    with tab2:
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")

        if st.button("Create Account"):
            if new_user in users_df["username"].values:
                st.error("Username already exists")
            elif not new_user or not new_pass:
                st.warning("Fill all fields")
            else:
                users_df.loc[len(users_df)] = [
                    new_user,
                    hash_password(new_pass)
                ]
                users_df.to_csv(USERS_FILE, index=False)
                os.makedirs(f"{DATA_DIR}/{new_user}", exist_ok=True)
                st.success("Account created. Please login.")

    st.stop()

# ---------------- MAIN APP ----------------
st.success(f"Logged in as **{st.session_state.user}**")

user_dir = f"{DATA_DIR}/{st.session_state.user}"
os.makedirs(user_dir, exist_ok=True)

# ---------------- DATA ENTRY ----------------
st.subheader("📝 Daily Entry")

with st.form("entry"):
    work_date = st.date_input("Date", date.today())
    school = st.text_input("School")
    work_done = st.text_area("Work Done")
    amendment = st.text_area("Amendment")
    distance = st.number_input("Distance (KM)", 0.0, step=0.1)
    save = st.form_submit_button("Save")

if save:
    month = work_date.strftime("%Y-%m")
    file_path = f"{user_dir}/{month}.csv"

    new_row = pd.DataFrame([{
        "Date": work_date.strftime("%Y-%m-%d"),
        "School": school,
        "Work Done": work_done,
        "Amendment": amendment,
        "Distance (KM)": distance
    }])

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        df = new_row

    df.to_csv(file_path, index=False)
    st.success(f"Saved to {month} report")

# ---------------- MONTHLY REPORTS ----------------
st.markdown("---")
st.subheader("📊 My Monthly Reports")

files = sorted(
    f.replace(".csv", "")
    for f in os.listdir(user_dir)
    if f.endswith(".csv")
)

if not files:
    st.info("No reports yet")
else:
    month = st.selectbox("Select Month", files)
    df = pd.read_csv(f"{user_dir}/{month}.csv")

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "📥 Download Spreadsheet",
        data=df.to_csv(index=False),
        file_name=f"{month}_work_report.csv",
        mime="text/csv"
    )

# ---------------- LOGOUT ----------------
st.markdown("---")
if st.button("Logout"):
    st.session_state.user = ""
    st.rerun()
