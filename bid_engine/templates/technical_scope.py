"""Technical Scope Exhibit template — contract-style no-pricing scope sheet."""

from datetime import date

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable

from bid_engine import styles as S
from bid_engine.models import Bid
from bid_engine.pdf_generator import PDFGenerator


class TechnicalScopeGenerator(PDFGenerator):
    """Generates a contract-oriented technical scope exhibit.

    This document intentionally excludes all pricing and is intended
    for GC/owner scope alignment and signature acknowledgment.
    """

    def output_filename(self) -> str:
        date_str = (
            self.bid.bid_date.strftime("%Y%m%d")
            if self.bid.bid_date
            else date.today().strftime("%Y%m%d")
        )
        company = self.bid.bidder.company_name.replace(" ", "_")
        trade = self.bid.trade.name
        return f"{company}_Technical_Scope_{trade}_{date_str}.pdf"

    def build_story(self) -> list:
        story: list = []
        b = self.bid
        p = b.project
        scope = p.technical_scope or {}

        project_name = scope.get("project_name", p.name)
        location = scope.get("location", f"{p.address}, {p.city}, {p.state}")
        developer = scope.get("developer_architect", p.owner or p.design_group or "Owner/GC")
        submitted_by = scope.get(
            "submitted_by",
            f"{b.bidder.primary_contact}, {b.bidder.company_name}",
        )
        reference_sheets = scope.get(
            "reference_sheets",
            p.reference_sheets.get("mechanical", "Per latest mechanical sheets"),
        )

        story.append(Paragraph("PROJECT CONTRACT SPECIFICATIONS: TECHNICAL SCOPE EXHIBIT", self.styles["DocTitle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=S.NAVY))
        story.append(Spacer(1, 0.18 * S.inch))

        info_data = [
            ["PROJECT NAME:", project_name],
            ["LOCATION:", location],
            ["DEVELOPER/ARCHITECT:", developer],
            ["SUBMITTED BY:", submitted_by],
            ["REFERENCE SHEETS:", reference_sheets],
        ]
        info_table = Table(info_data, colWidths=[2.1 * S.inch, 4.3 * S.inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(info_table)

        story.extend(self._section_scope_of_execution(scope))
        story.extend(self._section_codes(scope))
        story.extend(self._section_logistics(scope))
        story.extend(self._section_exclusions(scope))
        story.extend(self._section_acknowledgment(scope))

        return story

    def _section_scope_of_execution(self, scope: dict) -> list:
        story: list = []
        story.append(Spacer(1, 0.08 * S.inch))
        story.append(Paragraph("1.0 SCOPE OF MECHANICAL EXECUTION", self.styles["SectionHeader"]))

        line_items = scope.get("execution_scope") or [
            "Fabricated Ductwork: Galvanized sheet-metal ductwork fabrication and installation per project drawings and SMACNA standards.",
            "Air Distribution: Flexible drops, GRDs, and associated distribution accessories per approved submittals.",
            "Equipment Setting: Indoor and outdoor HVAC equipment placement, alignment, and final anchoring per manufacturer requirements.",
            "Ventilation: Exhaust fan installation and tie-in for occupied assembly support spaces.",
            "Support Systems: Duct supports, seismic bracing, turnbuckles, and safety hardware per IMC and structural coordination.",
        ]

        for item in line_items:
            story.append(Paragraph(f"• {item}", self.styles["BulletText"]))
        return story

    def _section_codes(self, scope: dict) -> list:
        story: list = []
        story.append(Spacer(1, 0.06 * S.inch))
        story.append(Paragraph("2.0 REGULATORY & TECHNICAL STANDARDS", self.styles["SectionHeader"]))

        code_items = scope.get("regulatory_standards")
        if not code_items:
            code_items = [
                f"Mechanical: {self.bid.project.governing_codes.get('mechanical', 'Applicable IMC')}",
                f"Energy: {self.bid.project.governing_codes.get('energy', 'Applicable IECC')} (minimum duct insulation per energy code and climate conditions)",
                f"Accessibility: {self.bid.project.governing_codes.get('accessibility', 'Applicable TAS/ADA')}",
                f"Electrical: {self.bid.project.governing_codes.get('electrical', 'Applicable NEC')} for controls and low-voltage interfaces",
            ]

        story.append(Paragraph("All work shall adhere to the governing project and jurisdictional codes.", self.styles["Body"]))
        for item in code_items:
            story.append(Paragraph(f"• {item}", self.styles["BulletText"]))
        return story

    def _section_logistics(self, scope: dict) -> list:
        story: list = []
        story.append(Spacer(1, 0.06 * S.inch))
        story.append(Paragraph("3.0 SPECIAL CONDITIONS & LOGISTICS", self.styles["SectionHeader"]))

        logistics = scope.get("special_conditions") or [
            "Access Requirements: Tight-clearance routing and rigging constraints shall be coordinated with field conditions.",
            "Clash Detection: Mechanical routing shall coordinate with structure, architectural, and other MEP systems.",
            "Quality Control: Sheet-metal seams and joints shall be sealed to maintain system integrity in local climate conditions.",
        ]
        for item in logistics:
            story.append(Paragraph(f"• {item}", self.styles["BulletText"]))
        return story

    def _section_exclusions(self, scope: dict) -> list:
        story: list = []
        story.append(Spacer(1, 0.06 * S.inch))
        story.append(Paragraph("4.0 EXCLUSIONS (NOT IN SCOPE)", self.styles["SectionHeader"]))

        exclusions = scope.get("exclusions") or self.bid.exclusions
        if not exclusions:
            exclusions = [
                "Permit application fees unless explicitly listed in contract inclusions.",
                "Structural modifications unless specifically identified as delegated design scope.",
                "Temporary utilities by others unless noted otherwise in writing.",
                "Final TAB by others unless explicitly included in awarded scope.",
            ]

        for item in exclusions:
            story.append(Paragraph(f"• {item}", self.styles["BulletText"]))
        return story

    def _section_acknowledgment(self, scope: dict) -> list:
        story: list = []
        signer_title = scope.get("submitted_title", "Estimator / Designer")
        signer_name = scope.get("submitted_name", self.bid.bidder.primary_contact)
        company_name = scope.get("submitted_company", self.bid.bidder.company_name)

        story.append(Spacer(1, 0.12 * S.inch))
        story.append(Paragraph("5.0 EXECUTION ACKNOWLEDGMENT", self.styles["SectionHeader"]))
        story.append(
            Paragraph(
                "The technical specifications and conditions above are accepted as the governing scope for this project.",
                self.styles["Body"],
            )
        )
        story.append(Spacer(1, 0.2 * S.inch))
        story.append(Paragraph("Authorized Signature (Imagine Design): _____________________________", self.styles["Body"]))
        story.append(Spacer(1, 0.1 * S.inch))
        story.append(Paragraph("Date: _______________", self.styles["Body"]))
        story.append(Spacer(1, 0.18 * S.inch))
        story.append(Paragraph(f"Submitted By: {signer_name} — {signer_title} — {company_name}", self.styles["Body"]))
        return story
