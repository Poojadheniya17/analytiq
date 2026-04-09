# backend/routers/ai.py
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.nlp_engine import query as nlp_query
from core.narrative  import generate_narrative
from langchain_groq  import ChatGroq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Absolute base path — works regardless of where uvicorn is run from ──
BASE_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")
)

router = APIRouter()

class QueryRequest(BaseModel):
    user_id:     int
    client_name: str
    question:    str

class NarrativeRequest(BaseModel):
    user_id:     int
    client_name: str
    domain:      str

def get_path(user_id: int, client_name: str) -> str:
    return os.path.join(BASE_DATA, str(user_id), client_name.lower().replace(" ", "_"))


@router.post("/query")
def run_query(req: QueryRequest):
    client_path  = get_path(req.user_id, req.client_name)
    cleaned_path = os.path.join(client_path, "cleaned_data.csv")
    if not os.path.exists(cleaned_path):
        raise HTTPException(status_code=404, detail="No data found. Upload and clean data first.")
    result = nlp_query(req.question, cleaned_path)
    if result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "question": result["question"],
        "sql":      result["sql"],
        "results":  result["results"].to_dict(orient="records") if result["results"] is not None else [],
        "answer":   result["answer"]
    }


@router.post("/narrative")
def run_narrative(req: NarrativeRequest):
    client_path    = get_path(req.user_id, req.client_name)
    insights_path  = os.path.join(client_path, "insights.json")
    metrics_path   = os.path.join(client_path, "model_metrics.json")
    narrative_path = os.path.join(client_path, "narrative.txt")
    if not os.path.exists(insights_path):
        raise HTTPException(status_code=404, detail="Run insights analysis first.")
    narrative = generate_narrative(
        insights_path = insights_path,
        metrics_path  = metrics_path if os.path.exists(metrics_path) else None,
        client_name   = req.client_name,
        domain        = req.domain
    )
    with open(narrative_path, "w") as f:
        f.write(narrative)
    return {"narrative": narrative}


@router.get("/narrative/{user_id}/{client_name}")
def get_narrative(user_id: int, client_name: str):
    client_path    = get_path(user_id, client_name)
    narrative_path = os.path.join(client_path, "narrative.txt")
    if not os.path.exists(narrative_path):
        return {"narrative": None}
    with open(narrative_path) as f:
        return {"narrative": f.read()}


@router.post("/recommendations")
def get_recommendations(req: NarrativeRequest):
    client_path   = get_path(req.user_id, req.client_name)
    insights_path = os.path.join(client_path, "insights.json")
    metrics_path  = os.path.join(client_path, "model_metrics.json")
    recs_path     = os.path.join(client_path, "recommendations.json")

    # Debug — print actual path being checked
    print(f"[DEBUG] Looking for insights at: {insights_path}")
    print(f"[DEBUG] Exists: {os.path.exists(insights_path)}")

    if not os.path.exists(insights_path):
        raise HTTPException(status_code=404, detail=f"Insights not found at {insights_path}")

    with open(insights_path) as f:
        insights = json.load(f)

    kpis     = insights.get("kpis", {})
    segments = insights.get("segment_insights", [])

    metrics_text = ""
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
        metrics_text = f"Model AUC: {metrics.get('auc_roc')}, F1: {metrics.get('f1_score')}"

    kpi_text = "\n".join([f"- {k.replace('_',' ').title()}: {v}" for k, v in list(kpis.items())[:6]])
    seg_text = ""
    for seg in segments[:3]:
        seg_text += f"\n- {seg['segment']}: highest risk in '{seg['highest_churn_value']}' at {seg['highest_churn_rate_%']}%"

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, api_key=os.environ.get("GROQ_API_KEY", ""))

    prompt = f"""You are a senior data analytics consultant at Bold Analytics.

Client: {req.client_name} ({req.domain})

Key Metrics:
{kpi_text}

Segment Analysis:{seg_text}

{metrics_text}

Generate exactly 3 specific, actionable business recommendations.
Each must reference a specific number, suggest a concrete action, and estimate impact.

Return ONLY a JSON array, no markdown, no explanation:
[
  {{"title": "Short title", "action": "Specific action", "impact": "Expected impact", "metric": "Supporting data point"}},
  {{"title": "Short title", "action": "Specific action", "impact": "Expected impact", "metric": "Supporting data point"}},
  {{"title": "Short title", "action": "Specific action", "impact": "Expected impact", "metric": "Supporting data point"}}
]"""

    try:
        response = llm.invoke(prompt)
        content  = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"): content = content[4:]
        recommendations = json.loads(content.strip())
    except Exception as e:
        print(f"[DEBUG] LLM error: {e}")
        recommendations = [
            {"title": "Reduce early churn", "action": "Target month-to-month customers in first 3 months with retention offers", "impact": "Could reduce churn by 15-20%", "metric": f"Churn rate: {kpis.get('target_rate_%', 'N/A')}%"},
            {"title": "Upsell to annual plans", "action": "Offer discounted annual plans to high-risk monthly customers", "impact": "Annual customers churn 85% less", "metric": "Two-year contracts show lowest churn"},
            {"title": "Focus on high-value at-risk", "action": "Prioritise retention calls for customers with high charges and low tenure", "impact": "Protect highest revenue customers", "metric": f"Total customers: {kpis.get('total_records', 'N/A')}"},
        ]

    with open(recs_path, "w") as f:
        json.dump(recommendations, f, indent=4)

    return {"recommendations": recommendations}


@router.get("/recommendations/{user_id}/{client_name}")
def fetch_recommendations(user_id: int, client_name: str):
    client_path = get_path(user_id, client_name)
    recs_path   = os.path.join(client_path, "recommendations.json")
    if not os.path.exists(recs_path):
        return {"recommendations": None}
    with open(recs_path) as f:
        return {"recommendations": json.load(f)}
