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

# ---------- GLOBAL SIDEBAR CSS ----------
st.markdown(
    """
    <style>
    div[data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- DASHBOARD HELPERS ----------
THRESHOLD = 5000  # cycles

def working_cycles_from_date(change_date: dt.date, today: dt.date) -> int:
    if not isinstance(change_date, dt.date):
        return 0
    d = change_date
    days = 0
    step = dt.timedelta(days=1)
    while d < today:
        if d.weekday() != 6:  # Sunday
            days += 1
        d += step
    return days * 1800

def get_due_items():
    today = dt.date.today()
    df_tmp = df_cfg.copy()

    # ignore rows with zero frequency
    df_tmp = df_tmp[df_tmp["frequency_cycles"] > 0]

    # recompute current frequency from date
    df_tmp["current_frequency"] = df_tmp[date_col].apply(
        lambda d: working_cycles_from_date(d, today)
    )

    diff = df_tmp["frequency_cycles"] - df_tmp["current_frequency"]
    df_tmp = df_tmp[diff.between(0, THRESHOLD)]

    # keep original row index so we can get the exact component row later
    df_tmp = df_tmp.reset_index().rename(columns={"index": "row_id"})
    df_tmp.insert(0, "S.No", df_tmp.index + 1)
    df_tmp.insert(1, "Audit No", df_tmp["S.No"])

    return df_tmp

# ---------- SIDEBAR WITH CLICKABLE BLOCKS ----------
PAGES = ["Login", "Dashboard", "Components", "Configure", "Audit History"]

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
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.session_state["page"] = "Login"
        else:
            st.session_state["page"] = label
        st.rerun()

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
    st.markdown(
        """
        <div style="font-size: 2.0rem; font-weight: 900; margin-bottom: 0.05rem;">
            Royal Enfield
        </div>
        <hr style="margin-top:0.25rem; margin-bottom:0.30rem; border:0; border-top:1px solid #444;">
        """,
        unsafe_allow_html=True,
    )

    nav_container = st.container()
    with nav_container:
        for p in PAGES:
            nav_card(p)

    st.markdown("<div style='flex:1 1 auto;'></div>", unsafe_allow_html=True)
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

    df_due = get_due_items()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Audits", len(df_due))
    with col2:
        st.metric("Completed Today", 0)
    with col3:
        st.metric("Threshold (cycles)", THRESHOLD)

    st.divider()
    st.subheader("Fixtures / Tools Near Due")

    if df_due.empty:
        st.write("No fixtures or tools within 5000 cycles of their limit.")
    else:
        for _, row in df_due.iterrows():
            s_no = int(row["S.No"])
            a_no = row["Audit No"]
            line = row["line"]
            sub_assembly = row["sub_assembly"]
            kind = row["kind"]
            fixture_no = row.get("fixture_no", None)
            station_no = row.get("station_no", None)
            row_id = int(row["row_id"])

            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([0.8, 2.2, 1.7, 2.0, 2.0, 3.0])
                with c1:
                    st.write(s_no)
                with c2:
                    if st.button(
                        f"Audit {a_no}",
                        key=f"audit_btn_{row_id}",
                        use_container_width=True,
                    ):
                        # store exact selection and component row, then go to Components
                        st.session_state["page"] = "Components"
                        st.session_state["selected_line"] = line
                        st.session_state["selected_sub_assembly"] = sub_assembly
                        st.session_state["selected_kind"] = kind
                        st.session_state["selected_fixture_no"] = (
                            str(fixture_no) if pd.notna(fixture_no) else None
                        )
                        st.session_state["selected_station_no"] = (
                            str(station_no) if pd.notna(station_no) else None
                        )
                        st.session_state["selected_row_id"] = row_id
                        st.rerun()
                with c3:
                    st.write(line)
                with c4:
                    st.write(sub_assembly)
                with c5:
                    st.write(kind)
                with c6:
                    st.write(row.get("fixture_part_desc", ""))

# ---------------- COMPONENTS PAGE ----------------
elif page == "Components":
    st.title("Components")

    # defaults passed from dashboard
    line_default = st.session_state.get("selected_line", None)
    sa_default = st.session_state.get("selected_sub_assembly", None)
    kind_default = st.session_state.get("selected_kind", "Fixture")
    fixture_default = st.session_state.get("selected_fixture_no", None)
    station_default = st.session_state.get("selected_station_no", None)
    selected_row_id = st.session_state.get("selected_row_id", None)

    # Line selection
    line_list = sorted(df_cfg["line"].unique())
    if line_default in line_list:
        line_index = line_list.index(line_default)
    else:
        line_index = 0
    line = st.selectbox("Line", line_list, index=line_index)

    # Sub-assembly selection; prefer pre-selected value
    sa_options_all = (
        df_cfg[df_cfg["line"] == line]["sub_assembly"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    sa_list = sorted(sa_options_all)
    if sa_default in sa_list:
        sa_index = sa_list.index(sa_default)
    else:
        sa_index = 0
    sub_assembly = st.selectbox("Sub Assembly", sa_list, index=sa_index)

    # Kind
    kind = st.radio(
        "What do you want to change?", ["Fixture", "Tool"],
        index=0 if kind_default == "Fixture" else 1,
    )

    base_subset = df_cfg[
        (df_cfg["line"] == line)
        & (df_cfg["sub_assembly"] == sub_assembly)
        & (df_cfg["kind"] == kind)
    ]

    # Fixture / Station selection
    if kind == "Fixture":
        fixture_options = base_subset["fixture_no"].dropna().astype(str).unique().tolist()
        if fixture_default in fixture_options:
            f_index = fixture_options.index(fixture_default)
        else:
            f_index = 0
        fixture = st.selectbox("Fixture No.", fixture_options, index=f_index)
        check_subset = base_subset[base_subset["fixture_no"].astype(str) == fixture]
        st.write(f"Selected fixture: {fixture}")
    else:
        station_options = base_subset["station_no"].dropna().astype(str).unique().tolist()
        if station_default in station_options:
            s_index = station_options.index(station_default)
        else:
            s_index = 0
        station = st.selectbox("Station No.", station_options, index=s_index)
        check_subset = base_subset[base_subset["station_no"].astype(str) == station]
        station_name = str(check_subset["station_name"].iloc[0])
        st.write(f"Selected station: {station} – {station_name}")

    # If we came from dashboard with a specific component row, filter to that row only
    if selected_row_id is not None and selected_row_id in check_subset.index:
        check_subset = check_subset.loc[[selected_row_id]]

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
