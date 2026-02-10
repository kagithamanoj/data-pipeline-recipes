"""
Text Cleaner — Clean and normalize text for LLM consumption.

Usage:
    python recipes/data_cleaning/text_cleaner.py --input raw.txt --output clean.txt
"""

import re
import argparse
from pathlib import Path


def clean_text(text: str, config: dict = None) -> str:
    """
    Clean raw text for LLM processing.
    
    Args:
        text: Raw input text
        config: Cleaning options (all default to True)
    """
    config = config or {}

    # Remove excessive whitespace
    if config.get("normalize_whitespace", True):
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)

    # Remove HTML tags
    if config.get("remove_html", True):
        text = re.sub(r"<[^>]+>", "", text)

    # Remove URLs (optional — sometimes you want to keep them)
    if config.get("remove_urls", False):
        text = re.sub(r"https?://\S+", "[URL]", text)

    # Remove email addresses
    if config.get("remove_emails", True):
        text = re.sub(r"\S+@\S+\.\S+", "[EMAIL]", text)

    # Normalize unicode
    if config.get("normalize_unicode", True):
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "—")
        text = text.replace("\u2026", "...")
        text = text.replace("\xa0", " ")

    # Remove non-printable characters
    if config.get("remove_control_chars", True):
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    return text.strip()


def clean_markdown(text: str) -> str:
    """Clean Markdown-specific artifacts from scraped content."""
    # Remove navigation artifacts
    text = re.sub(r"(Skip to (main )?content|Jump to|Table of [Cc]ontents)\n?", "", text)

    # Remove cookie/consent banners
    text = re.sub(r"(We use cookies|Accept all|Cookie policy).*?\n", "", text, flags=re.IGNORECASE)

    # Remove repeated separators
    text = re.sub(r"[-=]{5,}", "---", text)

    # Remove empty headers
    text = re.sub(r"^#{1,6}\s*$", "", text, flags=re.MULTILINE)

    # Normalize header spacing
    text = re.sub(r"\n{2,}(#{1,6})", r"\n\n\1", text)

    return clean_text(text)


def deduplicate_paragraphs(text: str) -> str:
    """Remove duplicate paragraphs (common in scraped content)."""
    paragraphs = text.split("\n\n")
    seen = set()
    unique = []

    for para in paragraphs:
        normalized = para.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(para)

    return "\n\n".join(unique)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean text for LLM consumption")
    parser.add_argument("--input", "-i", type=str, help="Input file path")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--remove-urls", action="store_true", help="Replace URLs with [URL]")
    args = parser.parse_args()

    if args.input:
        raw = Path(args.input).read_text(encoding="utf-8")
    else:
        # Demo
        raw = """
        <html>Hello    World!   </html>
        
        
        Visit us at https://example.com or email us at test@example.com
        
        We use cookies to improve your experience.
        
        Some \u201csmart quotes\u201d and an em\u2014dash.
        
        Some text here.
        
        Some text here.
        """
        print("📝 Demo mode (pass --input for real files)\n")

    config = {"remove_urls": args.remove_urls}
    cleaned = clean_text(raw, config)
    deduped = deduplicate_paragraphs(cleaned)

    print(f"📊 Before: {len(raw)} chars → After: {len(deduped)} chars")
    print(f"   Reduction: {(1 - len(deduped)/len(raw))*100:.1f}%\n")
    print(deduped)

    if args.output:
        Path(args.output).write_text(deduped, encoding="utf-8")
        print(f"\n💾 Saved to {args.output}")
