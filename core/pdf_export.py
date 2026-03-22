# core/pdf_export.py
# Analytiq — Auto PDF Report Generator (ASCII-safe)

import os
import json
from fpdf import FPDF
from datetime import datetime


def safe(text: str) -> str:
    """Convert any string to ASCII-safe for Helvetica font."""
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "\u2022": "-",   # bullet •
        "\u2192": ">>",  # arrow →
        "\u2190": "<<",  # arrow ←
        "\u00b7": "-",   # middle dot ·
        "\u2013": "-",   # en dash –
        "\u2014": "-",   # em dash —
        "\u2026": "...", # ellipsis …
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u25cf": "*",   # black circle
        "\u25cb": "o",   # white circle
        "\u2713": "OK",  # checkmark
        "\u2714": "OK",  # heavy checkmark
        "\u2715": "X",   # multiplication X
        "\u2716": "X",   # heavy X
        "\u00e9": "e",   # é
        "\u00e8": "e",   # è
        "\u00ea": "e",   # ê
        "\u00e0": "a",   # à
        "\u00e2": "a",   # â
        "\u00f9": "u",   # ù
        "\u00fb": "u",   # û
        "\u00ee": "i",   # î
        "\u00f4": "o",   # ô
        "\u00e7": "c",   # ç
        "\u00fc": "u",   # ü
        "\u00f6": "o",   # ö
        "\u00e4": "a",   # ä
        "\u00df": "ss",  # ß
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class AnalytiqPDF(FPDF):
    def __init__(self, client_name: str, domain: str):
        super().__init__()
        self.client_name = safe(client_name)
        self.domain      = safe(domain)
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_fill_color(15, 17, 23)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 5)
        self.cell(0, 8, "Analytiq", ln=False)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(156, 163, 175)
        self.set_xy(0, 5)
        self.cell(200, 8, f"Client Report - {self.client_name}", align="R")
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(156, 163, 175)
        self.cell(0, 10, f"Analytiq - Confidential - Page {self.page_no()} - Generated {datetime.now().strftime('%d %b %Y')}", align="C")

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(15, 17, 23)
        self.cell(0, 8, safe(title), ln=True)
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.8)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(5)

    def kpi_box(self, label: str, value: str, x: float, y: float, w: float = 40, h: float = 18):
        self.set_fill_color(247, 248, 250)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.rect(x, y, w, h, "FD")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(156, 163, 175)
        self.set_xy(x + 2, y + 2)
        self.cell(w - 4, 4, safe(label.upper()), ln=True)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(15, 17, 23)
        self.set_xy(x + 2, y + 7)
        self.cell(w - 4, 8, safe(str(value)))

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(55, 65, 81)
        self.multi_cell(0, 6, safe(text))
        self.ln(3)


