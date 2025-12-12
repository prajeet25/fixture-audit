import streamlit as st
import pandas as pd
import datetime as dt

# -------------------------------------------------
# BASIC PAGE SETUP
# -------------------------------------------------
st.set_page_config(page_title="Fixture Audit System", layout="wide")

# ---------- LOAD MASTER CONFIG ----------
# config_master.csv must have columns:
# line, sub_assembly, kind, fixture_no, station_no, station_name,
# fixture_part_desc, check_point, qty, frequency_cycles
df_cfg = pd.read_csv("config_master.csv")

# Clean important types
df_cfg["line"] = df_cfg["line"].astype(str)
df_cfg["sub_assembly"] = df_cfg["sub_assembly"].astype(str)
df_cfg["kind"] = df_cfg["kind"].astype(str)

# ---------- SIDEBAR NAV ----------
page = st.sidebar.selectbox(
    "Navigation",
    ["Login", "Dashboard", "Start New Audit", "Configure", "Audit History"],
)
st.sidebar.write("Royal Enfield")

# =================================================
# LOGIN PAGE
# =================================================
if page == "Login":
    st.title("FIXTURE AUDIT SYSTEM")
    st.subheader("Royal Enfield")

    username = st.text_input("Username / Employee ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.success("Login button clicked (demo only, no restriction).")

# =================================================
# DASHBOARD PAGE
# =================================================
elif page == "Dashboard":
    st.title("Dashboard")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader("Today's Assigned Fixtures")
        st.write("- Fixture 12 → J Line → Due Today")
        st.write("- Fixture 5 → J Line → Overdue")
    with col2:
        st.metric("Pending Audits", 5)
    with col3:
        st.metric("Completed Today", 3)

    st.divider()
    search = st.text_input("Search")
    st.button("Start New Audit")

# =================================================
# START NEW AUDIT PAGE
# =================================================
elif page == "Start New Audit":
    st.title("Start New Audit")

    # 1) Select Line
    line_options = (
        df_cfg["line"].dropna().astype(str).drop_duplicates().tolist()
    )
    line = st.selectbox("Line", sorted(line_options))

    # 2) Select Sub Assembly for that line
    sa_options = (
        df_cfg[df_cfg["line"] == line]["sub_assembly"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    sub_assembly = st.selectbox("Sub Assembly", sorted(sa_options))

    # 3) Fixture or Tool
    kind = st.radio("What do you want to change?", ["Fixture", "Tool"])

    base_subset = df_cfg[
        (df_cfg["line"] == line)
        & (df_cfg["sub_assembly"] == sub_assembly)
        & (df_cfg["kind"] == kind)
    ]

    # 4) Choose specific fixture / station
    if kind == "Fixture":
        fixture_options = (
            base_subset["fixture_no"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )
        fixture = st.selectbox("Fixture No.", fixture_options)
        check_subset = base_subset[base_subset["fixture_no"].astype(str) == fixture]
        st.write(f"Selected fixture: {fixture}")
    else:
        station_options = (
            base_subset["station_no"]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .tolist()
        )
        station = st.selectbox("Station No.", station_options)
        check_subset = base_subset[base_subset["station_no"].astype(str) == station]
        station_name = str(check_subset["station_name"].iloc[0])
        st.write(f"Selected station: {station} – {station_name}")

    # -------------------------------------------------
    # CHECKLIST TABLE WITH STATUS / REMARKS / IMAGE
    # -------------------------------------------------
    st.divider()
    st.subheader("Checklist")

    base_cols = ["fixture_part_desc", "check_point", "qty", "frequency_cycles"]
    table = check_subset[base_cols].rename(
        columns={
            "fixture_part_desc": "Fixture Part description",
            "check_point": "Check point",
            "qty": "Qty",
            "frequency_cycles": "Frequency (cycles)",
        }
    ).reset_index(drop=True)

    # ---- Header row (add S.No as first column) ----
    h0, h1, h2, h3, h4, h5, h_status, h8, h9, h10 = st.columns(
        [0.7, 3, 3, 0.7, 1.4, 1.6, 1.2, 1.8, 2.0, 2.0]
    )
    h0.write("**S.No**")
    h1.write("**Fixture Part description**")
    h2.write("**Check point**")
    h3.write("**Qty**")
    h4.write("**Frequency (cycles)**")
    h5.write("**Current Frequency (cycles)**")

    with h_status:
        st.write("**Status**")
        s1, s2 = st.columns(2)
        with s1:
            st.write("**Yes**")
        with s2:
            st.write("**No**")

    h8.write("**Changed before Date**")
    h9.write("**Remarks**")
    h10.write("**Image**")

    # State storage
    ss = st.session_state
    ss.setdefault("row_yes", {})
    ss.setdefault("row_no", {})
    ss.setdefault("row_change_date", {})
    ss.setdefault("row_remarks", {})
    ss.setdefault("row_files", {})

    today = dt.date.today()

    # ---- One visual row per checklist item ----
    for idx, row in table.iterrows():
        c0, c1, c2, c3, c4, c5, c_status, c8, c9, c10 = st.columns(
            [0.7, 3, 3, 0.7, 1.4, 1.6, 1.2, 1.8, 2.0, 2.0]
        )

        with c0:
            st.write(idx + 1)  # S.No

        with c1:
            st.write(row["Fixture Part description"])
        with c2:
            st.write(row["Check point"])
        with c3:
            st.write(int(row["Qty"]))
        with c4:
            base_freq = int(row["Frequency (cycles)"])
            st.write(base_freq)

        # Changed before Date: choose date
        with c8:
            key_dt = f"date_{idx}"
            default_dt = ss["row_change_date"].get(idx, today)
            date_val = st.date_input("", value=default_dt, key=key_dt)
            ss["row_change_date"][idx] = date_val

        # Compute working days from date_val to today (exclude Sundays)
        days = 0
        if isinstance(date_val, dt.date):
            d = date_val
            step = dt.timedelta(days=1)
            while d < today:
                if d.weekday() != 6:  # 6 = Sunday
                    days += 1
                d += step

        # Current frequency starts from 0 and increases 1800 per working day
        current_freq = days * 1800

        with c5:
            st.write(current_freq)

        # Status column with Yes/No under one header
        with c_status:
            s1, s2 = st.columns(2)
            with s1:
                key_yes = f"yes_{idx}"
                yes_val = st.checkbox("", key=key_yes)
                ss["row_yes"][idx] = yes_val
            with s2:
                key_no = f"no_{idx}"
                no_val = st.checkbox("", key=key_no)
                ss["row_no"][idx] = no_val

        # Only show Remarks & Image when Status is No
        show_extra = ss["row_no"].get(idx, False)

        with c9:
            if show_extra:
                key_rem = f"remark_{idx}"
                default_rem = ss["row_remarks"].get(idx, "")
                remark = st.text_input("", value=default_rem, key=key_rem)
                ss["row_remarks"][idx] = remark
            else:
                st.write("")

        with c10:
            if show_extra:
                key_file = f"file_{idx}"
                uploaded = st.file_uploader(
                    "", type=["jpg", "jpeg", "png"], key=key_file
                )
                ss["row_files"][idx] = uploaded
            else:
                st.write("")

    if st.button("Save Audit"):
        st.success("Audit saved (demo).")

# =================================================
# CONFIGURE PAGE
# =================================================
elif page == "Configure":
    st.title("Configure (view master data)")
    st.write("Master configuration from config_master.csv:")
    st.dataframe(df_cfg, use_container_width=True)

# =================================================
# AUDIT HISTORY PAGE (placeholder)
# =================================================
elif page == "Audit History":
    st.title("Audit History")
    st.write("Audit history table will go here.")
