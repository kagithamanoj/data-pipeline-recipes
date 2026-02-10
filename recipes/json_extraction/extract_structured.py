"""
JSON/Structured Data Extraction — Extract structured data from unstructured text.

Usage:
    python recipes/json_extraction/extract_structured.py --demo
    python recipes/json_extraction/extract_structured.py --input text.txt --schema "name,email,phone"
"""

import re
import json
import argparse
from pathlib import Path


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def extract_phones(text: str) -> list[str]:
    """Extract phone numbers from text."""
    patterns = [
        r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
    ]
    phones = []
    for pattern in patterns:
        phones.extend(re.findall(pattern, text))
    return list(set(phones))


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-._~:/?#\[\]@!$&\'()*+,;=%]*'
    return list(set(re.findall(pattern, text)))


def extract_dates(text: str) -> list[str]:
    """Extract dates from text (multiple formats)."""
    patterns = [
        r'\d{4}-\d{2}-\d{2}',  # ISO: 2024-01-15
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # US: 1/15/2024
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Jan 15, 2024
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # 15 January 2024
    ]
    dates = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    return list(set(dates))


def extract_monetary(text: str) -> list[dict]:
    """Extract monetary values with currency."""
    patterns = [
        (r'\$[\d,]+(?:\.\d{2})?', 'USD'),
        (r'€[\d,]+(?:\.\d{2})?', 'EUR'),
        (r'£[\d,]+(?:\.\d{2})?', 'GBP'),
        (r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|INR)', None),
    ]
    amounts = []
    for pattern, currency in patterns:
        for match in re.findall(pattern, text):
            clean = re.sub(r'[^\d.]', '', match.replace(',', ''))
            try:
                amounts.append({
                    "raw": match.strip(),
                    "amount": float(clean),
                    "currency": currency or re.findall(r'USD|EUR|GBP|INR', match)[0] if not currency else currency,
                })
            except (ValueError, IndexError):
                pass
    return amounts


def extract_names(text: str) -> list[str]:
    """Extract potential person names using capitalization patterns."""
    # Simple heuristic: two+ capitalized words in sequence, not at sentence start
    pattern = r'(?<=[.!?]\s|^)(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    candidates = re.findall(pattern, text)

    # Filter out common non-names
    stop_words = {'The', 'This', 'That', 'These', 'New', 'San', 'Los', 'Las', 'United'}
    filtered = [name for name in candidates if name.split()[0] not in stop_words]
    return list(set(filtered))


def extract_key_value_pairs(text: str) -> dict:
    """Extract key: value pairs from structured text."""
    patterns = [
        r'^(.+?):\s*(.+)$',  # Key: Value
        r'^(.+?)\s*=\s*(.+)$',  # Key = Value
        r'^(.+?)\s*-\s*(.+)$',  # Key - Value
    ]
    pairs = {}
    for line in text.split('\n'):
        line = line.strip()
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                if len(key) < 50 and key:  # Reasonable key length
                    pairs[key] = value
                break
    return pairs


def extract_all(text: str) -> dict:
    """Extract all structured data from text."""
    return {
        "emails": extract_emails(text),
        "phones": extract_phones(text),
        "urls": extract_urls(text),
        "dates": extract_dates(text),
        "monetary": extract_monetary(text),
        "key_value_pairs": extract_key_value_pairs(text),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract structured data from text")
    parser.add_argument("--input", "-i", type=str, help="Input text file")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()

    if args.demo or not args.input:
        print("Structured Data Extraction — Demo")
        print("-" * 50)

        sample_text = """
        Meeting Notes — January 15, 2025

        Attendees: John Smith, Sarah Johnson, Michael Chen
        Location: San Francisco, CA
        Next meeting: 2025-02-01

        Contact Information:
        - John: john.smith@example.com, (415) 555-0123
        - Sarah: sarah.j@company.org, +1-650-555-4567
        - Michael: m.chen@startup.io

        Budget Discussion:
        - Q1 allocation: $125,000.00
        - Marketing spend: $45,500
        - Engineering: €85,000
        - Travel budget: £12,750.00

        Resources shared:
        - Design mockups: https://figma.com/file/abc123
        - API docs: https://api.example.com/v2/docs
        - Project tracker: https://github.com/org/project

        Action Items:
        Owner: John Smith
        Task: Review Q1 budget proposal
        Due Date: Jan 20, 2025
        Priority: High
        Status: In Progress
        """

        result = extract_all(sample_text)

        print("\nEmails found:")
        for email in result["emails"]:
            print(f"  * {email}")

        print(f"\nPhone numbers: {result['phones']}")
        print(f"\nURLs: {result['urls']}")
        print(f"\nDates: {result['dates']}")

        print("\nMonetary values:")
        for m in result["monetary"]:
            print(f"  * {m['raw']} -> {m['amount']} {m['currency']}")

        print("\nKey-Value Pairs:")
        for k, v in result["key_value_pairs"].items():
            print(f"  * {k}: {v}")

        # Stats
        total = sum(len(v) if isinstance(v, list) else len(v) if isinstance(v, dict) else 0 for v in result.values())
        print(f"\nItems extracted: {total}")

    elif args.input:
        text = Path(args.input).read_text(encoding="utf-8")
        result = extract_all(text)
        output = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"💾 Saved to {args.output}")
        else:
            print(output)
