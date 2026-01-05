import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from io import BytesIO

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Monthly Work Report", layout="centered")

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    report_date TEXT,
    school TEXT,
    work_done TEXT,
    amendment TEXT,
    distance REAL
)
""")
conn.commit()

# Create default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute(
        "INSERT INTO users VALUES (?,?,?)",
        ("admin", "admin123", "admin")
    )
    conn.commit()

# --------------------------------------------------
# SESSION
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --------------------------------------------------
# LOGIN / SIGNUP
# --------------------------------------------------
if not st.session_state.logged_in:
    st.title("🔐 Work Report System")

    login_tab, signup_tab = st.tabs(["Login", "Signup"])

    # LOGIN
    with login_tab:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute(
                "SELECT role FROM users WHERE username=? AND password=?",
                (u, p)
            )
            r = c.fetchone()

            if r:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = r[0]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid login")

    # SIGNUP
    with signup_tab:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            if nu and np:
                try:
                    c.execute(
                        "INSERT INTO users VALUES (?,?,?)",
                        (nu, np, "user")
                    )
                    conn.commit()
                    st.success("Account created. Please login.")
                except:
                    st.error("Username already exists")
            else:
                st.warning("Fill all fields")

    st.stop()

# --------------------------------------------------
# MAIN
# --------------------------------------------------
st.title("📘 Monthly Work Report")
st.success(f"Logged in as {st.session_state.username}")

# --------------------------------------------------
# DATA ENTRY
# --------------------------------------------------
st.subheader("📝 Daily Entry")

with st.form("entry"):
    d = st.date_input("Date", date.today())
    school = st.text_input("School")
    work = st.text_area("Work Done")
    amend = st.text_area("Amendment")
    dist = st.number_input("Distance (KM)", 0.0, step=0.1)
    save = st.form_submit_button("Save")

if save:
    c.execute("""
    INSERT INTO reports
    (username, report_date, school, work_done, amendment, distance)
    VALUES (?,?,?,?,?,?)
    """, (
        st.session_state.username,
        d.strftime("%Y-%m-%d"),
        school,
        work,
        amend,
        dist
    ))
    conn.commit()
    st.success("Record saved")

# --------------------------------------------------
# MONTHLY REPORT
# --------------------------------------------------
st.markdown("---")
st.subheader("📊 Monthly Report")

if st.session_state.role == "admin":
    df = pd.read_sql("SELECT * FROM reports", conn)
else:
    df = pd.read_sql(
        "SELECT * FROM reports WHERE username=?",
        conn,
        params=(st.session_state.username,)
    )

if df.empty:
    st.info("No data found")
else:
    df["report_date"] = pd.to_datetime(df["report_date"])
    df["month"] = df["report_date"].dt.strftime("%Y-%m")

    month = st.selectbox("Select Month", sorted(df["month"].unique()))
    month_df = df[df["month"] == month].drop(columns=["month"])

    st.dataframe(month_df)

    # --------------------------------------------------
    # EXCEL DOWNLOAD (100% CLOUD SAFE)
    # --------------------------------------------------
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        month_df.to_excel(writer, index=False, sheet_name="Report")

    buffer.seek(0)

    st.download_button(
        "📥 Download Monthly Excel",
        data=buffer,
        file_name=f"{st.session_state.username}_{month}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
st.markdown("---")
if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
