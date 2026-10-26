"""PydanClean Studio - Modern CSV Sanitizer and Pydantic Schema Validation Suite."""

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
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PydanClean Studio | Smart CSV & Pydantic Sanitizer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Bespoke Titanium & Sunset Flame UI Theme Styling
# -----------------------------------------------------------------------------
BESPOKE_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    background-color: #141517;
    color: #F4F5F7;
}

code, pre, .mono {
    font-family: 'Fira Code', monospace !important;
}

/* Minimalist Studio Top Bar */
.studio-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #1b1d22;
    border: 1px solid rgba(255, 107, 53, 0.25);
    border-radius: 14px;
    padding: 16px 24px;
    margin-bottom: 22px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.studio-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.studio-logo {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #FF6B35 0%, #F97316 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1.25rem;
    color: #FFFFFF;
    box-shadow: 0 0 16px rgba(255, 107, 53, 0.4);
}

.studio-title-block h1 {
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.02em;
    color: #FFFFFF;
}

.studio-title-block p {
    font-size: 0.82rem;
    color: #9EACB9;
    margin: 0;
}

.studio-tags {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-chip {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.chip-flame {
    background: rgba(255, 107, 53, 0.15);
    border: 1px solid rgba(255, 107, 53, 0.4);
    color: #FF8A50;
}

.chip-gold {
    background: rgba(255, 184, 0, 0.15);
    border: 1px solid rgba(255, 184, 0, 0.35);
    color: #FFC72C;
}

.chip-muted {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #CBD5E1;
}

/* Executive Metric Ribbon */
.metric-ribbon {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    background: #1b1d22;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 20px;
}

.metric-node {
    padding: 0 10px;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.metric-node:last-child {
    border-right: none;
}

.node-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #9EACB9;
    margin-bottom: 4px;
}

.node-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.1;
    margin-bottom: 4px;
}

.node-sub {
    font-size: 0.78rem;
    font-weight: 600;
}

.text-flame { color: #FF6B35; }
.text-gold { color: #FFC72C; }
.text-green { color: #10B981; }
.text-rose { color: #F43F5E; }

/* Workbench View Card */
.workbench-card {
    background: #1b1d22;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
}

/* Rule Card for Schema Diagnostics */
.rule-card {
    background: #22252B;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}

.rule-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 700;
    font-size: 0.95rem;
    color: #FFFFFF;
    margin-bottom: 4px;
}

.rule-body {
    font-size: 0.84rem;
    color: #9EACB9;
    line-height: 1.4;
}

/* Custom Primary Button with Flame Gradient */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FF6B35 0%, #EA580C 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    box-shadow: 0 4px 16px rgba(255, 107, 53, 0.35) !important;
    transition: all 0.2s ease !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 22px rgba(255, 107, 53, 0.5) !important;
}

/* Custom Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1b1d22;
    border-radius: 10px;
    padding: 4px 6px;
    gap: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #9EACB9;
    border: none;
}

.stTabs [aria-selected="true"] {
    background: rgba(255, 107, 53, 0.2) !important;
    color: #FF8A50 !important;
    border: 1px solid rgba(255, 107, 53, 0.4) !important;
}

/* File Uploader Customization */
[data-testid="stFileUploader"] {
    background: #1b1d22;
    border: 2px dashed rgba(255, 107, 53, 0.3);
    border-radius: 14px;
    padding: 14px;
}
</style>
"""
st.markdown(BESPOKE_THEME_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Top Navigation Header
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="studio-nav">
        <div class="studio-brand">
            <div class="studio-logo">◈</div>
            <div class="studio-title-block">
                <h1>PydanClean Studio</h1>
                <p>Enterprise CSV Sanitization & Pydantic Schema Validation Suite</p>
            </div>
        </div>
        <div class="studio-tags">
            <span class="status-chip chip-flame">⚡ Pydantic v2 Engine</span>
            <span class="status-chip chip-gold">🛡️ Type-Safe</span>
            <span class="status-chip chip-muted">🔒 Safe In-Memory</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Sidebar Configuration Engine
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛠️ Cleaning Pipeline Controls")
    st.caption("Configure precision filtering, schema checks, and text hygiene.")

    with st.expander("🧹 1. Deduplication & Pruning", expanded=True):
        remove_empty = st.checkbox(
            "Prune all-blank / whitespace rows",
            value=True,
            help="Purge rows where all columns contain only empty strings, whitespace, or nulls.",
        )
        remove_duplicates = st.checkbox(
            "Prune exact duplicate rows",
            value=True,
            help="Drop redundant duplicate records while keeping the initial entry.",
        )

    with st.expander("🛡️ 2. Pydantic Model Validation", expanded=True):
        validate_pydantic = st.checkbox(
            "Enforce Pydantic schema validation",
            value=True,
            help="Validate customer review schemas via ReviewRowModel.",
        )
        enforce_rating_bounds = st.checkbox(
            "Strict Rating bounds [1.0 - 5.0]",
            value=True,
            help="Flag and purge records with ratings outside the range 1.0 to 5.0.",
        )

    with st.expander("✨ 3. Text Sanitization Rules", expanded=True):
        trim_whitespace = st.checkbox(
            "Trim leading & trailing spaces",
            value=True,
            help="Strip edge whitespace from all text columns.",
        )
        collapse_spaces = st.checkbox(
            "Collapse consecutive whitespace",
            value=True,
            help="Normalize multiple repeated spaces and tab characters to a single space.",
        )
        strip_html = st.checkbox(
            "Strip embedded HTML tags",
            value=True,
            help="Clean tags such as <p>, <br>, or <div> from feedback comments.",
        )

    st.markdown("---")
    st.caption("PydanClean Studio • Built with Python 3.12, Pandas, and Pydantic v2")


# -----------------------------------------------------------------------------
# Ingestion Strip & Demo Loader
# -----------------------------------------------------------------------------
col_upload, col_quick_actions = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload Customer Reviews CSV",
        type=["csv"],
        help="Upload any CSV file to clean and validate.",
    )

with col_quick_actions:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    demo_btn = st.button("◈ Load Demo Reviews", use_container_width=True, help="Load messy sample reviews (16 rows)")
    reset_btn = st.button("↺ Reset Studio", use_container_width=True)

if "active_demo" not in st.session_state:
    st.session_state.active_demo = False

if demo_btn:
    st.session_state.active_demo = True
    st.toast("Loaded sample customer review dataset!", icon="◈")

if reset_btn:
    st.session_state.active_demo = False
    st.rerun()

# Determine active dataset
active_df: pd.DataFrame | None = None
source_name = ""

if uploaded_file is not None:
    try:
        active_df = pd.read_csv(uploaded_file)
        source_name = uploaded_file.name
    except Exception as exc:
        st.error(f"Failed to parse CSV file: {exc}")
        st.stop()
elif st.session_state.active_demo:
    sample_file = Path("data/sample_reviews.csv")
    if sample_file.exists():
        active_df = pd.read_csv(sample_file)
        source_name = "sample_reviews.csv"
    else:
        st.warning("Sample dataset not found at data/sample_reviews.csv")


# -----------------------------------------------------------------------------
# Dynamic Column Settings (Sidebar)
# -----------------------------------------------------------------------------
key_columns: list[str] = []
required_col: str | None = None

if active_df is not None:
    with st.sidebar:
        with st.expander("🎯 4. Target Column Scopes", expanded=False):
            key_columns = st.multiselect(
                "Deduplicate on key columns only:",
                options=list(active_df.columns),
                default=[],
                help="Evaluate duplicates only on the chosen columns.",
            )
            selected_req = st.selectbox(
                "Mandatory non-empty column:",
                options=["(None)"] + list(active_df.columns),
                index=0,
                help="Drop rows if this column is blank.",
            )
            required_col = selected_req if selected_req != "(None)" else None


# -----------------------------------------------------------------------------
# Main Processing & Display
# -----------------------------------------------------------------------------
if active_df is not None:
    # Configure pipeline options
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

    # Process data
    cleaned_df, removed_df, stats = audit_cleaning(active_df, pipeline_options)

    # -------------------------------------------------------------------------
    # Executive Metric Ribbon
    # -------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="metric-ribbon">
            <div class="metric-node">
                <div class="node-label">Raw Ingestion</div>
                <div class="node-value">{stats.original_rows:,}</div>
                <div class="node-sub text-gold">{len(active_df.columns)} Columns Detected</div>
            </div>
            <div class="metric-node">
                <div class="node-label">Clean Retained</div>
                <div class="node-value">{stats.cleaned_rows:,}</div>
                <div class="node-sub text-green">✓ {stats.retention_rate:.1f}% Yield Retained</div>
            </div>
            <div class="metric-node">
                <div class="node-label">Purged Rows</div>
                <div class="node-value">{stats.removed_rows:,}</div>
                <div class="node-sub text-rose">✕ {stats.removed_rows} Records Cleaned</div>
            </div>
            <div class="metric-node">
                <div class="node-label">Pydantic Health</div>
                <div class="node-value">{stats.data_quality_score:.0f}<span style="font-size:1rem; color:#6B7280;">/100</span></div>
                <div class="node-sub text-flame">● Schema Integrity High</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Studio Tabs
    # -------------------------------------------------------------------------
    tab_workbench, tab_schema, tab_analytics, tab_export = st.tabs(
        [
            "📁 Unified Data Workbench",
            "🛡️ Pydantic Schema Diagnostics",
            "📊 Quality & Yield Analytics",
            "📦 Export & Audit Center",
        ]
    )

    # TAB 1: Unified Data Workbench
    with tab_workbench:
        st.markdown("#### 📁 Interactive Data Workbench")
        filter_col, mode_col, limit_col = st.columns([2, 1.2, 1])

        with mode_col:
            view_mode = st.radio(
                "Display Slice:",
                options=["Clean Records", "Purged Audit", "Raw Input"],
                horizontal=True,
            )

        with filter_col:
            search_query = st.text_input("🔍 Live Search Filter:", placeholder="Search by customer, rating, or text...")

        with limit_col:
            row_limit = st.slider("Display Limit:", min_value=5, max_value=min(100, max(10, stats.original_rows)), value=min(15, stats.original_rows))

        # Select data slice
        if view_mode == "Clean Records":
            target_slice = cleaned_df.copy()
            slice_title = f"Clean Records ({len(cleaned_df)} total)"
        elif view_mode == "Purged Audit":
            target_slice = removed_df.copy()
            slice_title = f"Purged Audit Records ({len(removed_df)} total)"
        else:
            target_slice = active_df.copy()
            slice_title = f"Raw Ingestion Records ({len(active_df)} total)"

        if search_query.strip():
            q = search_query.strip().lower()
            mask = target_slice.astype(str).apply(lambda row: row.str.lower().str.contains(q, regex=False)).any(axis=1)
            target_slice = target_slice[mask]

        st.caption(f"Showing **{slice_title}** • {len(target_slice)} rows matching filter")
        st.dataframe(target_slice.head(row_limit), use_container_width=True)

    # TAB 2: Pydantic Schema Diagnostics
    with tab_schema:
        st.markdown("#### 🛡️ Pydantic v2 Schema Constraints & Error Inspector")
        st.caption("Records are checked against the following type-safe specifications:")

        col_rules_left, col_rules_right = st.columns(2)

        with col_rules_left:
            st.markdown(
                """
                <div class="rule-card">
                    <div class="rule-header"><span>1. review_id</span><span class="text-flame">string / optional</span></div>
                    <div class="rule-body">Strips whitespace; casts empty values and 'nan' strings to None.</div>
                </div>
                <div class="rule-card">
                    <div class="rule-header"><span>2. customer_name</span><span class="text-gold">string (Title Case)</span></div>
                    <div class="rule-body">Normalizes names and standardizes capitalization automatically.</div>
                </div>
                <div class="rule-card">
                    <div class="rule-header"><span>3. rating</span><span class="text-green">float [1.0 - 5.0]</span></div>
                    <div class="rule-body">Numeric coercion; enforces valid ratings within 1.0 to 5.0 bounds.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_rules_right:
            st.markdown(
                """
                <div class="rule-card">
                    <div class="rule-header"><span>4. review_text</span><span class="text-flame">sanitized text</span></div>
                    <div class="rule-body">Strips HTML tags (<p>, <br>, etc.) and collapses repeated whitespace.</div>
                </div>
                <div class="rule-card">
                    <div class="rule-header"><span>5. review_date</span><span class="text-gold">string / date</span></div>
                    <div class="rule-body">Trims surrounding spaces and verifies string date formats.</div>
                </div>
                <div class="rule-card">
                    <div class="rule-header"><span>6. Row Completeness</span><span class="text-rose">anti-ghost rule</span></div>
                    <div class="rule-body">Purges records where every field evaluates to empty or space-only.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("##### 🔍 Detected Purge & Validation Exceptions")
        if not removed_df.empty:
            st.dataframe(removed_df[["removal_reason"] + [c for c in removed_df.columns if c != "removal_reason"]], use_container_width=True)
        else:
            st.success("No validation errors or purge exceptions were triggered!")

    # TAB 3: Quality & Yield Analytics
    with tab_analytics:
        st.markdown("#### 📊 Quality Metrics & Distribution Profiling")
        chart_c1, chart_c2 = st.columns(2)

        with chart_c1:
            st.markdown("##### 📈 Yield Breakdown")
            yield_data = pd.DataFrame(
                {
                    "Category": ["Clean Retained", "Purged Rows"],
                    "Count": [stats.cleaned_rows, stats.removed_rows],
                }
            )
            st.bar_chart(yield_data, x="Category", y="Count", color="Category", use_container_width=True)

        with chart_c2:
            st.markdown("##### 🔍 Removal Breakdown by Category")
            if stats.removal_breakdown:
                reasons_df = pd.DataFrame(
                    [{"Reason": k, "Count": v} for k, v in stats.removal_breakdown.items()]
                )
                st.bar_chart(reasons_df, x="Reason", y="Count", color="#FF6B35", use_container_width=True)
            else:
                st.info("No records removed; all rows met the quality threshold.")

        # Ratings histogram
        rating_col = next((c for c in cleaned_df.columns if "rating" in c.lower() or "score" in c.lower() or "star" in c.lower()), None)
        if rating_col:
            st.markdown("##### ⭐ Star Rating Distribution (Clean Dataset)")
            r_left, r_right = st.columns([2, 1])
            with r_left:
                rating_counts = cleaned_df[rating_col].value_counts().sort_index().reset_index()
                rating_counts.columns = ["Rating", "Count"]
                st.bar_chart(rating_counts, x="Rating", y="Count", color="#FF8A50", use_container_width=True)
            with r_right:
                numeric_ratings = pd.to_numeric(cleaned_df[rating_col], errors="coerce").dropna()
                if not numeric_ratings.empty:
                    st.metric("Average Rating", f"{numeric_ratings.mean():.2f} / 5.0")
                    st.metric("5-Star Reviews", f"{(numeric_ratings == 5).sum():,}")
                    st.metric("Critical (≤ 2.0)", f"{(numeric_ratings <= 2).sum():,}")

    # TAB 4: Export & Audit Center
    with tab_export:
        st.markdown("#### 📦 Export Center & Compliance Documentation")
        stem = Path(source_name).stem if source_name else "dataset"

        e1, e2, e3 = st.columns(3)
        with e1:
            st.download_button(
                "⬇️ Download Cleaned CSV",
                data=dataframe_to_csv_bytes(cleaned_df),
                file_name=f"{stem}_clean.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
        with e2:
            st.download_button(
                "📄 Export Cleaned JSON",
                data=dataframe_to_json_bytes(cleaned_df),
                file_name=f"{stem}_clean.json",
                mime="application/json",
                use_container_width=True,
            )
        with e3:
            if not removed_df.empty:
                st.download_button(
                    "🛡️ Export Purged Audit CSV",
                    data=dataframe_to_csv_bytes(removed_df),
                    file_name=f"{stem}_purged_audit.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.button("🛡️ Export Purged Audit CSV", disabled=True, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📝 Executive Markdown Audit Report")
        audit_md = generate_markdown_audit_report(stats, source_name)
        st.download_button(
            "📋 Download Full Audit Report (.md)",
            data=audit_md.encode("utf-8"),
            file_name=f"{stem}_audit_report.md",
            mime="text/markdown",
            use_container_width=False,
        )
        with st.expander("Preview Audit Report", expanded=True):
            st.markdown(audit_md)

else:
    # Initial State Guide
    st.markdown(
        """
        <div style="background: #1b1d22; border: 1px dashed rgba(255, 107, 53, 0.4); border-radius: 14px; padding: 36px; text-align: center;">
            <h3 style="color: #FFFFFF; margin-bottom: 8px;">Ready for Ingestion</h3>
            <p style="color: #9EACB9; max-width: 650px; margin: 0 auto 20px auto; font-size: 0.95rem;">
                Upload your customer reviews CSV or click <strong>◈ Load Demo Reviews</strong> to inspect how Pydantic v2 cleans whitespace, eliminates duplicates, and validates schema constraints.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
