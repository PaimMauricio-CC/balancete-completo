"""Generate compact, polished PDF summaries for completed audits."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#142B2A")
GREEN = colors.HexColor("#2F755A")
GREEN_SOFT = colors.HexColor("#DCEBE1")
CORAL = colors.HexColor("#E66F51")
PAPER = colors.HexColor("#F4F1E9")
MUTED = colors.HexColor("#69716C")
LINE = colors.HexColor("#D7D2C6")


def format_brl(value) -> str:
    number = Decimal(str(value or 0))
    formatted = f"{number:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def _styles():
    styles = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle("Eyebrow", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9, textColor=GREEN, spaceAfter=4, uppercase=True),
        "title": ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=INK, alignment=TA_LEFT, spaceAfter=6),
        "subtitle": ParagraphStyle("Subtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=14, textColor=MUTED),
        "section": ParagraphStyle("Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=8),
        "body": ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=12, textColor=INK),
        "small": ParagraphStyle("Small", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=10, textColor=MUTED),
        "table_header": ParagraphStyle("TableHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=10, textColor=colors.white),
        "metric_label": ParagraphStyle("MetricLabel", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=6.5, leading=8, textColor=MUTED, uppercase=True),
        "metric_value": ParagraphStyle("MetricValue", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=INK),
    }


def _page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(INK)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(18 * mm, height - 7.7 * mm, "CLARA  /  RELATORIO DE AUDITORIA")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 9 * mm, datetime.now().strftime("Gerado em %d/%m/%Y as %H:%M"))
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Pagina {doc.page}")
    canvas.restoreState()


def _metric_cards(metrics, styles):
    cells = []
    for label, value in metrics:
        cells.append([
            Paragraph(label.upper(), styles["metric_label"]),
            Spacer(1, 3),
            Paragraph(str(value), styles["metric_value"]),
        ])
    table = Table([cells], colWidths=[(A4[0] - 36 * mm) / max(1, len(cells))] * len(cells))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), .6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), .6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def _bar_chart(items, value_formatter=None):
    drawing = Drawing(500, 180)
    chart = VerticalBarChart()
    chart.x = 42
    chart.y = 32
    chart.height = 120
    chart.width = 420
    values = [float(value) for _label, value in items]
    chart.data = [values]
    chart.categoryAxis.categoryNames = [label for label, _value in items]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.dy = -6
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(values or [1]) * 1.18 or 1
    chart.valueAxis.valueStep = max(chart.valueAxis.valueMax / 4, 1)
    chart.valueAxis.labelTextFormat = lambda value: f"{value:,.0f}".replace(",", ".")
    chart.bars[0].fillColor = GREEN
    chart.bars[0].strokeColor = GREEN
    chart.barWidth = 22
    drawing.add(chart)
    if value_formatter:
        for index, value in enumerate(values):
            x = chart.x + (index + .5) * (chart.width / max(1, len(values)))
            y = chart.y + chart.height * (value / chart.valueAxis.valueMax) + 5
            drawing.add(String(x, y, value_formatter(value), textAnchor="middle", fontName="Helvetica-Bold", fontSize=6.5, fillColor=INK))
    return drawing


def build_audit_pdf(
    title: str,
    subtitle: str,
    metrics,
    chart_items,
    chart_title: str,
    details=None,
    observations=None,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm, bottomMargin=20 * mm, title=title, author="Clara")
    styles = _styles()
    story = [
        Paragraph("RESUMO DA ANALISE", styles["eyebrow"]),
        Paragraph(title, styles["title"]),
        Paragraph(subtitle, styles["subtitle"]),
        Spacer(1, 10 * mm),
        _metric_cards(metrics, styles),
        Spacer(1, 8 * mm),
    ]

    if chart_items:
        story.extend([
            Paragraph(chart_title, styles["section"]),
            _bar_chart(chart_items, lambda value: f"{value:,.0f}".replace(",", ".")),
            Spacer(1, 4 * mm),
        ])

    if details:
        story.append(Paragraph("Detalhamento", styles["section"]))
        detail_rows = [
            [Paragraph(str(cell), styles["table_header"] if row_index == 0 else styles["small"]) for cell in row]
            for row_index, row in enumerate(details)
        ]
        table = Table(detail_rows, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .5, LINE),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([table, Spacer(1, 5 * mm)])

    if observations:
        story.append(KeepTogether([
            Paragraph("Leitura do resultado", styles["section"]),
            Paragraph(observations, styles["body"]),
        ]))

    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buffer.getvalue()


def build_esocial_pdf(report) -> bytes:
    totals = report.totals
    details = [["Competencia", "Rendimentos", "INSS", "IRRF", "13o salario"]]
    details.extend([
        [month.period_label, format_brl(month.taxable_income), format_brl(month.inss), format_brl(month.irrf), format_brl(month.thirteenth_salary)]
        for month in report.months
    ])
    return build_audit_pdf(
        title="Informe de rendimentos eSocial",
        subtitle=f"CPF {report.worker_cpf_formatted}  |  {report.employer_registration_formatted}  |  {report.source_count} XML(s) validado(s)",
        metrics=[
            ("Rendimentos", format_brl(totals["taxable_income"])),
            ("INSS", format_brl(totals["inss"])),
            ("IRRF", format_brl(totals["irrf"])),
            ("13o salario", format_brl(totals["thirteenth_salary"])),
        ],
        chart_items=[(month.period_label, month.taxable_income) for month in report.months],
        chart_title="Evolucao dos rendimentos por competencia",
        details=details,
        observations="Os valores foram consolidados a partir dos grupos totInfoIR/consolidApurMen dos eventos eSocial S-5002 enviados. Registros duplicados foram desconsiderados.",
    )
