# core/pdf_export.py
# Analytiq — Professional PDF Report Generator

import os, json
from datetime import datetime
from fpdf import FPDF

# Colour palette
BLUE       = (37,  99,  235)
DARK       = (15,  23,  42)
GRAY       = (100, 116, 139)
LIGHT_GRAY = (248, 250, 252)
WHITE      = (255, 255, 255)
RED        = (239,  68,  68)
GREEN      = ( 16, 185, 129)
ORANGE     = (249, 115,  22)
BORDER     = (226, 232, 240)


class AnalytiqPDF(FPDF):

    def __init__(self, client_name: str, domain: str):
        super().__init__()
        self.client_name = client_name
        self.domain      = domain
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*BLUE)
        self.rect(0, 0, 210, 1.5, "F")
        self.set_xy(20, 6)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*BLUE)
        self.cell(60, 5, "Analytiq", ln=0)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.set_xy(100, 6)
        self.cell(90, 5, self.client_name[:40], align="R", ln=0)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(*BORDER)
        self.rect(0, self.get_y(), 210, 0.3, "F")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 10,
            f"Analytiq AI Analytics Platform  |  Confidential  |  Page {self.page_no()}",
            align="C")

    def section_title(self, text: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BLUE)
        self.cell(0, 8, text.upper(), ln=True)
        self.set_fill_color(*BLUE)
        self.rect(self.get_x(), self.get_y(), 30, 0.5, "F")
        self.ln(5)
        self.set_text_color(*DARK)

    def kpi_card(self, label: str, value: str, x: float, y: float, w: float = 40, color=BLUE):
        self.set_xy(x, y)
        self.set_fill_color(*LIGHT_GRAY)
        self.set_draw_color(*BORDER)
        self.rect(x, y, w, 18, "FD")
        self.set_fill_color(*color)
        self.rect(x, y, w, 1.2, "F")
        self.set_xy(x + 2, y + 3)
        self.set_font("Helvetica", "", 6.5)
        self.set_text_color(*GRAY)
        self.cell(w - 4, 4, label.upper()[:20], ln=True)
        self.set_xy(x + 2, y + 8)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*DARK)
        self.cell(w - 4, 7, str(value)[:12], ln=True)

    def info_row(self, label: str, value: str, fill: bool = False):
        if fill:
            self.set_fill_color(*LIGHT_GRAY)
        else:
            self.set_fill_color(*WHITE)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRAY)
        self.cell(70, 7, label, fill=True, border="B")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK)
        self.cell(0, 7, str(value)[:60], fill=True, border="B", ln=True)


