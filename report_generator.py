"""
report_generator.py
--------------------
Professional PDF incident-report generation using ReportLab.

Generates two kinds of documents:
    * generate_incident_report(alert, ...) -> per-alert emergency report
    * generate_admin_report(stats, alerts) -> system-wide analytics report

Reports are written to the reports/ directory and the path is recorded in
the `Reports` collection so they can be downloaded later.
"""

import os
import uuid
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from database import get_database

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

PRIMARY = colors.HexColor("#7b2ff7")
ACCENT = colors.HexColor("#d32f2f")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleBig",
            fontSize=20,
            leading=24,
            textColor=PRIMARY,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHead",
            fontSize=13,
            leading=16,
            textColor=ACCENT,
            spaceBefore=10,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small", fontSize=9, leading=12, textColor=colors.grey
        )
    )
    return styles


def _kv_table(rows):
    table = Table(rows, colWidths=[55 * mm, 110 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ]
        )
    )
    return table


# --------------------------------------------------------------------------- #
# Incident report
# --------------------------------------------------------------------------- #
def generate_incident_report(alert, recommendations=None, notifications=None):
    styles = _styles()
    report_id = str(uuid.uuid4())[:8]
    filename = f"incident_{report_id}.pdf"
    path = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=18 * mm)
    flow = []

    flow.append(Paragraph("Emergency Incident Report", styles["TitleBig"]))
    flow.append(
        Paragraph(
            "AI-Powered Smart Women Safety &amp; Emergency Response System",
            styles["Small"],
        )
    )
    flow.append(Spacer(1, 8))

    flow.append(Paragraph("Alert Summary", styles["SubHead"]))
    flow.append(
        _kv_table(
            [
                ["Alert ID", alert.get("alert_id", "—")],
                ["User", alert.get("user_name", "—")],
                ["Status", alert.get("status", "—")],
                ["Risk Level", alert.get("risk_level", "—")],
                ["Risk Score", str(alert.get("risk_score", "—"))],
                ["Battery Level", f"{alert.get('battery_level', '—')}%"],
                ["Created At", alert.get("created_at", "—")],
                ["Resolved At", alert.get("resolved_at") or "Not resolved"],
            ]
        )
    )

    flow.append(Paragraph("Location Details", styles["SubHead"]))
    flow.append(
        _kv_table(
            [
                ["Address", alert.get("address", "—")],
                ["Latitude", str(alert.get("latitude", "—"))],
                ["Longitude", str(alert.get("longitude", "—"))],
                ["Nearest Safe Place",
                 f"{alert.get('distance_to_safe_km', '—')} km away"],
            ]
        )
    )

    if recommendations:
        flow.append(Paragraph("Safety Recommendations", styles["SubHead"]))
        for r in recommendations:
            flow.append(Paragraph(f"• {r}", styles["Normal"]))

    if notifications:
        flow.append(Paragraph("Contacts Notified", styles["SubHead"]))
        rows = [["Contact", "Status"]]
        for n in notifications:
            rows.append([n.get("name", "—"),
                         "Notified" if n.get("ok") else n.get("message", "—")])
        t = Table(rows, colWidths=[80 * mm, 85 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#f6f1ff")]),
                ]
            )
        )
        flow.append(t)

    flow.append(Spacer(1, 16))
    flow.append(
        Paragraph(
            f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Small"],
        )
    )

    doc.build(flow)

    # Record in DB
    db = get_database()
    db.add(
        "Reports",
        {
            "report_id": report_id,
            "user_id": alert.get("user_id"),
            "alert_id": alert.get("alert_id"),
            "report_path": path,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return path


# --------------------------------------------------------------------------- #
# Admin report
# --------------------------------------------------------------------------- #
def generate_admin_report(stats, alerts):
    styles = _styles()
    report_id = str(uuid.uuid4())[:8]
    filename = f"admin_report_{report_id}.pdf"
    path = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=18 * mm)
    flow = []

    flow.append(Paragraph("System Safety Report", styles["TitleBig"]))
    flow.append(
        Paragraph("Administrator Analytics Summary", styles["Small"])
    )
    flow.append(Spacer(1, 8))

    flow.append(Paragraph("Key Metrics", styles["SubHead"]))
    flow.append(
        _kv_table(
            [
                ["Total Users", str(stats.get("total_users", 0))],
                ["Total Alerts", str(stats.get("total_alerts", 0))],
                ["Active Alerts", str(stats.get("active_alerts", 0))],
                ["Resolved Alerts", str(stats.get("resolved_alerts", 0))],
                ["High/Critical Alerts", str(stats.get("high_risk_alerts", 0))],
            ]
        )
    )

    flow.append(Paragraph("Recent Alerts", styles["SubHead"]))
    rows = [["Time", "User", "Risk", "Status"]]
    for _, a in alerts[:20]:
        rows.append(
            [
                str(a.get("created_at", ""))[:16],
                a.get("user_name", "—"),
                a.get("risk_level", "—"),
                a.get("status", "—"),
            ]
        )
    t = Table(rows, colWidths=[42 * mm, 50 * mm, 38 * mm, 35 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f6f1ff")]),
            ]
        )
    )
    flow.append(t)

    flow.append(Spacer(1, 16))
    flow.append(
        Paragraph(
            f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Small"],
        )
    )
    doc.build(flow)
    return path
