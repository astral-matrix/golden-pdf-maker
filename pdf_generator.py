"""
Golden PDF Generator (May 2025)
===============================
A single‑file utility that converts **GitHub‑flavoured Markdown** into a
print‑ready PDF using *ReportLab*.  It is designed for rapid, dependency‑light
report generation inside ChatGPT workflows but works equally well in any
Python script.

Key features
------------
* **Markdown parsing** – headings (H1/H2/H3), unordered lists, fenced code
  blocks, and GitHub‑style tables.
* **Inline formatting** – bold (`**text**`) and italic (`*text*`) render inside
  paragraphs *and* inside table cells.
* **Glyph‑safe output** – replaces fancy dashes, NBSPs, soft hyphens, and other
  problem glyphs that often show up as black boxes in PDFs.
* **Auto‑wrapping tables** – row height expands for multi‑line content; grid and
  header styling are applied automatically.
* **Reusable API** – call `build_pdf(markdown_str, "file.pdf")` or, for more
  control, use `markdown_to_flowables()` to embed the generated flowables in a
  larger ReportLab story.

Requirements
~~~~~~~~~~~~
```
reportlab>=3.6.0  # tested with 3.6.12
```
Install with: `python -m pip install -r requirements.txt`

Quick‑start
~~~~~~~~~~~
```python
from pdf_generator import build_pdf

md = """
### Demo
| **Bold** | *Italic* |
|----------|----------|
| cell A   | cell B   |
"""

build_pdf(md, "demo.pdf")
```
"""
from __future__ import annotations
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import html, re, unicodedata
from typing import List

# ─── Style sheet ──────────────────────────────────────────────────────
STYLES = getSampleStyleSheet()
_BASE = {
    "H1":  dict(fontSize=14, leading=18, spaceAfter=12, spaceBefore=18,
                alignment=1, fontName="Helvetica-Bold"),
    "H2":  dict(fontSize=12, leading=16, spaceAfter=8,  spaceBefore=12,
                fontName="Helvetica-Bold"),
    "H3":  dict(fontSize=11, leading=15, spaceAfter=6,  spaceBefore=10,
                fontName="Helvetica-Bold"),
    "Body": dict(fontSize=10, leading=14, spaceAfter=4),
    "Code": dict(fontName="Courier", fontSize=8, leading=10, spaceAfter=6),
}
for name, attrs in _BASE.items():
    if name not in STYLES:
        STYLES.add(ParagraphStyle(name=name, **attrs))

# ─── Glyph‑safe sanitizer ─────────────────────────────────────────────

def _sanitize(txt: str) -> str:
    """Replace unsupported glyphs and strip zero‑width/control chars."""
    repl = {
        "\u2013": "-", "\u2014": "-",      # en/em dash
        "\u00A0": " ", "\u202F": " ",      # NBSPs
        "\u00AD": "-", "\u2060": "",       # soft‑hyphen / word‑joiner
    }
    for bad, good in repl.items():
        txt = txt.replace(bad, good)
    txt = "".join(ch for ch in txt
                  if not unicodedata.category(ch).startswith("C") or ch in ("\n", "\t"))
    return (txt.replace("&nbsp;", " ")
               .replace("&quot;", "\"")
               .replace("&amp;",  "&"))

# ─── Inline markdown (bold / italic) ─────────────────────────────────

def _fmt_inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\\1</b>", t)
    t = re.sub(r"\*(.+?)\*",   r"<i>\\1</i>", t)
    return t

# ─── Table helper ────────────────────────────────────────────────────

def _table(rows: List[List[str]]):
    para_rows = [[Paragraph(cell, STYLES["Body"]) for cell in row] for row in rows]
    tbl = Table(para_rows, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.lightgrey),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
    ]))
    return tbl

# ─── Markdown → Flowables ────────────────────────────────────────────

def markdown_to_flowables(md: str) -> List:
    """Convert a Markdown string into a list of ReportLab *flowables*."""
    flow, code_buf, table_buf = [], [], []
    in_code = False

    def flush_code():
        if code_buf:
            flow.append(
                Paragraph(
                    html.escape("\n".join(code_buf))
                        .replace(" ", "&nbsp;")
                        .replace("\n", "<br/>"),
                    STYLES["Code"],
                )
            )
            code_buf.clear()

    def flush_table():
        if table_buf:
            flow.extend([_table(table_buf), Spacer(1, 0.15 * inch)])
            table_buf.clear()

    for raw in md.strip().splitlines() + [""]:
        line = _sanitize(raw)

        # fenced code blocks
        if line.strip().startswith("```"):
            in_code = not in_code
            if not in_code:
                flush_code()
            continue
        if in_code:
            code_buf.append(line)
            continue

        # GitHub‑style tables
        if "|" in line and not line.lstrip().startswith("#"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r"-+", c.replace(" ", "")) for c in cells):
                continue  # skip separator row
            table_buf.append([_fmt_inline(c) for c in cells])
            continue
        else:
            flush_table()

        # headings
        if line.startswith("# "):
            flow.append(Paragraph(_fmt_inline(line[2:]), STYLES["H1"])); continue
        if line.startswith("## "):
            flow.append(Paragraph(_fmt_inline(line[3:]), STYLES["H2"])); continue
        if line.startswith("### "):
            flow.append(Paragraph(_fmt_inline(line[4:]), STYLES["H3"])); continue

        # unordered list
        if line.startswith(("- ", "* ")):
            flow.append(Paragraph("• " + _fmt_inline(line[2:]), STYLES["Body"])); continue

        # blank lines
        if not line.strip():
            flow.append(Spacer(1, 0.15 * inch)); continue

        # normal paragraph
        flow.append(Paragraph(_fmt_inline(line), STYLES["Body"]))

    flush_table(); flush_code()
    return flow

# ─── High‑level helper ───────────────────────────────────────────────

def build_pdf(markdown: str, filename: str):
    """Render *markdown* to *filename* (PDF)."""
    story = markdown_to_flowables(markdown)
    SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=36,
    ).build(story)

# Smoke‑test when running this file directly -------------------------
if __name__ == "__main__":
    sample = """
    ### Quick Demo

    | **Bold** cell | *Italic* cell |
    |---------------|---------------|
    | **A**         | *B*           |

    ```python
    print('Hello PDF')
    ```
    """
    build_pdf(sample, "demo.pdf")
