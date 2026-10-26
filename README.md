# CSV-Cleaner

A clean, robust, and well-tested Python utility to process, sanitize, and clean customer review datasets using plain Python and `pandas`.

---

## 🎯 Goal

This project implements **Assignment 1: CSV Cleaning Script**. It demonstrates writing clean, deterministic, production-grade Python code without relying on LLMs. Plain code is fast, deterministic, cost-free, and reproducible.

### What it does:
1. **Reads Customer Reviews CSV**: Identifies and removes rows where every field is empty or contains only whitespace.
2. **Deduplicates**: Removes exact duplicate rows while retaining the first occurrence.
3. **Data Immutability**: Leaves the original data untouched and returns a new DataFrame copy with a clean index.
4. **Saves to File**: Exports the cleaned dataset to a target CSV file (automatically creating target directories).
5. **Resilient Retry Decorator**: Provides a `@retry` decorator that automatically re-runs functions up to $N$ times upon failure and raises the last error if all attempts fail.
6. **Comprehensive Test Suite**: Exceeds the 5-test minimum with 10 unit and pipeline tests executed with `pytest`.

---

## 📁 Folder Structure

```text
CSV-Cleaner/
├── .env.example            # Environment configuration template
├── .gitignore              # Ignores virtual envs, caches, outputs, secrets
├── .python-version         # Python version pin (3.12)
├── pyproject.toml          # Project metadata and dependencies via uv
├── uv.lock                 # Deterministic dependency lockfile
├── README.md               # Documentation and execution guide
├── data/
│   └── sample_reviews.csv  # Messy sample dataset (16 rows)
├── src/
│   ├── __init__.py
│   └── cleaner.py          # Cleaning functions and retry decorator
└── tests/
    ├── __init__.py
    └── test_cleaner.py     # 10 comprehensive pytest test cases
```

---

## ⚙️ Installation & Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for fast, reproducible dependency management.

### Prerequisites
- Python 3.12+
- `uv` installed ([uv installation guide](https://docs.astral.sh/uv/getting-started/installation/))

### 1. Clone & Navigate to Project
```bash
git clone <repository-url>
cd CSV-Cleaner
```

### 2. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### 3. Install Dependencies
Install all production and development dependencies using `uv`:
```bash
uv sync
```

---

## 🚀 How to Run

### 1. Run the Cleaning Pipeline Script
Execute the script to clean `data/sample_reviews.csv` and output to `data/cleaned_reviews.csv`:
```bash
uv run python src/cleaner.py
```

**Console Output:**
```text
--> Reading and cleaning reviews from: data/sample_reviews.csv
--> Success! 9 cleaned rows written to: data/cleaned_reviews.csv
```

### 2. Run the Test Suite
Run the test suite with `pytest`:
```bash
uv run pytest
```

To run with verbose output:
```bash
uv run pytest -v
```

All 10 tests will execute and pass:
```text
tests/test_cleaner.py::test_retry_succeeds_after_failing PASSED          [ 10%]
tests/test_cleaner.py::test_retry_gives_up_after_n_tries PASSED          [ 20%]
tests/test_cleaner.py::test_retry_specific_exception_filter PASSED       [ 30%]
tests/test_cleaner.py::test_retry_invalid_max_retries PASSED             [ 40%]
tests/test_cleaner.py::test_remove_empty_and_whitespace_rows PASSED      [ 50%]
tests/test_cleaner.py::test_remove_duplicate_rows PASSED                 [ 60%]
tests/test_cleaner.py::test_clean_reviews_does_not_mutate_original PASSED [ 70%]
tests/test_cleaner.py::test_save_cleaned_data PASSED                     [ 80%]
tests/test_cleaner.py::test_clean_reviews_file_not_found PASSED          [ 90%]
tests/test_cleaner.py::test_end_to_end_sample_reviews_cleaning PASSED    [100%]
```

---

## 🔍 Code Walkthrough

### 1. `clean_reviews(data)`
- Accepts either a file path (`str` or `Path`) or an in-memory `pd.DataFrame`.
- **Empty / Whitespace Detection**: Checks every cell using `pd.isna(val) or (isinstance(val, str) and val.strip() == "")`. A row is filtered out only if **all** of its columns evaluate to empty/whitespace. Valid rows with single empty fields (e.g., an optional review comment) are preserved.
- **Deduplication**: Calls `.drop_duplicates()` to eliminate exact redundant rows.
- **Immutability**: Operates on a `.copy()`, ensuring the original DataFrame or input data is never mutated in-place.

### 2. `save_cleaned_data(df, output_path)`
- Ensures the destination directory exists using `dest.parent.mkdir(parents=True, exist_ok=True)`.
- Writes the DataFrame to CSV without adding an unnecessary index column (`index=False`).

### 3. `@retry` Decorator
- Configurable with `max_retries`, `delay`, `backoff`, and specific `exceptions`.
- Re-runs the wrapped function up to $N$ total attempts upon encountering a caught exception.
- Re-raises the final error if all $N$ attempts are exhausted.
- Preserves the wrapped function's signature and metadata with `@functools.wraps`.

---

## 📋 Assignment Checklist

| Item | Requirement | Status |
| :--- | :--- | :---: |
| 1 | Empty and whitespace-only rows are removed | ✅ Passed |
| 2 | Duplicate rows are removed | ✅ Passed |
| 3 | Retry decorator works (tests for "succeeds after failing" and "gives up after N tries") | ✅ Passed |
| 4 | At least 5 tests pass with `uv run pytest` (10 passed) | ✅ Passed |
| 5 | README explains how to install and run it | ✅ Passed |
| 6 | Work merged through a PR with at least 3 small commits | ✅ Passed |
