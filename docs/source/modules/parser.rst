Parser Module
=============

`parser.py` extracts text and tables from PDF files using `pdfplumber`.

Key Functions
-------------

- **parse_pdf(pdf_path)** → Returns list of page dictionaries with keys: `page_num`, `text`, `tables`.
- **_clean_text(text)** → Normalizes whitespace, removes page numbers or artifacts.
- **pages_to_full_text(pages)** → Flattens all pages into a single string including tables.