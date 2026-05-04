"""Cost Summary template — standalone ductwork cost breakdown document."""

from datetime import date
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak

from bid_engine import styles as S
from bid_engine.models import Bid
from bid_engine.pdf_generator import PDFGenerator


class CostSummaryGenerator(PDFGenerator):
    """Generates the standalone cost summary / ductwork estimation PDF.

    Sections:
    1. Cover page
    2. Scope overview
    3. Ductwork pricing matrix
    4. Labor estimation
    5. Cost summary
    6. Compliance
    """

    def build_story(self) -> list:
        story: list = []
        b = self.bid
        p = b.project
        today_str = (b.bid_date or date.today()).strftime("%B %d, %Y")

        # Cover page
        story.append(Spacer(1, 1.5 * inch))
        story.append(S.Paragraph("DUCTWORK ESTIMATION", self.styles["CoverTitle"]))
        story.append(Spacer(1, 0.3 * inch))
        story.append(S.Paragraph(p.name, self.styles["CoverSubtitle"]))
        story.append(S.Paragraph(f"{p.address}, {p.city}, {p.state}", self.styles["CoverSubtitle"]))
        story.append(Spacer(1, 1.5 * inch))

        cover_data = [
            ["Prepared For:", p.owner],
            ["Project:", p.name],
            ["Scope:", "Sheet Metal & Ductwork Only"],
            ["Building Area:", f"{p.total_area_sf:,.0f} SF"],
            ["Date:", today_str],
            ["Prepared By:", b.bidder.company_name],
        ]
        cover_table = Table(cover_data, colWidths=[1.8 * inch, 4.0 * inch])
        cover_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(cover_table)
        story.append(PageBreak())

        # Scope Overview
        story.append(S.Paragraph("1.0 SCOPE OVERVIEW", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            S.Paragraph(
                f"This estimation covers the sheet metal and ductwork scope for the {p.name} "
                f"HVAC installation. Ductwork is suspended throughout the building.",
                self.styles["Body"],
            )
        )
        story.append(Spacer(1, 0.1 * inch))
        for cat in b.trade.equipment_categories[:5]:
            story.append(S.Paragraph(f"• {cat}", self.styles["Body"]))

        # Ductwork Pricing
        story.append(Spacer(1, 0.2 * inch))
        story.append(S.Paragraph("2.0 DUCTWORK PRICING MATRIX", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * inch))
        story.append(S.Paragraph("2.1 Material & Equipment", self.styles["SubHeader"]))

        mat_data = [
            [
                S._tc("Description", bold=True),
                S._tc("Quantity", bold=True),
                S._tc("Unit Cost", bold=True),
                S._tc("Total", bold=True),
            ],
        ]
        for li in b.line_items:
            if li.unit_cost_material > 0:
                mat_data.append(
                    [
                        S._tc(li.description),
                        S._tc(f"{li.quantity:,.0f} {li.unit}"),
                        S._tc(f"${li.unit_cost_material:.2f}"),
                        S._tc(f"${li.total_material:,.2f}"),
                    ]
                )
        mat_data.append(
            [
                S._tc("MATERIAL SUBTOTAL", bold=True),
                "",
                "",
                S._tc(f"${b.total_material:,.2f}", bold=True),
            ]
        )

        mat_table = Table(
            mat_data,
            colWidths=[2.5 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch],
            repeatRows=1,
        )
        mat_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(mat_table)

        story.append(Spacer(1, 0.15 * inch))
        story.append(S.Paragraph("2.2 Labor Estimation", self.styles["SubHeader"]))
        story.append(
            S.Paragraph(
                f"Based on ${b.trade.get_labor_rate(b.region):.2f}/hour fully burdened labor rate",
                self.styles["Body"],
            )
        )

        labor_data = [
            [
                S._tc("Phase", bold=True),
                S._tc("Scope", bold=True),
                S._tc("Qty", bold=True),
                S._tc("Rate", bold=True),
                S._tc("Hours", bold=True),
                S._tc("Cost", bold=True),
            ],
        ]
        for li in b.line_items:
            if li.labor_hours > 0:
                labor_data.append(
                    [
                        S._tc(li.cost_code),
                        S._tc(li.description[:25]),
                        S._tc(f"{li.quantity:,.0f} {li.unit}"),
                        S._tc(li.labor_factor or "N/A"),
                        S._tc(f"{li.labor_hours:.0f}"),
                        S._tc(f"${li.total_labor:,.2f}"),
                    ]
                )
        labor_data.append(
            [
                S._tc("LABOR SUBTOTAL", bold=True),
                "",
                "",
                "",
                S._tc(f"{b.total_labor_hours:.0f} hrs", bold=True),
                S._tc(f"${b.total_labor:,.2f}", bold=True),
            ]
        )

        labor_table = Table(
            labor_data,
            colWidths=[
                1.3 * inch,
                1.4 * inch,
                0.8 * inch,
                0.7 * inch,
                0.6 * inch,
                0.7 * inch,
            ],
            repeatRows=1,
        )
        labor_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(labor_table)
        story.append(PageBreak())

        # Cost Summary
        story.append(S.Paragraph("3.0 COST SUMMARY", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * inch))

        summary_data = [
            [S._tc("Category", bold=True), S._tc("Amount", bold=True)],
            ["Ductwork Material", f"${b.total_material:,.2f}"],
            [f"Ductwork Labor ({b.total_labor_hours:.0f} hrs)", f"${b.total_labor:,.2f}"],
            [
                S._tc("Total Direct Cost", bold=True),
                S._tc(f"${b.total_direct_cost:,.2f}", bold=True),
            ],
        ]
        summary_table = Table(summary_data, colWidths=[3.0 * inch, 1.5 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(summary_table)

        story.append(Spacer(1, 0.3 * inch))
        story.append(S.Paragraph("3.1 Unit Metrics", self.styles["SubHeader"]))
        sf_per_dollar = p.total_area_sf / b.total_direct_cost if b.total_direct_cost > 0 else 0
        metrics_data = [
            [S._tc("Metric", bold=True), S._tc("Value", bold=True)],
            [
                "Ductwork Cost per SF",
                f"${b.total_direct_cost / p.total_area_sf * 1000 / 1000:.2f}/SF (of {p.total_area_sf:,.0f} SF building)",
            ],
            [
                "Labor Hours per Pound",
                f"{b.total_labor_hours / max(b.total_material / 100, 1):.3f} hrs/lb",
            ],
            ["Total Ductwork Weight", f"~{b.total_material / 4.0:,.0f} lbs (est.)"],
            ["Total Labor Hours", f"{b.total_labor_hours:.0f} hrs"],
        ]
        metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 2.5 * inch])
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(metrics_table)

        # Compliance
        story.append(Spacer(1, 0.4 * inch))
        story.append(S.Paragraph("4.0 COMPLIANCE", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * inch))
        for code in b.trade.compliance_codes[:4]:
            story.append(
                S.Paragraph(f"• {code['code_name']} — {code['applies_to']}", self.styles["Body"])
            )

        story.append(Spacer(1, 0.4 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.2 * inch))
        sig_data = [
            ["Prepared By:", b.bidder.company_name],
            ["Contact:", f"{b.bidder.primary_contact}  |  {b.bidder.phone}"],
            ["Date:", today_str],
        ]
        sig_table = Table(sig_data, colWidths=[1.5 * inch, 3.0 * inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(sig_table)

        return story

    def output_filename(self) -> str:
        company = self.bid.bidder.company_name.replace(" ", "_")
        date_str = (self.bid.bid_date or date.today()).strftime("%Y%m%d")
        return f"{company}_INTERNAL_Cost_Summary_{date_str}.pdf"
