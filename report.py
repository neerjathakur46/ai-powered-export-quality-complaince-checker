from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from xml.sax.saxutils import escape


def create_pdf_report(
    report_path,
    assessment_id,
    created_at,
    product,
    assessment,
    extracted_text,
    image_count
):

    doc = SimpleDocTemplate(
        report_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "EXPORT QUALITY COMPLIANCE CHECKER",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            "Preliminary Digital Assessment Report",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "<b>Assessment ID:</b> " + escape(assessment_id),
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "<b>Date:</b> " + escape(created_at),
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    # PRODUCT DETAILS
    story.append(
        Paragraph("1. Product Information", styles["Heading2"])
    )

    product_rows = [
        ["Product name", product.get("name") or "Not provided"],
        ["Category", product.get("category") or "Not provided"],
        ["Destination", product.get("destination") or "Not provided"],
        ["Batch number", product.get("batch_number") or "Not provided"],
        ["Net weight", product.get("net_weight") or "Not provided"],
        ["Country of origin", product.get("country_origin") or "Not provided"],
        ["Images uploaded", str(image_count)]
    ]

    product_table = Table(
        product_rows,
        colWidths=[50 * mm, 110 * mm]
    )

    product_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(product_table)
    story.append(Spacer(1, 15))

    # ASSESSMENT RESULT
    story.append(
        Paragraph("2. Assessment Result", styles["Heading2"])
    )

    story.append(
        Paragraph(
            "<b>Compliance score:</b> "
            + str(assessment["score"]) + " / 100",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "<b>Status:</b> " + escape(assessment["status"]),
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 12))

    # CHECKS
    story.append(
        Paragraph("3. Checks Performed", styles["Heading2"])
    )

    check_rows = [["Check", "Result"]]

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=11
    )

    for check in assessment["checks"]:

        check_rows.append([
            Paragraph(escape(check["name"]), small_style),
            Paragraph(escape(check["result"]), small_style)
        ])

    check_table = Table(
        check_rows,
        colWidths=[60 * mm, 100 * mm],
        repeatRows=1
    )

    check_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(check_table)
    story.append(Spacer(1, 12))

    # OBSERVATIONS
    story.append(
        Paragraph("4. Observations", styles["Heading2"])
    )

    for observation in assessment["observations"]:

        story.append(
            Paragraph(
                "• " + escape(observation),
                small_style
            )
        )

        story.append(Spacer(1, 5))

    # OCR TEXT
    if extracted_text:

        story.append(
            Paragraph(
                "5. Extracted Label Text",
                styles["Heading2"]
            )
        )

        safe_text = escape(extracted_text[:2500])
        safe_text = safe_text.replace("\n", "<br/>")

        story.append(
            Paragraph(safe_text, small_style)
        )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>Important disclaimer:</b> This is an academic "
            "prototype and preliminary assessment only. It is not "
            "an official government certificate, legal opinion, "
            "laboratory test or guarantee of export eligibility. "
            "The checks use a limited set of generic demonstration "
            "rules. Consult the relevant authority or a qualified "
            "certification professional before exporting.",
            small_style
        )
    )

    doc.build(story)