def safe_text(text: str) -> str:
    """Replace non-latin characters with ASCII equivalents."""
    replacements = {
        "\u2713": "[OK]",   # checkmark
        "\u2717": "[X]",    # cross
        "\u2192": "->",     # right arrow
        "\u2190": "<-",     # left arrow
        "\u2022": "-",      # bullet
        "\u25cf": "-",      # filled circle
        "\u2014": "--",     # em dash
        "\u2013": "-",      # en dash
        "\u201c": '"',      # left quote
        "\u201d": '"',      # right quote
        "\u2018": "'",      # left single quote
        "\u2019": "'",      # right single quote
        "\u00b0": " deg",   # degree
        "\u00b1": "+/-",    # plus minus
        "\u00d7": "x",      # multiplication
        "\u00f7": "/",      # division
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(client_name: str, domain: str, insights_path: str,
                 metrics_path: str = None, narrative_path: str = None,
                 charts_dir: str = None, output_path: str = "report.pdf") -> str:

    with open(insights_path) as f:
        ins = json.load(f)

    metrics      = {}
    full_results = {}
    narrative    = ""
    recommendations = []

    if metrics_path and os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)

    full_path = metrics_path.replace("model_metrics.json", "model_full_results.json") if metrics_path else ""
    if full_path and os.path.exists(full_path):
        with open(full_path) as f:
            full_results = json.load(f)

    if narrative_path and os.path.exists(narrative_path):
        with open(narrative_path) as f:
            narrative = f.read()

    recs_path = insights_path.replace("insights.json", "recommendations.json")
    if os.path.exists(recs_path):
        with open(recs_path) as f:
            recommendations = json.load(f)

    kpis      = ins.get("kpis", {})
    segments  = ins.get("segment_insights", [])
    anomalies = ins.get("anomalies", [])

    at_risk = []
    at_risk_path = insights_path.replace("insights.json", "at_risk.csv")
    if os.path.exists(at_risk_path):
        try:
            import pandas as pd
            at_risk = pd.read_csv(at_risk_path).head(15).to_dict(orient="records")
        except: pass

    now = datetime.now().strftime("%B %d, %Y")
    pdf = AnalytiqPDF(client_name, domain)

    # ── PAGE 1: COVER ──────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, 210, 8, "F")
    pdf.set_xy(20, 40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 12, "Analytiq", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRAY)
    pdf.set_x(20)
    pdf.cell(0, 6, "AI-Powered Analytics Platform", ln=True)
    pdf.ln(12)
    pdf.set_fill_color(*BLUE)
    pdf.rect(20, pdf.get_y(), 80, 0.5, "F")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*DARK)
    pdf.set_x(20)
    pdf.cell(0, 10, safe_text(client_name[:40]), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRAY)
    pdf.set_x(20)
    pdf.cell(0, 6, safe_text(domain), ln=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(20)
    pdf.cell(0, 5, f"Analytics Report  |  {now}", ln=True)
    pdf.ln(15)

    # KPI summary on cover
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*BORDER)
    pdf.rect(20, pdf.get_y(), 170, 45, "FD")
    y_start = pdf.get_y() + 5
    auc_val = metrics.get("auc_roc") or (metrics.get("metrics") or {}).get("auc_roc", "N/A")
    stat_items = [
        ("Total Records",     f"{int(kpis.get('total_records', 0)):,}"),
        ("Target Rate",       f"{kpis.get('target_rate_%', 'N/A')}%"),
        ("Model AUC",         str(auc_val)),
        ("Segments Analysed", str(len(segments))),
    ]
    for i, (label, value) in enumerate(stat_items):
        pdf.kpi_card(label, value, x=22 + i*42, y=y_start, w=40)
    pdf.set_y(y_start + 55)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRAY)
    pdf.set_x(20)
    pdf.cell(0, 5, "CONFIDENTIAL  |  For internal use only  |  Generated by Analytiq", ln=True)
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 282, 210, 15, "F")
    pdf.set_xy(20, 285)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 5, "analytiq.ai  |  AI-Powered Analytics", ln=True)

    # ── PAGE 2: EXECUTIVE SUMMARY ──────────────────────────────
    pdf.add_page()
    pdf.section_title("Executive Summary")

    target_rate = kpis.get("target_rate_%", 0)
    total       = kpis.get("total_records", 0)
    total_pos   = kpis.get("total_positive", 0)
    target_col  = ins.get("target_col", "target").replace("_", " ").title()

    findings = []
    if target_rate:
        findings.append(f"The overall {target_col} rate is {target_rate}%, affecting {int(total_pos):,} out of {int(total):,} records.")
    if segments:
        seg = segments[0]
        findings.append(f"Highest risk segment: '{seg.get('highest_churn_value','N/A')}' in {seg.get('segment','').replace('_',' ')} at {seg.get('highest_churn_rate_%',0)}% {target_col.lower()} rate.")
    if metrics:
        auc = metrics.get("auc_roc") or (metrics.get("metrics") or {}).get("auc_roc")
        if auc:
            findings.append(f"Predictive model achieved AUC-ROC of {auc} -- strong discriminatory power.")
    if recommendations:
        findings.append(f"{len(recommendations)} data-driven recommendations generated for immediate action.")

    for i, finding in enumerate(findings[:4]):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*BLUE)
        pdf.cell(8, 6, f"0{i+1}", ln=0)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 6, safe_text(finding))
        pdf.ln(3)

    pdf.ln(5)
    pdf.section_title("Key Performance Indicators")
    kpi_items = [(k.replace("_"," ").title(), v) for k, v in list(kpis.items())[:8]]
    row_y = pdf.get_y()
    for i, (label, value) in enumerate(kpi_items):
        col = i % 4
        row = i // 4
        x   = 20 + col * 43
        y   = row_y + row * 22
        colors_list = [BLUE, RED, GREEN, ORANGE]
        pdf.kpi_card(safe_text(label[:18]), safe_text(str(value)[:12]), x=x, y=y, w=41, color=colors_list[col % 4])
    pdf.set_y(row_y + (((len(kpi_items)-1)//4)+1) * 22 + 5)

    # ── PAGE 3: SEGMENT ANALYSIS ───────────────────────────────
    if segments:
        pdf.add_page()
        pdf.section_title("Segment Analysis")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 5, safe_text(
            f"Segment breakdown identifying which customer groups carry the highest {target_col.lower()} risk."))
        pdf.ln(5)

        for seg in segments[:4]:
            seg_name  = safe_text(seg.get("segment","").replace("_"," ").title())
            highest   = safe_text(str(seg.get("highest_churn_value","N/A")))
            rate      = seg.get("highest_churn_rate_%", 0)
            breakdown = seg.get("full_breakdown", [])

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK)
            pdf.cell(0, 6, seg_name, ln=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*GRAY)
            pdf.cell(0, 5, f"Highest risk: {highest} at {rate}% {target_col.lower()} rate", ln=True)
            pdf.ln(1)

            if breakdown:
                bar_y    = pdf.get_y()
                max_rate = max([float(b.get("churn_rate_%", b.get("target_rate_%", 0))) for b in breakdown[:6]], default=1)
                if max_rate == 0: max_rate = 1

                for j, item in enumerate(breakdown[:6]):
                    seg_val  = safe_text(str(list(item.values())[0])[:20])
                    seg_rate = float(item.get("churn_rate_%", item.get("target_rate_%", 0)))
                    bar_w    = (seg_rate / max_rate) * 80

                    pdf.set_xy(22, bar_y + j * 8)
                    pdf.set_font("Helvetica", "", 7.5)
                    pdf.set_text_color(*DARK)
                    pdf.cell(45, 6, seg_val, ln=0)

                    bar_color = RED if seg_rate == max_rate else BLUE
                    pdf.set_fill_color(*LIGHT_GRAY)
                    pdf.rect(68, bar_y + j * 8 + 1, 80, 4, "F")
                    pdf.set_fill_color(*bar_color)
                    if bar_w > 0:
                        pdf.rect(68, bar_y + j * 8 + 1, bar_w, 4, "F")

                    pdf.set_xy(152, bar_y + j * 8)
                    pdf.set_font("Helvetica", "B", 7.5)
                    pdf.set_text_color(*bar_color)
                    pdf.cell(20, 6, f"{seg_rate}%", ln=0)

                pdf.set_y(bar_y + len(breakdown[:6]) * 8 + 5)
                pdf.set_draw_color(*BORDER)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(5)

    # ── PAGE 4: ML MODEL PERFORMANCE ───────────────────────────
    if metrics:
        pdf.add_page()
        pdf.section_title("ML Model Performance")

        best_model   = str(full_results.get("best_model") or metrics.get("best_model","XGBoost"))
        problem_type = str(full_results.get("problem_type") or metrics.get("problem_type","classification"))
        target_col_r = str(full_results.get("target_column") or metrics.get("target_column","target"))
        feat_count   = full_results.get("feature_count","N/A")
        train_rows_raw = full_results.get("training_rows", 0)
        train_rows   = int(train_rows_raw) if train_rows_raw and str(train_rows_raw).isdigit() else 0

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRAY)
        desc = (f"{best_model} was selected as the best model for this "
                f"{problem_type.replace('_',' ')} task, trained on "
                f"{train_rows:,} records using {feat_count} features "
                f"with '{target_col_r}' as the prediction target.")
        pdf.multi_cell(0, 5, safe_text(desc))
        pdf.ln(5)

        # Metrics table header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*WHITE)
        pdf.set_fill_color(*DARK)
        pdf.cell(80, 7, "Metric", fill=True, border=1)
        pdf.cell(50, 7, "Score", fill=True, border=1)
        pdf.cell(0,  7, "Interpretation", fill=True, border=1, ln=True)

        metric_explanations = {
            "auc_roc":         "Overall model quality. Score > 0.85 is strong.",
            "precision":       "Of predicted positives, how many were correct.",
            "recall":          "Of actual positives, how many were found.",
            "f1_score":        "Balance between precision and recall.",
            "accuracy":        "Overall prediction accuracy.",
            "rmse":            "Root mean square error. Lower is better.",
            "mae":             "Mean absolute error. Lower is better.",
            "r2_score":        "Variance explained by model. Closer to 1 is better.",
            "f1_macro":        "F1 averaged across all classes.",
            "silhouette_score":"Cluster quality. Closer to 1 is better.",
        }

        actual_metrics = full_results.get("metrics") or metrics
        if isinstance(actual_metrics, dict):
            for i, (k, v) in enumerate(actual_metrics.items()):
                if isinstance(v, (int, float, str)):
                    explanation = metric_explanations.get(k, "Performance metric")
                    fill_color  = LIGHT_GRAY if i % 2 == 0 else WHITE
                    pdf.set_fill_color(*fill_color)
                    pdf.set_text_color(*DARK)
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.cell(80, 6.5, safe_text(k.replace("_"," ").upper()), fill=True, border="B")
                    pdf.set_font("Helvetica", "B", 8.5)
                    pdf.set_text_color(*BLUE)
                    pdf.cell(50, 6.5, safe_text(str(v)), fill=True, border="B")
                    pdf.set_font("Helvetica", "", 7.5)
                    pdf.set_text_color(*GRAY)
                    pdf.cell(0, 6.5, safe_text(explanation), fill=True, border="B", ln=True)

        # AutoML comparison
        automl = full_results.get("automl_comparison", {})
        if automl:
            pdf.ln(8)
            pdf.section_title("AutoML Model Comparison")
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(*WHITE)
            pdf.set_fill_color(*DARK)
            first_metrics = list(list(automl.values())[0].keys())[:4] if automl else []
            pdf.cell(55, 7, "Model", fill=True, border=1)
            for col_name in first_metrics:
                pdf.cell(30, 7, safe_text(col_name.replace("_"," ").upper()[:10]), fill=True, border=1)
            pdf.cell(0, 7, "Selected", fill=True, border=1, ln=True)

            best = str(full_results.get("best_model",""))
            for i, (model_name, model_metrics) in enumerate(automl.items()):
                is_best = model_name == best
                pdf.set_fill_color(*LIGHT_GRAY if i % 2 == 0 else WHITE)
                pdf.set_font("Helvetica", "B" if is_best else "", 8.5)
                pdf.set_text_color(*BLUE if is_best else DARK)
                label = safe_text(model_name + (" [BEST]" if is_best else ""))
                pdf.cell(55, 6.5, label, fill=True, border="B")
                pdf.set_font("Helvetica", "", 8.5)
                for val in list(model_metrics.values())[:4]:
                    pdf.cell(30, 6.5, safe_text(str(val)), fill=True, border="B")
                pdf.cell(0, 6.5, "Best" if is_best else "-", fill=True, border="B", ln=True)

    # ── PAGE 5: AT-RISK RECORDS ─────────────────────────────────
    if at_risk:
        pdf.add_page()
        pdf.section_title("At-Risk Records")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 5, safe_text(
            f"Top {len(at_risk)} records identified as highest risk. Prioritise these for immediate intervention."))
        pdf.ln(5)

        headers = list(at_risk[0].keys())[:7]
        col_w   = 170 / len(headers)

        pdf.set_fill_color(*DARK)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 7.5)
        for h in headers:
            pdf.cell(col_w, 7, safe_text(str(h).replace("_"," ")[:12].upper()), fill=True, border=1)
        pdf.ln()

        for i, row in enumerate(at_risk[:15]):
            fill_color = LIGHT_GRAY if i % 2 == 0 else WHITE
            pdf.set_fill_color(*fill_color)
            pdf.set_font("Helvetica", "", 7.5)
            for h in headers:
                val = safe_text(str(row.get(h,""))[:12])
                if "risk" in h.lower() or "prob" in h.lower():
                    try:
                        risk_val = float(row.get(h, 0))
                        pdf.set_text_color(*RED if risk_val > 70 else ORANGE if risk_val > 40 else GREEN)
                    except:
                        pdf.set_text_color(*DARK)
                else:
                    pdf.set_text_color(*DARK)
                pdf.cell(col_w, 6, val, fill=True, border="B")
            pdf.ln()

    # ── PAGE 6: RECOMMENDATIONS ────────────────────────────────
    if recommendations:
        pdf.add_page()
        pdf.section_title("Strategic Recommendations")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 5, safe_text(
            "Data-driven recommendations derived from analysis and predictive model. "
            "Each includes a specific action, expected impact, and supporting data."))
        pdf.ln(5)

        colors_list = [BLUE, GREEN, ORANGE]
        for i, rec in enumerate(recommendations[:3]):
            c     = colors_list[i % 3]
            box_y = pdf.get_y()

            pdf.set_fill_color(*c)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_xy(20, box_y)
            pdf.cell(8, 8, str(i+1), fill=True, align="C", ln=0)

            pdf.set_xy(30, box_y + 1)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK)
            title = safe_text(rec.get("title", f"Recommendation {i+1}")[:60])
            pdf.cell(0, 6, title, ln=True)

            box_y2 = pdf.get_y()
            pdf.set_fill_color(*LIGHT_GRAY)
            pdf.set_draw_color(*BORDER)
            pdf.rect(30, box_y2, 160, 24, "FD")
            pdf.set_fill_color(*c)
            pdf.rect(30, box_y2, 1.5, 24, "F")

            pdf.set_xy(34, box_y2 + 2)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.set_text_color(*GRAY)
            pdf.cell(40, 4, "ACTION", ln=0)
            pdf.set_xy(104, box_y2 + 2)
            pdf.cell(40, 4, "EXPECTED IMPACT", ln=True)

            pdf.set_xy(34, box_y2 + 6)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(68, 4.5, safe_text(rec.get("action","")[:80]))

            pdf.set_xy(104, box_y2 + 6)
            pdf.multi_cell(82, 4.5, safe_text(rec.get("impact","")[:80]))

            pdf.set_xy(34, box_y2 + 18)
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.set_text_color(*GRAY)
            pdf.cell(0, 4, safe_text(f"Data: {rec.get('metric','')[:80]}"), ln=True)
            pdf.set_y(box_y2 + 28)

    # ── PAGE 7: CHARTS ─────────────────────────────────────────
    if charts_dir and os.path.exists(charts_dir):
        charts = [f for f in os.listdir(charts_dir) if f.endswith(".png")]
        if charts:
            pdf.add_page()
            pdf.section_title("Visual Insights")
            chart_y   = pdf.get_y()
            positions = [(20, chart_y), (110, chart_y), (20, chart_y+75), (110, chart_y+75)]
            for i, chart in enumerate(charts[:4]):
                chart_path = os.path.join(charts_dir, chart)
                if os.path.exists(chart_path) and i < len(positions):
                    try:
                        x, y = positions[i]
                        pdf.image(chart_path, x=x, y=y, w=85)
                        pdf.set_xy(x, y + 68)
                        pdf.set_font("Helvetica", "", 7)
                        pdf.set_text_color(*GRAY)
                        name = safe_text(chart.replace("_"," ").replace(".png","").title())
                        pdf.cell(85, 4, name, align="C", ln=False)
                    except: pass

    # ── PAGE 8: EXECUTIVE NARRATIVE ────────────────────────────
    if narrative:
        pdf.add_page()
        pdf.section_title("Executive Narrative")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 5, f"AI-generated analysis  |  {now}", ln=True)
        pdf.ln(3)
        paragraphs = [p.strip() for p in narrative.split("\n\n") if p.strip()]
        for para in paragraphs:
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(0, 5.5, safe_text(para))
            pdf.ln(4)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    pdf.output(output_path)
    return output_path
