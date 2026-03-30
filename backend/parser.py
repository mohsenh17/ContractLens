"""
parser.py
---------
Extracts text and tables from a PDF contract using pdfplumber.
Returns a list of page dicts: { page_num, text, tables }

"""

from typing import List, Dict, Any
import pdfplumber



def parse_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parse a PDF and return structured page data.

    Returns:
        List of dicts:
        [
            {
                "page_num": 1,          # 1-indexed
                "text": "...",          # cleaned plain text
                "tables": [             # list of tables found on this page
                    [["col1", "col2"], ["val1", "val2"], ...],
                    ...
                ]
            },
            ...
        ]
    """
    pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1

            # --- Extract plain text ---
            raw_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            text = _clean_text(raw_text)

            # --- Extract tables ---
            tables = []
            try:
                extracted = page.extract_tables()
                if extracted:
                    for table in extracted:
                        # Filter out fully-None rows
                        clean_table = [
                            [cell or "" for cell in row]
                            for row in table
                            if any(cell for cell in row)
                        ]
                        if clean_table:
                            tables.append(clean_table)
            except Exception:
                pass  # Table extraction failing is non-fatal

            pages.append({
                "page_num": page_num,
                "text": text,
                "tables": tables,
            })

    return pages


def _clean_text(text: str) -> str:
    """
    Normalize whitespace and remove common PDF extraction artifacts.
    """
    if not text:
        return ""

    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        # Drop lines that are just page numbers or single characters
        if len(line) <= 2:
            continue
        # Collapse multiple spaces within a line
        line = " ".join(line.split())
        cleaned.append(line)

    return "\n".join(cleaned)




def pages_to_full_text(pages: List[Dict[str, Any]]) -> str:
    """
    Flatten all pages into a single string, including table content.
    """
    parts = []
    for p in pages:
        parts.append(f"--- Page {p['page_num']} ---")
        parts.append(p["text"])
        for table in p.get("tables", []):
            parts.append("[TABLE]")
            for row in table:
                parts.append(" | ".join(row))
            parts.append("[/TABLE]")
    return "\n".join(parts)
