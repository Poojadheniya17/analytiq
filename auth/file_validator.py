# auth/file_validator.py
# Analytiq — CSV upload validation

import os
from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE_MB  = 50
MAX_FILE_SIZE     = MAX_FILE_SIZE_MB * 1024 * 1024
MIN_ROWS          = 50
MAX_ROWS          = 500_000
ALLOWED_TYPES     = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}
ALLOWED_EXTENSIONS= {".csv"}


def validate_upload(file: UploadFile, content: bytes) -> None:
    # Extension check
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only CSV files are accepted. Got: {ext or 'no extension'}"
        )

    # Size check
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    # Content validation — check it's actually parseable CSV
    try:
        text = content.decode("utf-8", errors="replace")
        lines = [l for l in text.splitlines() if l.strip()]

        if len(lines) < 2:
            raise HTTPException(
                status_code=400,
                detail="CSV must have at least a header row and one data row."
            )

        # Check row count
        data_rows = len(lines) - 1  # subtract header
        if data_rows < MIN_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset too small. Minimum {MIN_ROWS} rows required. Your file has {data_rows} rows."
            )
        if data_rows > MAX_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset too large. Maximum {MAX_ROWS:,} rows. Your file has {data_rows:,} rows."
            )

        # Check header has at least 2 columns
        header_cols = len(lines[0].split(","))
        if header_cols < 2:
            raise HTTPException(
                status_code=400,
                detail="CSV must have at least 2 columns."
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read file. Make sure it is a valid UTF-8 encoded CSV."
        )


def sanitize_filename(filename: str) -> str:
    """Remove path traversal and unsafe characters from filename."""
    name = os.path.basename(filename or "upload.csv")
    safe = "".join(c for c in name if c.isalnum() or c in "._-")
    return safe or "upload.csv"
