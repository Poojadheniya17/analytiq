# core/narrative.py
# AI Executive Narrative Generator using Groq

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY") or "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"


def generate_narrative(insights_path: str, metrics_path: str = None, client_name: str = "the client", domain: str = "business") -> str:
    """
    Generate a consultant-style executive narrative from insights and model metrics.
    """
    # Load insights
    if not os.path.exists(insights_path):
        return "No insights found. Please run the analysis first."

    with open(insights_path) as f:
        insights = json.load(f)

    kpis     = insights.get("kpis", {})
    segments = insights.get("segment_insights", [])
    anomalies = insights.get("anomalies", [])

    # Load model metrics if available
    metrics_text = ""
    if metrics_path and os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
        metrics_text = f"""
ML Model Performance:
- AUC-ROC: {metrics.get('auc_roc', 'N/A')}
- Precision: {metrics.get('precision', 'N/A')}
- Recall: {metrics.get('recall', 'N/A')}
- F1-Score: {metrics.get('f1_score', 'N/A')}
"""

    # Build segment summary
    seg_text = ""
    for seg in segments[:3]:
        seg_text += f"\n- {seg['segment']}: highest risk in '{seg['highest_churn_value']}' at {seg['highest_churn_rate_%']}%"

    # Build KPI summary
    kpi_text = "\n".join([f"- {k.replace('_',' ').title()}: {v}" for k, v in list(kpis.items())[:8]])

    prompt = f"""You are a senior data analytics consultant at a top-tier firm. 
You have just completed a data analysis for {client_name}, a company in the {domain} industry.

Here is the data analysis output:

Key Business Metrics:
{kpi_text}

Segment Analysis:{seg_text}

Anomalies Detected: {len(anomalies)} anomalies found
{metrics_text}

Write a professional executive summary that:
1. Opens with the most critical business finding in 1-2 sentences
2. Explains what is driving the key metric (2-3 sentences with specific numbers)
3. Highlights the most important segment insight (1-2 sentences)
4. Gives 2-3 specific, actionable recommendations a business leader can act on immediately
5. Closes with the expected business impact if recommendations are followed

Tone: Senior consultant, confident, data-driven, no fluff.
Length: 4-5 paragraphs.
Do NOT use bullet points — write in flowing paragraphs like a consulting report."""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        api_key=GROQ_KEY
    )

    response = llm.invoke(prompt)
    return response.content.strip()
