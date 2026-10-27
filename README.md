# PydanClean Studio (CSV-Cleaner)

An enterprise-grade, high-performance customer reviews CSV sanitization and schema validation suite powered by **Python 3.12**, **Pandas**, **Pydantic v2**, and **Streamlit**.

---

## 🎯 Overview & Key Capabilities

**PydanClean Studio** combines deterministic Python data hygiene with modern type-safe Pydantic schema validation and an interactive visual dashboard:

1. **Deterministic Core Cleaning Engine**:
   - Drops rows where every field is empty, null, or whitespace-only.
   - Eliminates duplicate rows across all columns or user-specified key subsets.
   - Non-destructive processing (original data is never mutated; returns a fresh copy with a reset index).
   - Built-in `@retry` resilience decorator applied directly to file I/O operations ([`read_csv_safely`](file:///src/cleaner.py) and [`save_cleaned_data`](file:///src/cleaner.py)) to withstand transient disk lock contention on Windows or network filesystems.

2. **Pydantic v2 Type-Safe Schema Validation**:
   - Enforces the [`ReviewRowModel`](file:///src/models.py) schema on each record:
     - **`review_id`**: String identifier; strips whitespace and normalizes empty strings to `None`.
     - **`customer_name`**: Automatically standardizes casing to **Title Case** and strips padding.
     - **`rating`**: Strict float coercion enforcing valid ratings between `1.0` and `5.0`.
     - **`review_text`**: Strips embedded HTML tags (`<p>`, `<br>`, `<b>`) and collapses repeated spaces/tabs.
     - **`review_date`**: Trims edge whitespace.
     - **Anti-Ghost Validation**: Discards rows where all fields evaluate to empty.

3. **Interactive Visual Dashboard (`app.py`)**:
   - **Bespoke UI Theme**: Modern Titanium Charcoal (`#141517`) & Sunset Flame Coral (`#FF6B35`) with Gold accents (`#FFB800`).
   - **Executive Metric Ribbon**: Instant KPI nodes for Raw Ingestion, Clean Retained rows, Purged Records, and Pydantic Health Score.
   - **Unified Data Workbench**: Segmented view switcher (`[Clean Records]` / `[Purged Audit]` / `[Raw Input]`) with real-time keyword search.
   - **Pydantic Schema Diagnostics**: Real-time inspection of field validation constraints and error logs.
   - **Quality & Yield Analytics**: Visual charts for retention flow, removal reason breakdowns, and rating distribution histograms.
   - **Multi-Format Export Center**: One-click download for Cleaned CSV, Cleaned JSON, Purged Rows Audit CSV, and Executive Markdown Audit Reports.

---

## 📁 Project Architecture

```text
CSV-Cleaner/
├── .streamlit/
│   └── config.toml          # Bespoke Titanium & Sunset Flame theme configuration
├── src/
│   ├── __init__.py
│   ├── models.py            # Pydantic v2 models (ReviewRowModel, CleaningOptions, CleaningStats)
│   └── cleaner.py           # Core cleaning functions, I/O retry wrappers, and audit engine
├── tests/
│   ├── __init__.py
│   └── test_cleaner.py      # 15 comprehensive unit, retry, and Pydantic tests
├── data/
│   └── sample_reviews.csv   # Messy sample reviews dataset (16 rows)
├── app.py                   # Streamlit web application & visual workbench
├── Dockerfile               # Multi-stage container setup for cloud deployment
├── pyproject.toml           # Project manifest and dependency declarations (uv)
├── uv.lock                  # Deterministic cryptographic lockfile
├── requirements.txt         # Standard pip dependency specification
├── .gitignore               # Ignores virtualenvs, caches, secrets, and generated outputs
├── .env.example             # Environment template
└── README.md                # Comprehensive documentation and usage guide
```

---

## ⚙️ Installation & Setup

You can set up the project using either **`uv`** (fastest, recommended) or traditional **`pip`**.

### Option A: Using `uv` (Recommended)
```bash
# Clone the repository
git clone https://github.com/ExplorerPVR/CSV-Cleaner.git
cd CSV-Cleaner

# Sync virtual environment and all dependencies in milliseconds
uv sync
```

### Option B: Using traditional `pip`
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

---

## 🚀 How to Run

### 1. Launch the Interactive Web Studio
```bash
uv run streamlit run app.py
# Or with standard environment activated:
# streamlit run app.py
```
Open your browser at **`http://localhost:8501`**. You can upload any CSV or click **◈ Load Demo Reviews** to test immediately.

### 2. Run the Command-Line Pipeline Script
```bash
uv run python src/cleaner.py
```
**Console Output:**
```text
--> Reading and cleaning reviews from: data/sample_reviews.csv
--> Success! 9 cleaned rows written to: data/cleaned_reviews.csv
```

### 3. Run the Full Test Suite
```bash
uv run pytest -v
```

All 15 tests will execute and pass:
```text
collected 15 items

tests/test_cleaner.py::test_retry_succeeds_after_failing PASSED          [  6%]
tests/test_cleaner.py::test_retry_gives_up_after_n_tries PASSED          [ 13%]
tests/test_cleaner.py::test_retry_specific_exception_filter PASSED       [ 20%]
tests/test_cleaner.py::test_retry_invalid_max_retries PASSED             [ 26%]
tests/test_cleaner.py::test_remove_empty_and_whitespace_rows PASSED      [ 33%]
tests/test_cleaner.py::test_remove_duplicate_rows PASSED                 [ 40%]
tests/test_cleaner.py::test_clean_reviews_does_not_mutate_original PASSED [ 46%]
tests/test_cleaner.py::test_save_cleaned_data PASSED                     [ 53%]
tests/test_cleaner.py::test_clean_reviews_file_not_found PASSED          [ 60%]
tests/test_cleaner.py::test_end_to_end_sample_reviews_cleaning PASSED    [ 66%]
tests/test_cleaner.py::test_pydantic_review_model_sanitization PASSED    [ 73%]
tests/test_cleaner.py::test_pydantic_invalid_rating_raises_error PASSED  [ 80%]
tests/test_cleaner.py::test_audit_cleaning_pipeline_with_stats PASSED    [ 86%]
tests/test_cleaner.py::test_dataframe_serialization_bytes PASSED         [ 93%]
tests/test_cleaner.py::test_read_csv_safely_retry_integration PASSED     [100%]

============================= 15 passed in 0.82s ==============================
```

---

## 🛡️ Resilience & File I/O Retry Architecture

The `@retry` decorator provides configurable exponential backoff and exception filtering:

```python
@retry(max_retries=3, delay=0.05, exceptions=(OSError, IOError))
def read_csv_safely(file_path: str | Path) -> pd.DataFrame:
    ...

@retry(max_retries=3, delay=0.05, exceptions=(OSError, IOError))
def save_cleaned_data(df: pd.DataFrame, output_path: str | Path) -> Path:
    ...
```

- **Why file I/O?** Retrying in-memory CPU calculations on static bad data is deterministic (it will fail identically every time). In contrast, filesystem reads and writes on Windows or network storage can encounter temporary file locks (e.g., antivirus scanners, concurrent access). `@retry` ensures seamless automatic recovery.

---

## 🌐 How to Host Anywhere

### 1. Streamlit Community Cloud (Free 1-Click Hosting)
1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
3. Click **"New app"**, choose repository `ExplorerPVR/CSV-Cleaner`, select the `development` branch, and specify `app.py` as the entrypoint.
4. Click **Deploy!**

### 2. Docker Container Deployment (Render, Railway, AWS, VPS)
Build and run the containerized application on any hosting provider:

```bash
# Build the Docker image
docker build -t pydanclean-studio .

# Run container on port 8501
docker run -p 8501:8501 pydanclean-studio
```

---

## 📋 Assignment & Enhancement Checklist

| Requirement | Implementation Detail | Status |
| :--- | :--- | :---: |
| **All-Empty Rows Pruned** | Drops rows where every column is empty, null, or whitespace-only | ✅ Passed |
| **Duplicate Rows Removed** | Eliminates redundant duplicate records while retaining the first occurrence | ✅ Passed |
| **Retry Decorator** | `@retry` decorator supporting `max_retries`, `delay`, `backoff`, and `exceptions` | ✅ Passed |
| **Retry Applied to Code** | Applied to file I/O (`read_csv_safely` and `save_cleaned_data`) to prevent file locks | ✅ Passed |
| **Unit & Integration Tests** | 15 test cases passing via `uv run pytest` (exceeds the 5-test minimum) | ✅ Passed |
| **Pydantic v2 Schema** | Type-safe validation (`ReviewRowModel`) enforcing title case & rating bounds | ✅ Passed |
| **Bespoke Web Frontend** | Streamlit UI with Titanium & Sunset Flame theme, metrics ribbon & workbench | ✅ Passed |
| **Multi-Format Export** | Export Cleaned CSV, JSON, Purged Records CSV, and Markdown Audit Report | ✅ Passed |
| **Standard Dependencies** | Both modern `pyproject.toml` / `uv.lock` and standard `requirements.txt` | ✅ Passed |
| **Production Ready** | Containerized with `Dockerfile` and configured `.streamlit/config.toml` | ✅ Passed |
| **Branch Workflow** | Work organized through clean, small commits on `development` | ✅ Passed |
