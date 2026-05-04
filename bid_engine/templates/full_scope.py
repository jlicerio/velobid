"""Full Scope template — comprehensive HVAC scope document with pricing matrix."""

from datetime import date
from reportlab.platypus import Table, TableStyle

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak

from bid_engine import styles as S
from bid_engine.models import Bid
from bid_engine.pdf_generator import PDFGenerator


class FullScopeGenerator(PDFGenerator):
    """Generates the full HVAC scope PDF with pricing matrix and manpower estimation.

    Sections:
    1. Cover page
    2. Table of contents
    3. Executive summary
    4. Project specifications
    5. Scope of work (Div 23 HVAC)
    6. HVAC pricing matrix
    7. Manpower estimation matrix
    8. Cost summary
    9. Compliance
    """

    def build_story(self) -> list:
        story: list = []
        b = self.bid
        p = b.project
        today_str = (b.bid_date or date.today()).strftime("%B %d, %Y")

        # Cover page
        story.extend(self._build_cover(p, today_str))
        # TOC
        story.extend(self._build_toc())
        # Exec summary
        story.extend(self._build_executive_summary())
        # Project specs
        story.extend(self._build_project_specs())
        # Scope of work
        story.extend(self._build_scope_of_work())
        # Manpower estimation
        story.extend(self._build_manpower())
        # Cost summary
        story.extend(self._build_cost_summary())
        # Compliance
        story.extend(self._build_compliance())

        return story

    def _build_cover(self, p, today_str: str) -> list:
        story = []
        story.append(Spacer(1, 2 * S.inch))
        story.append(Paragraph("CONSTRUCTION BID PROPOSAL", self.styles["CoverTitle"]))
        story.append(Spacer(1, 0.3 * S.inch))
        story.append(Paragraph(p.name, self.styles["CoverSubtitle"]))
        story.append(Spacer(1, 0.2 * S.inch))
        story.append(Paragraph(f"{p.address}, {p.city}, {p.state}", self.styles["CoverSubtitle"]))
        story.append(Spacer(1, 1.5 * S.inch))

        cover_data = [
            ["Prepared For:", p.owner],
            ["Project Location:", f"{p.address}, {p.city}, {p.state}"],
            ["Total Building Area:", f"{p.total_area_sf:,.0f} SF"],
            ["Project Type:", f"{p.occupancy_group} Church Assembly"],
            ["Construction Type:", p.construction_type],
            ["Scope:", f"{self.bid.trade.full_name} (Div {self.bid.trade.division})"],
            ["Date:", today_str],
            ["Prepared By:", self.bid.bidder.company_name],
        ]
        cover_table = Table(cover_data, colWidths=[2.0 * S.inch, 4.0 * S.inch])
        cover_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(cover_table)
        story.append(Spacer(1, 2 * S.inch))
        story.append(
            Paragraph("CONFIDENTIAL — FOR PROPOSAL PURPOSES ONLY", self.styles["CoverSubtitle"])
        )
        story.append(PageBreak())
        return story

    def _build_toc(self) -> list:
        story = []
        story.append(Paragraph("TABLE OF CONTENTS", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=2, color=S.NAVY))
        story.append(Spacer(1, 0.2 * S.inch))

        # TOC is conditional based on package type (client hides internal sections)
        toc_items: list[tuple[str, str, str]] = [
            ("1.0", "Executive Summary", "3"),
            ("2.0", "Project Specifications", "3"),
            (
                "3.0",
                f"Scope of Work — Division {self.bid.trade.division} {self.bid.trade.full_name}",
                "4",
            ),
        ]
        if self.package_name != "client":
            # Manpower Estimation Matrix is internal-only
            toc_items.append(("4.0", "Manpower Estimation Matrix", "5"))
            toc_items.append(("5.0", "Cost Summary & Pricing", "6"))
            toc_items.append(("6.0", "Compliance & Certifications", "7"))
        else:
            # Client package: Cost Summary & Compliance only
            toc_items.append(("4.0", "Cost Summary & Pricing", "5"))
            toc_items.append(("5.0", "Compliance & Certifications", "6"))

        toc_data = [[t[0], t[1], t[2]] for t in toc_items]
        toc_table = Table(toc_data, colWidths=[0.6 * S.inch, 5.2 * S.inch, 0.5 * S.inch])
        toc_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(toc_table)
        story.append(PageBreak())
        return story

    def _build_executive_summary(self) -> list:
        story = []
        story.append(Paragraph("1.0 EXECUTIVE SUMMARY", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))
        story.append(
            Paragraph(
                f"This bid proposal covers the {self.bid.trade.name} scope and manpower estimation "
                f"for the {self.bid.project.name} project located at "
                f"{self.bid.project.address}, {self.bid.project.city}, {self.bid.project.state}. "
                f"The project consists of a {self.bid.project.total_area_sf:,.0f} SF church assembly building.",
                self.styles["Body"],
            )
        )
        story.append(Spacer(1, 0.2 * S.inch))
        return story

    def _build_project_specs(self) -> list:
        story = []
        p = self.bid.project
        story.append(Paragraph("2.0 PROJECT SPECIFICATIONS", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))

        story.append(Paragraph("2.1 Project Metadata", self.styles["SubHeader"]))
        spec_data = [
            ["Project Name:", p.name],
            ["Location:", f"{p.address}, {p.city}, {p.state}"],
            ["Design Group:", p.design_group],
            ["Structural/Civil:", p.structural_engineer],
            ["MEP Engineer:", p.mep_engineer],
            ["Occupancy:", f"{p.occupancy_group} (Church Assembly)"],
            ["Construction Type:", p.construction_type],
            ["Total Area:", f"{p.total_area_sf:,.0f} SF"],
            ["Max Building Height:", p.max_height],
        ]
        spec_table = Table(spec_data, colWidths=[2.0 * S.inch, 4.5 * S.inch])
        spec_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(spec_table)
        story.append(Spacer(1, 0.15 * S.inch))

        story.append(Paragraph("2.2 Governing Codes & Standards", self.styles["SubHeader"]))
        codes_data = [
            ["Building & Fire:", self.bid.project.governing_codes.get("building", "N/A")],
            ["Mechanical & Energy:", self.bid.project.governing_codes.get("mechanical", "N/A")],
            ["Plumbing & Gas:", self.bid.project.governing_codes.get("plumbing", "N/A")],
            ["Electrical:", self.bid.project.governing_codes.get("electrical", "N/A")],
            ["Accessibility:", self.bid.project.governing_codes.get("accessibility", "N/A")],
        ]
        codes_table = Table(codes_data, colWidths=[2.0 * S.inch, 4.5 * S.inch])
        codes_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(codes_table)
        story.append(PageBreak())
        return story

    def _build_scope_of_work(self) -> list:
        story = []
        b = self.bid
        story.append(
            Paragraph(
                f"3.0 SCOPE OF WORK — DIVISION {b.trade.division} {b.trade.full_name.upper()}",
                self.styles["SectionHeader"],
            )
        )
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))

        story.append(Paragraph("3.1 Mechanical Systems", self.styles["SubHeader"]))
        
        scope_items = []
        trade_scope_key = f"{b.trade.name.lower()}_scope"
        if trade_scope_key in b.project.technical_scope:
            for k, v in b.project.technical_scope[trade_scope_key].items():
                scope_items.append(f"{k.replace('_', ' ').title()}: {v}")
        else:
            scope_items = b.trade.equipment_categories[:8]

        for cat in scope_items:
            story.append(Paragraph(f"• {cat}", self.styles["Body"]))

        story.append(Spacer(1, 0.2 * S.inch))

        # Section 3.2 (Pricing Matrix) is INTERNAL ONLY - never show to clients
        if self.package_name != "client":
            story.append(Paragraph("3.2 Pricing Matrix", self.styles["SubHeader"]))
            story.append(
                Paragraph(
                    f"Based on fully burdened commercial labor rate of ${b.trade.get_labor_rate(b.region):.2f}/hour",
                    self.styles["Body"],
                )
            )

            hvac_data = [
                [
                    S._tc("Scope Category", bold=True),
                    S._tc("Qty / Metric", bold=True),
                    S._tc("Mat. Unit", bold=True),
                    S._tc("Total Mat.", bold=True),
                    S._tc("Labor Hrs", bold=True),
                    S._tc("Labor Cost", bold=True),
                    S._tc("TOTAL", bold=True),
                ],
            ]
            for li in b.line_items:
                hvac_data.append(
                    [
                        S._tc(li.description[:30]),
                        S._tc(f"{li.quantity:,.0f} {li.unit}"),
                        S._tc(f"${li.unit_cost_material:.2f}"),
                        S._tc(f"${li.total_material:,.2f}"),
                        S._tc(f"{li.labor_hours:.1f}"),
                        S._tc(f"${li.total_labor:,.2f}"),
                        S._tc(f"${li.total_phase:,.2f}"),
                    ]
                )

            hvac_data.append(
                [
                    S._tc("SUBTOTAL", bold=True),
                    "",
                    "",
                    S._tc(f"${b.total_material:,.2f}"),
                    S._tc(f"{b.total_labor_hours:.0f} hrs"),
                    S._tc(f"${b.total_labor:,.2f}"),
                    S._tc(f"${b.total_direct_cost:,.2f}", bold=True),
                ]
            )

            hvac_table = Table(
                hvac_data,
                colWidths=[
                    1.4 * S.inch,
                    0.9 * S.inch,
                    0.7 * S.inch,
                    0.75 * S.inch,
                    0.55 * S.inch,
                    0.7 * S.inch,
                    0.75 * S.inch,
                ],
                repeatRows=1,
            )
            hvac_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(hvac_table)

        story.append(PageBreak())
        return story

    def _build_manpower(self) -> list:
        story = []
        b = self.bid

        # Section 4 (Manpower Estimation Matrix) is INTERNAL ONLY - never show to clients
        if self.package_name == "client":
            return story

        story.append(Paragraph("4.0 MANPOWER ESTIMATION MATRIX", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))

        story.append(Paragraph("4.1 Labor Takeoff Pipeline", self.styles["SubHeader"]))
        story.append(
            Paragraph(
                f"Baseline: {b.total_labor_hours:.0f} hrs --> Complexity Multipliers --> Final Adjusted Man-Hours",
                self.styles["Body"],
            )
        )

        man_data = [
            [
                S._tc("Phase", bold=True),
                S._tc("Scope Element", bold=True),
                S._tc("Qty", bold=True),
                S._tc("Factor", bold=True),
                S._tc("Hours", bold=True),
            ],
        ]
        for li in b.line_items:
            if li.labor_hours > 0:
                man_data.append(
                    [
                        li.cost_code,
                        S._tc(li.description),
                        S._tc(f"{li.quantity:,.0f} {li.unit}"),
                        S._tc(li.labor_factor or "N/A"),
                        S._tc(f"{li.labor_hours:.1f}"),
                    ]
                )

        man_data.append(
            [
                S._tc("TOTAL", bold=True),
                "",
                "",
                "",
                S._tc(f"~{b.total_labor_hours:.0f} hrs", bold=True),
            ]
        )

        man_table = Table(
            man_data,
            colWidths=[1.2 * S.inch, 1.7 * S.inch, 0.9 * S.inch, 0.9 * S.inch, 0.8 * S.inch],
            repeatRows=1,
        )
        man_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(man_table)

        story.append(Spacer(1, 0.2 * S.inch))
        story.append(Paragraph("4.2 Complexity Multipliers", self.styles["SubHeader"]))
        mult_data = [
            [
                S._tc("Factor", bold=True),
                S._tc("Adjustment", bold=True),
                S._tc("Rationale", bold=True),
            ],
        ]
        for m in self.bid.trade.complexity_multipliers:
            mult_data.append(
                [
                    S._tc(m["name"]),
                    S._tc(f"+{(m['adjustment'] - 1) * 100:.0f}%"),
                    S._tc(m["rationale"]),
                ]
            )
        mult_table = Table(
            mult_data, colWidths=[1.5 * S.inch, 1.5 * S.inch, 3.0 * S.inch], repeatRows=1
        )
        mult_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(mult_table)
        story.append(PageBreak())
        return story

    def _build_cost_summary(self) -> list:
        story = []
        b = self.bid
        story.append(Paragraph("5.0 COST SUMMARY & PRICING", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))

        # Client mode: show only blended total turnkey amount
        if self.package_name == "client":
            story.append(
                Paragraph(
                    "The following breakdown is a turnkey schedule of values.",
                    self.styles["Body"],
                )
            )
            story.append(Spacer(1, 0.1 * S.inch))
            
            turnkey_data = [
                [S._tc("Description", bold=True), S._tc("Total Amount", bold=True)],
                [f"{b.trade.name} Complete System", f"${b.total_bid_amount:,.2f}"],
            ]
            turnkey_table = Table(turnkey_data, colWidths=[4.0 * S.inch, 1.5 * S.inch])
            turnkey_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 11),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, -1), (-1, -1), 12),
                    ]
                )
            )
            story.append(turnkey_table)
        else:
            # Internal mode: show full cost breakdown
            cost_data = [
                [S._tc("Category", bold=True), S._tc("Amount", bold=True)],
                ["Total Material Cost", f"${b.total_material:,.2f}"],
                [
                    f"Total Labor Cost ({b.total_labor_hours:.0f} hrs @ ${b.trade.get_labor_rate(b.region):.2f}/hr)",
                    f"${b.total_labor:,.2f}",
                ],
                [
                    S._tc("Total Direct Costs", bold=True),
                    S._tc(f"${b.total_direct_cost:,.2f}", bold=True),
                ],
            ]
            cost_table = Table(cost_data, colWidths=[3.5 * S.inch, 1.5 * S.inch])
            cost_table.setStyle(
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
            story.append(cost_table)

            story.append(Spacer(1, 0.15 * S.inch))
            story.append(Paragraph("5.2 Markups & Final Bid", self.styles["SubHeader"]))
            bid_data = [
                [S._tc("Description", bold=True), S._tc("Rate", bold=True), S._tc("Amount", bold=True)],
                ["Total Direct Costs", "-", f"${b.total_direct_cost:,.2f}"],
                ["Contingency", f"{b.contingency_pct:.1f}%", f"${b.contingency_amount:,.2f}"],
                [
                    "Overhead & Profit",
                    f"{b.overhead_profit_pct:.1f}%",
                    f"${b.overhead_profit_amount:,.2f}",
                ],
                [
                    S._tc(f"{b.trade.name} BID SUBTOTAL", bold=True),
                    "",
                    S._tc(f"${b.total_bid_amount:,.2f}", bold=True),
                ],
            ]
            bid_table = Table(bid_data, colWidths=[2.5 * S.inch, 1.0 * S.inch, 1.5 * S.inch])
            bid_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BACKGROUND", (0, -1), (-1, -1), S.LIGHT_GRAY),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, -1), (-1, -1), 11),
                    ]
                )
            )
            story.append(bid_table)
        
        story.append(PageBreak())
        return story

    def _build_compliance(self) -> list:
        story = []
        b = self.bid
        story.append(Paragraph("6.0 COMPLIANCE & CERTIFICATIONS", self.styles["SectionHeader"]))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.1 * S.inch))
        story.append(
            Paragraph("All work shall be performed in strict accordance with:", self.styles["Body"])
        )
        for code in b.trade.compliance_codes:
            story.append(
                Paragraph(f"• {code['code_name']} — {code['applies_to']}", self.styles["Body"])
            )
        story.append(Spacer(1, 0.4 * S.inch))
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY))
        story.append(Spacer(1, 0.2 * S.inch))
        sig_data = [
            ["Submitted By:", b.bidder.primary_contact],
            ["Company:", b.bidder.company_name],
            ["Signature:", ""],
            ["Date:", (b.bid_date or date.today()).strftime("%B %d, %Y")],
            ["Contact:", f"{b.bidder.phone}  |  {b.bidder.contact_email}"],
        ]
        sig_table = Table(sig_data, colWidths=[1.5 * S.inch, 3.0 * S.inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (1, 2), (1, 2), 1, S.black),
                ]
            )
        )
        story.append(sig_table)
        return story

    def output_filename(self) -> str:
        company = self.bid.bidder.company_name.replace(" ", "_")
        date_str = (self.bid.bid_date or date.today()).strftime("%Y%m%d")
        trade = self.bid.trade.name
        
        # Add INTERNAL_ prefix only if package is internal, not for client mode
        if self.package_name == "client":
            return f"{company}_Full_Scope_{trade}_{date_str}.pdf"
        else:
            return f"{company}_INTERNAL_Full_Scope_{trade}_{date_str}.pdf"
