"""
PDF Text Extraction Recipe — Extract clean text from PDFs for LLM consumption.

Usage:
    python recipes/pdf_extraction/extract_pdf.py --input document.pdf
    python recipes/pdf_extraction/extract_pdf.py --input ./pdf_folder/
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def extract_text_pymupdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF (fast, reliable)."""
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"--- Page {i + 1} ---\n{text.strip()}")

    doc.close()
    return "\n\n".join(pages)


def extract_text_fallback(pdf_path: str) -> str:
    """Fallback: extract text using built-in methods (less reliable)."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(f"--- Page {i + 1} ---\n{text.strip()}")
        return "\n\n".join(pages)
    except ImportError:
        print("⚠️  Install PyMuPDF or pypdf: pip install pymupdf pypdf")
        sys.exit(1)


def extract_pdf(pdf_path: str) -> dict:
    """
    Extract text from a PDF file.

    Returns:
        dict with 'text', 'pages', 'source'
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if HAS_PYMUPDF:
        text = extract_text_pymupdf(pdf_path)
        extractor = "PyMuPDF"
    else:
        text = extract_text_fallback(pdf_path)
        extractor = "pypdf"

    # Count pages
    page_count = text.count("--- Page ")

    return {
        "text": text,
        "pages": page_count,
        "source": str(path.resolve()),
        "extractor": extractor,
        "chars": len(text),
    }


def extract_directory(dir_path: str) -> list[dict]:
    """Extract text from all PDFs in a directory."""
    results = []
    pdf_files = sorted(Path(dir_path).glob("*.pdf"))

    if not pdf_files:
        print(f"⚠️  No PDF files found in {dir_path}")
        return results

    for pdf in pdf_files:
        try:
            result = extract_pdf(str(pdf))
            results.append(result)
            print(f"  ✅ {pdf.name}: {result['pages']} pages, {result['chars']:,} chars")
        except Exception as e:
            print(f"  ❌ {pdf.name}: {e}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from PDFs")
    parser.add_argument("--input", "-i", type=str, help="PDF file or directory")
    parser.add_argument("--output", "-o", type=str, help="Output text file")
    args = parser.parse_args()

    if not args.input:
        print("📝 PDF Text Extraction Recipe")
        print("="*50)
        print()
        print("Usage:")
        print("  python extract_pdf.py --input document.pdf")
        print("  python extract_pdf.py --input ./pdfs/ --output combined.txt")
        print()
        print(f"PyMuPDF available: {'✅' if HAS_PYMUPDF else '❌ (install: pip install pymupdf)'}")
        sys.exit(0)

    input_path = Path(args.input)

    if input_path.is_dir():
        print(f"📂 Extracting all PDFs from {input_path}/")
        results = extract_directory(str(input_path))
        combined = "\n\n".join(r["text"] for r in results)
        total_pages = sum(r["pages"] for r in results)
        print(f"\n📊 Total: {len(results)} PDFs, {total_pages} pages, {len(combined):,} chars")
    else:
        result = extract_pdf(str(input_path))
        combined = result["text"]
        print(f"📊 {input_path.name}: {result['pages']} pages, {result['chars']:,} chars ({result['extractor']})")

    if args.output:
        Path(args.output).write_text(combined, encoding="utf-8")
        print(f"💾 Saved to {args.output}")
    else:
        print(f"\n{combined[:500]}...")
