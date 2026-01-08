import streamlit as st
import pandas as pd
import datetime as dt
import os

# ---------------- BASIC SETUP ----------------
st.set_page_config(
    page_title="Fixture Audit System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MASTER_PATH = "config_master.csv"
HISTORY_PATH = "audit_history.csv"
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------- NEW DARK-CYAN THEME CSS ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-main: #020617;
        --bg-panel: #020617;
        --bg-card: #0b1120;
        --accent: #38bdf8;
        --accent-soft: #0ea5e9;
        --accent-strong: #0284c7;
        --text-main: #e5e7eb;
        --text-muted: #9ca3af;
        --border-soft: #1f2937;
    }

    .stApp {
        background: radial-gradient(circle at top left, #1e293b 0, #020617 50%, #020617 100%);
        color: var(--text-main);
        font-family: "Poppins", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.0rem;
        max-width: 1200px;
    }

    h1 {
        font-size: 2.3rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        color: #f9fafb;
    }
    h2, h3 {
        color: #f9fafb;
        font-weight: 600;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #111827, #020617);
        border-radius: 14px;
        border: 1px solid var(--border-soft);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.8);
        padding-top: 0.7rem;
        padding-bottom: 0.7rem;
    }
    [data-testid="stMetricValue"] {
        color: #f9fafb;
        font-weight: 700;
        font-size: 1.4rem;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.75rem;
    }

    [data-testid="stSidebar"] {
        background: #020617;
        border-right: 1px solid #1f2937;
    }

    .hide-sidebar [data-testid="stSidebar"] {
        display: none;
    }
    .hide-sidebar [data-testid="collapsedControl"] {
        display: none;
    }

    .sidebar-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f9fafb;
        margin-bottom: 0.2rem;
    }
    .sidebar-subtitle {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-bottom: 0.7rem;
    }

    div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        background: #020617;
        color: var(--text-main);
        border-radius: 999px;
        border: 1px solid #1f2937;
        padding: 0.35rem 0.7rem;
        font-weight: 500;
        font-size: 0.9rem;
    }
    div[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #0b1120;
        border-color: var(--accent);
        color: #f9fafb;
    }

    .login-card {
        max-width: 520px;
        margin: 3rem auto 0 auto;
        padding: 0;
        background: transparent;
        border-radius: 0;
        box-shadow: none;
        border: none;
    }
    .login-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #f9fafb;
        margin-bottom: 0.15rem;
    }
    .login-subtitle {
        font-size: 0.95rem;
        color: var(--text-muted);
        margin-bottom: 1.4rem;
    }

    .stTextInput > label {
        font-weight: 500;
        color: var(--text-main);
    }
    .stTextInput input {
        background-color: #020617;
        color: #e5e7eb;
        border-radius: 999px;
        border: 1px solid #1f2937;
    }
    .stTextInput input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent-soft);
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong)) !important;
        color: #0b1120 !important;
        border-radius: 999px !important;
        border: 1px solid var(--accent-strong) !important;
        padding: 0.45rem 1.6rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--accent-strong), var(--accent)) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- LOAD MASTER CONFIG ----------
df_cfg = pd.read_csv(MASTER_PATH)


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
    df_tmp = df_tmp[df_tmp["frequency_cycles"] > 0]
    df_tmp["current_frequency"] = df_tmp[date_col].apply(
        lambda d: working_cycles_from_date(d, today)
    )
    diff = df_tmp["frequency_cycles"] - df_tmp["current_frequency"]
    df_tmp = df_tmp[diff.between(0, THRESHOLD)]
    df_tmp = df_tmp.reset_index().rename(columns={"index": "row_id"})
    df_tmp.insert(0, "S.No", df_tmp.index + 1)
    df_tmp.insert(1, "Audit No", df_tmp["S.No"])
    return df_tmp

