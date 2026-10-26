"""DataForge Studio - Modern CSV Sanitizer and Pydantic Schema Validator."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import pandas as pd
import streamlit as st

from src.cleaner import (
    audit_cleaning,
    dataframe_to_csv_bytes,
    dataframe_to_json_bytes,
    generate_markdown_audit_report,
)
from src.models import CleaningOptions

# -----------------------------------------------------------------------------
# Streamlit Application Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DataForge Studio | Smart CSV Cleaner & Schema Validator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Bespoke Nordic-Emerald & Obsidian Theme Styling
# -----------------------------------------------------------------------------
STUDIO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', -apple-system, sans-serif;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Studio Hero Header */
.forge-header {
    background: radial-gradient(120% 120% at 50% 0%, rgba(16, 185, 129, 0.15) 0%, rgba(20, 184, 166, 0.05) 50%, rgba(9, 13, 22, 0.95) 100%);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 20px;
    padding: 30px 36px;
    margin-bottom: 24px;
    box-shadow: 0 12px 36px -12px rgba(0, 0, 0, 0.5);
    position: relative;
    overflow: hidden;
}

.forge-status-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}

.engine-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.pydantic-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(6, 182, 212, 0.15);
    border: 1px solid rgba(6, 182, 212, 0.35);
    color: #22d3ee;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.forge-title {
    font-size: 2.3rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    margin: 0 0 8px 0;
    color: #f8fafc;
}

.forge-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    margin: 0;
    font-weight: 400;
    line-height: 1.6;
    max-width: 900px;
}

/* Bento Metrics Grid */
.bento-card {
    background: #131b2e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 22px;
    position: relative;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.bento-card:hover {
    border-color: rgba(16, 185, 129, 0.4);
    transform: translateY(-2px);
}

.bento-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}

.bento-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.1;
    margin-bottom: 8px;
}

.bento-footer {
    font-size: 0.8rem;
    color: #cbd5e1;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Custom Tag Badges */
.tag-emerald {
    color: #34d399;
    font-weight: 600;
}
.tag-rose {
    color: #f43f5e;
    font-weight: 600;
}
.tag-cyan {
    color: #38bdf8;
    font-weight: 600;
}

/* Custom File Uploader & Buttons */
[data-testid="stFileUploader"] {
    background: rgba(19, 27, 46, 0.6);
    border: 2px dashed rgba(16, 185, 129, 0.35);
    border-radius: 16px;
    padding: 16px;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: none;
    font-weight: 600;
    border-radius: 10px;
    padding: 10px 20px;
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
}
</style>
"""
st.markdown(STUDIO_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Studio Top Banner
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="forge-header">
        <div class="forge-status-row">
            <span class="engine-chip">⚡ Pipeline Engine v2.0</span>
            <span class="pydantic-badge">🛡️ Pydantic Type-Safe Validator</span>
            <span class="engine-chip" style="color: #cbd5e1; border-color: rgba(255,255,255,0.15); background: rgba(255,255,255,0.05);">🔒 Non-Destructive In-Memory</span>
        </div>
        <h1 class="forge-title">DataForge Studio</h1>
        <p class="forge-subtitle">
            Enterprise CSV sanitization, ghost whitespace pruning, Pydantic type-safe schema validation, and interactive audit reporting.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Sidebar: Cleaning Engine & Pydantic Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Pipeline Configuration")
    st.caption("Customize deduplication, text hygiene, and schema constraints.")

    with st.expander("🧹 1. Deduplication & Pruning", expanded=True):
        remove_empty = st.checkbox(
            "Remove all-blank / whitespace rows",
            value=True,
            help="Purge rows where every single column is empty, NaN, or whitespace-only.",
        )
        remove_duplicates = st.checkbox(
            "Remove exact duplicate rows",
            value=True,
            help="Eliminate identical records, preserving the first occurrence.",
        )

    with st.expander("🛡️ 2. Pydantic Model Validation", expanded=True):
        validate_pydantic = st.checkbox(
            "Enable Pydantic row validation",
            value=True,
            help="Validate data against the ReviewRowModel schema and flag type inconsistencies.",
        )
        enforce_rating_bounds = st.checkbox(
            "Enforce Rating bounds [1.0 - 5.0]",
            value=True,
            help="Flag and purge records whose ratings are invalid or outside 1.0 - 5.0.",
        )

    with st.expander("✨ 3. Text Sanitization", expanded=True):
        trim_whitespace = st.checkbox(
            "Trim leading/trailing spaces",
            value=True,
            help="Strip whitespace from strings without mutating non-string types.",
        )
        collapse_spaces = st.checkbox(
            "Collapse multiple spaces / tabs",
            value=True,
            help="Replace repeated spaces and tab characters with a single space.",
        )
        strip_html = st.checkbox(
            "Strip embedded HTML tags",
            value=True,
            help="Remove tags like <p>, <br>, or <b> frequently found in web reviews.",
        )

    st.markdown("---")
    st.markdown("### ℹ️ Engine Information")
    st.caption(
        "Built with **Python 3.12**, **Pandas**, and **Pydantic v2**. "
        "Safe and memory-isolated."
    )


# -----------------------------------------------------------------------------
# File Ingestion & Demo Data Loader
# -----------------------------------------------------------------------------
col_uploader, col_demo_actions = st.columns([3, 1])

with col_uploader:
    uploaded_file = st.file_uploader(
        "Upload Customer Reviews (.csv)",
        type=["csv"],
        help="Upload any standard CSV file containing review or customer feedback data.",
    )

with col_demo_actions:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    demo_clicked = st.button("⚡ Load Demo Reviews", use_container_width=True, help="Load messy sample dataset (16 rows)")
    reset_clicked = st.button("🔄 Reset Workspace", use_container_width=True)

if "active_demo" not in st.session_state:
    st.session_state.active_demo = False

if demo_clicked:
    st.session_state.active_demo = True
    st.toast("Loaded sample customer reviews dataset!", icon="⚡")

if reset_clicked:
    st.session_state.active_demo = False
    st.rerun()

# Resolve Active Dataset
active_df: pd.DataFrame | None = None
source_name = ""

if uploaded_file is not None:
    try:
        active_df = pd.read_csv(uploaded_file)
        source_name = uploaded_file.name
    except Exception as exc:
        st.error(f"⚠️ Error reading CSV: {exc}")
        st.stop()
elif st.session_state.active_demo:
    sample_file = Path("data/sample_reviews.csv")
    if sample_file.exists():
        active_df = pd.read_csv(sample_file)
        source_name = "sample_reviews.csv"
    else:
        st.warning("Sample dataset not found at data/sample_reviews.csv")


# -----------------------------------------------------------------------------
# Dynamic Column Scope Configuration
# -----------------------------------------------------------------------------
key_columns: list[str] = []
required_col: str | None = None

if active_df is not None:
    with st.sidebar:
        with st.expander("🎯 4. Column Scope (Optional)", expanded=False):
            key_columns = st.multiselect(
                "Deduplicate by specific key columns:",
                options=list(active_df.columns),
                default=[],
                help="If selected, duplicates are matched only against these columns. Leave blank for all columns.",
            )
            selected_req = st.selectbox(
                "Require non-empty value in:",
                options=["(None)"] + list(active_df.columns),
                index=0,
                help="Purge rows where this specific column is empty or whitespace.",
            )
            required_col = selected_req if selected_req != "(None)" else None


# -----------------------------------------------------------------------------
# Processing Engine & Visual Dashboard
# -----------------------------------------------------------------------------
if active_df is not None:
    # Build options
    pipeline_options = CleaningOptions(
        remove_empty_rows=remove_empty,
        remove_duplicates=remove_duplicates,
        trim_whitespace=trim_whitespace,
        collapse_spaces=collapse_spaces,
        strip_html=strip_html,
        validate_with_pydantic=validate_pydantic,
        enforce_rating_bounds=enforce_rating_bounds,
        key_columns=key_columns,
        required_column=required_col,
    )

    # Execute cleaning pipeline
    cleaned_df, removed_df, stats = audit_cleaning(active_df, pipeline_options)

    # -------------------------------------------------------------------------
    # Bento Metric KPI Cards
    # -------------------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            f"""
            <div class="bento-card">
                <div class="bento-label">Raw Records</div>
                <div class="bento-value">{stats.original_rows:,}</div>
                <div class="bento-footer"><span class="tag-cyan">●</span> {len(active_df.columns)} columns detected</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="bento-card">
                <div class="bento-label">Clean Retained</div>
                <div class="bento-value">{stats.cleaned_rows:,}</div>
                <div class="bento-footer"><span class="tag-emerald">↑</span> {stats.retention_rate:.1f}% dataset retention</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        st.markdown(
            f"""
            <div class="bento-card">
                <div class="bento-label">Purged Records</div>
                <div class="bento-value">{stats.removed_rows:,}</div>
                <div class="bento-footer"><span class="tag-rose">↓</span> {stats.removed_rows} rows sanitized</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        score_tag = "tag-emerald" if stats.data_quality_score >= 80 else ("tag-cyan" if stats.data_quality_score >= 60 else "tag-rose")
        st.markdown(
            f"""
            <div class="bento-card">
                <div class="bento-label">Quality Score</div>
                <div class="bento-value">{stats.data_quality_score:.0f}<span style="font-size:1.1rem; color:#64748b;">/100</span></div>
                <div class="bento-footer"><span class="{score_tag}">●</span> Pydantic integrity verified</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Quick Export Toolbar
    # -------------------------------------------------------------------------
    stem = Path(source_name).stem if source_name else "dataset"
    btn1, btn2, btn3, btn4 = st.columns(4)

    with btn1:
        st.download_button(
            "⬇️ Download Cleaned CSV",
            data=dataframe_to_csv_bytes(cleaned_df),
            file_name=f"{stem}_cleaned.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with btn2:
        st.download_button(
            "📄 Export Cleaned JSON",
            data=dataframe_to_json_bytes(cleaned_df),
            file_name=f"{stem}_cleaned.json",
            mime="application/json",
            use_container_width=True,
        )
    with btn3:
        if not removed_df.empty:
            st.download_button(
                "🛡️ Download Removed Audit CSV",
                data=dataframe_to_csv_bytes(removed_df),
                file_name=f"{stem}_removed_audit.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("🛡️ Download Removed Audit CSV", disabled=True, use_container_width=True)
    with btn4:
        report_md = generate_markdown_audit_report(stats, source_name)
        st.download_button(
            "📝 Download Audit Report (.md)",
            data=report_md.encode("utf-8"),
            file_name=f"{stem}_audit_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Workspace Tabs
    # -------------------------------------------------------------------------
    tab_analytics, tab_diff, tab_audit, tab_report = st.tabs(
        [
            "📊 Studio Analytics",
            "🔬 Diff & Inspection Matrix",
            f"🛡️ Pydantic & Removed Log ({stats.removed_rows})",
            "📜 Executive Audit Report",
        ]
    )

    # TAB 1: Studio Analytics
    with tab_analytics:
        col_flow, col_reasons = st.columns(2)

        with col_flow:
            st.markdown("##### 📈 Dataset Flow Breakdown")
            chart_df = pd.DataFrame(
                {
                    "Status": ["Clean Retained", "Purged Records"],
                    "Count": [stats.cleaned_rows, stats.removed_rows],
                }
            )
            st.bar_chart(chart_df, x="Status", y="Count", color="Status", use_container_width=True)

        with col_reasons:
            st.markdown("##### 🔍 Removal Breakdown by Reason")
            if stats.removal_breakdown:
                reasons_df = pd.DataFrame(
                    [{"Reason": k, "Rows": v} for k, v in stats.removal_breakdown.items()]
                )
                st.bar_chart(reasons_df, x="Reason", y="Rows", color="#f43f5e", use_container_width=True)
            else:
                st.success("✅ Zero records purged! The entire dataset satisfied all quality constraints.")

        # Rating Distribution if rating column exists
        rating_col = next((c for c in cleaned_df.columns if "rating" in c.lower() or "score" in c.lower() or "star" in c.lower()), None)
        if rating_col:
            st.markdown("##### ⭐ Star Rating Distribution (Clean Dataset)")
            r1, r2 = st.columns([2, 1])
            with r1:
                r_counts = cleaned_df[rating_col].value_counts().sort_index().reset_index()
                r_counts.columns = ["Rating", "Reviews"]
                st.bar_chart(r_counts, x="Rating", y="Reviews", color="#10b981", use_container_width=True)
            with r2:
                numeric_r = pd.to_numeric(cleaned_df[rating_col], errors="coerce").dropna()
                if not numeric_r.empty:
                    st.metric("Average Rating", f"{numeric_r.mean():.2f} / 5.0")
                    st.metric("5-Star Reviews", f"{(numeric_r == 5).sum():,}")
                    st.metric("Critical Reviews (≤ 2)", f"{(numeric_r <= 2).sum():,}")

    # TAB 2: Diff & Inspection Matrix
    with tab_diff:
        st.markdown("##### 🔬 Side-by-Side Data Matrix")
        search_kw = st.text_input("🔍 Live Keyword Filter:", placeholder="Search by customer, review text, or rating...")
        limit_rows = st.slider("Rows to Preview:", min_value=5, max_value=min(100, max(10, stats.original_rows)), value=min(15, stats.original_rows))

        orig_view = active_df.copy()
        clean_view = cleaned_df.copy()

        if search_kw.strip():
            kw = search_kw.strip().lower()
            orig_view = orig_view[orig_view.astype(str).apply(lambda row: row.str.lower().str.contains(kw, regex=False)).any(axis=1)]
            clean_view = clean_view[clean_view.astype(str).apply(lambda row: row.str.lower().str.contains(kw, regex=False)).any(axis=1)]

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown(f"**Original Dataset** (`{len(orig_view)}` matching rows)")
            st.dataframe(orig_view.head(limit_rows), use_container_width=True)

        with c_right:
            st.markdown(f"**Cleaned Dataset** (`{len(clean_view)}` matching rows)")
            st.dataframe(clean_view.head(limit_rows), use_container_width=True)

    # TAB 3: Pydantic Validation & Audit Log
    with tab_audit:
        st.markdown("##### 🛡️ Audit Table of Purged Records")
        if not removed_df.empty:
            st.caption("Each purged row below includes the exact reason it failed quality or schema constraints.")
            st.dataframe(removed_df, use_container_width=True)
        else:
            st.info("✨ No records were purged. Your dataset satisfies all quality constraints.")

    # TAB 4: Executive Audit Report
    with tab_report:
        st.markdown(report_md)

else:
    # Empty State Guide Cards
    st.markdown("### 🚀 Get Started")
    st.markdown(
        """
        Upload your customer reviews CSV using the file uploader above, or click **⚡ Load Demo Reviews** to run with sample data.
        """
    )
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(
            """
            <div class="bento-card">
                <div class="bento-label">1. Automatic Sanitization</div>
                <p style="color:#cbd5e1; font-size:0.92rem;">
                    Identifies ghost whitespace, empty rows, and redundant duplicate rows across any CSV schema.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g2:
        st.markdown(
            """
            <div class="bento-card">
                <div class="bento-label">2. Pydantic v2 Integrity</div>
                <p style="color:#cbd5e1; font-size:0.92rem;">
                    Validates customer names, rating bounds (1.0 to 5.0), and strips embedded HTML tags automatically.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g3:
        st.markdown(
            """
            <div class="bento-card">
                <div class="bento-label">3. Audit & Multi-Export</div>
                <p style="color:#cbd5e1; font-size:0.92rem;">
                    Export cleaned records in CSV or JSON, review purged records with reasons, and download an audit report.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
