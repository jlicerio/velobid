"""Homeowner-facing proposal PDF for residential HVAC estimates."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_residential_proposal(
    output_path: str,
    project_name: str,
    customer_name: str,
    customer_address: str,
    customer_phone: str,
    scope_description: str,
    equipment_list: list[dict],
    labor_list: list[dict],
    totals: dict,
    bidder_name: str = "Similitude AI",
    bidder_phone: str = "(956) 586-2118",
    proposal_date: str = "",
    valid_days: int = 30,
):
    """Generate a homeowner-facing proposal PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CoverTitle", fontName="Helvetica-Bold", fontSize=22,
        alignment=TA_CENTER, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", fontName="Helvetica", fontSize=12,
        alignment=TA_CENTER, textColor=colors.HexColor("#555555"),
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "SectionHeader", fontName="Helvetica-Bold", fontSize=13,
        spaceBefore=16, spaceAfter=6,
        textColor=colors.HexColor("#1a365d"),
    )
    body_style = ParagraphStyle(
        "Body", fontName="Helvetica", fontSize=10,
        leading=14, spaceAfter=4,
    )
    total_style = ParagraphStyle(
        "Total", fontName="Helvetica-Bold", fontSize=14,
        alignment=TA_RIGHT, spaceBefore=12,
        textColor=colors.HexColor("#1a365d"),
    )
    footer_style = ParagraphStyle(
        "Footer", fontName="Helvetica", fontSize=8,
        alignment=TA_CENTER, textColor=colors.HexColor("#999999"),
        spaceBefore=20,
    )

    story = []

    # Cover
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("HVAC PROPOSAL", title_style))
    story.append(Paragraph(f"{bidder_name} | {bidder_phone}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a365d")))
    story.append(Spacer(1, 0.3 * inch))

    # Project info
    story.append(Paragraph(f"<b>Prepared for:</b> {customer_name}", body_style))
    story.append(Paragraph(f"<b>Property:</b> {customer_address}", body_style))
    if customer_phone:
        story.append(Paragraph(f"<b>Phone:</b> {customer_phone}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {proposal_date}", body_style))
    story.append(Paragraph(f"<b>Valid for:</b> {valid_days} days", body_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))

    # Scope
    story.append(Paragraph("Scope of Work", section_style))
    story.append(Paragraph(scope_description, body_style))
    story.append(Spacer(1, 0.15 * inch))

    # Equipment
    if equipment_list:
        story.append(Paragraph("Equipment", section_style))
        eq_data = [[Paragraph("<b>Item</b>", body_style),
                     Paragraph("<b>Brand</b>", body_style),
                     Paragraph("<b>Model</b>", body_style),
                     Paragraph("<b>Qty</b>", body_style),
                     Paragraph("<b>Total</b>", body_style)]]
        for eq in equipment_list:
            eq_data.append([
                Paragraph(eq.get("description", ""), body_style),
                Paragraph(eq.get("detail", ""), body_style),
                Paragraph("", body_style),
                Paragraph(str(eq.get("qty", 1)), body_style),
                Paragraph(f"${eq.get('total', 0):,.2f}", body_style),
            ])
        eq_table = Table(eq_data, colWidths=[2*inch, 1.3*inch, 1.5*inch, 0.5*inch, 0.8*inch])
        eq_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(eq_table)

    # Labor
    if labor_list:
        story.append(Paragraph("Labor", section_style))
        lab_data = [[Paragraph("<b>Task</b>", body_style),
                      Paragraph("<b>Hours</b>", body_style),
                      Paragraph("<b>Rate</b>", body_style),
                      Paragraph("<b>Total</b>", body_style)]]
        for task in labor_list:
            lab_data.append([
                Paragraph(task.get("description", ""), body_style),
                Paragraph(str(task.get("hours", 0)), body_style),
                Paragraph(f"${task.get('rate', 0):.2f}/hr", body_style),
                Paragraph(f"${task.get('total', 0):,.2f}", body_style),
            ])
        lab_table = Table(lab_data, colWidths=[3*inch, 0.8*inch, 1*inch, 0.8*inch])
        lab_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(lab_table)

    # Totals
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a365d")))
    t = totals
    story.append(Paragraph(f"Equipment Total: ${t.get('equipment_total', 0):,.2f}", body_style))
    story.append(Paragraph(f"Labor Total ({t.get('labor_hours', 0)} hrs): ${t.get('labor_total', 0):,.2f}", body_style))
    story.append(Paragraph(f"Miscellaneous Materials: ${t.get('misc_materials', 0):,.2f}", body_style))
    story.append(Paragraph(f"Permit Fee: ${t.get('permit_fee', 0):,.2f}", body_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"Subtotal: ${t.get('subtotal', 0):,.2f}", body_style))
    story.append(Paragraph(f"Sales Tax ({t.get('tax_rate', 0)*100:.2f}%): ${t.get('tax', 0):,.2f}", body_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"GRAND TOTAL: ${t.get('grand_total', 0):,.2f}", total_style))

    # Terms
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Terms & Conditions", section_style))
    story.append(Paragraph(
        "This proposal is valid for 30 days from the date above. "
        "Payment is due upon completion unless otherwise agreed. "
        f"All work carries a {t.get('labor_warranty_months', 12)}-month labor warranty. "
        "Manufacturer warranties apply to equipment as per their terms. "
        "Any additional work discovered during installation will be quoted separately.",
        body_style,
    ))

    # Signature
    story.append(Spacer(1, 0.5 * inch))
    sig_data = [
        ["Accepted by: ________________________", f"Date: ______________"],
        ["", ""],
        [f"{bidder_name} Representative: ________________________", "Date: ______________"],
    ]
    sig_table = Table(sig_data, colWidths=[3*inch, 2*inch])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Paragraph(
        f"{bidder_name} | {bidder_phone} | Licensed & Insured",
        footer_style,
    ))

    doc.build(story)
    return output_path
