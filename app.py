import streamlit as st
import pandas as pd
import datetime as dt
import os


# ---------------- BASIC SETUP ----------------
st.set_page_config(
    page_title="Fixture Audit System",
    layout="wide",
    initial_sidebar_state="expanded",
)

MASTER_PATH = "config_master.csv"
HISTORY_PATH = "audit_history.csv"
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)


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
    """Count audits completed today from history"""
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
        st.session_state["employee_id"] = username.strip()
        st.success("Login button clicked (demo only, no restriction).")


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
                c1, c2, c3, c4, c5, c6 = st.columns([0.8, 2.2, 1.7, 2.0, 2.0, 3.0])
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

    # ensure audit_no is always numeric and unique (if not coming from dashboard)
    current_audit_no = st.session_state.get("current_audit_no", None)
    if current_audit_no is None:
        current_audit_no = get_next_audit_no()
        st.session_state["current_audit_no"] = current_audit_no
    audit_no = current_audit_no

    st.info(f"**Current Audit: #{audit_no}**")

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

    # ---- frequency and current frequency (per-row, used in table) ----
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

    h0, h1, h2, h3, h4, h5, h_status, h8, h9, h10 = st.columns(
        [0.7, 3.5, 3, 0.8, 1.6, 1.8, 1.6, 1.8, 2.0, 2.4]
    )
    h0.write("**S.No**")
    h1.write("**Fixture Part description**")
    h2.write("**Check point**")
    h3.write("**Quantity**")
    h4.write("**Frequency (cycles)**")
    h5.write("**Current frequency**")
    with h_status:
        st.write("**Status**")
    h8.write("**Changed before Date**")
    h9.write("**Remarks**")
    h10.write("**Image**")

    ss = st.session_state
    ss.setdefault("row_status", {})
    ss.setdefault("row_change_date", {})
    ss.setdefault("row_remarks", {})
    ss.setdefault("row_image_mode", {})
    ss.setdefault("row_image_path", {})

    original_indices = check_subset.index.to_list()
    history_rows = []

    for local_idx, row in table.iterrows():
        df_index = original_indices[local_idx]

        c0, c1, c2, c3, c4, c5, c_status, c8, c9, c10 = st.columns(
            [0.7, 3.5, 3, 0.8, 1.6, 1.8, 1.6, 1.8, 2.0, 2.4]
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
        with c5:
            st.write(int(row["Current frequency"]))

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
                st.write("")

        img_path = ss["row_image_path"].get(df_index, "")

        with c10:
            if show_extra:
                mode_key = f"img_mode_{df_index}"
                current_mode = ss["row_image_mode"].get(df_index, "Upload")
                mode = st.radio(
                    " ",
                    ["Upload", "Camera"],
                    index=0 if current_mode == "Upload" else 1,
                    key=mode_key,
                    horizontal=True,
                    label_visibility="collapsed",
                )
                ss["row_image_mode"][df_index] = mode

                base_name = f"audit_{audit_no}_row_{local_idx + 1}.jpg"
                full_path = os.path.join(IMAGES_DIR, base_name)

                if mode == "Upload":
                    file_key = f"file_{df_index}"
                    uploaded = st.file_uploader(
                        "",
                        type=["jpg", "jpeg", "png"],
                        key=file_key,
                    )
                    if uploaded is not None:
                        with open(full_path, "wb") as f:
                            f.write(uploaded.getbuffer())
                        img_path = full_path
                else:
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
                    st.write(os.path.basename(img_path))
            else:
                st.write("")

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

    # Save all audited items and remove from dashboard
    if st.button("Save Audit"):
        audited_items = []
        for idx in original_indices:
            if idx in ss.get("row_status", {}):
                audited_items.append(idx)

        if not audited_items:
            st.warning("No items to audit.")
            st.rerun()

        # update Changed before date for all audited items
        for idx in audited_items:
            date_val = ss.get("row_change_date", {}).get(idx)
            if isinstance(date_val, dt.date):
                df_cfg.loc[idx, date_col] = date_val

        # only "No" rows go to audit history
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

        # Clear session and return to dashboard
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
                # S.No, Audit No, Fixture, Line, Status, Remarks, Image
                c_sn, c_aud, c_fix, c_line, c_stat, c_rem, c_img = st.columns(
                    [0.7, 1.0, 3.0, 2.0, 1.4, 2.5, 2.0]
                )
                with c_sn:
                    st.write(i + 1)  # serial number
                with c_aud:
                    st.write(f"#{row.get('audit_no', '')}")
                with c_fix:
                    fixture_desc = row.get("fixture_part_desc", "")
                    st.write(f"Fixture: {fixture_desc if fixture_desc else 'N/A'}")
                with c_line:
                    st.write(f"Line: {row.get('line', '')}")
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
