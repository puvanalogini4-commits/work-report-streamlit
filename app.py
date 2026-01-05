import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Daily Work Report", layout="centered")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Reports table
c.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    report_date DATE,
    school TEXT,
    work_done TEXT,
    amendment TEXT,
    distance REAL
)
""")
conn.commit()

# Default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute(
        "INSERT INTO users VALUES (?,?,?)",
        ("admin", "admin123", "admin")
    )
    conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN / SIGNUP ----------------
if not st.session_state.logged_in:
    st.title("🔐 Daily Work Report System")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    # LOGIN
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute(
                "SELECT role FROM users WHERE username=? AND password=?",
                (username, password)
            )
            result = c.fetchone()

            if result:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = result[0]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # SIGNUP
    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            if new_user and new_pass:
                try:
                    c.execute(
                        "INSERT INTO users VALUES (?,?,?)",
                        (new_user, new_pass, "user")
                    )
                    conn.commit()
                    st.success("Account created. Please login.")
                except:
                    st.error("Username already exists")
            else:
                st.warning("Please fill all fields")

    st.stop()

# ---------------- MAIN APP ----------------
st.title("📘 Daily Work Report System")
st.success(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")

# ---------------- DATA ENTRY ----------------
st.subheader("📝 Daily Work Entry")

with st.form("entry_form"):
    report_date = st.date_input("Date", date.today())
    school = st.text_input("School")
    work_done = st.text_area("Work Done")
    amendment = st.text_area("Amendment (if any)")
    distance = st.number_input(
        "Distance from Zonal Office (KM)",
        min_value=0.0,
        step=0.1
    )
    save = st.form_submit_button("Save")

if save:
    c.execute("""
    INSERT INTO reports
    (username, report_date, school, work_done, amendment, distance)
    VALUES (?,?,?,?,?,?)
    """, (
        st.session_state.username,
        report_date,
        school,
        work_done,
        amendment,
        distance
    ))
    conn.commit()
    st.success("✅ Record saved successfully")

# ---------------- MONTHLY REPORTS ----------------
st.markdown("---")
st.subheader("📊 Monthly Reports")

# Admin sees all, user sees own
if st.session_state.role == "admin":
    df = pd.read_sql("SELECT * FROM reports", conn)
else:
    df = pd.read_sql(
        "SELECT * FROM reports WHERE username=?",
        conn,
        params=(st.session_state.username,)
    )

if df.empty:
    st.info("No records available")
else:
    df["report_date"] = pd.to_datetime(df["report_date"])

    available_months = sorted(df["report_date"].dt.strftime("%Y-%m").unique())
    selected_month = st.selectbox("Select Month", available_months)

    # STRICT month separation
    month_df = df[df["report_date"].dt.strftime("%Y-%m") == selected_month]

    st.dataframe(month_df)

    # ---------------- EDIT / DELETE ----------------
    for _, row in month_df.iterrows():
        with st.expander(f"{row['report_date'].date()} | {row['school']}"):
            s = st.text_input("School", row["school"], key=f"s{row['id']}")
            w = st.text_area("Work Done", row["work_done"], key=f"w{row['id']}")
            a = st.text_area("Amendment", row["amendment"], key=f"a{row['id']}")
            d = st.number_input("Distance (KM)", row["distance"], key=f"d{row['id']}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Update", key=f"u{row['id']}"):
                    c.execute("""
                    UPDATE reports
                    SET school=?, work_done=?, amendment=?, distance=?
                    WHERE id=?
                    """, (s, w, a, d, row["id"]))
                    conn.commit()
                    st.success("Updated")
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete", key=f"x{row['id']}"):
                    c.execute("DELETE FROM reports WHERE id=?", (row["id"],))
                    conn.commit()
                    st.warning("Deleted")
                    st.rerun()

    # ---------------- EXCEL DOWNLOAD (CLOUD SAFE) ----------------
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        month_df.to_excel(writer, index=False, sheet_name="Monthly Report")

    buffer.seek(0)

    st.download_button(
        label="📥 Download Monthly Excel",
        data=buffer,
        file_name=f"{st.session_state.username}_{selected_month}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------- LOGOUT ----------------
st.markdown("---")
if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()