def generate_pdf(
    client_name:    str,
    domain:         str,
    insights_path:  str,
    metrics_path:   str  = None,
    narrative_path: str  = None,
    charts_dir:     str  = None,
    output_path:    str  = "report.pdf"
) -> str:

    pdf = AnalytiqPDF(client_name, domain)
    pdf.add_page()

    # ── Cover block ──────────────────────────────────────────
    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(191, 219, 254)
    pdf.set_line_width(0.3)
    pdf.rect(20, 25, 170, 38, "FD")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(15, 17, 23)
    pdf.set_xy(28, 30)
    pdf.cell(0, 12, "Analytics Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(107, 114, 128)
    pdf.set_x(28)
    pdf.cell(0, 7, safe(f"{client_name}  -  {domain}"), ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(28)
    pdf.cell(0, 6, f"Generated {datetime.now().strftime('%d %B %Y  %H:%M')}", ln=True)
    pdf.ln(14)

    # ── Load insights ─────────────────────────────────────────
    if not os.path.exists(insights_path):
        pdf.output(output_path)
        return output_path

    with open(insights_path) as f:
        insights = json.load(f)

    kpis      = insights.get("kpis", {})
    segments  = insights.get("segment_insights", [])
    anomalies = insights.get("anomalies", [])

    # ── KPI Section ───────────────────────────────────────────
    pdf.section_title("Key Performance Indicators")
    kpi_items = list(kpis.items())[:8]
    x_start, y_start = 20, pdf.get_y()
    per_row, w, h, gap = 4, 40, 18, 2.5

    for i, (k, v) in enumerate(kpi_items):
        col = i % per_row
        row = i // per_row
        x   = x_start + col * (w + gap)
        y   = y_start + row * (h + gap)
        label = k.replace("_", " ").title()[:18]
        val   = f"{v:,.2f}" if isinstance(v, float) else str(v)
        pdf.kpi_box(label, val, x, y, w, h)

    rows_used = (len(kpi_items) + per_row - 1) // per_row
    pdf.set_y(y_start + rows_used * (h + gap) + 6)

    # ── Segment Section ───────────────────────────────────────
    if segments:
        pdf.section_title("Segment Analysis")
        for seg in segments[:4]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(37, 99, 235)
            pdf.cell(0, 6, safe(seg["segment"].replace("_", " ").title()), ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(55, 65, 81)
            pdf.cell(0, 5, safe(f"Highest risk: {seg['highest_churn_value']}  >>  {seg['highest_churn_rate_%']}%"), ln=True)
            pdf.ln(2)

            breakdown = seg["full_breakdown"][:5]
            col_w = [80, 50]
            pdf.set_fill_color(247, 248, 250)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(col_w[0], 6, safe(seg["segment"].upper()), border="B", fill=True)
            pdf.cell(col_w[1], 6, "RISK RATE %", border="B", fill=True, ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 17, 23)
            for item in breakdown:
                pdf.cell(col_w[0], 6, safe(str(item[seg["segment"]])[:30]))
                pdf.cell(col_w[1], 6, safe(f"{item['churn_rate_%']}%"), ln=True)
            pdf.ln(5)

    # ── Anomalies ─────────────────────────────────────────────
    if anomalies:
        pdf.section_title("Anomaly Detection")
        pdf.body_text(f"{len(anomalies)} anomalous features detected in the dataset.")
        for a in anomalies[:5]:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(55, 65, 81)
            pdf.cell(0, 5, safe(f"  - {a['column']}: {a['outlier_count']} outliers ({a['outlier_%']}%)"), ln=True)
        pdf.ln(3)

    # ── Model Metrics ─────────────────────────────────────────
    if metrics_path and os.path.exists(metrics_path):
        pdf.add_page()
        pdf.section_title("ML Model Performance")
        with open(metrics_path) as f:
            metrics = json.load(f)

        m_items = [
            ("AUC-ROC",   metrics.get("auc_roc",   "N/A"), "Overall discrimination ability"),
            ("Precision", metrics.get("precision", "N/A"), "Accuracy of positive predictions"),
            ("Recall",    metrics.get("recall",    "N/A"), "Coverage of actual positives"),
            ("F1-Score",  metrics.get("f1_score",  "N/A"), "Balance of precision and recall"),
        ]
        y_m = pdf.get_y()
        for i, (label, val, desc) in enumerate(m_items):
            pdf.kpi_box(label, str(val), 20 + i * 43, y_m, 40, 18)
        pdf.set_y(y_m + 26)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(107, 114, 128)
        for label, val, desc in m_items:
            pdf.cell(0, 5, safe(f"  - {desc}"), ln=True)
        pdf.ln(5)

        # Charts
        if charts_dir and os.path.exists(charts_dir):
            chart_files = ["roc_curve.png", "confusion_matrix.png", "feature_importance.png"]
            for i, chart in enumerate(chart_files):
                path = os.path.join(charts_dir, chart)
                if os.path.exists(path):
                    if i % 2 == 0 and i > 0:
                        pdf.add_page()
                    x = 20 if i % 2 == 0 else 110
                    try:
                        pdf.image(path, x=x, y=pdf.get_y(), w=85)
                        if i % 2 == 1:
                            pdf.ln(65)
                    except Exception:
                        pass

    # ── Executive Narrative ───────────────────────────────────
    if narrative_path and os.path.exists(narrative_path):
        pdf.add_page()
        pdf.section_title("Executive Summary")
        with open(narrative_path) as f:
            narrative = f.read()
        pdf.body_text(narrative)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    pdf.output(output_path)
    return output_path
