import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Import logic and theme modules
from utils import (
    clean_dataframe, parse_dates, get_numeric_cols, generate_summary_stats,
    get_outliers, generate_pdf
)
from theme import COLOR_THEMES, CURRENCIES, get_theme_vars, get_plot_template, inject_css

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="SpendSense AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# THEME — load active theme vars
# ==============================
T = get_theme_vars()
inject_css(T)

# Unpack theme vars for convenience
BG          = T["BG"]
BG2         = T["BG2"]
BG3         = T["BG3"]
BORDER      = T["BORDER"]
TEXT        = T["TEXT"]
TEXT2       = T["TEXT2"]
ACCENT1     = T["ACCENT1"]
ACCENT2     = T["ACCENT2"]
ACCENT3     = T["ACCENT3"]
SHADOW      = T["SHADOW"]
FILL_COLOR  = T["FILL_COLOR"]
CHART_COLORS= T["CHART_COLORS"]
CURR_SYMBOL = T["CURR_SYMBOL"]
SIDEBAR_BG  = T["SIDEBAR_BG"]
PLOT_PAPER  = T["PLOT_PAPER"]
PLOT_BG     = T["PLOT_BG"]
PLOT_GRID   = T["PLOT_GRID"]
PLOT_TPL    = get_plot_template(T)

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:

    st.markdown(f"""
    <div style='padding:20px 4px 16px 4px;border-bottom:2px solid {BORDER};margin-bottom:4px;'>
        <div style='font-family:Syne,sans-serif;font-size:1.55rem;font-weight:800;
        color:{ACCENT1};line-height:1.1;'>
            SpendSense 
        </div>
        <div style='color:{TEXT2};font-size:0.78rem;margin-top:5px;letter-spacing:0.3px;'>
            Smart Expense Analyzer
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ---- COLOR THEME ----
    st.markdown(f"<div class='sidebar-label'>🎨 Color Theme</div>", unsafe_allow_html=True)
    theme_keys = list(COLOR_THEMES.keys())
    chosen_theme = st.selectbox("theme", label_visibility="collapsed", options=theme_keys,
        index=theme_keys.index(st.session_state["color_theme"]))
    if chosen_theme != st.session_state["color_theme"]:
        st.session_state["color_theme"] = chosen_theme
        st.rerun()
    _prev = COLOR_THEMES[chosen_theme]
    st.markdown(
        f"<div style='display:flex;gap:6px;margin:4px 0 10px 0;'>"
        f"<div style='width:16px;height:16px;border-radius:50%;background:{_prev['a1']};'></div>"
        f"<div style='width:16px;height:16px;border-radius:50%;background:{_prev['a2']};'></div>"
        f"<div style='width:16px;height:16px;border-radius:50%;background:{_prev['a3']};'></div>"
        f"</div>", unsafe_allow_html=True)

    # ---- CURRENCY ----
    st.markdown(f"<div class='sidebar-label'>🔢 Currency</div>", unsafe_allow_html=True)
    curr_keys = list(CURRENCIES.keys())
    chosen_curr = st.selectbox("currency", label_visibility="collapsed", options=curr_keys,
        index=curr_keys.index(st.session_state["currency"]))
    if chosen_curr != st.session_state["currency"]:
        st.session_state["currency"] = chosen_curr
        st.rerun()

    # ---- UPLOAD ----
    st.markdown(f"<div class='sidebar-label'>📁 Upload CSV</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <style>
    /* Hide default uploader box, keep only functionality */
    section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] > div {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] .stFileUploader > label {{
        display: none !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] button {{
        display: none !important;
    }}
    /* Make entire styled box clickable via uploader overlay */
    .sidebar-upload-wrap {{
        position: relative;
        cursor: pointer;
    }}
    .sidebar-upload-wrap [data-testid="stFileUploadDropzone"] {{
        position: absolute !important;
        inset: 0 !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10 !important;
    }}
    </style>
    <div style='border:2px dashed {ACCENT1};border-radius:14px;
    background:linear-gradient(135deg,#13131f,#1a1a2e);
    padding:18px 12px 14px 12px;text-align:center;margin-bottom:6px;
    box-shadow:0 0 18px rgba(167,139,250,0.08);cursor:pointer;
    transition:all 0.25s ease;'>
        <div style='font-size:2rem;margin-bottom:6px;'>📂</div>
        <div style='font-family:Syne,sans-serif;font-size:0.88rem;font-weight:700;
        color:{TEXT};margin-bottom:3px;'>Drop CSV here</div>
        <div style='color:{TEXT2};font-size:0.73rem;margin-bottom:10px;'>or click to browse</div>
        <div style='display:flex;justify-content:center;gap:6px;flex-wrap:wrap;'>
            <span style='background:{ACCENT1}22;border:1px solid {ACCENT1}55;color:{ACCENT1};
            padding:2px 7px;border-radius:20px;font-size:0.68rem;font-weight:600;'>📅 Date</span>
            <span style='background:{ACCENT2}22;border:1px solid {ACCENT2}55;color:{ACCENT2};
            padding:2px 7px;border-radius:20px;font-size:0.68rem;font-weight:600;'>💰 Amount</span>
            <span style='background:{ACCENT3}22;border:1px solid {ACCENT3}55;color:{ACCENT3};
            padding:2px 7px;border-radius:20px;font-size:0.68rem;font-weight:600;'>🏷️ Category</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")

# ==============================
# MAIN CONTENT
# ==============================

if uploaded_file is None and "df" not in st.session_state:

    st.markdown(f"""
    <div class='hero-wrap'>
        <div class='hero-title'>💸 SpendSense</div>
        <p class='hero-sub'>Your personal expense analyzer — upload a CSV and get instant charts, trends, and smart financial advice from Groq AI.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='section-title'>🚀 How It Works</div>", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    for col_w, num, title, sub in zip(
        [s1,s2,s3,s4],
        ["1","2","3","4"],
        ["Upload CSV","Explore Charts","Add Groq Key","Get AI Insights"],
        ["Your expense data","Interactive visuals","Free from groq.com","Savings & tips"],
    ):
        with col_w:
            st.markdown(f"""
            <div class='step-card'>
                <div class='step-num'>{num}</div>
                <div style='font-weight:700;color:{TEXT};font-size:0.9rem;'>{title}</div>
                <div style='color:{TEXT2};font-size:0.78rem;margin-top:4px;'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    # Hide default uploader UI completely, overlay it on custom box
    st.markdown(f"""
    <div class='upload-hint' style='padding-bottom:24px;cursor:pointer;'>
        <div class='upload-icon-wrap'>📂</div>
        <div style='font-family:Syne,sans-serif;font-size:1.25rem;font-weight:800;color:{TEXT};margin-bottom:8px;'>
            Upload your CSV from the sidebar 👈
        </div>
        <div style='color:{TEXT2};font-size:0.86rem;margin-bottom:10px;'>
            Supports any CSV with date, amount, and category columns
        </div>
        <div style='display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-bottom:4px;'>
            <span style='background:{ACCENT1}22;border:1px solid {ACCENT1}55;color:{ACCENT1};
            padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;'>📅 Date</span>
            <span style='background:{ACCENT2}22;border:1px solid {ACCENT2}55;color:{ACCENT2};
            padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;'>💰 Amount</span>
            <span style='background:{ACCENT3}22;border:1px solid {ACCENT3}55;color:{ACCENT3};
            padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;'>🏷️ Category</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='section-title'>🎲 No CSV? Try Sample Data</div>", unsafe_allow_html=True)
    if st.button("Load Sample Data"):
        np.random.seed(42)
        categories = ["Food","Transport","Shopping","Utilities","Entertainment","Health"]
        months = pd.date_range("2024-01-01", periods=120, freq="W")
        demo_df = pd.DataFrame({
            "Date":     months,
            "Amount":   np.random.randint(500,15000,120),
            "Category": np.random.choice(categories,120),
            "Income":   np.random.randint(30000,60000,120),
            "Savings":  np.random.randint(1000,10000,120),
        })
        st.session_state["df"] = clean_dataframe(demo_df)
        st.rerun()

else:
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("uploaded_file_id") != file_id:
            # Genuinely new file — reset everything
            df_raw = pd.read_csv(uploaded_file)
            df_raw = parse_dates(df_raw)
            st.session_state["df"]               = df_raw
            st.session_state["eda_df"]           = df_raw.copy()
            st.session_state["uploaded_file_id"] = file_id

    # Always use eda_df as source of truth for entire dashboard
    if "eda_df" not in st.session_state:
        st.session_state["eda_df"] = st.session_state["df"].copy()

    df           = st.session_state["eda_df"]
    numeric_cols = get_numeric_cols(df)
    cat_cols     = df.select_dtypes(include=["object"]).columns.tolist()
    summary      = generate_summary_stats(df)

    # HERO (compact)
    st.markdown(f"""
    <div class='hero-wrap' style='padding:20px 28px;margin-bottom:20px;'>
        <div class='hero-title' style='font-size:1.7rem;'>💸 Personal Expense Intelligence</div>
        <p class='hero-sub'>
            {df.shape[0]} records &nbsp;·&nbsp; {df.shape[1]} columns &nbsp;·&nbsp;
            {len(numeric_cols)} numeric fields &nbsp;·&nbsp;
            {'Year '+str(int(df["Year"].min()))+'–'+str(int(df["Year"].max())) if "Year" in df.columns else ""}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='section-title'>📈 Dataset Overview</div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    for col_w, (icon, val, lbl, sub) in zip([m1,m2,m3,m4], [
        ("📋", f"{df.shape[0]:,}", "Total Rows",    "Records loaded"),
        ("🗂️", str(df.shape[1]),   "Columns",       "Data fields"),
        ("🔢", str(len(numeric_cols)), "Numeric Cols", "Analyzable"),
        ("📅", f"{int(df['Year'].min())}–{int(df['Year'].max())}" if "Year" in df.columns else "N/A", "Date Range", "Coverage"),
    ]):
        with col_w:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:1.5rem;margin-bottom:8px;'>{icon}</div>
                <div class='metric-value'>{val}</div>
                <div class='metric-label'>{lbl}</div>
                <div style='font-size:0.78rem;color:{TEXT2};margin-top:4px;'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    if numeric_cols:
        st.markdown("<br>", unsafe_allow_html=True)
        stat_cols = st.columns(min(4, len(numeric_cols)))
        for col_widget, col_name in zip(stat_cols, numeric_cols[:4]):
            with col_widget:
                col_total = df[col_name].sum()
                col_avg   = df[col_name].mean()
                col_max   = df[col_name].max()
                st.markdown(f"""
                <div class='metric-card' style='text-align:center;'>
                    <div style='font-size:0.72rem;font-weight:700;color:{TEXT2};
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>{col_name}</div>
                    <div class='metric-value' style='font-size:1.7rem;'>{col_total:,.0f}</div>
                    <div class='metric-label'>Total</div>
                    <div style='margin-top:8px;color:{TEXT2};font-size:0.8rem;'>
                        Avg <span style='color:{ACCENT2};font-weight:600;'>{col_avg:,.0f}</span>
                        &nbsp;·&nbsp;
                        Max <span style='color:{ACCENT1};font-weight:600;'>{col_max:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ==============================
    # TABS
    # ==============================
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab_eda, tab2, tab3, tab6 = st.tabs([
        "📊 Analytics", "🔍 EDA", "🗃️ Raw Data", "🔬 Deep Dive",
        "📈 Forecast & PDF"
    ])

    # ---- TAB 1: ANALYTICS ----
    with tab1:
        if numeric_cols:
            st.markdown(f"<div class='section-title'>Distribution Analysis</div>", unsafe_allow_html=True)
            for i in range(0, min(len(numeric_cols), 4), 2):
                row_cols = st.columns(2)
                for j, col_name in enumerate(numeric_cols[i:i+2]):
                    with row_cols[j]:
                        fig = px.histogram(df, x=col_name, nbins=30,
                            title=f"Distribution of {col_name}",
                            color_discrete_sequence=[CHART_COLORS[j]])
                        fig.update_layout(**PLOT_TPL)
                        fig.update_traces(marker_line_width=0.4, marker_line_color=PLOT_BG)
                        st.plotly_chart(fig, use_container_width=True)

        if "Month_Name" in df.columns and numeric_cols:
            st.markdown(f"<div class='section-title'>📅 Monthly Trend</div>", unsafe_allow_html=True)
            selected_metric = st.selectbox("Select metric:", numeric_cols, key="ts_metric")
            month_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                         7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            monthly = df.groupby("Month")[selected_metric].sum().reset_index().sort_values("Month")
            monthly["Month_Name"] = monthly["Month"].map(month_map)
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=monthly["Month_Name"], y=monthly[selected_metric],
                mode="lines+markers",
                line=dict(color=ACCENT1, width=3, shape="spline"),
                marker=dict(size=9, color=ACCENT2, line=dict(color=ACCENT1, width=2)),
                fill="tozeroy", fillcolor=FILL_COLOR, name=selected_metric
            ))
            fig_line.update_layout(title=f"Monthly {selected_metric} Trend", **PLOT_TPL)
            st.plotly_chart(fig_line, use_container_width=True)

        if cat_cols:
            st.markdown(f"<div class='section-title'>🏷️ Category Breakdown</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            selected_cat = st.selectbox("Select category column:", cat_cols, key="cat_col")
            cat_counts = df[selected_cat].value_counts().reset_index()
            cat_counts.columns = [selected_cat, "Count"]
            with c1:
                fig_bar = px.bar(cat_counts.head(10), x=selected_cat, y="Count",
                    title=f"Top {selected_cat} Categories", color="Count",
                    color_continuous_scale=[PLOT_BG, ACCENT1, ACCENT2])
                fig_bar.update_layout(**PLOT_TPL)
                st.plotly_chart(fig_bar, use_container_width=True)
            with c2:
                fig_pie = px.pie(cat_counts.head(8), values="Count", names=selected_cat,
                    title=f"{selected_cat} Distribution",
                    color_discrete_sequence=CHART_COLORS, hole=0.38)
                fig_pie.update_layout(**PLOT_TPL)
                fig_pie.update_traces(textposition="outside", textinfo="percent+label",
                                      textfont=dict(color=TEXT))
                st.plotly_chart(fig_pie, use_container_width=True)

            if numeric_cols:
                st.markdown(f"<div class='section-title'>💰 Spending by Category</div>", unsafe_allow_html=True)
                selected_num = st.selectbox("Select numeric metric:", numeric_cols, key="cat_num")
                cat_spend = df.groupby(selected_cat)[selected_num].sum().reset_index().sort_values(selected_num, ascending=True)
                fig_h = px.bar(cat_spend, y=selected_cat, x=selected_num, orientation="h",
                    title=f"Total {selected_num} by {selected_cat}", color=selected_num,
                    color_continuous_scale=[PLOT_BG, ACCENT1, ACCENT2])
                fig_h.update_layout(**PLOT_TPL)
                st.plotly_chart(fig_h, use_container_width=True)

        if len(numeric_cols) > 1:
            st.markdown(f"<div class='section-title'>🔗 Correlation Matrix</div>", unsafe_allow_html=True)
            corr_matrix = df[numeric_cols].corr()
            fig_heat = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                color_continuous_scale=[PLOT_BG, ACCENT1, ACCENT2],
                title="Correlation Heatmap")
            fig_heat.update_layout(**PLOT_TPL)
            st.plotly_chart(fig_heat, use_container_width=True)

    # ---- TAB EDA ----
    with tab_eda:
        # ── HANDLE EDITS FIRST (before any rendering) ──
        if st.session_state.get("_eda_action"):
            action = st.session_state.pop("_eda_action")
            tmp    = st.session_state["eda_df"].copy()

            if action == "fill_missing":
                col  = st.session_state.get("_eda_miss_col")
                strat= st.session_state.get("_eda_miss_strat","Mean")
                if col:
                    if strat == "Mean":     tmp[col] = tmp[col].fillna(tmp[col].mean())
                    elif strat == "Median": tmp[col] = tmp[col].fillna(tmp[col].median())
                    elif strat == "Mode":   tmp[col] = tmp[col].fillna(tmp[col].mode()[0] if len(tmp[col].mode())>0 else 0)
                    else:                   tmp[col] = tmp[col].fillna(0)
                    st.session_state["eda_df"] = tmp
                    st.session_state["_eda_msg"] = f"✅ '{col}' missing values filled with {strat}!"

            elif action == "drop_dupes":
                before = len(tmp)
                tmp = tmp.drop_duplicates().reset_index(drop=True)
                st.session_state["eda_df"] = tmp
                st.session_state["_eda_msg"] = f"✅ {before - len(tmp)} duplicate rows removed!"

            elif action == "rename_col":
                old = st.session_state.get("_eda_ren_old")
                new = st.session_state.get("_eda_ren_new","").strip()
                if old and new:
                    st.session_state["eda_df"] = tmp.rename(columns={old: new})
                    st.session_state["_eda_msg"] = f"✅ '{old}' renamed to '{new}'!"

            elif action == "drop_col":
                col = st.session_state.get("_eda_drop_col")
                if col:
                    st.session_state["eda_df"] = tmp.drop(columns=[col])
                    st.session_state["_eda_msg"] = f"✅ '{col}' column removed!"

            elif action == "change_dtype":
                col  = st.session_state.get("_eda_dtype_col")
                dtype= st.session_state.get("_eda_dtype_new","str")
                if col:
                    try:
                        if dtype == "int":       tmp[col] = pd.to_numeric(tmp[col], errors="coerce").astype("Int64")
                        elif dtype == "float":   tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
                        elif dtype == "str":     tmp[col] = tmp[col].astype(str)
                        elif dtype == "datetime":tmp[col] = pd.to_datetime(tmp[col], errors="coerce")
                        st.session_state["eda_df"] = tmp
                        st.session_state["_eda_msg"] = f"✅ '{col}' type changed to {dtype}!"
                    except Exception as ex:
                        st.session_state["_eda_msg"] = f"❌ Error: {ex}"

            elif action == "reset":
                st.session_state["eda_df"] = st.session_state["_eda_original"].copy()
                st.session_state["_eda_msg"] = "✅ Original data restored!"

        # Save original on first load
        if "_eda_original" not in st.session_state:
            st.session_state["_eda_original"] = st.session_state["eda_df"].copy()

        # Live reference
        E = st.session_state["eda_df"]

        st.markdown(f"<div class='section-title'>🔍 Full EDA Report</div>", unsafe_allow_html=True)

        # ── SHOW MESSAGE IF ANY ──
        if st.session_state.get("_eda_msg"):
            st.success(st.session_state.pop("_eda_msg"))

        # ── OVERVIEW CARDS ──
        total_missing = int(E.isnull().sum().sum())
        dup_count     = int(E.duplicated().sum())
        e1,e2,e3,e4 = st.columns(4)
        for cw,(icon,val,lbl,clr) in zip([e1,e2,e3,e4],[
            ("📋", f"{E.shape[0]:,}",    "Total Rows",     ACCENT2),
            ("🗂️", f"{E.shape[1]}",     "Total Columns",  ACCENT1),
            ("❓", f"{total_missing:,}", "Missing Values", "#f87171" if total_missing>0 else ACCENT3),
            ("👯", f"{dup_count:,}",     "Duplicate Rows", "#fbbf24" if dup_count>0 else ACCENT3),
        ]):
            with cw:
                st.markdown(f"""
                <div class='metric-card' style='text-align:center;'>
                    <div style='font-size:1.4rem;margin-bottom:6px;'>{icon}</div>
                    <div style='font-size:1.6rem;font-weight:800;color:{clr};'>{val}</div>
                    <div class='metric-label'>{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── COLUMN INFO ──
        st.markdown(f"<div class='section-title'>📋 Column Info</div>", unsafe_allow_html=True)
        col_info = []
        for c in E.columns:
            miss = E[c].isnull().sum()
            col_info.append({"Column": c, "Type": str(E[c].dtype),
                "Unique": E[c].nunique(), "Missing": miss,
                "Missing %": f"{round(miss/len(E)*100,1)}%",
                "Sample": str(E[c].dropna().iloc[0]) if E[c].dropna().shape[0]>0 else "N/A"})
        st.dataframe(pd.DataFrame(col_info), use_container_width=True, hide_index=True)

        # ── MISSING HEATMAP ──
        if total_missing > 0:
            st.markdown(f"<div class='section-title'>❓ Missing Values Heatmap</div>", unsafe_allow_html=True)
            fig_miss = px.imshow(E.isnull().astype(int).T,
                color_continuous_scale=["#1a1a2e","#f87171"],
                title="Missing Values (Red = Missing)", aspect="auto")
            fig_miss.update_layout(**PLOT_TPL)
            st.plotly_chart(fig_miss, use_container_width=True)
        else:
            st.success("✅ No missing values!")

        # ── KEY STATS ──
        nc_eda = get_numeric_cols(E)
        if nc_eda:
            st.markdown(f"<div class='section-title'>📊 Key Stats</div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{
                "Column": c, "Mean": round(E[c].mean(),2),
                "Median": round(E[c].median(),2),
                "Mode": round(E[c].mode()[0],2) if len(E[c].mode())>0 else "N/A",
                "Std": round(E[c].std(),2), "Min": round(E[c].min(),2), "Max": round(E[c].max(),2)
            } for c in nc_eda]), use_container_width=True, hide_index=True)

        # ── OUTLIERS ──
        if nc_eda:
            st.markdown(f"<div class='section-title'>📦 Outlier Detection</div>", unsafe_allow_html=True)
            sel_out = st.selectbox("Select column:", nc_eda, key="eda_out_col")
            fig_out = px.box(E, y=sel_out, title=f"{sel_out} Outliers",
                color_discrete_sequence=[ACCENT1], points="all")
            fig_out.update_layout(**PLOT_TPL)
            st.plotly_chart(fig_out, use_container_width=True)
            q1,q3 = E[sel_out].quantile(0.25), E[sel_out].quantile(0.75)
            iqr   = q3-q1
            outs  = E[(E[sel_out]<q1-1.5*iqr)|(E[sel_out]>q3+1.5*iqr)]
            st.markdown(f"<div class='ai-response'><b style='color:{ACCENT1};'>{sel_out}</b> — <b style='color:#f87171;'>{len(outs)} outliers</b> (IQR: &lt;{q1-1.5*iqr:,.1f} or &gt;{q3+1.5*iqr:,.1f})</div>", unsafe_allow_html=True)

        # ══════════════════════════════
        # EDITING SECTION
        # ══════════════════════════════
        st.markdown(f"<div class='section-title'>✏️ Edit Your Data</div>", unsafe_allow_html=True)
        ed1, ed2 = st.columns(2)

        # ── FIX MISSING ──
        with ed1:
            st.markdown(f"<div style='font-weight:700;color:{ACCENT1};margin-bottom:8px;'>❓ Fill Missing Values</div>", unsafe_allow_html=True)
            nc_eda2 = get_numeric_cols(E)
            if nc_eda2:
                miss_col   = st.selectbox("Column:", nc_eda2, key="eda_miss_col")
                miss_strat = st.selectbox("Strategy:", ["Mean","Median","Mode","Zero"], key="eda_miss_strat")
                if st.button("Fill Missing", key="eda_fill", use_container_width=True):
                    st.session_state["_eda_action"]     = "fill_missing"
                    st.session_state["_eda_miss_col"]   = miss_col
                    st.session_state["_eda_miss_strat"] = miss_strat
                    st.rerun()
            else:
                st.info("No numeric columns found.")

        # ── DROP DUPLICATES ──
        with ed2:
            st.markdown(f"<div style='font-weight:700;color:{ACCENT1};margin-bottom:8px;'>👯 Duplicate Rows</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:{TEXT2};font-size:0.85rem;margin-bottom:8px;'>{dup_count} duplicate rows found</div>", unsafe_allow_html=True)
            if st.button("Delete Duplicates", key="eda_dup", use_container_width=True):
                st.session_state["_eda_action"] = "drop_dupes"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        ed3, ed4 = st.columns(2)

        # ── RENAME COLUMN ──
        with ed3:
            st.markdown(f"<div style='font-weight:700;color:{ACCENT1};margin-bottom:8px;'>✏️ Rename Column</div>", unsafe_allow_html=True)
            ren_old = st.selectbox("Column:", list(E.columns), key="eda_ren_old")
            ren_new = st.text_input("New name:", key="eda_ren_new", placeholder="Enter new name...")
            if st.button("Rename", key="eda_rename", use_container_width=True):
                st.session_state["_eda_action"]  = "rename_col"
                st.session_state["_eda_ren_old"] = ren_old
                st.session_state["_eda_ren_new"] = ren_new
                st.rerun()

        # ── DROP COLUMN ──
        with ed4:
            st.markdown(f"<div style='font-weight:700;color:{ACCENT1};margin-bottom:8px;'>🗑️ Drop Column</div>", unsafe_allow_html=True)
            drop_col = st.selectbox("Column:", list(E.columns), key="eda_drop_col")
            if st.button("Drop Column", key="eda_drop", use_container_width=True):
                st.session_state["_eda_action"]   = "drop_col"
                st.session_state["_eda_drop_col"] = drop_col
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── CHANGE DTYPE ──
        st.markdown(f"<div style='font-weight:700;color:{ACCENT1};margin-bottom:8px;'>🔄 Change Data Type</div>", unsafe_allow_html=True)
        dt1, dt2, dt3 = st.columns(3)
        with dt1: dtype_col = st.selectbox("Column:", list(E.columns), key="eda_dtype_col")
        with dt2: dtype_new = st.selectbox("New Type:", ["int","float","str","datetime"], key="eda_dtype_new")
        with dt3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Change Type", key="eda_dtype_btn", use_container_width=True):
                st.session_state["_eda_action"]    = "change_dtype"
                st.session_state["_eda_dtype_col"] = dtype_col
                st.session_state["_eda_dtype_new"] = dtype_new
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── PREVIEW ──
        st.markdown(f"<div class='section-title'>👁️ Edited Data Preview</div>", unsafe_allow_html=True)
        st.dataframe(st.session_state["eda_df"], use_container_width=True, height=300)

        # ── DOWNLOAD + RESET ──
        dl1, dl2 = st.columns(2)
        with dl1:
            csv_eda = io.StringIO()
            st.session_state["eda_df"].to_csv(csv_eda, index=False)
            st.download_button("Download Edited CSV", csv_eda.getvalue().encode(),
                file_name=f"edited_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True)
        with dl2:
            if st.button("Reset to Original", key="eda_reset", use_container_width=True):
                st.session_state["_eda_action"] = "reset"
                st.rerun()

    # ---- TAB 2: RAW DATA ----
    with tab2:
        st.markdown(f"<div class='section-title'>🗃️ Dataset</div>", unsafe_allow_html=True)
        search = st.text_input("Filter rows:", placeholder="Type to filter...", key="search")
        if search:
            mask = df.astype(str).apply(lambda row: row.str.contains(search, case=False)).any(axis=1)
            st.dataframe(df[mask], use_container_width=True, height=400)
        else:
            st.dataframe(df, use_container_width=True, height=400)
        st.markdown(f"<div class='section-title'>📊 Statistical Summary</div>", unsafe_allow_html=True)
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button("Download Cleaned Data", csv_buf.getvalue().encode(),
            file_name=f"spendsense_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    # ---- TAB 3: DEEP DIVE ----
    with tab3:
        st.markdown(f"<div class='section-title'>🔬 Custom Analysis</div>", unsafe_allow_html=True)
        if len(numeric_cols) >= 2:
            c1, c2 = st.columns(2)
            with c1: x_col = st.selectbox("X Axis:", numeric_cols, key="x_col")
            with c2: y_col = st.selectbox("Y Axis:", numeric_cols, index=min(1, len(numeric_cols)-1), key="y_col")
            color_col = st.selectbox("Color by (optional):", ["None"] + cat_cols, key="color_col")
            color_arg = None if color_col == "None" else color_col
            fig_scatter = px.scatter(df, x=x_col, y=y_col, color=color_arg,
                title=f"{x_col} vs {y_col}", trendline="ols",
                color_discrete_sequence=CHART_COLORS, opacity=0.75)
            fig_scatter.update_layout(**PLOT_TPL)
            st.plotly_chart(fig_scatter, use_container_width=True)

        if cat_cols and numeric_cols:
            st.markdown(f"<div class='section-title'>📦 Distribution by Category</div>", unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            with bc1: box_cat = st.selectbox("Category:", cat_cols, key="box_cat")
            with bc2: box_num = st.selectbox("Numeric:", numeric_cols, key="box_num")
            fig_box = px.box(df, x=box_cat, y=box_num,
                title=f"{box_num} by {box_cat}", color=box_cat,
                color_discrete_sequence=CHART_COLORS)
            fig_box.update_layout(**PLOT_TPL)
            st.plotly_chart(fig_box, use_container_width=True)

    # ---- TAB 6: FORECAST + PDF ----
    with tab6:
        st.markdown(f"<div class='section-title'>📈 Spending Forecast</div>", unsafe_allow_html=True)
        if numeric_cols and "Month" in df.columns:
            fc1, fc2 = st.columns(2)
            with fc1: forecast_col = st.selectbox("Column to forecast:", numeric_cols, key="fc_col")
            with fc2: forecast_months = st.slider("Months ahead:", 1, 6, 3)
            monthly_data = df.groupby("Month")[forecast_col].sum().reset_index().sort_values("Month")
            month_map2   = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            monthly_data["Month_Name"] = monthly_data["Month"].map(month_map2)
            if len(monthly_data) >= 2:
                x      = np.arange(len(monthly_data))
                y      = monthly_data[forecast_col].values
                coeffs = np.polyfit(x, y, 1)
                trend  = np.poly1d(coeffs)
                future_x      = np.arange(len(monthly_data), len(monthly_data) + forecast_months)
                future_y      = trend(future_x)
                last_month    = monthly_data["Month"].iloc[-1]
                future_months = [(last_month + i) % 12 + 1 for i in range(1, forecast_months + 1)]
                future_names  = [month_map2[m] for m in future_months]
                fig_fc = go.Figure()
                fig_fc.add_trace(go.Scatter(x=monthly_data["Month_Name"], y=monthly_data[forecast_col],
                    mode="lines+markers", name="Actual", line=dict(color=ACCENT2, width=3),
                    marker=dict(size=8, color=ACCENT2)))
                fig_fc.add_trace(go.Scatter(x=future_names, y=future_y,
                    mode="lines+markers", name="Forecast", line=dict(color=ACCENT1, width=3, dash="dot"),
                    marker=dict(size=8, color=ACCENT1, symbol="diamond")))
                fig_fc.update_layout(title=f"{forecast_col} — {forecast_months} Month Forecast", **PLOT_TPL)
                st.plotly_chart(fig_fc, use_container_width=True)
                avg_actual   = y.mean()
                avg_forecast = future_y.mean()
                trend_dir    = "📈 Increasing" if coeffs[0] > 0 else "📉 Decreasing"
                change_pct   = ((avg_forecast - avg_actual) / avg_actual * 100) if avg_actual else 0
                fs1, fs2, fs3 = st.columns(3)
                for cw, (icon, val, lbl, clr) in zip([fs1,fs2,fs3], [
                    ("📊", f"{CURR_SYMBOL} {avg_actual:,.0f}",   "Avg Monthly (Actual)",   ACCENT2),
                    ("🔮", f"{CURR_SYMBOL} {avg_forecast:,.0f}", "Avg Monthly (Forecast)", ACCENT1),
                    ("📉", f"{change_pct:+.1f}%",     "Expected Change",        ACCENT3 if change_pct < 0 else "#f87171"),
                ]):
                    with cw:
                        st.markdown(f"""
                        <div class='metric-card' style='text-align:center;'>
                            <div style='font-size:1.5rem;margin-bottom:8px;'>{icon}</div>
                            <div style='font-size:1.4rem;font-weight:800;color:{clr};'>{val}</div>
                            <div class='metric-label'>{lbl}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class='ai-response' style='margin-top:16px;'>
                    <div style='font-weight:700;color:{ACCENT1};margin-bottom:8px;'>📊 Trend Summary</div>
                    <b>Direction:</b> {trend_dir} &nbsp;·&nbsp;
                    <b>Monthly Change:</b> {CURR_SYMBOL} {abs(coeffs[0]):,.0f}/month &nbsp;·&nbsp;
                    <b>Next Month Est.:</b> {CURR_SYMBOL} {trend(len(monthly_data)):,.0f}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("📅 At least 2 months of data is required for forecasting.")
        else:
            st.info("📅 Please upload a CSV with a date column to use the forecast feature.")

        # PDF EXPORT
        st.markdown(f"<div class='section-title'>🖨️ Export PDF Report</div>", unsafe_allow_html=True)
        if st.button("Generate PDF Report", use_container_width=True):
            if not PDF_AVAILABLE:
                st.error("Please run: pip install fpdf2 to enable PDF export.")
            else:
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.set_font("Helvetica", "B", 22)
                    pdf.set_text_color(99, 102, 241)
                    pdf.cell(0, 14, "SpendSense AI - Expense Report", ln=True, align="C")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(120, 120, 150)
                    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", ln=True, align="C")
                    pdf.ln(4)
                    pdf.set_draw_color(99, 102, 241)
                    pdf.set_line_width(0.8)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(6)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.set_text_color(30, 30, 60)
                    pdf.cell(0, 10, "Dataset Overview", ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(60, 60, 80)
                    pdf.cell(0, 7, f"Records: {df.shape[0]}  |  Columns: {df.shape[1]}  |  Numeric: {len(numeric_cols)}", ln=True)
                    if "Year" in df.columns:
                        pdf.cell(0, 7, f"Date Range: {int(df['Year'].min())} - {int(df['Year'].max())}", ln=True)
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.set_text_color(30, 30, 60)
                    pdf.cell(0, 10, "Numeric Summary", ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(60, 60, 80)
                    for col in numeric_cols[:6]:
                        pdf.cell(0, 7, f"{col}: Total={df[col].sum():,.0f}  Avg={df[col].mean():,.0f}  Max={df[col].max():,.0f}", ln=True)
                    pdf.ln(4)
                    if cat_cols:
                        pdf.set_font("Helvetica", "B", 13)
                        pdf.set_text_color(30, 30, 60)
                        pdf.cell(0, 10, "Category Breakdown", ln=True)
                        for col in cat_cols[:2]:
                            pdf.set_font("Helvetica", "B", 10)
                            pdf.set_text_color(60, 60, 80)
                            pdf.cell(0, 7, f"{col}:", ln=True)
                            pdf.set_font("Helvetica", "", 10)
                            for val, cnt in df[col].value_counts().head(5).items():
                                pdf.cell(0, 6, f"   {val}: {cnt} records", ln=True)
                        pdf.ln(4)
                    ai_sections = {"overview":"Overview","savings":"Savings Tips","income":"Income Ideas","warnings":"Red Flags"}
                    if any(f"ai_result_{k}" in st.session_state for k in ai_sections):
                        pdf.set_font("Helvetica", "B", 13)
                        pdf.set_text_color(30, 30, 60)
                        pdf.cell(0, 10, "AI Insights", ln=True)
                        for k, title in ai_sections.items():
                            if f"ai_result_{k}" in st.session_state:
                                pdf.set_font("Helvetica", "B", 11)
                                pdf.set_text_color(99, 102, 241)
                                pdf.cell(0, 8, title, ln=True)
                                pdf.set_font("Helvetica", "", 9)
                                pdf.set_text_color(60, 60, 80)
                                txt = st.session_state[f"ai_result_{k}"].encode("latin-1","replace").decode("latin-1")
                                pdf.multi_cell(0, 6, txt)
                                pdf.ln(2)
                    pdf.set_y(-18)
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(150, 150, 170)
                    pdf.cell(0, 8, "Generated by SpendSense AI  |  Powered by Groq", align="C")
                    pdf_buf = io.BytesIO()
                    pdf_buf.write(pdf.output())
                    pdf_buf.seek(0)
                    st.success("✅ PDF ready!")
                    st.download_button("Download PDF Report", pdf_buf,
                        file_name=f"spendsense_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"PDF Error: {str(e)}")

