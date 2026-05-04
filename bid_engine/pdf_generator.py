"""Base PDF generator class — all templates inherit from this."""

import os
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)

from bid_engine.models import Bid, Project, Bidder, TradeConfig
from bid_engine import styles as S


class PDFGenerator(ABC):
    """Abstract base class for all PDF template generators.

    Subclasses must implement `build_story()` which populates the
    ReportLab story (list of flowables). The `render()` method handles
    document setup, style injection, and PDF output.
    """

    DEFAULT_MARGIN = 0.75 * inch
    PAGE_SIZE = letter
    OUTPUT_DIR = "bid_projects"

    def __init__(
        self,
        bid: Bid,
        output_dir: str | None = None,
        margin: float | None = None,
        package_name: str = "all",
    ) -> None:
        """Initialize the generator with a Bid object.

        Args:
            bid: The complete Bid to render.
            output_dir: Directory to write PDFs. Defaults to "bid_projects".
            margin: Page margin in points. Defaults to 0.75in.
            package_name: Package mode ("client", "internal", or "all"). Defaults to "all".
        """
        self.bid = bid
        self.output_dir = Path(output_dir or self.OUTPUT_DIR)
        self.margin = margin if margin is not None else self.DEFAULT_MARGIN
        self.package_name = package_name
        self._styles: dict | None = None

    @property
    def styles(self) -> dict:
        """Lazy-load shared styles once per generator instance."""
        if self._styles is None:
            self._styles = S.build_styles()
        return self._styles

    @abstractmethod
    def build_story(self) -> list:
        """Build and return the list of ReportLab flowables.

        Subclasses must implement this method to populate the document.
        """

    def output_filename(self) -> str:
        """Return the output filename for this template.

        Override in subclasses to customize. Defaults to
        `{CompanyName}_{Trade}_{BidDate}_{TemplateName}.pdf`
        """
        date_str = (
            self.bid.bid_date.strftime("%Y%m%d")
            if self.bid.bid_date
            else date.today().strftime("%Y%m%d")
        )
        company = self.bid.bidder.company_name.replace(" ", "_")
        trade = self.bid.trade.name
        return f"{company}_{trade}_{date_str}.pdf"

    def render(self, filename: str | None = None) -> str:
        """Build and write the PDF to disk.

        Args:
            filename: Output filename. Defaults to self.output_filename().

        Returns:
            The absolute path of the written PDF file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / (filename or self.output_filename())

        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=self.PAGE_SIZE,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        story = self.build_story()
        doc.build(story)
        return str(out_path.resolve())

    # --- Shared helper methods used across templates ---

    def project_info_table(self) -> Table:
        """Build a standard project info table (name, location, area, etc.)."""
        p = self.bid.project
        b = self.bid.bidder
        data = [
            ["Project Name:", p.name],
            ["Location:", f"{p.address}, {p.city}, {p.state}"],
            ["Total Building Area:", f"{p.total_area_sf:,.0f} SF"],
            ["Occupancy:", p.occupancy_group],
            ["Construction Type:", p.construction_type],
            ["Prepared By:", b.company_name],
            ["Date:", (self.bid.bid_date or date.today()).strftime("%B %d, %Y")],
        ]
        table = Table(data, colWidths=[2.0 * inch, 4.0 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table

    def cover_block(self, title: str, subtitle: str | None = None) -> list:
        """Return a standard cover page as a list of flowables."""
        elems = []
        elems.append(Spacer(1, 1.5 * inch))
        elems.append(Paragraph(title, self.styles["CoverTitle"]))
        if subtitle:
            elems.append(Spacer(1, 0.2 * inch))
            elems.append(Paragraph(subtitle, self.styles["CoverSubtitle"]))
        elems.append(Spacer(1, 1.0 * inch))
        elems.append(self.project_info_table())
        elems.append(Spacer(1, 1.0 * inch))
        elems.append(
            Paragraph(
                "CONFIDENTIAL — FOR PROPOSAL PURPOSES ONLY",
                self.styles["CoverSubtitle"],
            )
        )
        elems.append(PageBreak())
        return elems

    def section_header(self, text: str) -> Paragraph:
        return Paragraph(text, self.styles["SectionHeader"])

    def hr(self, thickness: float = 1, color: HexColor = S.NAVY) -> HRFlowable:
        return HRFlowable(width="100%", thickness=thickness, color=color)

    def spacer(self, height: float = 0.15) -> Spacer:
        return Spacer(1, height * inch)

    def body(self, text: str) -> Paragraph:
        return Paragraph(text, self.styles["Body"])

    def bullet(self, text: str) -> Paragraph:
        return Paragraph(f"• {text}", self.styles["BulletText"])

    def sub_header(self, text: str) -> Paragraph:
        return Paragraph(text, self.styles["SubHeader"])
