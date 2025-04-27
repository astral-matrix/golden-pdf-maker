# Golden PDF Generator

A single-file utility (`pdf_generator.py`) that converts **GitHub‑flavoured Markdown** into production‑ready PDFs using [ReportLab].

## ✨ Features

| Category | Details |
|----------|---------|
| Markdown parsing | H1‑H3 headings, unordered lists, fenced code‑blocks, GitHub‑style tables |
| Inline formatting | **Bold** and *italic* rendered inside paragraphs **and** table cells |
| Glyph safety | Replaces fancy dashes, NBSPs, zero‑width chars that cause “black boxes” |
| Auto‑wrapping tables | Dynamic row height, header shading, and grid styling |
| Simple API | `build_pdf(markdown, filename)` for one‑liner output, or `markdown_to_flowables()` for advanced stories |

## Requirements

```txt
reportlab>=3.6.0   # tested with 3.6.12
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Quick‑start

```python
from pdf_generator import build_pdf

markdown = """### Demo

| **Bold** cell | *Italic* cell |
|---------------|---------------|
| **A**         | *B*           |

```python
print('Hello PDF')
```
"""  # (triple‑quoted string ends above)

build_pdf(markdown, "demo.pdf")
```

Run the script and open **demo.pdf** to view the result.

## Advanced Usage

Need to embed the Markdown output into a larger ReportLab story?

```python
from pdf_generator import markdown_to_flowables
from reportlab.platypus import SimpleDocTemplate

flowables = markdown_to_flowables("# Section\nSome text")
flowables.append(Paragraph("Additional page content", getSampleStyleSheet()["BodyText"]))

SimpleDocTemplate("combined.pdf").build(flowables)
```

## How it works

1. **Sanitize glyphs** – converts problematic Unicode characters to ASCII replacements.
2. **Parse Markdown** – processes line‑by‑line to detect code fences, tables, headings, lists, and paragraphs.
3. **Flowables** – converts parsed elements into ReportLab `Paragraph`, `Table`, and `Spacer` objects.
4. **Build PDF** – feeds the flowables into `SimpleDocTemplate` to generate a Letter‑sized PDF with sensible margins.

---

MIT‑licensed. Happy PDF‑ing!
