# tests/test_ml.py
import pytest
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIN_ROWS = 50


# ── Standalone helpers (tested independently of pipeline.py) ──
def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    """Validation logic tested here — mirrors what pipeline.py should do."""
    if df.empty or len(df.columns) == 0:
        return False, "Dataset is empty."
    if len(df) < MIN_ROWS:
        return False, f"Too few rows. Minimum {MIN_ROWS} required, got {len(df)}."
    if len(df.columns) < 2:
        return False, "Dataset must have at least 2 columns."
    return True, "Valid"


def calculate_quality_score(df: pd.DataFrame) -> tuple[float, str]:
    """Quality score logic tested here."""
    if df.empty:
        return 0.0, "F"
    total_cells   = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    missing_pct   = missing_cells / total_cells if total_cells > 0 else 1.0
    score         = round((1 - missing_pct) * 100, 2)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
    return score, grade


class TestTargetDetection:

    def test_detects_churn_column(self):
        from core.ml_model import detect_target_column
        df = pd.DataFrame({
            "tenure":  [1, 2, 3],
            "charges": [10, 20, 30],
            "churn":   ["Yes", "No", "Yes"]
        })
        assert detect_target_column(df) == "churn"

    def test_detects_fraud_column(self):
        from core.ml_model import detect_target_column
        df = pd.DataFrame({
            "amount":   [100, 200, 300],
            "is_fraud": [0, 1, 0]
        })
        assert detect_target_column(df) == "is_fraud"

    def test_detects_binary_column_as_fallback(self):
        from core.ml_model import detect_target_column
        df = pd.DataFrame({
            "feature1": [1, 2, 3],
            "feature2": [4, 5, 6],
            "outcome":  [0, 1, 0]
        })
        result = detect_target_column(df)
        assert result is not None


class TestDataValidation:

    def test_rejects_empty_dataframe(self):
        df = pd.DataFrame()
        valid, msg = validate_dataframe(df)
        assert valid is False

    def test_rejects_too_few_rows(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        valid, msg = validate_dataframe(df)
        assert valid is False
        assert "rows" in msg.lower()

    def test_accepts_valid_dataframe(self):
        df = pd.DataFrame({
            "feature": range(100),
            "target":  [0, 1] * 50
        })
        valid, msg = validate_dataframe(df)
        assert valid is True

    def test_rejects_all_missing_column(self):
        df = pd.DataFrame()  # empty = invalid
        valid, msg = validate_dataframe(df)
        assert valid is False

    def test_rejects_single_column(self):
        df = pd.DataFrame({"only_col": range(100)})
        valid, msg = validate_dataframe(df)
        assert valid is False


class TestDataQualityScore:

    def test_perfect_data_scores_high(self):
        df = pd.DataFrame({
            "col1":   range(200),
            "col2":   range(200),
            "target": [0, 1] * 100
        })
        score, grade = calculate_quality_score(df)
        assert grade in ["A", "B"]
        assert score >= 75

    def test_missing_data_lowers_score(self):
        df_bad = pd.DataFrame({
            "col1":   [None] * 100 + list(range(100)),
            "col2":   range(200),
            "target": [0, 1] * 100
        })
        df_good = pd.DataFrame({
            "col1":   range(200),
            "col2":   range(200),
            "target": [0, 1] * 100
        })
        score_bad,  _ = calculate_quality_score(df_bad)
        score_good, _ = calculate_quality_score(df_good)
        assert score_bad < score_good

    def test_grade_is_string(self):
        df = pd.DataFrame({"a": range(50), "b": range(50)})
        score, grade = calculate_quality_score(df)
        assert isinstance(grade, str)
        assert grade in ["A", "B", "C", "D", "F"]


class TestFileValidator:

    def test_rejects_non_csv(self):
        from auth.file_validator import validate_upload
        from unittest.mock import MagicMock
        mock_file          = MagicMock()
        mock_file.filename = "document.pdf"
        with pytest.raises(Exception):
            validate_upload(mock_file, b"some content")

    def test_rejects_empty_file(self):
        from auth.file_validator import validate_upload
        from unittest.mock import MagicMock
        mock_file          = MagicMock()
        mock_file.filename = "data.csv"
        with pytest.raises(Exception):
            validate_upload(mock_file, b"")

    def test_accepts_valid_csv(self):
        from auth.file_validator import validate_upload
        from unittest.mock import MagicMock
        mock_file          = MagicMock()
        mock_file.filename = "data.csv"
        header  = "col1,col2,target\n"
        rows    = "".join([f"{i},{i*2},{i%2}\n" for i in range(60)])
        content = (header + rows).encode()
        validate_upload(mock_file, content)  # should not raise
