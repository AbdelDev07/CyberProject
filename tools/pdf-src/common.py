"""Styles + helpers de dessin vectoriel partagés par les deux PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Preformatted, KeepTogether, Flowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle, PolyLine
from reportlab.graphics import renderPDF

FD = "/usr/share/fonts/truetype/dejavu/"
for n, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
             ("DV-I", "DejaVuSans-Oblique.ttf"), ("DVM", "DejaVuSansMono.ttf"),
             ("DVM-B", "DejaVuSansMono-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(n, FD + f))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-B")

NAVY = colors.HexColor("#1f3a5f")
BLUE = colors.HexColor("#2b6cb0")
LBLUE = colors.HexColor("#dbeafe")
RED = colors.HexColor("#c0392b")
LRED = colors.HexColor("#fdecea")
GREEN = colors.HexColor("#1e7e34")
LGREEN = colors.HexColor("#e6f4ea")
ORANGE = colors.HexColor("#b26a00")
LORANGE = colors.HexColor("#fff4e0")
GREY = colors.HexColor("#f2f4f7")
DGREY = colors.HexColor("#6b7280")
CODEBG = colors.HexColor("#f6f8fa")
BORDER = colors.HexColor("#c9ced6")

S = {
    "title": ParagraphStyle("t", fontName="DV-B", fontSize=25, leading=31, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6),
    "sub": ParagraphStyle("s", fontName="DV", fontSize=12, leading=17, textColor=colors.HexColor("#555"), alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=15.5, leading=20, textColor=NAVY, spaceBefore=14, spaceAfter=7),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=12, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="DV-B", fontSize=10.3, leading=14, textColor=BLUE, spaceBefore=7, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="DV", fontSize=9.7, leading=14, spaceAfter=5, allowWidows=0),
    "pj": ParagraphStyle("pj", fontName="DV", fontSize=9.7, leading=14, spaceAfter=5, alignment=TA_JUSTIFY),
    "li": ParagraphStyle("li", fontName="DV", fontSize=9.7, leading=13.6, leftIndent=14, bulletIndent=3, spaceAfter=2.5),
    "exo": ParagraphStyle("exo", fontName="DV-B", fontSize=10.5, leading=14, textColor=RED, spaceBefore=9, spaceAfter=3),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=8.1, leading=10.6, backColor=CODEBG, borderPadding=(5, 6, 5, 6),
                           borderColor=BORDER, borderWidth=0.5, leftIndent=2, rightIndent=2, spaceBefore=3, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=8.5, leading=11),
    "cellc": ParagraphStyle("cellc", fontName="DVM", fontSize=8, leading=10.5),
    "cellb": ParagraphStyle("cellb", fontName="DV-B", fontSize=8.5, leading=11, textColor=colors.white),
    "cap": ParagraphStyle("cap", fontName="DV-I", fontSize=8.4, leading=11, textColor=DGREY, alignment=TA_CENTER, spaceAfter=9, spaceBefore=1),
}


def _boxstyle(bg, bd, tc):
    return ParagraphStyle("b", fontName="DV", fontSize=9.4, leading=13.4, backColor=bg, borderColor=bd,
                          borderWidth=0.9, borderPadding=(6, 8, 6, 8), leftIndent=3, rightIndent=3,
                          textColor=tc, spaceBefore=6, spaceAfter=9)


S["boxi"] = _boxstyle(LBLUE, BLUE, colors.HexColor("#123"))      # info
S["boxw"] = _boxstyle(LORANGE, ORANGE, colors.HexColor("#3a2600"))  # attention
S["boxe"] = _boxstyle(LRED, RED, colors.HexColor("#3a0d08"))      # erreur
S["boxg"] = _boxstyle(LGREEN, GREEN, colors.HexColor("#062812"))  # correct
S["quote"] = ParagraphStyle("q", fontName="DV-I", fontSize=9.4, leading=13, textColor=colors.HexColor("#1a5fa8"),
                            leftIndent=10, borderPadding=(4, 6, 4, 6), backColor=colors.HexColor("#f0f6ff"),
                            spaceBefore=3, spaceAfter=5)

W = A4[0] - 4 * cm


class Builder:
    def __init__(self):
        self.story = []

    # --- texte ---
    def P(self, t, s="p"): self.story.append(Paragraph(t, S[s])); return self
    def H1(self, t): self.story.append(Paragraph(t, S["h1"]))
    def H2(self, t): self.story.append(Paragraph(t, S["h2"]))
    def H3(self, t): self.story.append(Paragraph(t, S["h3"]))
    def EXO(self, t): self.story.append(Paragraph(t, S["exo"]))
    def BOX(self, t, kind="i"): self.story.append(KeepTogether(Paragraph(t, S["box" + kind])))
    def QUOTE(self, t): self.story.append(Paragraph("« " + t + " »", S["quote"]))
    def CAP(self, t): self.story.append(Paragraph(t, S["cap"]))
    def SP(self, h=8): self.story.append(Spacer(1, h))
    def PB(self): self.story.append(PageBreak())

    def LI(self, items, bullet="•"):
        for i in items:
            self.story.append(Paragraph(i, S["li"], bulletText=bullet))

    def NUM(self, items, start=1):
        for n, i in enumerate(items, start):
            self.story.append(Paragraph(i, S["li"], bulletText=f"{n}."))

    def CODE(self, t, keep=None):
        t = t.strip("\n")
        f = Preformatted(t, S["code"])
        if keep is None:
            keep = t.count("\n") <= 15      # les blocs courts ne doivent pas se couper
        self.story.append(KeepTogether(f) if keep else f)

    def TABLE(self, head, rows, widths, keep=None, align=None, mono=None):
        if keep is None:
            keep = len(rows) <= 5
        mono = mono or []
        data = [[Paragraph(h, S["cellb"]) for h in head]]
        for r in rows:
            data.append([Paragraph(c, S["cellc"] if j in mono else S["cell"]) for j, c in enumerate(r)])
        t = Table(data, colWidths=widths, repeatRows=1)
        cmds = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GREY]),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        if align:
            cmds += align
        t.setStyle(TableStyle(cmds))
        self.story.append(KeepTogether(t) if keep else t)
        self.story.append(Spacer(1, 8))

    def FIG(self, drawing, caption=None):
        self.story.append(KeepTogether(
            [drawing] + ([Paragraph(caption, S["cap"])] if caption else [])))
        self.story.append(Spacer(1, 4))


# ---------------------------------------------------------------- dessin ----
def _wrap(d, text, x, y, w, size, font, color, anchor="middle"):
    """Écrit du texte multi-lignes centré verticalement autour de y."""
    lines = text.split("\n")
    total = len(lines) * (size + 1.6) - 1.6
    ty = y + total / 2 - size * 0.82
    for ln in lines:
        d.add(String(x, ty, ln, fontName=font, fontSize=size, fillColor=color, textAnchor=anchor))
        ty -= size + 1.6


def box(d, x, y, w, h, text, fill=colors.white, stroke=NAVY, tc=None, size=7.6,
        font="DV", radius=3, sw=1.0, dash=None):
    """Rectangle centré en (x, y) avec texte."""
    r = Rect(x - w / 2, y - h / 2, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=sw)
    if radius:
        r.rx = r.ry = radius
    if dash:
        r.strokeDashArray = dash
    d.add(r)
    if text:
        _wrap(d, text, x, y, w, size, font, tc or NAVY)
    return d


def arrow(d, x1, y1, x2, y2, color=NAVY, sw=1.2, head=5.0, label=None, lsize=6.8,
          lcolor=None, dash=None, lside=0):
    """Flèche droite de (x1,y1) vers (x2,y2)."""
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    ln = Line(x1, y1, bx, by, strokeColor=color, strokeWidth=sw)
    if dash:
        ln.strokeDashArray = dash
    d.add(ln)
    p = math.pi
    d.add(Polygon([x2, y2,
                   x2 - head * 1.5 * math.cos(ang - 0.42), y2 - head * 1.5 * math.sin(ang - 0.42),
                   x2 - head * 1.5 * math.cos(ang + 0.42), y2 - head * 1.5 * math.sin(ang + 0.42)],
                  fillColor=color, strokeColor=color))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        off = 6 + lside
        if abs(y2 - y1) > abs(x2 - x1):   # flèche verticale -> label à côté
            _wrap(d, label, mx + off + 2, my, 0, lsize, "DV", lcolor or color, anchor="start")
        else:
            _wrap(d, label, mx, my + off, 0, lsize, "DV", lcolor or color)
    return d


def elbow(d, pts, color=NAVY, sw=1.2, head=5.0, label=None, lsize=6.8, lat=None):
    """Polyligne avec pointe de flèche au dernier segment."""
    d.add(PolyLine([c for p in pts[:-1] for c in p] + list(pts[-1]),
                   strokeColor=color, strokeWidth=sw))
    import math
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    d.add(Polygon([x2, y2,
                   x2 - head * 1.5 * math.cos(ang - 0.42), y2 - head * 1.5 * math.sin(ang - 0.42),
                   x2 - head * 1.5 * math.cos(ang + 0.42), y2 - head * 1.5 * math.sin(ang + 0.42)],
                  fillColor=color, strokeColor=color))
    if label and lat:
        _wrap(d, label, lat[0], lat[1], 0, lsize, "DV", color, anchor=lat[2] if len(lat) > 2 else "middle")


def txt(d, x, y, t, size=7.5, color=NAVY, font="DV", anchor="middle"):
    _wrap(d, t, x, y, 0, size, font, color, anchor=anchor)


def band(d, x, y, w, h, text, fill, tc=colors.white, size=8, font="DV-B"):
    d.add(Rect(x - w / 2, y - h / 2, w, h, fillColor=fill, strokeColor=fill))
    _wrap(d, text, x, y, w, size, font, tc)


def footer_factory(label):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("DV", 7.8)
        canvas.setFillColor(DGREY)
        canvas.drawString(2 * cm, 1.15 * cm, label)
        canvas.drawRightString(A4[0] - 2 * cm, 1.15 * cm, f"Page {doc.page}")
        canvas.setStrokeColor(colors.HexColor("#d5d9e0"))
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, 1.45 * cm, A4[0] - 2 * cm, 1.45 * cm)
        canvas.restoreState()
    return footer


def build(story, path, title, footer_label, subject=""):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.9 * cm, bottomMargin=1.9 * cm,
                            title=title, author="Claude", subject=subject)
    f = footer_factory(footer_label)
    doc.build(story, onFirstPage=f, onLaterPages=f)
    return path
