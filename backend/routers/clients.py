# backend/routers/clients.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from auth.auth import get_clients, add_client, delete_client
import pandas as pd
import numpy as np
import shutil

router = APIRouter()

BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")
)

class ClientRequest(BaseModel):
    user_id: int
    name:    str
    domain:  str

def get_client_path(user_id: int, client_name: str) -> str:
    safe = client_name.lower().replace(" ", "_")
    return os.path.join(BASE_DATA, str(user_id), safe)

def clean_for_json(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, np.bool_):    return bool(obj)
    if isinstance(obj, np.integer):  return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray):  return obj.tolist()
    return obj


@router.get("/{user_id}")
def list_clients(user_id: int):
    return get_clients(user_id)


@router.post("/")
def create_client(req: ClientRequest):
    success, msg = add_client(req.user_id, req.name, req.domain)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    clients = get_clients(req.user_id)
    return {"message": msg, "client": clients[0] if clients else None}


@router.delete("/{client_id}")
def remove_client(client_id: int, user_id: int):
    success, msg = delete_client(client_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/{user_id}/{client_name}/upload")
async def upload_file(user_id: int, client_name: str, file: UploadFile = File(...)):
    client_path = get_client_path(user_id, client_name)
    os.makedirs(client_path, exist_ok=True)
    file_path = os.path.join(client_path, "raw_data.csv")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    df = pd.read_csv(file_path)
    return {
        "message":        "File uploaded successfully",
        "rows":           int(df.shape[0]),
        "columns":        int(df.shape[1]),
        "column_names":   df.columns.tolist(),
        "missing_values": int(df.isnull().sum().sum()),
        "duplicates":     int(df.duplicated().sum()),
        "preview":        df.head(5).to_dict(orient="records")
    }


@router.get("/{user_id}/{client_name}/quality")
def data_quality_score(user_id: int, client_name: str):
    client_path = get_client_path(user_id, client_name)
    raw_path    = os.path.join(client_path, "raw_data.csv")

    if not os.path.exists(raw_path):
        raise HTTPException(status_code=404, detail="No data found.")

    df          = pd.read_csv(raw_path)
    total_cells = df.shape[0] * df.shape[1]

    missing_pct   = round(float(df.isnull().sum().sum() / total_cells * 100), 2)
    duplicate_pct = round(float(df.duplicated().sum() / len(df) * 100), 2)

    outlier_cols = []
    for col in df.select_dtypes(include=["float64", "int64"]).columns:
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR    = Q3 - Q1
        if IQR == 0:
            continue
        n_out = int(len(df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]))
        if n_out > 0:
            outlier_cols.append({"column": str(col), "count": n_out})

    mixed_cols = []
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            pd.to_numeric(df[col])
            mixed_cols.append(str(col))
        except:
            pass

    score  = 100
    score -= min(30, missing_pct * 3)
    score -= min(20, duplicate_pct * 4)
    score -= min(20, len(outlier_cols) * 4)
    score -= min(10, len(mixed_cols) * 5)
    score  = int(max(0, round(score)))
    grade  = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"

    null_col = str(df.isnull().sum().idxmax()) if df.isnull().sum().sum() > 0 else None

    recommendations = []
    if missing_pct > 5 and null_col:
        recommendations.append(f"Fix missing values in '{null_col}' column")
    if duplicate_pct > 1:
        recommendations.append(f"Remove {int(df.duplicated().sum())} duplicate rows")
    if outlier_cols:
        recommendations.append(f"Investigate outliers in '{outlier_cols[0]['column']}'")

    result = {
        "score":         score,
        "grade":         grade,
        "total_rows":    int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "checks": {
            "missing_values": {
                "passed":  bool(missing_pct < 5),
                "value":   missing_pct,
                "message": f"{missing_pct}% missing values" if missing_pct > 0 else "No missing values"
            },
            "duplicates": {
                "passed":  bool(duplicate_pct < 1),
                "value":   duplicate_pct,
                "message": f"{duplicate_pct}% duplicate rows" if duplicate_pct > 0 else "No duplicates found"
            },
            "outliers": {
                "passed":  bool(len(outlier_cols) == 0),
                "value":   len(outlier_cols),
                "message": f"{len(outlier_cols)} columns with outliers" if outlier_cols else "No significant outliers"
            },
            "type_consistency": {
                "passed":  bool(len(mixed_cols) == 0),
                "value":   len(mixed_cols),
                "message": f"{len(mixed_cols)} columns with mixed types" if mixed_cols else "All types consistent"
            },
        },
        "outlier_details":  outlier_cols[:5],
        "recommendations":  recommendations,
    }

    return clean_for_json(result)
