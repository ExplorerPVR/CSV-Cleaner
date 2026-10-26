# DataForge Studio (CSV-Cleaner)

A clean, robust, and full-featured customer reviews CSV sanitization suite powered by **Python 3.12**, **Pandas**, **Pydantic v2**, and **Streamlit**.

---

## 🎯 Overview & Key Capabilities

**DataForge Studio** bridges deterministic Python data cleaning with modern interactive visual auditing:

1. **Deterministic Core Engine**:
   - Drops rows where every field is empty or whitespace-only.
   - Eliminates duplicate rows across all columns or user-specified key subsets.
   - Non-destructive processing (original data is never mutated).
   - Built-in `@retry` decorator for failure recovery with exponential backoff.
2. **Pydantic v2 Type-Safe Validation**:
   - Validates each row through [`ReviewRowModel`](file:///src/models.py): standardizes customer names (Title Case), enforces numeric rating boundaries (`1.0` - `5.0`), strips embedded HTML tags, and collapses irregular whitespace.
3. **Interactive Web Dashboard (Streamlit)**:
   - **Upload & Test**: Drag-and-drop any CSV or click **"Load Demo Reviews"** for instant sample testing.
   - **Bento Metric Grid**: Real-time KPI cards displaying raw rows, clean retained rows, purged count, and a dynamic Pydantic Quality Score.
   - **Visual Analytics**: Interactive bar charts for dataset flow dynamics, removal reason distributions, and star rating histograms.
   - **Side-by-Side Diff Matrix**: Live keyword search and preview slider comparing original vs. sanitized data.
   - **Purged Records Audit**: Transparent table listing every dropped record with its exact failure reason.
   - **Multi-Format Export**: One-click download for Cleaned CSV, Cleaned JSON, Purged Audit CSV, and Executive Markdown Audit Reports.

---

## 📁 Project Architecture

```text
CSV-Cleaner/
├── .streamlit/
│   └── config.toml          # Nordic Emerald custom theme & headless server settings
├── src/
│   ├── __init__.py
│   ├── models.py            # Pydantic v2 schemas (ReviewRowModel, CleaningOptions, CleaningStats)
│   └── cleaner.py           # Core cleaning functions, retry decorator, and audit pipeline
├── tests/
│   ├── __init__.py
│   └── test_cleaner.py      # 14 comprehensive unit, pipeline, and Pydantic tests
├── data/
│   └── sample_reviews.csv   # Messy sample reviews dataset (16 rows)
├── app.py                   # Streamlit web application & visual dashboard
├── Dockerfile               # Multi-stage production container setup
├── pyproject.toml           # Project metadata and dependencies via uv
├── uv.lock                  # Deterministic lockfile
├── .gitignore               # Environment secrets, cache, and generated data
├── .env.example             # Configuration template
└── README.md                # Documentation and deployment guide
```

---

## ⚙️ Quickstart & Local Setup

### Prerequisites
- Python 3.12+
- `uv` package manager ([installation instructions](https://docs.astral.sh/uv/getting-started/installation/))

### 1. Install Dependencies
```bash
uv sync
```

### 2. Launch the Web Studio
```bash
uv run streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Command-Line Pipeline Script
```bash
uv run python src/cleaner.py
```

### 4. Run the Full Test Suite
```bash
uv run pytest -v
```

All 14 tests will execute and pass:
```text
collected 14 items

tests/test_cleaner.py::test_retry_succeeds_after_failing PASSED          [  7%]
tests/test_cleaner.py::test_retry_gives_up_after_n_tries PASSED          [ 14%]
tests/test_cleaner.py::test_retry_specific_exception_filter PASSED       [ 21%]
tests/test_cleaner.py::test_retry_invalid_max_retries PASSED             [ 28%]
tests/test_cleaner.py::test_remove_empty_and_whitespace_rows PASSED      [ 35%]
tests/test_cleaner.py::test_remove_duplicate_rows PASSED                 [ 42%]
tests/test_cleaner.py::test_clean_reviews_does_not_mutate_original PASSED [ 50%]
tests/test_cleaner.py::test_save_cleaned_data PASSED                     [ 57%]
tests/test_cleaner.py::test_clean_reviews_file_not_found PASSED          [ 64%]
tests/test_cleaner.py::test_end_to_end_sample_reviews_cleaning PASSED    [ 71%]
tests/test_cleaner.py::test_pydantic_review_model_sanitization PASSED    [ 78%]
tests/test_cleaner.py::test_pydantic_invalid_rating_raises_error PASSED  [ 85%]
tests/test_cleaner.py::test_audit_cleaning_pipeline_with_stats PASSED    [ 92%]
tests/test_cleaner.py::test_dataframe_serialization_bytes PASSED         [100%]
```

---

## 🌐 How to Host Anywhere

### Option A: Streamlit Community Cloud (Free 1-Click Hosting)
1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Click **"New app"**, select your repository, branch (`development` or `main`), and set the main file path to `app.py`.
4. Click **Deploy!**

### Option B: Docker Container Deployment (Render / Railway / AWS / VPS)
Build and run the container locally or on any cloud platform:

```bash
# Build the Docker image
docker build -t csv-cleaner-studio .

# Run the container on port 8501
docker run -p 8501:8501 csv-cleaner-studio
```

---

## 📋 Assignment & Enhancement Checklist

| Requirement | Description | Status |
| :--- | :--- | :---: |
| **Empty Rows Pruned** | Strips rows where all fields are null or whitespace | ✅ Passed |
| **Duplicates Removed** | Eliminates exact duplicate records | ✅ Passed |
| **Resilience Decorator** | `@retry` with test for early success and gives-up after $N$ tries | ✅ Passed |
| **Pytest Test Suite** | 14 test cases passing via `uv run pytest` | ✅ Passed |
| **Pydantic Validation** | Type-safe schema validation via `ReviewRowModel` | ✅ Passed |
| **Interactive Frontend** | Modern Streamlit dashboard with Bento metrics & charts | ✅ Passed |
| **Multi-Format Export** | Clean CSV, Clean JSON, Removed CSV, Audit Report MD | ✅ Passed |
| **Hostable Anywhere** | Configured with `.streamlit/config.toml` & `Dockerfile` | ✅ Passed |
