"""BOM & Manpower template — bill of materials with labor estimation."""

from datetime import date
from reportlab.platypus import Table, TableStyle

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak

from bid_engine import styles as S
from bid_engine.models import Bid
from bid_engine.pdf_generator import PDFGenerator


class BOMManpowerGenerator(PDFGenerator):
    """Generates the BOM + Manpower document.

    Sections:
    1. Header with project info
    2. Bill of Materials (BOM) table
    3. Manpower estimation table
    4. Productivity factors
    5. Cost summary
    6. Compliance references
    """

    def build_story(self) -> list:
        story: list = []
        b = self.bid
        today_str = (b.bid_date or date.today()).strftime("%B %d, %Y")
        p = b.project

        # Header
        story.append(Paragraph("BILL OF MATERIALS & MANPOWER", self.styles["CoverTitle"]))
        story.append(Spacer(1, 0.15 * S.inch))
        story.append(
            Paragraph(
                f"{b.trade.name} Scope — Sheet Metal & Installation",
                self.styles["CoverSubtitle"],
            )
        )
        story.append(HRFlowable(width="100%", thickness=2, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))

        proj_info = [
            ["Project:", f"{p.name} — {p.address}, {p.city}, {p.state}"],
            ["Owner:", p.owner],
            ["Prepared By:", b.bidder.company_name],
            ["Date:", today_str],
            ["Reference:", p.reference_sheets.get("mechanical", "N/A")],
        ]
        proj_table = Table(proj_info, colWidths=[1.2 * S.inch, 4.8 * S.inch])
        proj_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(proj_table)
        story.append(Spacer(1, 0.2 * S.inch))

        # Section 1: Bill of Materials
        story.append(Paragraph("SECTION 1: BILL OF MATERIALS", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))
        story.append(Paragraph("1.1 Sheet Metal Ductwork", self.styles["SubHeader"]))

        bom_duct_data = [
            [
                S._tc("Item #", bold=True),
                S._tc("Description", bold=True),
                S._tc("Specification", bold=True),
                S._tc("Qty", bold=True),
                S._tc("Unit", bold=True),
                S._tc("Unit Cost", bold=True),
                S._tc("Total", bold=True),
            ],
            [
                "1.01",
                S._tc("Fabricated Sheet Metal Duct"),
                S._tc("24ga galvanized, SMACNA Class A"),
                "6,000",
                "lbs",
                "$4.00",
                "$24,000",
            ],
            [
                "1.02",
                S._tc("Fabricated Sheet Metal Duct"),
                S._tc("22ga galvanized, SMACNA Class A"),
                "1,500",
                "lbs",
                "$4.50",
                "$6,750",
            ],
            [
                "1.03",
                S._tc("Duct Takeoff Fittings"),
                "Elbows, tees, reducers",
                "Incl",
                "lot",
                "-",
                "$3,000",
            ],
            [
                "1.04",
                S._tc("Flex Duct (Conn./Drops)"),
                S._tc('R-8 insulated, 12" dia'),
                "40",
                "ea",
                "$30",
                "$1,200",
            ],
            ["1.05", "Duct End Caps/Plenums", "24ga galvanized", "20", "ea", "$15", "$300"],
            [
                "",
                S._tc("DUCTWORK MATERIAL SUBTOTAL", bold=True),
                "",
                "",
                "",
                "",
                S._tc("$35,250", bold=True),
            ],
        ]
        bom_duct_table = Table(
            bom_duct_data,
            colWidths=[
                0.5 * S.inch,
                1.6 * S.inch,
                1.5 * S.inch,
                0.6 * S.inch,
                0.5 * S.inch,
                0.7 * S.inch,
                0.7 * S.inch,
            ],
            repeatRows=1,
        )
        bom_duct_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (3, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(bom_duct_table)

        story.append(Spacer(1, 0.15 * S.inch))
        story.append(Paragraph("1.2 Duct Hangers & Supports", self.styles["SubHeader"]))
        bom_hanger_data = [
            [
                S._tc("Item #", bold=True),
                S._tc("Description", bold=True),
                S._tc("Specification", bold=True),
                S._tc("Qty", bold=True),
                S._tc("Unit", bold=True),
                S._tc("Unit Cost", bold=True),
                S._tc("Total", bold=True),
            ],
            [
                "2.01",
                S._tc("Galvanized Strap Hangers"),
                S._tc('1" x 26ga galvanized'),
                "500",
                "ea",
                "$0.85",
                "$425",
            ],
            [
                "2.02",
                S._tc('Threaded Rod (1/4")'),
                S._tc('12" long with hardware'),
                "200",
                "ea",
                "$2.50",
                "$500",
            ],
            ["2.03", "Duct Standoff Brackets", "12ga galvanized", "100", "ea", "$3.00", "$300"],
            [
                "2.04",
                S._tc("Turnbuckles/Safety Brackets"),
                "For seismic",
                "50",
                "ea",
                "$5.00",
                "$250",
            ],
            ["2.05", "Splice Connectors", "Duct-to-duct", "80", "ea", "$1.50", "$120"],
            [
                "",
                S._tc("HANGERS & SUPPORTS SUBTOTAL", bold=True),
                "",
                "",
                "",
                "",
                S._tc("$1,595", bold=True),
            ],
        ]
        bom_hanger_table = Table(
            bom_hanger_data,
            colWidths=[
                0.5 * S.inch,
                1.6 * S.inch,
                1.5 * S.inch,
                0.6 * S.inch,
                0.5 * S.inch,
                0.7 * S.inch,
                0.7 * S.inch,
            ],
            repeatRows=1,
        )
        bom_hanger_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (3, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(bom_hanger_table)

        story.append(Spacer(1, 0.15 * S.inch))
        story.append(Paragraph("1.3 Insulation", self.styles["SubHeader"]))
        bom_insul_data = [
            [
                S._tc("Item #", bold=True),
                S._tc("Description", bold=True),
                S._tc("Specification", bold=True),
                S._tc("Qty", bold=True),
                S._tc("Unit", bold=True),
                S._tc("Unit Cost", bold=True),
                S._tc("Total", bold=True),
            ],
            [
                "3.01",
                "Duct Wrap Insulation",
                S._tc('R-8, 2" thick, foil faced'),
                "3,000",
                "SF",
                "$1.25",
                "$3,750",
            ],
            ["3.02", "Insulation Jackets", "For external duct", "500", "LF", "$2.00", "$1,000"],
            ["3.03", "Mastic/Sealant", "Duct sealer", "5", "gal", "$35", "$175"],
            ["3.04", "UV Protective Wrap", "Exterior exposed duct", "500", "SF", "$2.50", "$1,250"],
            [
                "",
                S._tc("INSULATION SUBTOTAL", bold=True),
                "",
                "",
                "",
                "",
                S._tc("$6,175", bold=True),
            ],
        ]
        bom_insul_table = Table(
            bom_insul_data,
            colWidths=[
                0.5 * S.inch,
                1.6 * S.inch,
                1.5 * S.inch,
                0.6 * S.inch,
                0.5 * S.inch,
                0.7 * S.inch,
                0.7 * S.inch,
            ],
        )
        bom_insul_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (3, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(bom_insul_table)

        # BOM Summary
        story.append(Spacer(1, 0.2 * S.inch))
        bom_summary_data = [
            [S._tc("BOM Summary", bold=True), S._tc("Amount", bold=True)],
            ["1. Sheet Metal Ductwork", "$35,250"],
            ["2. Hangers & Supports", "$1,595"],
            ["3. Insulation", "$6,175"],
            [S._tc("TOTAL BOM", bold=True), S._tc("$43,020", bold=True)],
        ]
        bom_summary_table = Table(bom_summary_data, colWidths=[3.5 * S.inch, 1.5 * S.inch])
        bom_summary_table.setStyle(
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
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, -1), (-1, -1), 11),
                ]
            )
        )
        story.append(bom_summary_table)
        story.append(PageBreak())

        # Section 2: Manpower
        story.append(Paragraph("SECTION 2: MANPOWER ESTIMATION", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))
        story.append(Paragraph("2.1 Labor Takeoff — Ductwork Scope", self.styles["SubHeader"]))
        story.append(
            Paragraph(
                f"Burdened Labor Rate: ${self.bid.trade.get_labor_rate(self.bid.region):.2f}/hour",
                self.styles["Body"],
            )
        )

        labor_data = [
            [
                S._tc("Phase", bold=True),
                S._tc("Scope Element", bold=True),
                S._tc("Qty", bold=True),
                S._tc("Factor", bold=True),
                S._tc("Hrs", bold=True),
                S._tc("Cost", bold=True),
            ],
        ]
        for li in self.bid.line_items:
            if li.labor_hours > 0:
                labor_data.append(
                    [
                        li.cost_code.split("-")[0] if "-" in li.cost_code else "",
                        S._tc(li.description),
                        S._tc(f"{li.quantity:,.0f} {li.unit}"),
                        S._tc(li.labor_factor or "N/A"),
                        S._tc(f"{li.labor_hours:.0f}"),
                        S._tc(f"${li.total_labor:,.2f}"),
                    ]
                )

        labor_data.append(
            [
                "",
                S._tc("SUBTOTAL LABOR", bold=True),
                "",
                "",
                S._tc(f"{self.bid.total_labor_hours:.0f} hrs", bold=True),
                S._tc(f"${self.bid.total_labor:,.2f}", bold=True),
            ]
        )

        labor_table = Table(
            labor_data,
            colWidths=[
                0.9 * S.inch,
                1.6 * S.inch,
                0.7 * S.inch,
                0.7 * S.inch,
                0.5 * S.inch,
                0.8 * S.inch,
            ],
            repeatRows=1,
        )
        labor_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(labor_table)

        story.append(Spacer(1, 0.2 * S.inch))
        story.append(Paragraph("2.2 Productivity Factors Applied", self.styles["SubHeader"]))
        prod_data = [
            [
                S._tc("Factor", bold=True),
                S._tc("Description", bold=True),
                S._tc("Adjustment", bold=True),
            ],
        ]
        for m in self.bid.trade.complexity_multipliers:
            prod_data.append(
                [
                    S._tc(m["name"]),
                    S._tc(m["rationale"]),
                    S._tc(f"+{(m['adjustment'] - 1) * 100:.0f}% {m['applies_to']}"),
                ]
            )
        prod_table = Table(
            prod_data, colWidths=[1.5 * S.inch, 3.0 * S.inch, 1.5 * S.inch], repeatRows=1
        )
        prod_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(prod_table)

        # Section 3: Cost Summary
        story.append(Spacer(1, 0.2 * S.inch))
        story.append(Paragraph("SECTION 3: COST SUMMARY", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))
        total_cost_data = [
            [S._tc("Category", bold=True), S._tc("Amount", bold=True)],
            ["Bill of Materials (BOM)", f"${self.bid.total_material:,.2f}"],
            [
                f"Manpower/Labor ({self.bid.total_labor_hours:.0f} hrs @ ${self.bid.trade.get_labor_rate(self.bid.region):.2f}/hr)",
                f"${self.bid.total_labor:,.2f}",
            ],
            [
                S._tc("TOTAL DIRECT COST", bold=True),
                S._tc(f"${self.bid.total_direct_cost:,.2f}", bold=True),
            ],
            ["Contingency (5%)", f"${self.bid.contingency_amount:,.2f}"],
            ["Overhead & Profit (15%)", f"${self.bid.overhead_profit_amount:,.2f}"],
            [
                S._tc(f"{self.bid.trade.name} BID TOTAL", bold=True),
                S._tc(f"${self.bid.total_bid_amount:,.2f}", bold=True),
            ],
        ]
        total_cost_table = Table(total_cost_data, colWidths=[3.5 * S.inch, 1.5 * S.inch])
        total_cost_table.setStyle(
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
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, -1), (-1, -1), 12),
                ]
            )
        )
        story.append(total_cost_table)

        # Compliance
        story.append(Spacer(1, 0.4 * S.inch))
        story.append(Paragraph("COMPLIANCE REFERENCES", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))
        for code in self.bid.trade.compliance_codes:
            story.append(
                Paragraph(f"• {code['code_name']} — {code['applies_to']}", self.styles["Body"])
            )

        return story

    def output_filename(self) -> str:
        company = self.bid.bidder.company_name.replace(" ", "_")
        date_str = (self.bid.bid_date or date.today()).strftime("%Y%m%d")
        return f"{company}_INTERNAL_BOM_Manpower_{date_str}.pdf"
