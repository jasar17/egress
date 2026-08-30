"""
EGRESS Platform - Deployed System Technical & Product Specification Generator
Target URL: https://egress-jade.vercel.app/
API Backend: https://egressandco.onrender.com
Database: Supabase Managed Cloud PostgreSQL

Produces a publication-grade, multi-page technical and product specification PDF
with custom vector diagrams, layout wireframes, pipeline architectures,
statutory code matrices, and multi-phase future roadmaps.
"""

import os
import sys
import shutil
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import (
    Drawing,
    Rect,
    String,
    Line,
    Group,
    Polygon,
    Circle
)

# ----------------------------------------------------------------------
# COLOR PALETTE
# ----------------------------------------------------------------------
PRIMARY = colors.HexColor("#0F172A")       # Deep Slate / Navy
SECONDARY = colors.HexColor("#1E293B")     # Dark Slate
ACCENT_BLUE = colors.HexColor("#2563EB")   # Royal Blue
ACCENT_CYAN = colors.HexColor("#0891B2")   # Cyan / Teal
ACCENT_RED = colors.HexColor("#DC2626")    # Critical Fire Crimson
ACCENT_ORANGE = colors.HexColor("#D97706") # Amber / Warning
ACCENT_GREEN = colors.HexColor("#059669")  # Emerald Compliant
BG_LIGHT = colors.HexColor("#F8FAFC")      # Off-white / canvas
BG_CARD = colors.HexColor("#FFFFFF")       # Pure White
BORDER_COLOR = colors.HexColor("#E2E8F0")  # Soft Gray Border
TEXT_DARK = colors.HexColor("#0F172A")     # Body Text Primary
TEXT_MUTED = colors.HexColor("#64748B")    # Secondary Gray Text
HIGHLIGHT_BG = colors.HexColor("#EFF6FF")  # Subtle Blue Tint

