import streamlit as st
import pandas as pd
import datetime as dt

# ---------------- BASIC SETUP ----------------
st.set_page_config(
    page_title="Fixture Audit System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- LOAD MASTER CONFIG ----------
df_cfg = pd.read_csv("config_master.csv")

for col in ["qty", "frequency_cycles"]:
    if col in df_cfg.columns:
        df_cfg[col] = pd.to_numeric(df_cfg[col], errors="coerce").fillna(0).astype(int)

date_col = "Changed before date"
if date_col in df_cfg.columns:
    df_cfg[date_col] = pd.to_datetime(
        df_cfg[date_col].astype(str).str.strip(),
        format="%d-%m-%Y",
        errors="coerce",
    ).dt.date

df_cfg["line"] = df_cfg["line"].astype(str)
df_cfg["sub_assembly"] = df_cfg["sub_assembly"].astype(str)
df_cfg["kind"] = df_cfg["kind"].astype(str)

# ---------- GLOBAL SIDEBAR CSS (flex column) ----------
st.markdown(
    """
    <style>
    /* make sidebar a flex column so we can push logout to bottom */
    div[data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- SIDEBAR WITH CLICKABLE BLOCKS ----------
PAGES = ["Login", "Dashboard", "Start New Audit", "Configure", "Audit History"]

if "page" not in st.session_state:
    st.session_state["page"] = "Login"

def nav_card(label: str, danger: bool = False):
    is_active = st.session_state["page"] == label
    if danger:
        bg = "#7F1D1D"
        border = "#F97373"
    else:
        bg = "#31333F" if is_active else "#1F2630"
        border = "#FF4B4B" if is_active else "#4F4F4F"

    if st.button(label, key=f"nav_{label}", use_container_width=True):
        if danger:
            # logout: clear session and go to Login
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.session_state["page"] = "Login"
        else:
            st.session_state["page"] = label
        st.rerun()

    # very small vertical spacing and compact cards
    st.markdown(
        f"""
        <style>
        div[data-testid="stSidebar"] div[data-testid="stButton"][key="nav_{label}"] > button {{
            background-color: {bg};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 0.22rem 0.45rem;
            margin-top: 0.06rem;
            margin-bottom: 0.06rem;
            text-align: center;
            font-weight: 600;
            font-size: 0.86rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    # HEADER AREA
    st.markdown(
        """
        <div style="font-size: 2.0rem; font-weight: 900; margin-bottom: 0.05rem;">
            Royal Enfield
        </div>
        <hr style="margin-top:0.25rem; margin-bottom:0.30rem; border:0; border-top:1px solid #444;">
        """,
        unsafe_allow_html=True,
    )

    # NAVIGATION AREA (top part of flex)
    nav_container = st.container()
    with nav_container:
        for p in PAGES:
            nav_card(p)

    # SPACER to push logout to very bottom
    st.markdown(
        "<div style='flex:1 1 auto;'></div>",
        unsafe_allow_html=True,
    )

    # LOGOUT AT BOTTOM
    st.markdown(
        "<hr style='margin:0.25rem 0 0.18rem 0; border-top:1px solid #444;'>",
        unsafe_allow_html=True,
    )
    nav_card("Logout", danger=True)

page = st.session_state["page"]

# ---------------- LOGIN PAGE ----------------
if page == "Login":
    st.title("FIXTURE AUDIT SYSTEM")
    st.subheader("Royal Enfield")

    username = st.text_input("Username / Employee ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.success("Login button clicked (demo only, no restriction).")

# ---------------- DASHBOARD PAGE ----------------
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

# ---------------- START NEW AUDIT PAGE ----------------
elif page == "Start New Audit":
    st.title("Start New Audit")

    line = st.selectbox("Line", sorted(df_cfg["line"].unique()))

    sa_options = (
        df_cfg[df_cfg["line"] == line]["sub_assembly"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    sub_assembly = st.selectbox("Sub Assembly", sorted(sa_options))

    kind = st.radio("What do you want to change?", ["Fixture", "Tool"])

    base_subset = df_cfg[
        (df_cfg["line"] == line)
        & (df_cfg["sub_assembly"] == sub_assembly)
        & (df_cfg["kind"] == kind)
    ]

    if kind == "Fixture":
        fixture = st.selectbox(
            "Fixture No.",
            base_subset["fixture_no"].dropna().astype(str).unique(),
        )
        check_subset = base_subset[base_subset["fixture_no"].astype(str) == fixture]
        st.write(f"Selected fixture: {fixture}")
    else:
        station = st.selectbox(
            "Station No.",
            base_subset["station_no"].dropna().astype(str).unique(),
        )
        check_subset = base_subset[base_subset["station_no"].astype(str) == station]
        station_name = str(check_subset["station_name"].iloc[0])
        st.write(f"Selected station: {station} – {station_name}")

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

    h0, h1, h2, h3, h4, h5, h_status, h8, h9, h10 = st.columns(
        [0.7, 3, 3, 0.7, 1.4, 1.6, 1.2, 1.8, 2.0, 2.0]
    )
    h0.write("**S.N o**")
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

    ss = st.session_state
    ss.setdefault("row_yes", {})
    ss.setdefault("row_no", {})
    ss.setdefault("row_change_date", {})
    ss.setdefault("row_remarks", {})
    ss.setdefault("row_files", {})

    today = dt.date.today()
    original_indices = check_subset.index.to_list()

    for local_idx, row in table.iterrows():
        df_index = original_indices[local_idx]

        c0, c1, c2, c3, c4, c5, c_status, c8, c9, c10 = st.columns(
            [0.7, 3, 3, 0.7, 1.4, 1.6, 1.2, 1.8, 2.0, 2.0]
        )

        with c0:
            st.write(local_idx + 1)

        with c1:
            st.write(row["Fixture Part description"])
        with c2:
            st.write(row["Check point"])
        with c3:
            st.write(int(row["Qty"]))
        with c4:
            st.write(int(row["Frequency (cycles)"]))

        csv_date = df_cfg.loc[df_index, date_col] if date_col in df_cfg.columns else None
        default_date = csv_date if isinstance(csv_date, dt.date) else today

        with c8:
            key_dt = f"date_{df_index}"
            chosen_date = st.date_input("", value=default_date, key=key_dt)
            ss["row_change_date"][df_index] = chosen_date

        days = 0
        if isinstance(chosen_date, dt.date):
            d = chosen_date
            step = dt.timedelta(days=1)
            while d < today:
                if d.weekday() != 6:
                    days += 1
                d += step
        current_freq = days * 1800

        with c5:
            st.write(current_freq)

        with c_status:
            s1, s2 = st.columns(2)
            with s1:
                key_yes = f"yes_{df_index}"
                ss["row_yes"][df_index] = st.checkbox("", key=key_yes)
            with s2:
                key_no = f"no_{df_index}"
                ss["row_no"][df_index] = st.checkbox("", key=key_no)

        show_extra = ss["row_no"].get(df_index, False)

        with c9:
            if show_extra:
                key_rem = f"remark_{df_index}"
                default_rem = ss["row_remarks"].get(df_index, "")
                ss["row_remarks"][df_index] = st.text_input(
                    "", value=default_rem, key=key_rem
                )
            else:
                st.write("")

        with c10:
            if show_extra:
                key_file = f"file_{df_index}"
                ss["row_files"][df_index] = st.file_uploader(
                    "", type=["jpg", "jpeg", "png"], key=key_file
                )
            else:
                st.write("")

    if st.button("Save Audit"):
        for idx, date_val in ss.get("row_change_date", {}).items():
            if isinstance(date_val, dt.date):
                df_cfg.loc[idx, date_col] = date_val

        df_to_save = df_cfg.copy()
        df_to_save[date_col] = pd.to_datetime(
            df_to_save[date_col], errors="coerce"
        ).dt.strftime("%d-%m-%Y")
        df_to_save[date_col] = df_to_save[date_col].fillna("")
        df_to_save.to_csv("config_master.csv", index=False)

        st.success("Audit saved.")

# ---------------- CONFIGURE PAGE ----------------
elif page == "Configure":
    st.title("Configure (view master data)")
    st.write("Master configuration from config_master.csv:")
    st.dataframe(df_cfg, use_container_width=True)

# ---------------- AUDIT HISTORY PAGE ----------------
elif page == "Audit History":
    st.title("Audit History")
    st.write("Audit history table will go here.")
