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
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT role FROM users WHERE username=? AND password=?",(user,pwd))
            r = c.fetchone()
            if r:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.role = r[0]
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        new_user = st.text_input("New Username")
        new_pwd = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?)",(new_user,new_pwd,"user"))
                conn.commit()
                st.success("Account created. Login now.")
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
    INSERT INTO reports (username,report_date,school,work_done,amendment,distance)
    VALUES (?,?,?,?,?,?)
    """,(st.session_state.user,d,school,work,amend,dist))
    conn.commit()
    st.success("Record saved")

# ---------------- VIEW / EDIT / DELETE ----------------
st.markdown("---")
st.subheader("📋 My Records")

if st.session_state.role == "admin":
    df = pd.read_sql("SELECT * FROM reports", conn)
else:
    df = pd.read_sql("SELECT * FROM reports WHERE username=?", conn,
                     params=(st.session_state.user,))

if not df.empty:
    df["report_date"] = pd.to_datetime(df["report_date"])
    month = st.selectbox("Select Month",
                         sorted(df["report_date"].dt.strftime("%Y-%m").unique()))
    mdf = df[df["report_date"].dt.strftime("%Y-%m")==month]

    for _,row in mdf.iterrows():
        with st.expander(f"{row['report_date'].date()} | {row['school']}"):
            new_school = st.text_input("School",row["school"],key=f"s{row['id']}")
            new_work = st.text_area("Work Done",row["work_done"],key=f"w{row['id']}")
            new_amend = st.text_area("Amendment",row["amendment"],key=f"a{row['id']}")
            new_dist = st.number_input("Distance",row["distance"],key=f"d{row['id']}")

            col1,col2 = st.columns(2)
            with col1:
                if st.button("✏️ Update", key=f"u{row['id']}"):
                    c.execute("""
                    UPDATE reports SET school=?,work_done=?,amendment=?,distance=?
                    WHERE id=?
                    """,(new_school,new_work,new_amend,new_dist,row["id"]))
                    conn.commit()
                    st.success("Updated")
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"x{row['id']}"):
                    c.execute("DELETE FROM reports WHERE id=?",(row["id"],))
                    conn.commit()
                    st.warning("Deleted")
                    st.rerun()

    # Excel Export
    file = f"{st.session_state.user}_{month}.xlsx"
    mdf.to_excel(file,index=False)
    with open(file,"rb") as f:
        st.download_button("📥 Download Excel",f,file_name=file)

else:
    st.info("No records")

# ---------------- LOGOUT ----------------
if st.button("Logout"):
    st.session_state.logged_in=False
    st.rerun()
