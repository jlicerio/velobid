"""Shared ReportLab styles and helpers for all PDF templates."""

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer


NAVY = HexColor("#1a365d")
LIGHT_GRAY = HexColor("#e8e8e8")
MID_GRAY = HexColor("#e8f0fb")
LINE_GRAY = HexColor("#cccccc")


def build_styles() -> dict:
    """Build and return all custom ParagraphStyles for the platform.

    Returns a dict keyed by style name.
    """
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            fontName="Helvetica",
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=NAVY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=13,
            spaceBefore=14,
            spaceAfter=8,
            textColor=NAVY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeader",
            fontName="Helvetica-Bold",
            fontSize=11,
            spaceBefore=10,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LegalBody",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletText",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=16,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BlockLabel",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BlockValue",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=9,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FootNote",
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
    )

    return styles


def _tc(text: str, font_size: int = 9, bold: bool = False) -> Paragraph:
    """Wrap text in a Paragraph to prevent table cell overflow.

    Args:
        text: The string content to wrap.
        font_size: Font size in points. Defaults to 9.
        bold: Whether to use Helvetica-Bold. Defaults to False.

    Returns:
        A ReportLab Paragraph instance.
    """
    font = "Helvetica-Bold" if bold else "Helvetica"
    return Paragraph(
        str(text),
        ParagraphStyle(
            "_tc",
            fontName=font,
            fontSize=font_size,
            leading=font_size + 3,
            spaceAfter=0,
            spaceBefore=0,
        ),
    )


TABLE_BASE_STYLE = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 0.5, LINE_GRAY),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
]

TABLE_TOTAL_STYLE = [
    ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GRAY),
    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
]

HEADER_STYLE = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
]