# ----------------------------------------------------------------------
# DYNAMIC TWO-PASS NUMBERED CANVAS
# ----------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and stamp total page count
    along with corporate running headers and footers.
    """
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

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_w, page_h = A4

        # Skip headers and footers on cover page
        if self._pageNumber > 1:
            # Top Running Header
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.75)
            self.line(36, page_h - 38, page_w - 36, page_h - 38)

            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(PRIMARY)
            self.drawString(36, page_h - 32, "EGRESS PLATFORM")

            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(125, page_h - 32, "|  Deployed System Technical & Product Specification")
            self.drawRightString(page_w - 36, page_h - 32, "https://egress-jade.vercel.app/")

            # Bottom Running Footer
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.75)
            self.line(36, 42, page_w - 36, 42)

            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(36, 30, "Confidential - For Architecture, Engineering & Civil Defence Review")
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(page_w - 36, 30, page_str)

        self.restoreState()


# ----------------------------------------------------------------------
# VECTOR DIAGRAM GENERATORS
# ----------------------------------------------------------------------
def create_cloud_architecture_diagram():
    """
    Vector diagram showing the end-to-end cloud topology:
    Vercel Edge Frontend -> Render Containerized Backend -> Supabase Cloud PostgreSQL
    """
    d = Drawing(520, 160)
    
    # Outer Background Container
    d.add(Rect(0, 0, 520, 160, rx=8, ry=8, fillColor=BG_LIGHT, strokeColor=BORDER_COLOR, strokeWidth=1))
    
    # 1. User & Vercel Frontend Box
    d.add(Rect(15, 20, 145, 120, rx=6, ry=6, fillColor=BG_CARD, strokeColor=ACCENT_BLUE, strokeWidth=1.5))
    d.add(Rect(15, 115, 145, 25, rx=6, ry=6, fillColor=ACCENT_BLUE, strokeColor=None))
    d.add(String(87, 123, "FRONTEND LAYER", fontName="Helvetica-Bold", fontSize=8.5, fillColor=colors.white, textAnchor="middle"))
    d.add(String(87, 98, "Vercel Edge Platform", fontName="Helvetica-Bold", fontSize=9, fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(87, 85, "egress-jade.vercel.app", fontName="Helvetica-Oblique", fontSize=7.5, fillColor=ACCENT_BLUE, textAnchor="middle"))
    d.add(String(87, 68, "React 18 + Vite SPA", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(87, 54, "Tri-Mode Canvas Viewer", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(87, 40, "Interactive Audit Studio", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(87, 26, "Responsive CSS Engine", fontName="Helvetica", fontSize=7.5, fillColor=TEXT_MUTED, textAnchor="middle"))

    # Arrow 1: Frontend to Backend
    d.add(Line(160, 80, 185, 80, strokeColor=ACCENT_BLUE, strokeWidth=2))
    d.add(Polygon([185, 84, 192, 80, 185, 76], fillColor=ACCENT_BLUE, strokeColor=None))
    d.add(String(176, 88, "HTTPS / REST", fontName="Helvetica-Bold", fontSize=6.5, fillColor=ACCENT_BLUE, textAnchor="middle"))

    # 2. Render Backend API Box
    d.add(Rect(192, 20, 155, 120, rx=6, ry=6, fillColor=BG_CARD, strokeColor=ACCENT_CYAN, strokeWidth=1.5))
    d.add(Rect(192, 115, 155, 25, rx=6, ry=6, fillColor=ACCENT_CYAN, strokeColor=None))
    d.add(String(269, 123, "COMPUTATION API", fontName="Helvetica-Bold", fontSize=8.5, fillColor=colors.white, textAnchor="middle"))
    d.add(String(269, 98, "Render Cloud Web Service", fontName="Helvetica-Bold", fontSize=9, fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(269, 85, "egressandco.onrender.com", fontName="Helvetica-Oblique", fontSize=7.5, fillColor=ACCENT_CYAN, textAnchor="middle"))
    d.add(String(269, 68, "FastAPI + Python 3.11", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(269, 54, "ezdxf + PyMuPDF Parsers", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(269, 40, "Shapely Planar Geometry", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(269, 26, "NetworkX Shortest Paths", fontName="Helvetica", fontSize=7.5, fillColor=TEXT_MUTED, textAnchor="middle"))

    # Arrow 2: Backend to Supabase
    d.add(Line(347, 80, 372, 80, strokeColor=ACCENT_GREEN, strokeWidth=2))
    d.add(Polygon([372, 84, 379, 80, 372, 76], fillColor=ACCENT_GREEN, strokeColor=None))
    d.add(String(363, 88, "Postgres SSL", fontName="Helvetica-Bold", fontSize=6.5, fillColor=ACCENT_GREEN, textAnchor="middle"))

    # 3. Supabase Cloud Database Box
    d.add(Rect(379, 20, 126, 120, rx=6, ry=6, fillColor=BG_CARD, strokeColor=ACCENT_GREEN, strokeWidth=1.5))
    d.add(Rect(379, 115, 126, 25, rx=6, ry=6, fillColor=ACCENT_GREEN, strokeColor=None))
    d.add(String(442, 123, "PERSISTENCE", fontName="Helvetica-Bold", fontSize=8.5, fillColor=colors.white, textAnchor="middle"))
    d.add(String(442, 98, "Supabase Managed DB", fontName="Helvetica-Bold", fontSize=9, fillColor=PRIMARY, textAnchor="middle"))
    d.add(String(442, 85, "Seoul AP-Northeast-2", fontName="Helvetica-Oblique", fontSize=7.5, fillColor=ACCENT_GREEN, textAnchor="middle"))
    d.add(String(442, 68, "Cloud PostgreSQL 15+", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(442, 54, "BYTEA File Storage", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(442, 40, "168 UAE FLSC Clauses", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(442, 26, "Zero-Data-Loss Invariant", fontName="Helvetica", fontSize=7.5, fillColor=TEXT_MUTED, textAnchor="middle"))

    return d


def create_ui_layout_diagram():
    """
    Vector diagram representing the deployed UI layout:
    Top Header, Left Controls Sidebar, Central Tri-Mode Canvas, Right Findings Panel
    """
    d = Drawing(520, 190)
    
    # Outer Frame
    d.add(Rect(0, 0, 520, 190, rx=6, ry=6, fillColor=PRIMARY, strokeColor=BORDER_COLOR, strokeWidth=1))
    
    # Top Application Header Bar
    d.add(Rect(8, 158, 504, 24, rx=4, ry=4, fillColor=SECONDARY, strokeColor=None))
    d.add(Circle(22, 170, 5, fillColor=ACCENT_RED, strokeColor=None))
    d.add(String(34, 167, "EGRESS CO.", fontName="Helvetica-Bold", fontSize=8.5, fillColor=colors.white))
    d.add(String(100, 167, "Al Noor Business Centre - Level 06", fontName="Helvetica", fontSize=8, fillColor=TEXT_MUTED))
    d.add(Rect(375, 162, 60, 16, rx=3, ry=3, fillColor=colors.HexColor("#334155"), strokeColor=None))
    d.add(String(405, 166, "[F] Fullscreen", fontName="Helvetica", fontSize=7, fillColor=colors.white, textAnchor="middle"))
    d.add(Rect(440, 162, 66, 16, rx=3, ry=3, fillColor=ACCENT_BLUE, strokeColor=None))
    d.add(String(473, 166, "+ New Upload", fontName="Helvetica-Bold", fontSize=7, fillColor=colors.white, textAnchor="middle"))

    # Left Sidebar: Project Controls & Multi-Floor Navigation
    d.add(Rect(8, 8, 120, 145, rx=4, ry=4, fillColor=SECONDARY, strokeColor=BORDER_COLOR, strokeWidth=0.5))
    d.add(String(16, 137, "PROJECT METRICS", fontName="Helvetica-Bold", fontSize=7.5, fillColor=ACCENT_CYAN))
    d.add(Rect(14, 102, 108, 28, rx=3, ry=3, fillColor=PRIMARY, strokeColor=None))
    d.add(String(20, 118, "FLOOR AREA", fontName="Helvetica", fontSize=6, fillColor=TEXT_MUTED))
    d.add(String(20, 106, "414.0 m2", fontName="Helvetica-Bold", fontSize=9, fillColor=colors.white))
    d.add(String(68, 118, "OCCUPANTS", fontName="Helvetica", fontSize=6, fillColor=TEXT_MUTED))
    d.add(String(68, 106, "360 persons", fontName="Helvetica-Bold", fontSize=9, fillColor=colors.white))

    d.add(String(16, 90, "MULTI-FLOOR NAV", fontName="Helvetica-Bold", fontSize=7.5, fillColor=ACCENT_CYAN))
    d.add(Rect(14, 66, 108, 18, rx=2, ry=2, fillColor=ACCENT_BLUE, strokeColor=None))
    d.add(String(20, 71, "Level 02 - Layout (Active)", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.white))
    d.add(Rect(14, 46, 108, 16, rx=2, ry=2, fillColor=PRIMARY, strokeColor=None))
    d.add(String(20, 51, "Level 01 - Typical Floor", fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED))
    d.add(Rect(14, 26, 108, 16, rx=2, ry=2, fillColor=PRIMARY, strokeColor=None))
    d.add(String(20, 31, "Level 00 - Ground Concourse", fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED))
    d.add(Rect(14, 11, 108, 12, rx=2, ry=2, fillColor=colors.HexColor("#047857"), strokeColor=None))
    d.add(String(68, 14, "Export CSV / Audit PDF", fontName="Helvetica-Bold", fontSize=6, fillColor=colors.white, textAnchor="middle"))

    # Center Stage: Architectural Viewer Canvas
    d.add(Rect(132, 8, 240, 145, rx=4, ry=4, fillColor=colors.HexColor("#020617"), strokeColor=BORDER_COLOR, strokeWidth=0.5))
    # Tri-mode Selector Toolbar
    d.add(Rect(140, 131, 224, 18, rx=3, ry=3, fillColor=SECONDARY, strokeColor=None))
    d.add(Rect(142, 133, 50, 14, rx=2, ry=2, fillColor=ACCENT_BLUE, strokeColor=None))
    d.add(String(167, 137, "Hybrid View", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.white, textAnchor="middle"))
    d.add(String(218, 137, "Vector Blueprint", fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(275, 137, "Raster Arch", fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(String(340, 137, "Layers (7)", fontName="Helvetica", fontSize=6.5, fillColor=ACCENT_CYAN, textAnchor="middle"))

    # Simulated Floor Plan Blueprint Inside Stage
    d.add(Rect(155, 25, 195, 95, rx=2, ry=2, fillColor=None, strokeColor=colors.HexColor("#1E293B"), strokeWidth=1))
    d.add(Rect(165, 35, 90, 75, rx=0, ry=0, fillColor=colors.HexColor("#0B132B"), strokeColor=colors.HexColor("#334155"), strokeWidth=0.8))
    d.add(String(210, 70, "MULTI-PURPOSE HALL", fontName="Helvetica", fontSize=5.5, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(Rect(265, 35, 75, 35, rx=0, ry=0, fillColor=colors.HexColor("#0B132B"), strokeColor=colors.HexColor("#334155"), strokeWidth=0.8))
    d.add(String(302, 50, "OFFICE 01", fontName="Helvetica", fontSize=5.5, fillColor=TEXT_MUTED, textAnchor="middle"))
    d.add(Rect(265, 75, 75, 35, rx=0, ry=0, fillColor=colors.HexColor("#0B132B"), strokeColor=colors.HexColor("#334155"), strokeWidth=0.8))
    d.add(String(302, 90, "OFFICE 02", fontName="Helvetica", fontSize=5.5, fillColor=TEXT_MUTED, textAnchor="middle"))

    # Exits and Doors
    d.add(Rect(155, 55, 6, 16, rx=1, ry=1, fillColor=ACCENT_GREEN, strokeColor=None))
    d.add(String(148, 60, "EXIT 1", fontName="Helvetica-Bold", fontSize=5, fillColor=ACCENT_GREEN))
    d.add(Rect(344, 55, 6, 16, rx=1, ry=1, fillColor=ACCENT_GREEN, strokeColor=None))
    d.add(String(354, 60, "EXIT 2", fontName="Helvetica-Bold", fontSize=5, fillColor=ACCENT_GREEN))

    # Egress Path (Dashed Line)
    d.add(Line(205, 50, 205, 40, strokeColor=ACCENT_RED, strokeWidth=1.2, strokeDashArray=[2, 2]))
    d.add(Line(205, 40, 345, 63, strokeColor=ACCENT_RED, strokeWidth=1.2, strokeDashArray=[2, 2]))

    # Pulsing Violation Pin
    d.add(Circle(205, 50, 7, fillColor=ACCENT_RED, strokeColor=colors.white, strokeWidth=1))
    d.add(String(205, 48, "!", fontName="Helvetica-Bold", fontSize=7, fillColor=colors.white, textAnchor="middle"))
    d.add(String(205, 32, "V-B55899: 339p >= 100p Single Exit", fontName="Helvetica-Bold", fontSize=5, fillColor=ACCENT_RED, textAnchor="middle"))

    # Right Panel: Interactive Findings Drawer
    d.add(Rect(376, 8, 136, 145, rx=4, ry=4, fillColor=SECONDARY, strokeColor=BORDER_COLOR, strokeWidth=0.5))
    d.add(String(384, 137, "CODE FINDINGS (2)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=ACCENT_RED))
    d.add(Rect(470, 133, 36, 12, rx=2, ry=2, fillColor=ACCENT_RED, strokeColor=None))
    d.add(String(488, 136, "NON-COMP", fontName="Helvetica-Bold", fontSize=5.5, fillColor=colors.white, textAnchor="middle"))

    # Finding Card 1
    d.add(Rect(382, 75, 124, 52, rx=3, ry=3, fillColor=PRIMARY, strokeColor=ACCENT_RED, strokeWidth=1))
    d.add(String(387, 116, "CRITICAL | V-B55899", fontName="Helvetica-Bold", fontSize=6, fillColor=ACCENT_RED))
    d.add(String(387, 107, "Single Exit Door Exceeded", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.white))
    d.add(String(387, 98, "Load: 339 persons >= 100 limit", fontName="Helvetica", fontSize=5.5, fillColor=TEXT_MUTED))
    d.add(String(387, 89, "Clause: UAE FLSC Table 3.19", fontName="Helvetica-Oblique", fontSize=5.5, fillColor=ACCENT_CYAN))
    d.add(Rect(387, 78, 48, 8, rx=1, ry=1, fillColor=ACCENT_RED, strokeColor=None))
    d.add(String(411, 80, "Status: Open", fontName="Helvetica-Bold", fontSize=5, fillColor=colors.white, textAnchor="middle"))

    # Finding Card 2
    d.add(Rect(382, 18, 124, 52, rx=3, ry=3, fillColor=PRIMARY, strokeColor=ACCENT_ORANGE, strokeWidth=1))
    d.add(String(387, 59, "HIGH | V-22C2B6", fontName="Helvetica-Bold", fontSize=6, fillColor=ACCENT_ORANGE))
    d.add(String(387, 50, "Exit Remoteness Deficit", fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.white))
    d.add(String(387, 41, "Sep: 4.26m < 16.11m (1/3 Diag)", fontName="Helvetica", fontSize=5.5, fillColor=TEXT_MUTED))
    d.add(String(387, 32, "Clause: UAE FLSC Table 3.15.a", fontName="Helvetica-Oblique", fontSize=5.5, fillColor=ACCENT_CYAN))
    d.add(Rect(387, 21, 48, 8, rx=1, ry=1, fillColor=ACCENT_ORANGE, strokeColor=None))
    d.add(String(411, 23, "Status: Open", fontName="Helvetica-Bold", fontSize=5, fillColor=colors.white, textAnchor="middle"))

    return d


def create_pipeline_flowchart():
    """
    Vector diagram showing the 5-stage mathematical compliance pipeline
    """
    d = Drawing(520, 85)
    
    stages = [
        ("STAGE 1", "Ingestion", "PDF / DXF Binary", "Supabase BYTEA", ACCENT_BLUE),
        ("STAGE 2", "Extraction", "Wall / Door / Exit", "Polygonization", ACCENT_CYAN),
        ("STAGE 3", "Graph Path", "Medial Axis Mesh", "Dijkstra Egress", colors.HexColor("#7C3AED")),
        ("STAGE 4", "Code Rules", "168 UAE Clauses", "Statutory Checks", ACCENT_RED),
        ("STAGE 5", "Live Studio", "Tri-Mode Canvas", "Audit Resolution", ACCENT_GREEN),
    ]

    x_step = 104
    for i, (tag, title, sub1, sub2, col) in enumerate(stages):
        x = i * x_step + 4
        # Box
        d.add(Rect(x, 6, 94, 73, rx=4, ry=4, fillColor=BG_CARD, strokeColor=col, strokeWidth=1.2))
        d.add(Rect(x, 61, 94, 18, rx=4, ry=4, fillColor=col, strokeColor=None))
        d.add(String(x + 47, 66, tag, fontName="Helvetica-Bold", fontSize=7, fillColor=colors.white, textAnchor="middle"))
        d.add(String(x + 47, 48, title, fontName="Helvetica-Bold", fontSize=8.5, fillColor=PRIMARY, textAnchor="middle"))
        d.add(String(x + 47, 34, sub1, fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED, textAnchor="middle"))
        d.add(String(x + 47, 20, sub2, fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED, textAnchor="middle"))

        # Arrow to next stage
        if i < len(stages) - 1:
            arr_x = x + 94
            d.add(Line(arr_x + 1, 42, arr_x + 8, 42, strokeColor=PRIMARY, strokeWidth=1.5))
            d.add(Polygon([arr_x + 7, 45, arr_x + 10, 42, arr_x + 7, 39], fillColor=PRIMARY, strokeColor=None))

    return d


def create_roadmap_diagram():
    """
    Vector diagram depicting the 4 evolutionary horizons of the EGRESS platform
    """
    d = Drawing(520, 110)
    
    phases = [
        ("CURRENT V1.2 (DEPLOYED)", "Production Baseline", "2D CAD & PDF Analysis\n168 UAE FLSC Clauses\nTri-Mode Canvas Studio\nCloud Persistent DB", ACCENT_GREEN),
        ("PHASE 1 (NEAR-TERM)", "BIM & Official Stamping", "IFC 4.3 3D BIM Ingestion\nAuto Civil Defence PDF\nDigital Auditor Seal\nAutomated Revit Sync", ACCENT_BLUE),
        ("PHASE 2 (MEDIUM-TERM)", "Evacuation Dynamics", "Multi-Stair Vertical Flow\nRVO2 Agent Simulation\nSmoke Dynamic Block\nAI Layout Optimizer", ACCENT_ORANGE),
        ("PHASE 3 (ENTERPRISE)", "Government Ecosystem", "Civil Defence Portal API\nEnterprise Multi-Tenancy\nLive BIM360 Webhooks\nUAE Municipal E-Permit", colors.HexColor("#7C3AED")),
    ]

    card_w = 122
    for i, (title, subtitle, bullets, col) in enumerate(phases):
        x = i * (card_w + 8) + 4
        # Card Background
        d.add(Rect(x, 6, card_w, 98, rx=4, ry=4, fillColor=BG_CARD, strokeColor=col, strokeWidth=1.2))
        d.add(Rect(x, 82, card_w, 22, rx=4, ry=4, fillColor=col, strokeColor=None))
        d.add(String(x + card_w/2, 88, title, fontName="Helvetica-Bold", fontSize=6.5, fillColor=colors.white, textAnchor="middle"))
        d.add(String(x + card_w/2, 71, subtitle, fontName="Helvetica-Bold", fontSize=7.5, fillColor=PRIMARY, textAnchor="middle"))
        
        # Split bullets
        bullet_lines = bullets.split("\n")
        y = 56
        for bl in bullet_lines:
            d.add(String(x + 8, y, f"- {bl}", fontName="Helvetica", fontSize=6.5, fillColor=TEXT_MUTED))
            y -= 12

    return d


# ----------------------------------------------------------------------
# PDF COMPILER & REPORT GENERATOR
# ----------------------------------------------------------------------
def build_pdf(filename: str):
    """
    Compiles the complete Technical and Product Document for https://egress-jade.vercel.app/
    into a publication-grade PDF file.
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=ACCENT_BLUE,
        spaceAfter=14
    )
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'Header3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=SECONDARY,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=TEXT_DARK,
        spaceAfter=6
    )
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=PRIMARY
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=TEXT_DARK
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10.5,
        textColor=PRIMARY
    )
    table_cell_code = ParagraphStyle(
        'TableCellCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9.5,
        textColor=SECONDARY
    )

    story = []

    # ==================================================================
    # PAGE 1: COVER & EXECUTIVE LANDSCAPE
    # ==================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("EGRESS CLOUD PLATFORM", ParagraphStyle('Eyebrow', fontName='Helvetica-Bold', fontSize=10, textColor=ACCENT_RED, spaceAfter=4)))
    story.append(Paragraph("Deployed System Technical & Product Specification", title_style))
    story.append(Paragraph("Autonomous Fire & Life Safety (FLS) Architectural Review Engine", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceBefore=2, spaceAfter=10))

    # Deployment Details Box
    deploy_info = [
        [Paragraph("<b>Production Frontend URL:</b>", table_cell), Paragraph("<font color='#2563EB'><u>https://egress-jade.vercel.app/</u></font> (Vercel Edge Global CDN)", table_cell)],
        [Paragraph("<b>Production API Backend:</b>", table_cell), Paragraph("<font color='#0891B2'><u>https://egressandco.onrender.com</u></font> (Render Python 3.11 Container)", table_cell)],
        [Paragraph("<b>Database & Storage Layer:</b>", table_cell), Paragraph("Supabase Managed Cloud PostgreSQL (aws-0-ap-northeast-2.pooler.supabase.com)", table_cell)],
        [Paragraph("<b>Regulatory Code Baseline:</b>", table_cell), Paragraph("UAE Fire & Life Safety Code of Practice (FLSC) 2018 Edition - Chapter 3", table_cell)],
        [Paragraph("<b>Current Release Version:</b>", table_cell), Paragraph("v1.2.0-cloud-production (Verified Persistent Multi-Container Build)", table_cell)],
        [Paragraph("<b>Primary Architectural Personas:</b>", table_cell), Paragraph("Civil Defence Reviewers, Fire Safety Engineers, Principal Architects, BIM/MEP Consultants", table_cell)]
    ]
    t_deploy = Table(deploy_info, colWidths=[150, 370])
    t_deploy.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_deploy)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Executive Product Manifesto", h1_style))
    story.append(Paragraph(
        "Modern architectural compliance evaluation remains one of the most critical, labor-intensive, and error-prone bottlenecks in urban property development across the Middle East. Architectural reviews for statutory egress compliance--including occupant load derivations, exit capacity sizing, travel distance thresholds, and exit separation geometries--are traditionally calculated manually by fire engineers over 2D drawings. This manual process introduces severe subjective variances, missed non-compliances, and multi-week approval delays with municipal authorities.",
        body_style
    ))
    story.append(Paragraph(
        "<b>EGRESS</b> is a zero-trust, automated compliance verification engine deployed in the cloud. It accepts commercial architectural CAD drawings (AutoCAD DXF) and vector/raster floor plans (PDF), executes deterministic geometric polygonization, builds a true walkable medial-axis graph, and automatically audits the design against the statutory requirements of the <b>UAE Fire and Life Safety Code of Practice 2018 (Chapter 3: Means of Egress)</b>. The system delivers mathematical certainty, pinpointing non-compliant rooms, undersized doors, excessive travel distances, and deficient exit remoteness with spatial exactness.",
        body_style
    ))

    # Architecture Diagram
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Figure 1:</b> Deployed Cloud Topology & Distributed Architecture", h3_style))
    story.append(create_cloud_architecture_diagram())
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # ==================================================================
    # PAGE 2: USER INTERFACE & FEATURE MAP (WHAT IT DOES & WHERE)
    # ==================================================================
    story.append(Paragraph("2. Deployed User Interface & Interaction Blueprint", h1_style))
    story.append(Paragraph(
        "The live production interface at <b>https://egress-jade.vercel.app/</b> is designed for high-density, professional architectural inspection. It integrates real-time viewport transformations, spatial layer controls, multi-floor tab switching, and an interactive audit tracking workflow. The schematic below maps the spatial layout of the live web application.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Figure 2:</b> Deployed Web Studio Interface Schematic (https://egress-jade.vercel.app/)", h3_style))
    story.append(create_ui_layout_diagram())
    story.append(Spacer(1, 8))

    story.append(Paragraph("Detailed Component & Feature Directory", h2_style))

    ui_components = [
        [
            Paragraph("<b>Component Name</b>", table_cell_bold),
            Paragraph("<b>Physical Screen Location</b>", table_cell_bold),
            Paragraph("<b>Operational Functionality & User Actions</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>EgressCo Home Landing</b>", table_cell_bold),
            Paragraph("Initial View (<code>screen === 'egress'</code>)", table_cell),
            Paragraph("Editorial landing hero highlighting UAE Civil Defence compliance, statutory code matrix reference, drag-and-drop file upload zone, and quick demo project launcher.", table_cell)
        ],
        [
            Paragraph("<b>Upload Modal & Config</b>", table_cell_bold),
            Paragraph("Top Header Button <code>[+ New Upload]</code>", table_cell),
            Paragraph("Accepts AutoCAD DXF (.dxf) and architectural PDF (.pdf). Configures Occupancy Type (Business, Assembly, Mercantile, etc.), Sprinkler Protection toggle, and CAD drawing scale factor.", table_cell)
        ],
        [
            Paragraph("<b>Studio Left Sidebar</b>", table_cell_bold),
            Paragraph("Left Panel (Width: 320px)", table_cell),
            Paragraph("Displays active project metadata, gross floor area (m2), total calculated occupant load (persons), code limits summary, dynamic multi-floor page selector tabs, and CSV/Audit export buttons.", table_cell)
        ],
        [
            Paragraph("<b>Tri-Mode Canvas Viewer</b>", table_cell_bold),
            Paragraph("Central Viewport Stage", table_cell),
            Paragraph("Hardware-accelerated viewport with Pan (drag/middle-click) and Zoom (scroll wheel / on-screen +/-). Supports 3 viewing modes: <b>Hybrid</b> (raster base + vector overlays), <b>Vector Blueprint</b> (high-contrast geometry), and <b>Raster Arch</b> (220 DPI crisp PyMuPDF rendering).", table_cell)
        ],
        [
            Paragraph("<b>Spatial Layer Controls</b>", table_cell_bold),
            Paragraph("Top Floating Toolbar in Canvas", table_cell),
            Paragraph("Independent visibility toggles for: <i>Walls, Rooms, Doors, Exits, Walkable Egress Paths, Violation Pins, and Metric Measurement Grid</i>.", table_cell)
        ],
        [
            Paragraph("<b>Interactive Violation Pins</b>", table_cell_bold),
            Paragraph("Overlaid on Canvas Floor Plan", table_cell),
            Paragraph("Pulsing, severity-coded pins anchored to the exact coordinates of non-compliances. Clicking a pin pans the viewport, highlights the affected room/door, and selects the finding card in the right drawer.", table_cell)
        ],
        [
            Paragraph("<b>Audit Findings Panel</b>", table_cell_bold),
            Paragraph("Right Panel (Width: 360px)", table_cell),
            Paragraph("Real-time compliance checklist categorized by Critical, High, and Medium severity. Allows searching, filtering, reading exact UAE code clauses, and updating status (Open, Confirmed, False Positive, Resolved) with auditor notes.", table_cell)
        ],
        [
            Paragraph("<b>Multi-Floor Overview Modal</b>", table_cell_bold),
            Paragraph("Invoked from Left Sidebar Tab", table_cell),
            Paragraph("Comprehensive building-wide summary aggregating room count, exits count, occupant load, maximum travel distance, and compliance status across every level in a multi-page PDF/CAD set.", table_cell)
        ],
        [
            Paragraph("<b>Fullscreen Studio Mode</b>", table_cell_bold),
            Paragraph("Key <code>[F]</code> or Header Button", table_cell),
            Paragraph("Maximizes the architectural canvas to full monitor resolution with docked layer controls and a collapsible findings drawer for unobstructed plan review.", table_cell)
        ]
    ]
    t_ui = Table(ui_components, colWidths=[110, 110, 300])
    t_ui.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG_CARD, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_ui)

    story.append(PageBreak())

    # ==================================================================
    # PAGE 3: END-TO-END COMPUTATIONAL PIPELINE & RULES ENGINE
    # ==================================================================
    story.append(Paragraph("3. End-to-End Mathematical Computation Pipeline", h1_style))
    story.append(Paragraph(
        "When an architectural floor plan is uploaded through <code>https://egress-jade.vercel.app/</code>, the system executes an automated, five-stage computational geometry and statutory audit pipeline on the Render backend before returning spatial features to the React frontend.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Figure 3:</b> Five-Stage Architectural Ingestion & Statutory Audit Pipeline", h3_style))
    story.append(create_pipeline_flowchart())
    story.append(Spacer(1, 8))

    story.append(Paragraph("Stage-by-Stage Mathematical Mechanics", h2_style))

    story.append(Paragraph(
        "<b>Stage 1: Ingestion, Validation & Persistent Binary Commit:</b> The multipart upload is validated against MIME constraints (.dxf, .pdf). The binary payload is immediately committed into the Supabase PostgreSQL <code>drawing_files</code> table as a <code>BYTEA</code> blob, ensuring 100% cloud persistence across Render container restarts. A local filesystem cache is populated for fast I/O.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Stage 2: Geometric Extraction & Planar Polygonization:</b> For AutoCAD DXF files, <code>ezdxf</code> extracts <code>LINE</code>, <code>LWPOLYLINE</code>, and <code>TEXT</code> entities across architectural layers (A-WALL, A-DOOR, A-EXIT). For vector PDFs, <code>pymupdf</code> vector drawing command paths are parsed into closed Shapely polygons using <code>shapely.ops.polygonize</code>. Rooms are validated for topological validity, calculating exact net and gross usable floor area in square meters (m2).",
        body_style
    ))
    story.append(Paragraph(
        "<b>Stage 3: Medial Axis Network Graph & Shortest Egress Path:</b> To compute true walkable egress distance (rather than simplistic Euclidean straight-line distance), the engine constructs a geometric medial axis graph using <code>networkx</code>. Obstacles (walls, structural columns, utility shafts) are subtracted from the walkable corridor envelope. Dijkstra's shortest-path algorithm calculates the exact path from the most remote point of each room to the nearest approved fire exit discharge door.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Stage 4: Statutory Code Rules Engine (UAE FLSC 2018):</b> The extracted spatial entities and derived metrics are evaluated against the statutory parameters stored in the <code>code_clauses</code> database table. If measured values breach code thresholds, a formal violation record is instantiated with severity, clause citation, measured vs limit values, and spatial coordinates.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Stage 5: Live Studio Hydration & Dynamic Interaction:</b> The computed features (rooms, walls, doors, exits, paths, violations) are returned as GeoJSON-compatible vectors to the Vercel frontend. The React client binds the spatial data to the canvas, rendering interactive SVG overlays and populating the audit findings checklist.",
        body_style
    ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Statutory Code Clauses Implemented (UAE FLSC 2018)", h2_style))

    flsc_table = [
        [
            Paragraph("<b>Clause Reference</b>", table_cell_bold),
            Paragraph("<b>Topic & Description</b>", table_cell_bold),
            Paragraph("<b>Statutory Limit / Condition</b>", table_cell_bold),
            Paragraph("<b>Severity</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>UAE-FLS-3.1-BUS-LOAD</b><br/>Table 3.1", table_cell_code),
            Paragraph("<b>Occupant Load Factor</b><br/>Derivation of room occupants from net usable floor area.", table_cell),
            Paragraph("<b>9.3 m2 / person</b> (Business office)<br/>Assembly: 0.65 - 1.4 m2 / person", table_cell),
            Paragraph("<font color='#059669'><b>Standard</b></font>", table_cell)
        ],
        [
            Paragraph("<b>UAE-FLS-3.14-LT500</b><br/>Table 3.14", table_cell_code),
            Paragraph("<b>Minimum Floor Exit Count</b><br/>Mandatory fire egress stairs based on floor occupant load.", table_cell),
            Paragraph("<b>&le; 500 occ: &ge; 2 exits</b><br/>501-1000 occ: &ge; 3 exits<br/>&gt; 1000 occ: &ge; 4 exits", table_cell),
            Paragraph("<font color='#DC2626'><b>Critical</b></font>", table_cell)
        ],
        [
            Paragraph("<b>UAE-FLS-3.15A-REMOTE</b><br/>Table 3.15.a", table_cell_code),
            Paragraph("<b>Exit Remoteness Separation</b><br/>Distance between two exits relative to floor diagonal.", table_cell),
            Paragraph("<b>&ge; 0.333 &times; Diagonal</b> (Sprinklered)<br/>&ge; 0.500 &times; Diagonal (Non-sprinklered)", table_cell),
            Paragraph("<font color='#DC2626'><b>Critical</b></font>", table_cell)
        ],
        [
            Paragraph("<b>UAE-FLS-3.16-BUS-TD</b><br/>Table 3.16", table_cell_code),
            Paragraph("<b>Maximum Travel Distance</b><br/>Walkable distance from remote corner to nearest exit door.", table_cell),
            Paragraph("<b>&le; 76.0 m</b> (Sprinklered Business)<br/>&le; 45.0 m (Non-sprinklered)", table_cell),
            Paragraph("<font color='#D97706'><b>High</b></font>", table_cell)
        ],
        [
            Paragraph("<b>UAE-FLS-3.19-SINGLE-DOOR</b><br/>Table 3.19", table_cell_code),
            Paragraph("<b>Single Exit Door Permission</b><br/>Room occupant threshold allowing a single egress door.", table_cell),
            Paragraph("<b>&lt; 50 persons</b> (Standard rooms)<br/>&lt; 100 persons (Direct exterior discharge)", table_cell),
            Paragraph("<font color='#DC2626'><b>Critical</b></font>", table_cell)
        ],
        [
            Paragraph("<b>UAE-FLS-3.17-DEAD-END</b><br/>Section 3.17", table_cell_code),
            Paragraph("<b>Dead-End Corridor Limit</b><br/>Maximum pocket corridor distance with single egress direction.", table_cell),
            Paragraph("<b>&le; 15.0 m</b> (Sprinklered buildings)<br/>&le; 6.0 m (Non-sprinklered buildings)", table_cell),
            Paragraph("<font color='#D97706'><b>High</b></font>", table_cell)
        ]
    ]
    t_flsc = Table(flsc_table, colWidths=[120, 150, 180, 70])
    t_flsc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG_CARD, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_flsc)

    story.append(PageBreak())

    # ==================================================================
    # PAGE 4: DATA ARCHITECTURE, PERSISTENCE & API REFERENCE
    # ==================================================================
    story.append(Paragraph("4. Cloud Data Architecture & Persistence Invariant", h1_style))
    story.append(Paragraph(
        "A foundational engineering requirement of the deployed system is the <b>Zero-Data-Loss Invariant</b>. Render's free/standard tier operates inside ephemeral Docker containers where local filesystem storage is destroyed on every redeployment or restart. To eliminate data loss, EGRESS implements an enterprise dual-storage architecture backed by Supabase Cloud PostgreSQL.",
        body_style
    ))

    schema_info = [
        [
            Paragraph("<b>Table Name</b>", table_cell_bold),
            Paragraph("<b>Primary Key & Columns</b>", table_cell_bold),
            Paragraph("<b>Storage Type & Purpose</b>", table_cell_bold)
        ],
        [
            Paragraph("<code>projects</code>", table_cell_code),
            Paragraph("<code>id (TEXT PK), name, client_name, created_at, occupancy_type, sprinklered</code>", table_cell),
            Paragraph("Relational table storing parent client projects and default building fire protection configurations.", table_cell)
        ],
        [
            Paragraph("<code>drawings</code>", table_cell_code),
            Paragraph("<code>id (TEXT PK), project_id (FK), file_url, file_type, scale, status, sprinklered, page_index, floor_name</code>", table_cell),
            Paragraph("Core drawing entities linking CAD/PDF metadata, page indices, scale factors, and processing state.", table_cell)
        ],
        [
            Paragraph("<code>drawing_files</code>", table_cell_code),
            Paragraph("<code>drawing_id (TEXT PK FK), filename, file_type, file_bytes (BYTEA), created_at</code>", table_cell),
            Paragraph("<b>Persistent Binary Store:</b> Stores raw architectural PDF and DXF binaries up to 1GB per file in Postgres BYTEA, surviving container resets.", table_cell)
        ],
        [
            Paragraph("<code>extracted_elements</code>", table_cell_code),
            Paragraph("<code>id (TEXT PK), drawing_id (FK), type, name, geometry (GeoJSON), properties (JSON)</code>", table_cell),
            Paragraph("Extracted architectural entities: walls, rooms, doors, stairs, and calculated occupant loads.", table_cell)
        ],
        [
            Paragraph("<code>violations</code>", table_cell_code),
            Paragraph("<code>id (TEXT PK), drawing_id (FK), type, clause_ref, measured_value, limit_value, severity, status, note, geometry</code>", table_cell),
            Paragraph("Audit findings table recording non-compliances, auditor disposition (open/confirmed/resolved), and spatial pins.", table_cell)
        ],
        [
            Paragraph("<code>code_clauses</code>", table_cell_code),
            Paragraph("<code>clause_id (TEXT PK), topic, occupancy, requirement_type, value, unit, condition, note, source_table, source_page</code>", table_cell),
            Paragraph("168 statutory UAE FLSC 2018 clauses seeded directly into PostgreSQL for instantaneous query evaluation.", table_cell)
        ]
    ]
    t_schema = Table(schema_info, colWidths=[90, 220, 210])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG_CARD, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_schema)

    story.append(Spacer(1, 8))
    story.append(Paragraph("Production REST API Endpoint Reference", h2_style))

    api_endpoints = [
        [
            Paragraph("<b>HTTP Method & Route</b>", table_cell_bold),
            Paragraph("<b>Request Payload / Parameters</b>", table_cell_bold),
            Paragraph("<b>Response Structure & Operational Behavior</b>", table_cell_bold)
        ],
        [
            Paragraph("<code>GET /health</code>", table_cell_code),
            Paragraph("None", table_cell),
            Paragraph("Returns <code>{\"status\": \"ok\"}</code>. Used by Render health-checks and edge uptime monitors.", table_cell)
        ],
        [
            Paragraph("<code>GET /projects</code>", table_cell_code),
            Paragraph("None", table_cell),
            Paragraph("Returns array of all saved building projects with occupancy classification and sprinkler status.", table_cell)
        ],
        [
            Paragraph("<code>POST /projects</code>", table_cell_code),
            Paragraph("<code>{ name, client_name, occupancy_type, sprinklered }</code>", table_cell),
            Paragraph("Creates a new building review project record in PostgreSQL and returns generated UUID.", table_cell)
        ],
        [
            Paragraph("<code>POST /projects/{id}/drawings</code>", table_cell_code),
            Paragraph("<code>multipart/form-data: file, occupancy_type, sprinklered, scale</code>", table_cell),
            Paragraph("Uploads CAD/PDF, commits binary to <code>drawing_files</code>, triggers Stage 2-4 computation pipeline.", table_cell)
        ],
        [
            Paragraph("<code>GET /drawings/{id}/image</code>", table_cell_code),
            Paragraph("<code>?page=0</code> (optional page index)", table_cell),
            Paragraph("Streams crisp 220 DPI PNG rasterization of architectural PDF directly from memory or restored cache.", table_cell)
        ],
        [
            Paragraph("<code>GET /drawings/{id}/file</code>", table_cell_code),
            Paragraph("None", table_cell),
            Paragraph("Downloads the exact original binary PDF/DXF file with original filename and Content-Disposition headers.", table_cell)
        ],
        [
            Paragraph("<code>GET /drawings/{id}/violations</code>", table_cell_code),
            Paragraph("None", table_cell),
            Paragraph("Returns list of code violations with clause references, measured values, and spatial coordinates.", table_cell)
        ],
        [
            Paragraph("<code>PATCH /violations/{id}</code>", table_cell_code),
            Paragraph("<code>{ status: 'confirmed'|'false_positive'|'resolved', note: '...' }</code>", table_cell),
            Paragraph("Updates auditor review status and persists justification notes in the database.", table_cell)
        ]
    ]
    t_api = Table(api_endpoints, colWidths=[150, 160, 210])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG_CARD, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_api)

    story.append(PageBreak())

    # ==================================================================
    # PAGE 5: CURRENT CAPABILITIES AUDIT VS. STRATEGIC FUTURE ROADMAP
    # ==================================================================
    story.append(Paragraph("5. Current Production Capabilities vs. Limitations Audit", h1_style))
    story.append(Paragraph(
        "To provide complete transparency for engineering directors and statutory reviewers, this section audits what the live deployed system (v1.2.0) is actively performing right now, alongside acknowledged operational boundaries.",
        body_style
    ))

    audit_matrix = [
        [
            Paragraph("<b>Operational Dimension</b>", table_cell_bold),
            Paragraph("<b>What It Is Doing Now (Live Deployed Capability)</b>", table_cell_bold),
            Paragraph("<b>Current Operational Boundaries & Mitigations</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>CAD & PDF Ingestion</b>", table_cell_bold),
            Paragraph("Ingests AutoCAD DXF (R12 through 2018) and vector/raster PDF files. Auto-detects layers and text annotations.", table_cell),
            Paragraph("Requires vector or standard CAD layers. Pure low-resolution scanned raster images without vector lines require PDF vector export.", table_cell)
        ],
        [
            Paragraph("<b>Egress Distance</b>", table_cell_bold),
            Paragraph("Computes true walkable shortest paths around architectural walls using Dijkstra graph traversal.", table_cell),
            Paragraph("Currently evaluated floor-by-floor in 2D. Vertical stair traversal is calculated as discrete floor-level discharge points.", table_cell)
        ],
        [
            Paragraph("<b>Cloud Persistence</b>", table_cell_bold),
            Paragraph("100% verified cross-redeploy persistence for both relational project data and binary drawing files in Supabase.", table_cell),
            Paragraph("Render free-tier cold starts (~30s spin-up upon initial wake-up after 15 min idle). Paid standard instances eliminate cold starts.", table_cell)
        ],
        [
            Paragraph("<b>Interactive Audit</b>", table_cell_bold),
            Paragraph("Auditors can review findings, mark dispositions (Confirmed/False Positive/Resolved), and record sign-off notes.", table_cell),
            Paragraph("Currently session-linked; multi-user concurrent presence locking is scheduled for Phase 3 enterprise release.", table_cell)
        ],
        [
            Paragraph("<b>Statutory Rules</b>", table_cell_bold),
            Paragraph("168 UAE FLSC Chapter 3 clauses active for Business, Mercantile, Storage, and Assembly occupancies.", table_cell),
            Paragraph("Industrial hazardous chemical storage occupancies (Chapter 4) are currently undergoing code mapping.", table_cell)
        ]
    ]
    t_audit = Table(audit_matrix, colWidths=[110, 205, 205])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG_CARD, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_audit)

    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Future Strategic Roadmap & Planned Capabilities", h1_style))
    story.append(Paragraph(
        "The strategic engineering roadmap for the EGRESS platform expands from 2D statutory auditing into full Building Information Modeling (BIM 3D), dynamic evacuation crowd simulation, and direct government civil defence e-portal integration.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Figure 4:</b> Four-Horizon Evolutionary Roadmap for the EGRESS Platform", h3_style))
    story.append(create_roadmap_diagram())
    story.append(Spacer(1, 8))

    story.append(Paragraph("Roadmap Phase Breakdown & Milestones", h2_style))

    roadmap_details = [
        [
            Paragraph("<b>Release Phase</b>", table_cell_bold),
            Paragraph("<b>Target Horizon</b>", table_cell_bold),
            Paragraph("<b>Key Engineering Deliverables & Value Propositions</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>Phase 1: Near-Term</b><br/>BIM & Formal Stamping", table_cell_bold),
            Paragraph("Q3 - Q4 2026", table_cell),
            Paragraph("<b>1. Industry Foundation Classes (IFC 4.3) Ingestion:</b> Native 3D BIM extraction via <code>ifcopenshell</code>.<br/><b>2. Automated Civil Defence PDF Stamper:</b> Generates official municipal submission PDFs with embedded digital signatures, cryptographic hashes, and clause audit tables.<br/><b>3. Autodesk Revit & BIM 360 Plugin:</b> Direct export from Revit without manual DXF exports.", table_cell)
        ],
        [
            Paragraph("<b>Phase 2: Medium-Term</b><br/>Evacuation Dynamics", table_cell_bold),
            Paragraph("Q1 - Q2 2027", table_cell),
            Paragraph("<b>1. Multi-Stair Vertical Evacuation Modeling:</b> Simulates stairwell descent velocities and merging flows at intermediate landings.<br/><b>2. Agent-Based Crowd Simulation (RVO2):</b> Reciprocal Velocity Obstacle modeling simulating human egress bottlenecks and panic discharge dynamics.<br/><b>3. Generative Layout Optimizer:</b> AI-assisted floor plan adjustments suggesting compliant door placements and corridor widening.", table_cell)
        ],
        [
            Paragraph("<b>Phase 3: Long-Term</b><br/>Government Ecosystem", table_cell_bold),
            Paragraph("Q3 - Q4 2027", table_cell),
            Paragraph("<b>1. Dubai & Abu Dhabi Civil Defence API Integration:</b> Direct automated submission to the Civil Defence E-Permit approval portal.<br/><b>2. Multi-Tenant Enterprise Accounts:</b> Role-based access control (Auditor, Senior Engineer, Authority Having Jurisdiction).<br/><b>3. Real-Time IoT Building Sensor Sync:</b> Ingests live turnstile counts to evaluate dynamic emergency egress during operational hours.", table_cell)
        ]
    ]
    t_road = Table(roadmap_details, colWidths=[120, 80, 320])
    t_road.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BG_CARD, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_road)

    story.append(Spacer(1, 10))
    # Closing Sign-off Callout
    signoff = [
        [
            Paragraph(
                "<b>AUTHORITY NOTICE & CERTIFICATION:</b><br/>"
                "This technical and product specification describes the active deployed architecture of the EGRESS Platform operating at <b>https://egress-jade.vercel.app/</b>. "
                "All statutory compliance algorithms adhere strictly to the <i>UAE Fire & Life Safety Code of Practice (2018 Edition)</i>. "
                "Verified by Automated Engineering Assurance Pipeline on August 30, 2026.",
                callout_style
            )
        ]
    ]
    t_sign = Table(signoff, colWidths=[520])
    t_sign.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HIGHLIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, ACCENT_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_sign)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Technical & Product PDF at: {filename}")


if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent.parent / "summary"
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "EGRESS_Deployed_Technical_and_Product_Document.pdf"
    
    build_pdf(str(pdf_path))
    
    # Also copy to root
    root_pdf = Path(__file__).resolve().parent.parent / "EGRESS_Deployed_Technical_and_Product_Document.pdf"
    shutil.copyfile(str(pdf_path), str(root_pdf))
    print(f"Copied master PDF to project root: {root_pdf}")
