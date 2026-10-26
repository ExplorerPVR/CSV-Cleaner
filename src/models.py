"""Pydantic data models and schemas for CSV validation and cleaning configuration."""

from __future__ import annotations

import re
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ReviewRowModel(BaseModel):
    """Pydantic model representing a sanitized customer review row."""

    review_id: Optional[str] = Field(default=None, description="Unique identifier for the review")
    customer_name: Optional[str] = Field(default=None, description="Name of the customer")
    rating: Optional[float] = Field(default=None, description="Numerical rating between 1 and 5")
    review_text: Optional[str] = Field(default=None, description="Customer review comment")
    review_date: Optional[str] = Field(default=None, description="Date of review submission")

    @field_validator("review_id", mode="before")
    @classmethod
    def clean_id(cls, value: Any) -> Optional[str]:
        if value is None or str(value).strip().lower() in ("nan", "none", ""):
            return None
        return str(value).strip()

    @field_validator("customer_name", mode="before")
    @classmethod
    def clean_customer_name(cls, value: Any) -> Optional[str]:
        if value is None or str(value).strip().lower() in ("nan", "none", ""):
            return None
        cleaned = str(value).strip()
        # Standardize name formatting (Title Case)
        return " ".join(word.capitalize() for word in cleaned.split())

    @field_validator("rating", mode="before")
    @classmethod
    def parse_rating(cls, value: Any) -> Optional[float]:
        if value is None or str(value).strip().lower() in ("nan", "none", ""):
            return None
        try:
            val_float = float(value)
            if not (1.0 <= val_float <= 5.0):
                raise ValueError(f"Rating {val_float} is outside the allowed range [1.0, 5.0]")
            return round(val_float, 2)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid rating value '{value}': {exc}")

    @field_validator("review_text", mode="before")
    @classmethod
    def clean_review_text(cls, value: Any) -> Optional[str]:
        if value is None or str(value).strip().lower() in ("nan", "none", ""):
            return None
        text = str(value)
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Collapse excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text if text else None

    @field_validator("review_date", mode="before")
    @classmethod
    def clean_date(cls, value: Any) -> Optional[str]:
        if value is None or str(value).strip().lower() in ("nan", "none", ""):
            return None
        return str(value).strip()

    @model_validator(mode="after")
    def check_not_entirely_empty(self) -> ReviewRowModel:
        """Verify the model contains at least one populated field."""
        fields = [self.review_id, self.customer_name, self.rating, self.review_text, self.review_date]
        if all(f is None for f in fields):
            raise ValueError("Row is completely empty across all fields")
        return self


class CleaningOptions(BaseModel):
    """User-configurable options for the CSV cleaning pipeline."""

    remove_empty_rows: bool = Field(default=True, description="Remove rows where all fields are blank")
    remove_duplicates: bool = Field(default=True, description="Remove exact duplicate rows")
    trim_whitespace: bool = Field(default=True, description="Strip leading/trailing whitespace")
    collapse_spaces: bool = Field(default=True, description="Normalize multiple consecutive spaces")
    strip_html: bool = Field(default=True, description="Remove HTML tags from text fields")
    validate_with_pydantic: bool = Field(default=True, description="Enforce Pydantic schema validation")
    enforce_rating_bounds: bool = Field(default=True, description="Enforce rating bounds between 1.0 and 5.0")
    key_columns: list[str] = Field(default_factory=list, description="Columns to evaluate for deduplication")
    required_column: Optional[str] = Field(default=None, description="Drop row if this specific column is empty")


class CleaningStats(BaseModel):
    """Statistical summary of the CSV cleaning operation."""

    original_rows: int
    cleaned_rows: int
    removed_rows: int
    retention_rate: float
    data_quality_score: float
    removal_breakdown: dict[str, int]
    column_null_counts: dict[str, int]
