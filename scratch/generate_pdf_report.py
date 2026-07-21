# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Automated Technical PDF Report Generator
-----------------------------------------------------------
Uses ReportLab to parse FINAL_REPORT.md and compile it into a beautifully styled,
press-ready PDF documentation report under the reports/ directory.
"""

import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Define target paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_FILE_PATH = os.path.join(PROJECT_ROOT, "FINAL_REPORT.md")
PDF_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "reports", "Project_FORESIGHT_Technical_Documentation.pdf")

# Primary color palette (Indigo-Violet style)
PRIMARY_COLOR = colors.HexColor("#4f46e5")    # Indigo
SECONDARY_COLOR = colors.HexColor("#a855f7")  # Violet
TEXT_COLOR = colors.HexColor("#1f2937")       # Dark charcoal
LIGHT_BG = colors.HexColor("#f9fafb")         # Cool white/grey
BORDER_COLOR = colors.HexColor("#e5e7eb")     # Light border

class NumberedCanvas(canvas.Canvas):
    """Dynamically calculates total pages and renders footer/headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        if self._pageNumber == 1:
            # Draw beautiful side color band on cover page
            self.setFillColor(PRIMARY_COLOR)
            self.rect(0, 0, 0.4 * inch, 11 * inch, fill=True, stroke=False)
            self.setFillColor(SECONDARY_COLOR)
            self.rect(0.4 * inch, 0, 0.05 * inch, 11 * inch, fill=True, stroke=False)
            self.restoreState()
            return

        # Running Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(PRIMARY_COLOR)
        self.drawString(0.75 * inch, 10.3 * inch, "PROJECT FORESIGHT")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6b7280"))
        self.drawRightString(7.75 * inch, 10.3 * inch, "TECHNICAL DOCUMENTATION")
        
        # Header rule line
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(0.75 * inch, 10.2 * inch, 7.75 * inch, 10.2 * inch)

        # Running Footer
        self.line(0.75 * inch, 0.9 * inch, 7.75 * inch, 0.9 * inch)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6b7280"))
        self.drawString(0.75 * inch, 0.7 * inch, "Confidential - NorthBay Living & Zidio Development")
        self.drawRightString(7.75 * inch, 0.7 * inch, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def convert_md_inline_tags(text: str) -> str:
    """Converts basic markdown inline formats to ReportLab HTML tags."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italic: *text* -> <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Inline code: `text` -> <font name="Courier" color="#374151"><b>\1</b></font>
    text = re.sub(r"`(.*?)`", r'<font name="Courier"><b>\1</b></font>', text)
    # LaTeX formulas conversion (e.g. \text{WAPE} or \sigma)
    text = text.replace(r"\text{WAPE} = \frac{\sum |Actual - Forecast|}{\sum Actual}", "WAPE = sum(|Actual - Forecast|) / sum(Actual)")
    text = text.replace(r"\sigma", "sigma")
    text = text.replace(r"\times \sqrt{h}", "x sqrt(h)")
    return text.strip()


def parse_markdown_to_elements(md_path: str, styles) -> list:
    """Parses MD headers, tables, lists, and paragraphs into Platypus Flowables."""
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    story = []
    
    # 1. Cover Page Title Elements
    story.append(Spacer(1, 1.8 * inch))
    story.append(Paragraph("PROJECT FORESIGHT", styles["CoverTitle"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("TECHNICAL DOCUMENTATION", styles["CoverSubtitle"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Weekly Demand Forecasting & Inventory Intelligence System", styles["CoverDesc"]))
    
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("<b>Client:</b> NorthBay Living", styles["CoverMeta"]))
    story.append(Paragraph("<b>Author:</b> Senior Data Science Team (Zidio Development)", styles["CoverMeta"]))
    story.append(Paragraph("<b>Status:</b> Production Ready & Restored v1.0", styles["CoverMeta"]))
    story.append(Paragraph("<b>Date:</b> July 2026", styles["CoverMeta"]))
    story.append(PageBreak())

    # Parse state variables
    in_table = False
    table_data = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip horizontal rules
        if stripped == "---":
            continue

        # Handle tables
        if stripped.startswith("|"):
            in_table = True
            # Parse columns
            row_cells = [convert_md_inline_tags(cell.strip()) for cell in stripped.split("|")[1:-1]]
            # Skip delimiter line like |:---|:---|
            if len(row_cells) > 0 and all(c.startswith("-") or c.startswith(":") or c == "" for c in row_cells[0]):
                continue
            table_data.append(row_cells)
            continue
        elif in_table:
            # End of table
            in_table = False
            if table_data:
                # Compile table flowable
                formatted_table_data = []
                for i, row in enumerate(table_data):
                    formatted_row = []
                    for cell in row:
                        if i == 0:
                            formatted_row.append(Paragraph(cell, styles["TableHeader"]))
                        else:
                            formatted_row.append(Paragraph(cell, styles["TableCell"]))
                    formatted_table_data.append(formatted_row)
                
                t = Table(formatted_table_data, colWidths=[2.2 * inch, 2.4 * inch, 2.4 * inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('TOPPADDING', (0,0), (-1,0), 8),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
                    ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
                    ('TOPPADDING', (0,1), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 12))
                table_data = []

        # Empty lines
        if not stripped:
            continue

        # Headings
        if stripped.startswith("# "):
            title = convert_md_inline_tags(stripped[2:])
            story.append(Spacer(1, 15))
            story.append(Paragraph(title, styles["ReportTitle"]))
            story.append(Spacer(1, 10))
        elif stripped.startswith("## "):
            h1 = convert_md_inline_tags(stripped[3:])
            story.append(Spacer(1, 12))
            story.append(Paragraph(h1, styles["SectionH1"]))
            story.append(Spacer(1, 8))
        elif stripped.startswith("### "):
            h2 = convert_md_inline_tags(stripped[4:])
            story.append(Spacer(1, 10))
            story.append(Paragraph(h2, styles["SectionH2"]))
            story.append(Spacer(1, 6))
        
        # Bullet list items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            item_text = convert_md_inline_tags(stripped[2:])
            bullet_p = Paragraph(f"&bull; {item_text}", styles["BulletItem"])
            story.append(bullet_p)
            story.append(Spacer(1, 4))
        
        # Numbered list items
        elif re.match(r"^\d+\.\s+", stripped):
            match = re.match(r"^(\d+)\.\s+(.*)", stripped)
            num = match.group(1)
            item_text = convert_md_inline_tags(match.group(2))
            num_p = Paragraph(f"<b>{num}.</b> {item_text}", styles["NumberedItem"])
            story.append(num_p)
            story.append(Spacer(1, 4))

        # Standard Paragraphs
        else:
            p_text = convert_md_inline_tags(stripped)
            story.append(Paragraph(p_text, styles["BodyText"]))
            story.append(Spacer(1, 8))

    return story


def build_pdf_documentation():
    """Compiles the final PDF report with custom layouts and styles."""
    styles = getSampleStyleSheet()

    # Custom typography style sheets
    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=38,
        textColor=PRIMARY_COLOR,
        alignment=0, # Left
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=SECONDARY_COLOR,
        alignment=0,
    ))
    styles.add(ParagraphStyle(
        name="CoverDesc",
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#4b5563"),
        alignment=0,
    ))
    styles.add(ParagraphStyle(
        name="CoverMeta",
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=TEXT_COLOR,
        alignment=0,
    ))

    # Document Section Typography
    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=12,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="SectionH1",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="SectionH2",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=SECONDARY_COLOR,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    ))
    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles["BodyText"].textColor = TEXT_COLOR
    styles["BodyText"].spaceAfter = 8

    # Bullet & List layouts
    styles.add(ParagraphStyle(
        name="BulletItem",
        parent=styles["BodyText"],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="NumberedItem",
        parent=styles["BodyText"],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    ))

    # Table Typography
    styles.add(ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=TEXT_COLOR,
    ))

    # Initialize Document Flow
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.1 * inch,
    )

    # Parse md and build story
    print(f"Parsing {MD_FILE_PATH}...")
    story = parse_markdown_to_elements(MD_FILE_PATH, styles)

    print(f"Building PDF document at {PDF_OUTPUT_PATH}...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF build complete!")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(PDF_OUTPUT_PATH), exist_ok=True)
    build_pdf_documentation()
