"""Bid Proposal template — formal legal bid document with SOV table."""

from datetime import date
from reportlab.platypus import Table, TableStyle

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak

from bid_engine import styles as S
from bid_engine.models import Bid
from bid_engine.pdf_generator import PDFGenerator


class BidProposalGenerator(PDFGenerator):
    """Generates the formal bid proposal PDF (legaldoc format).

    This template reproduces the original Air Hero bid proposal format:
    - From/To header block
    - Project details
    - Scope of work bullet list
    - CSI-formatted SOV table with cost codes
    - Compliance section
    - Exclusions list
    - Signature/acceptance block
    """

    def build_story(self) -> list:
        story: list = []
        b = self.bid
        p = b.project
        bidder = b.bidder
        today_str = (b.bid_date or date.today()).strftime("%B %d, %Y")

        # Title
        story.append(Spacer(1, 0.15))
        story.append(Paragraph("BID PROPOSAL", self.styles["DocTitle"]))
        div_name = f"Division {b.trade.division} — {b.trade.full_name}"
        story.append(Paragraph(div_name, self.styles["DocTitle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=S.NAVY))
        story.append(Spacer(1, 0.2))

        # From / To block
        from_to_data = [
            [
                Paragraph("<b>FROM:</b>", self.styles["LegalBody"]),
                Paragraph("<b>TO:</b>", self.styles["LegalBody"]),
            ],
            [
                Paragraph(
                    f"<b>{bidder.company_name}</b><br/>"
                    f"{bidder.primary_contact}<br/>"
                    f"{bidder.contact_email}<br/>"
                    f"{bidder.phone}<br/>"
                    f"{bidder.location}",
                    self.styles["LegalBody"],
                ),
                Paragraph(
                    f"<b>{p.owner}</b><br/>"
                    f"Attn: {p.owner_contact.get('name', 'N/A')}<br/>"
                    f"{p.owner_contact.get('address', '')}<br/>"
                    f"{p.owner_contact.get('email', '')}",
                    self.styles["LegalBody"],
                ),
            ],
        ]
        party_table = Table(from_to_data, colWidths=[3.2 * S.inch, 3.2 * S.inch])
        party_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LINEAFTER", (0, 0), (0, -1), 0.5, S.LINE_GRAY),
                    ("LEFTPADDING", (1, 0), (1, -1), 14),
                ]
            )
        )
        story.append(party_table)
        story.append(Spacer(1, 0.15))
        story.append(HRFlowable(width="100%", thickness=0.5, color=S.LINE_GRAY))

        # Project details
        proj_data = [
            ["Project Name:", p.name],
            ["Location:", f"{p.address}, {p.city}, {p.state}"],
            ["Bid Date:", today_str],
            ["Reference Sheets:", p.reference_sheets.get("mechanical", "N/A")],
            ["Scope Specification:", div_name],
        ]
        proj_table = Table(proj_data, colWidths=[1.5 * S.inch, 5.0 * S.inch])
        proj_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(Spacer(1, 0.1))
        story.append(proj_table)

        # Section 1: Scope of Work
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY, spaceBefore=10))
        story.append(Paragraph("1.0  SCOPE OF WORK", self.styles["SectionHeader"]))
        scope_text = (
            f"Execution of all {b.trade.name.lower()} scope work required for the "
            f"{p.name}. "
            f"Building area: {p.total_area_sf:,.0f} SF."
        )
        story.append(Paragraph(scope_text, self.styles["LegalBody"]))

        sow_items = []
        trade_scope_key = f"{b.trade.name.lower()}_scope"
        if trade_scope_key in p.technical_scope:
            for k, v in p.technical_scope[trade_scope_key].items():
                sow_items.append(f"{k.replace('_', ' ').title()}: {v}")
        else:
            sow_items = b.trade.templates.get("bid_proposal", {}).get("sow_items", [])
            if not sow_items:
                sow_items = b.trade.equipment_categories[:6]
                
        for item in sow_items:
            story.append(Paragraph(f"• {item}", self.styles["BulletText"]))

        # Section 2: SOV
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY, spaceBefore=10))
        story.append(Paragraph("2.0  SCHEDULE OF VALUES (SOV)", self.styles["SectionHeader"]))
        story.append(
            Paragraph(
                "The following breakdown is a turnkey schedule of values.",
                self.styles["LegalBody"],
            )
        )

        sov_data = [
            [
                S._tc("Cost Code", bold=True),
                S._tc("Description", bold=True),
                S._tc("Amount", bold=True),
            ],
        ]
        
        # Apply markups to line items
        multiplier = (1.0 + b.contingency_pct / 100.0) * (1.0 + b.overhead_profit_pct / 100.0)
        sum_burdened = 0.0
        
        for i, li in enumerate(b.line_items):
            burdened_cost = round(li.total_phase * multiplier, 2)
            sum_burdened += burdened_cost
            sov_data.append(
                [
                    li.cost_code,
                    S._tc(li.description),
                    S._tc(f"${burdened_cost:,.2f}"),
                ]
            )
            
        diff = round(b.total_bid_amount - sum_burdened, 2)
        if diff != 0 and len(b.line_items) > 0:
            last_burdened = round(b.line_items[-1].total_phase * multiplier, 2) + diff
            sov_data[-1][2] = S._tc(f"${last_burdened:,.2f}")

        sov_data.append(
            [
                "",
                S._tc("TOTAL PROPOSAL AMOUNT", bold=True),
                S._tc(f"${b.total_bid_amount:,.2f}", bold=True),
            ]
        )

        sov_table = Table(
            sov_data,
            colWidths=[1.0 * S.inch, 4.1 * S.inch, 1.25 * S.inch],
        )
        sov_ts = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), S.NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), S.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, S.LINE_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, len(sov_data) - 1), (-1, len(sov_data) - 1), S.LIGHT_GRAY),
                ("FONTNAME", (0, len(sov_data) - 1), (-1, len(sov_data) - 1), "Helvetica-Bold"),
            ]
        )
        sov_table.setStyle(sov_ts)
        story.append(sov_table)

        # Section 3: Compliance
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY, spaceBefore=10))
        story.append(
            Paragraph("3.0  REGULATORY COMPLIANCE & QUALIFICATIONS", self.styles["SectionHeader"])
        )

        # Build compliance list: use project-level codes where specified,
        # fall back to trade-level codes for categories not in project config
        proj_codes = b.project.governing_codes
        trade_code_map = {c["code_name"]: c for c in b.trade.compliance_codes}

        # Map project keys to trade code_name prefixes for matching
        code_name_map = {
            "mechanical": "IMC",
            "energy": "IECC",
            "plumbing": "IPC",
            "electrical": "NEC",
            "accessibility": "TAS",
        }

        # Start with trade codes as fallback baseline
        final_codes: list[str] = []
        for code in b.trade.compliance_codes:
            final_codes.append(f"<b>{code['code_name']}:</b> {code['description']} — {code['applies_to']}")

        # Override with project-level codes where specified (replace matching trade codes)
        if proj_codes.get("mechanical"):
            proj_mech = proj_codes["mechanical"]
            final_codes = [c for c in final_codes if "IMC" not in c]
            final_codes.insert(0, f"<b>{proj_mech}:</b> International Mechanical Code — Duct systems, refrigerant handling, equipment installation")
        if proj_codes.get("energy"):
            proj_energy = proj_codes["energy"]
            final_codes = [c for c in final_codes if "IECC" not in c]
            final_codes.insert(0, f"<b>{proj_energy}:</b> International Energy Conservation Code — Duct insulation R-values, equipment efficiency")
        if proj_codes.get("plumbing"):
            proj_plumb = proj_codes["plumbing"]
            final_codes = [c for c in final_codes if "IPC" not in c]
            final_codes.insert(0, f"<b>{proj_plumb}:</b> International Plumbing Code — Condensate drain connections")
        if proj_codes.get("electrical"):
            proj_elec = proj_codes["electrical"]
            final_codes = [c for c in final_codes if "NEC" not in c]
            final_codes.insert(0, f"<b>{proj_elec}:</b> National Electrical Code — Low-voltage control wiring")
        if proj_codes.get("accessibility"):
            proj_access = proj_codes["accessibility"]
            final_codes = [c for c in final_codes if "TAS" not in c]
            final_codes.insert(0, f"<b>{proj_access}:</b> Texas Accessibility Standards — Equipment access, controls placement")

        for code_text in final_codes:
            story.append(Paragraph(f"• {code_text}", self.styles["BulletText"]))
        story.append(
            Paragraph(
                "• <b>Warranty:</b> Standard 1-year general workmanship warranty from substantial completion.",
                self.styles["BulletText"],
            )
        )
        story.append(
            Paragraph(
                "• <b>Safety:</b> All work complies with applicable OSHA requirements.",
                self.styles["BulletText"],
            )
        )

        # Section 4: Exclusions
        story.append(HRFlowable(width="100%", thickness=1, color=S.NAVY, spaceBefore=10))
        story.append(Paragraph("4.0  EXCLUSIONS", self.styles["SectionHeader"]))
        story.append(
            Paragraph(
                "The following items are strictly excluded from this proposal:",
                self.styles["LegalBody"],
            )
        )
        for i, item in enumerate(b.exclusions or b.trade.default_exclusions, 1):
            story.append(Paragraph(f"{i}.  {item}", self.styles["BulletText"]))

        # Signature block
        story.append(Spacer(1, 0.3))
        story.append(HRFlowable(width="100%", thickness=1.5, color=S.NAVY))
        story.append(Spacer(1, 0.15))
        story.append(Paragraph("ACCEPTANCE OF PROPOSAL", self.styles["SectionHeader"]))
        story.append(
            Paragraph(
                f"The above prices, specifications, and conditions are satisfactory and are hereby accepted. "
                f"{bidder.company_name} is authorized to proceed upon receipt of an executed agreement.",
                self.styles["LegalBody"],
            )
        )
        story.append(Spacer(1, 0.25))

        sig_data = [
            ["Submitted By:", f"{bidder.primary_contact} — {bidder.company_name}"],
            ["Signature:", ""],
            ["Date:", today_str],
            ["", ""],
            ["Authorized (Client):", ""],
            ["Signature:", ""],
            ["Date:", ""],
        ]
        sig_table = Table(sig_data, colWidths=[2.0 * S.inch, 3.5 * S.inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (1, 1), (1, 1), 1, S.black),
                    ("LINEBELOW", (1, 5), (1, 5), 1, S.black),
                    ("LINEBELOW", (1, 6), (1, 6), 0.5, S.LINE_GRAY),
                ]
            )
        )
        story.append(sig_table)

        # Footer
        story.append(Spacer(1, 0.3))
        story.append(HRFlowable(width="100%", thickness=0.5, color=S.LINE_GRAY))
        story.append(
            Paragraph(
                f"{bidder.company_name}  |  {bidder.location}  |  {bidder.phone}  |  "
                f"{bidder.contact_email}  |  {today_str}",
                self.styles["FootNote"],
            )
        )

        return story

    def output_filename(self) -> str:
        company = self.bid.bidder.company_name.replace(" ", "_")
        date_str = (
            self.bid.bid_date.strftime("%Y%m%d")
            if self.bid.bid_date
            else date.today().strftime("%Y%m%d")
        )
        trade = self.bid.trade.name
        return f"{company}_Bid_Proposal_{trade}_{date_str}.pdf"
