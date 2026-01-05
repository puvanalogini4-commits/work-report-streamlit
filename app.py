import streamlit as st
import pandas as pd
import requests
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Daily Work Report", layout="centered")

# ---------------- CONFIG ----------------
# 🔴 PASTE YOUR GOOGLE APPS SCRIPT WEB APP URL HERE
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzgB9ZsV8udVEFjc0c6CtdI6kLkZ8LO4BDkd9iLHAdZE6WmSVXSKLAuKR1GzMQ5T1woKQ/exec"
# ---------------- LOGIN ----------------
if "username" not in st.session_state:
    st.session_state.username = ""

st.title("📘 Daily Work Report System")

if not st.session_state.username:
    st.subheader("🔐 Login")
    name = st.text_input("Enter your name / username")

    if st.button("Login"):
        if name.strip():
            st.session_state.username = name.strip()
            st.rerun()
        else:
            st.warning("Please enter your name")

    st.stop()

st.success(f"Logged in as **{st.session_state.username}**")

# ---------------- DATA ENTRY ----------------
st.subheader("📝 Daily Work Entry")

with st.form("entry_form"):
    work_date = st.date_input("Date", date.today())
    school = st.text_input("School")
    work_done = st.text_area("Work Done")
    amendment = st.text_area("Amendment (if any)")
    distance = st.number_input("Distance (KM)", 0.0, step=0.1)
    save = st.form_submit_button("💾 Save")

if save:
    payload = {
        "date": work_date.strftime("%Y-%m-%d"),
        "month": work_date.strftime("%Y-%m"),
        "username": st.session_state.username,
        "school": school,
        "work_done": work_done,
        "amendment": amendment,
        "distance": distance
    }

    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 200:
            st.success("✅ Data saved to Google Sheet")
        else:
            st.error("❌ Failed to save data")
    except Exception as e:
        st.error("❌ Connection error")

# ---------------- LOGOUT ----------------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.username = ""
    st.rerun()