def get_completed_today_count():
    if not os.path.exists(HISTORY_PATH):
        return 0
    df_hist = pd.read_csv(HISTORY_PATH)
    if df_hist.empty or "timestamp" not in df_hist.columns:
        return 0
    today_str = dt.date.today().strftime("%Y-%m-%d")
    today_audits = df_hist[df_hist["timestamp"].str.startswith(today_str)]
    return len(today_audits)

# ---------- AUDIT HISTORY HELPERS ----------
def get_next_audit_no() -> int:
    if not os.path.exists(HISTORY_PATH):
        return 1
    df_hist = pd.read_csv(HISTORY_PATH)
    if "audit_no" not in df_hist.columns or df_hist.empty:
        return 1
    nums = pd.to_numeric(df_hist["audit_no"], errors="coerce").dropna()
    if nums.empty:
        return 1
    return int(nums.max()) + 1

def append_audit_history(records: list):
    if not records:
        return
    new_df = pd.DataFrame(records)
    if os.path.exists(HISTORY_PATH):
        new_df.to_csv(HISTORY_PATH, mode="a", header=False, index=False)
    else:
        new_df.to_csv(HISTORY_PATH, mode="w", header=True, index=False)

# ---------- PAGE / NAV STATE ----------
PAGES = ["Dashboard", "Components", "Configure", "Audit History"]

if "page" not in st.session_state:
    st.session_state["page"] = "Login"

page = st.session_state["page"]

def nav_card(label: str, danger: bool = False):
    is_active = st.session_state["page"] == label

    if danger:
        bg = "#fef2f2"
        border = "#b91c1c"
        txt = "#b91c1c"
    else:
        bg = "#0b1120" if is_active else "#020617"
        border = "#38bdf8" if is_active else "#1f2937"
        txt = "#e5e7eb"

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
            border-radius: 999px;
            padding: 0.35rem 0.7rem;
            margin-top: 0.12rem;
            margin-bottom: 0.12rem;
            text-align: left;
            font-weight: 500;
            font-size: 0.9rem;
            color: {txt};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
