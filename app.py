import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Daily Work Report", layout="centered")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")

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
    c.execute("INSERT INTO users VALUES (?,?,?)", ("admin","admin123","admin"))
    conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN / SIGNUP ----------------
if not st.session_state.logged_in:
    st.title("🔐 Daily Work Report System")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT role FROM users WHERE username=? AND password=?",(u,p))
            r = c.fetchone()
            if r:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.session_state.role = r[0]
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?)",(nu,np,"user"))
                conn.commit()
                st.success("Account created. Please login.")
            except:
                st.error("Username already exists")

    st.stop()

# ---------------- MAIN ----------------
st.title("📘 Daily Work Report")
st.success(f"Logged in as {st.session_state.user}")

# ---------------- DATA ENTRY ----------------
with st.form("add_form"):
    d = st.date_input("Date", date.today())
    school = st.text_input("School")
    work = st.text_area("Work Done")
    amend = st.text_area("Amendment")
    dist = st.number_input("Distance (KM)",0.0,step=0.1)
    save = st.form_submit_button("Save")

if save:
    c.execute("""
    INSERT INTO reports
    (username,report_date,school,work_done,amendment,distance)
    VALUES (?,?,?,?,?,?)
    """,(st.session_state.user,d,school,work,amend,dist))
    conn.commit()
    st.success("✅ Record saved")

# ---------------- MONTHLY REPORTS ----------------
st.markdown("---")
st.subheader("📊 Monthly Reports")

if st.session_state.role == "admin":
    df = pd.read_sql("SELECT * FROM reports", conn)
else:
    df = pd.read_sql(
        "SELECT * FROM reports WHERE username=?",
        conn,
        params=(st.session_state.user,)
    )

if df.empty:
    st.info("No records available")
else:
    df["report_date"] = pd.to_datetime(df["report_date"])

    available_months = sorted(df["report_date"].dt.strftime("%Y-%m").unique())
    selected_month = st.selectbox("Select Month", available_months)

    # 🔒 STRICT MONTH FILTER (NO MIXING)
    month_df = df[df["report_date"].dt.strftime("%Y-%m") == selected_month]

    st.dataframe(month_df)

    # ---------------- EDIT / DELETE ----------------
    for _,row in month_df.iterrows():
        with st.expander(f"{row['report_date'].date()} | {row['school']}"):
            s = st.text_input("School",row["school"],key=f"s{row['id']}")
            w = st.text_area("Work Done",row["work_done"],key=f"w{row['id']}")
            a = st.text_area("Amendment",row["amendment"],key=f"a{row['id']}")
            d = st.number_input("Distance",row["distance"],key=f"d{row['id']}")

            col1,col2 = st.columns(2)
            with col1:
                if st.button("✏️ Update", key=f"u{row['id']}"):
                    c.execute("""
                    UPDATE reports
                    SET school=?,work_done=?,amendment=?,distance=?
                    WHERE id=?
                    """,(s,w,a,d,row["id"]))
                    conn.commit()
                    st.success("Updated")
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"x{row['id']}"):
                    c.execute("DELETE FROM reports WHERE id=?",(row["id"],))
                    conn.commit()
                    st.warning("Deleted")
                    st.rerun()

    # ---------------- EXCEL EXPORT (MONTH ONLY) ----------------
    file = f"{st.session_state.user}_{selected_month}.xlsx"
    month_df.to_excel(file,index=False)

    with open(file,"rb") as f:
        st.download_button(
            "📥 Download Monthly Excel",
            f,
            file_name=file
        )

# ---------------- LOGOUT ----------------
if st.button("Logout"):
    st.session_state.logged_in=False
    st.rerun()