# ---------- SIDEBAR (ONLY AFTER LOGIN) ----------
if page != "Login":
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-title">Fixture Audit</div>
            <div class="sidebar-subtitle">Royal Enfield – Engine Assembly</div>
            <hr style="margin-top:0.25rem; margin-bottom:0.6rem; border:0; border-top:1px solid #1f2937;">
            """,
            unsafe_allow_html=True,
        )
        nav_container = st.container()
        with nav_container:
            for p in PAGES:
                nav_card(p)
        st.markdown("<div style='flex:1 1 auto;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<hr style='margin:0.6rem 0 0.4rem 0; border-top:1px solid #1f2937;'>",
            unsafe_allow_html=True,
        )
        nav_card("Logout", danger=True)
else:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
# ---------------- LOGIN PAGE ----------------
if page == "Login":
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="
            width: 50%;
            margin: 0 auto 1.4rem auto;
            padding: 0.9rem 1.2rem;
            border-radius: 10px;
            background: rgba(15,23,42,0.88);
            border: 1px solid rgba(148,163,184,0.45);
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #e5e7eb;
        ">
            Fixture Audit System
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='login-title'>Royal Enfield</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='login-subtitle'>Please sign in to continue.</div>",
        unsafe_allow_html=True,
    )

    username = st.text_input("Employee ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.session_state["employee_id"] = username.strip()
        st.session_state["page"] = "Dashboard"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- DASHBOARD PAGE ----------------
elif page == "Dashboard":
    st.title("Dashboard")

    df_due = get_due_items()
    completed_today = get_completed_today_count()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Audits", len(df_due))
    with col2:
        st.metric("Completed Today", completed_today)
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
                c1, c2, c3, c4, c5, c6 = st.columns([0.8, 2.2, 1.8, 2.0, 2.0, 3.0])
                with c1:
                    st.write(s_no)
                with c2:
                    if st.button(
                        f"Audit {a_no}",
                        key=f"audit_btn_{row_id}",
                        use_container_width=True,
                    ):
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
                        st.session_state["current_audit_no"] = a_no
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

    current_audit_no = st.session_state.get("current_audit_no", None)
    if current_audit_no is None:
        current_audit_no = get_next_audit_no()
        st.session_state["current_audit_no"] = current_audit_no
    audit_no = current_audit_no

    st.info(f"Current Audit: #{audit_no}")

    line_default = st.session_state.get("selected_line", None)
    sa_default = st.session_state.get("selected_sub_assembly", None)
    kind_default = st.session_state.get("selected_kind", "Fixture")
    fixture_default = st.session_state.get("selected_fixture_no", None)
    station_default = st.session_state.get("selected_station_no", None)
    selected_row_id = st.session_state.get("selected_row_id", None)
    employee_id = st.session_state.get("employee_id", "")

    line_list = sorted(df_cfg["line"].unique())
    line_index = line_list.index(line_default) if line_default in line_list else 0
    line = st.selectbox("Line", line_list, index=line_index)

    sa_options_all = (
        df_cfg[df_cfg["line"] == line]["sub_assembly"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    sa_list = sorted(sa_options_all)
    sa_index = sa_list.index(sa_default) if sa_default in sa_list else 0
    sub_assembly = st.selectbox("Sub Assembly", sa_list, index=sa_index)


    kind = st.radio(
        "What do you want to change?", ["Fixture", "Tool"],
        index=0 if kind_default == "Fixture" else 1,
    )

    base_subset = df_cfg[
        (df_cfg["line"] == line)
        & (df_cfg["sub_assembly"] == sub_assembly)
        & (df_cfg["kind"] == kind)
    ]

    if kind == "Fixture":
        fixture_options = base_subset["fixture_no"].dropna().astype(str).unique().tolist()
        f_index = fixture_options.index(fixture_default) if fixture_default in fixture_options else 0
        fixture = st.selectbox("Fixture No.", fixture_options, index=f_index)
        check_subset = base_subset[base_subset["fixture_no"].astype(str) == fixture]
        st.write(f"Selected fixture: {fixture}")
        station = ""
    else:
        station_options = base_subset["station_no"].dropna().astype(str).unique().tolist()
        s_index = station_options.index(station_default) if station_default in station_options else 0
        station = st.selectbox("Station No.", station_options, index=s_index)
        check_subset = base_subset[base_subset["station_no"].astype(str) == station]
        station_name = str(check_subset["station_name"].iloc[0])
        st.write(f"Selected station: {station} – {station_name}")
        fixture = ""

    if selected_row_id is not None and selected_row_id in check_subset.index:
        check_subset = check_subset.loc[[selected_row_id]]

    st.divider()
    st.subheader("Checklist")

    today = dt.date.today()

    def row_current_freq(idx):
        change_date = df_cfg.loc[idx, date_col] if date_col in df_cfg.columns else None
        return working_cycles_from_date(change_date, today)

    base_cols = ["fixture_part_desc", "check_point", "qty", "frequency_cycles"]
    table = check_subset[base_cols].copy()
    table["current_frequency"] = [
        row_current_freq(idx) for idx in check_subset.index
    ]
    table = table.rename(
        columns={
            "fixture_part_desc": "Fixture Part description",
            "check_point": "Check point",
            "qty": "Qty",
            "frequency_cycles": "Frequency (cycles)",
            "current_frequency": "Current frequency",
        }
    ).reset_index(drop=True)

    ss = st.session_state
    ss.setdefault("row_status", {})
    ss.setdefault("row_change_date", {})
    ss.setdefault("row_remarks", {})
    ss.setdefault("row_image_mode", {})
    ss.setdefault("row_image_path", {})

    original_indices = check_subset.index.to_list()
    history_rows = []

    # helper for left-aligned cell content
    def left(text):
        st.markdown(
            f"<div style='text-align:left;'>{text}</div>",
            unsafe_allow_html=True,
        )

    # scrollable checklist container
    st.markdown(
        """
        <div style="width:100%; overflow-x:auto;">
          <div style="min-width:1300px;">
        """,
        unsafe_allow_html=True,
    )

    # header row with centered headers
    h0, h1, h2, h3, h4, h5, h_status, h8, h9, h10 = st.columns(
        [1.0, 3.6, 2.5, 0.8, 1.8, 1.8, 1.4, 2.5, 2.7, 2.0]
    )

    def center_header(text: str):
        st.markdown(
            f"<div style='text-align:center; font-weight:600;'>{text}</div>",
            unsafe_allow_html=True,
        )

    with h0:
        center_header("S.No")
    with h1:
        center_header("Fixture Part description")
    with h2:
        center_header("Check point")
    with h3:
        center_header("Qty")
    with h4:
        center_header("Frequency (cycles)")
    with h5:
        center_header("Current frequency")
    with h_status:
        center_header("Status")
    with h8:
        center_header("Changed before Date")
    with h9:
        center_header("Remark")
    with h10:
        center_header("Image")

    # rows
    for local_idx, row in table.iterrows():
        df_index = original_indices[local_idx]

        c0, c1, c2, c3, c4, c5, c_status, c8, c9, c10 = st.columns(
            [1.0, 3.6, 2.5, 0.5, 1.8, 1.8, 1.6, 2.3, 2.5, 2.1]
        )
        with c0:
            left(local_idx + 1)
        with c1:
            left(row["Fixture Part description"])
        with c2:
            left(row["Check point"])
        with c3:
            left(int(row["Qty"]))
        with c4:
            left(int(row["Frequency (cycles)"]))
        with c5:
            left(int(row["Current frequency"]))

        csv_date = df_cfg.loc[df_index, date_col] if date_col in df_cfg.columns else None
        default_date = csv_date if isinstance(csv_date, dt.date) else today

        with c8:
            key_dt = f"date_{df_index}"
            chosen_date = st.date_input("", value=default_date, key=key_dt)
            ss["row_change_date"][df_index] = chosen_date

        with c_status:
            current_status = ss["row_status"].get(df_index, "Yes")
            status = st.radio(
                " ",
                options=["Yes", "No"],
                index=0 if current_status == "Yes" else 1,
                key=f"status_{df_index}",
                horizontal=True,
                label_visibility="collapsed",
            )
            ss["row_status"][df_index] = status

        show_extra = (ss["row_status"][df_index] == "No")

        with c9:
            if show_extra:
                key_rem = f"remark_{df_index}"
                default_rem = ss["row_remarks"].get(df_index, "")
                ss["row_remarks"][df_index] = st.text_input(
                    "", value=default_rem, key=key_rem
                )
            else:
                left("")


        img_path = ss["row_image_path"].get(df_index, "")

        # ---- CAMERA-ONLY IMAGE CAPTURE ----
        with c10:
            if show_extra:
                base_name = f"audit_{audit_no}_row_{local_idx + 1}.jpg"
                full_path = os.path.join(IMAGES_DIR, base_name)

                cam_key = f"cam_{df_index}"
                photo = st.camera_input(
                    "",
                    key=cam_key,
                )
                if photo is not None:
                    with open(full_path, "wb") as f:
                        f.write(photo.getvalue())
                    img_path = full_path

                ss["row_image_path"][df_index] = img_path

                if img_path:
                    left(os.path.basename(img_path))
                else:
                    left("")
            else:
                left("")
        # -----------------------------------

        history_rows.append(
            {
                "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                "audit_no": audit_no,
                "employee_id": employee_id,
                "line": line,
                "sub_assembly": sub_assembly,
                "kind": kind,
                "fixture_no": fixture if kind == "Fixture" else "",
                "station_no": station if kind != "Fixture" else "",
                "fixture_part_desc": row["Fixture Part description"],
                "check_point": row["Check point"],
                "qty": int(row["Qty"]),
                "status": ss["row_status"].get(df_index, ""),
                "changed_before_date": chosen_date.strftime("%d-%m-%Y")
                if isinstance(chosen_date, dt.date)
                else "",
                "remarks": ss["row_remarks"].get(df_index, ""),
                "image_info": img_path,
            }
        )

    st.markdown(
        """
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # --------- UPDATED SAVE AUDIT LOGIC ---------
    if st.button("Save Audit"):
        audited_items = []
        for idx in original_indices:
            if idx in ss.get("row_status", {}):
                audited_items.append(idx)

        if not audited_items:
            st.warning("No items to audit.")
            st.rerun()

        today = dt.date.today()

        for idx in audited_items:
            status_val = ss.get("row_status", {}).get(idx, "Yes")
            if status_val == "No":
                df_cfg.loc[idx, date_col] = today
                ss["row_change_date"][idx] = today
            else:
                date_val = ss.get("row_change_date", {}).get(idx)
                if isinstance(date_val, dt.date):
                    df_cfg.loc[idx, date_col] = date_val


        filtered_history = [r for r in history_rows if r["status"] == "No"]


        df_to_save = df_cfg.copy()
        df_to_save[date_col] = pd.to_datetime(
            df_to_save[date_col], errors="coerce"
        ).dt.strftime("%d-%m-%Y")
        df_to_save[date_col] = df_to_save[date_col].fillna("")
        df_to_save.to_csv(MASTER_PATH, index=False)

        append_audit_history(filtered_history)

        total_items = len(audited_items)
        issues_found = len(filtered_history)
        st.success(
            f"Audit #{audit_no} completed! {total_items} items checked, {issues_found} issues logged"
        )

        for key in [
            "selected_line",
            "selected_sub_assembly",
            "selected_kind",
            "selected_fixture_no",
            "selected_station_no",
            "selected_row_id",
            "current_audit_no",
            "row_status",
            "row_change_date",
            "row_remarks",
            "row_image_mode",
            "row_image_path",
        ]:
            if key in st.session_state:
                del st.session_state[key]


        st.session_state["page"] = "Dashboard"
        st.rerun()

# ---------------- CONFIGURE PAGE ----------------
elif page == "Configure":
    st.title("Configure (view master data)")
    st.write("Master configuration from config_master.csv:")
    st.dataframe(df_cfg, use_container_width=True)

# ---------------- AUDIT HISTORY PAGE ----------------
elif page == "Audit History":
    st.title("Audit History")
    if os.path.exists(HISTORY_PATH):
        df_hist = pd.read_csv(HISTORY_PATH)
        if df_hist.empty:
            st.write("No audits recorded yet.")
        else:
            for i, row in df_hist.iterrows():
                c_sn, c_aud, c_fix, c_line, c_stat, c_rem, c_img = st.columns(
                    [1.1, 1.1, 4.0, 1.5, 1.2, 3.0, 2.0]
                )
                with c_sn:
                    st.write(i + 1)
                with c_aud:
                    st.write(f"#{row.get('audit_no', '')}")
                with c_fix:
                    fixture_desc = row.get("fixture_part_desc", "")
                    st.write(f"Fixture: {fixture_desc if fixture_desc else 'N/A'}")
                with c_line:
                    st.write(f"{row.get('line', '')}")
                with c_stat:
                    st.write(f"Status: {row.get('status', '')}")
                with c_rem:
                    remarks = row.get("remarks", "")
                    st.write(f"Remarks: {remarks if remarks else 'N/A'}")
                with c_img:
                    img_path = str(row.get("image_info", ""))
                    if img_path and os.path.exists(img_path):
                        if st.button("📷 View Image", key=f"hist_view_{i}"):
                            st.image(
                                img_path,
                                caption=f"Audit {row.get('audit_no', '')} - {row.get('fixture_part_desc', '')}",
                            )
                    else:
                        st.write("No image")
                st.divider()
    else:
        st.write("No audits recorded yet.")
