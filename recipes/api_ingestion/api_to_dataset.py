"""
API Data Ingestion Recipe — Fetch, paginate, and normalize data from REST APIs.

Usage:
    python recipes/api_ingestion/api_to_dataset.py --url "https://api.github.com/users/kagithamanoj/repos"
    python recipes/api_ingestion/api_to_dataset.py --demo
"""

import argparse
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def fetch_json(url: str, headers: dict = None, timeout: int = 30) -> dict | list:
    """Fetch JSON from a URL with error handling."""
    req = Request(url)
    req.add_header("User-Agent", "DataPipelineRecipes/1.0")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.reason}")
        raise
    except URLError as e:
        print(f"❌ Connection error: {e.reason}")
        raise


def fetch_paginated(
    base_url: str,
    page_param: str = "page",
    per_page_param: str = "per_page",
    per_page: int = 30,
    max_pages: int = 10,
    headers: dict = None,
    delay: float = 0.5,
) -> list:
    """
    Fetch all pages from a paginated REST API.

    Args:
        base_url: API endpoint
        page_param: Query parameter name for page number
        per_page_param: Query parameter name for items per page
        per_page: Items per page
        max_pages: Maximum pages to fetch (safety limit)
        headers: Optional headers (e.g., auth tokens)
        delay: Delay between requests (respect rate limits)
    """
    all_items = []
    separator = "&" if "?" in base_url else "?"

    for page in range(1, max_pages + 1):
        url = f"{base_url}{separator}{page_param}={page}&{per_page_param}={per_page}"
        print(f"  📥 Page {page}: {url}")

        data = fetch_json(url, headers=headers)

        if isinstance(data, list):
            if not data:
                print(f"  ⏹️  Empty page {page} — done")
                break
            all_items.extend(data)
        elif isinstance(data, dict):
            # Handle APIs that wrap results (e.g., {"results": [...], "next": ...})
            items = data.get("results", data.get("items", data.get("data", [])))
            if not items:
                break
            all_items.extend(items)
        else:
            break

        if delay > 0:
            time.sleep(delay)

    return all_items


def normalize_records(records: list, fields: list[str] = None) -> list[dict]:
    """
    Flatten and normalize a list of API records.

    Args:
        records: List of dicts from API
        fields: Specific fields to extract (None = all)
    """
    if not records:
        return []

    if fields:
        return [{k: record.get(k) for k in fields} for record in records]

    return records


def save_dataset(records: list, output_path: str, format: str = "jsonl"):
    """Save records to file (JSONL or JSON)."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if format == "jsonl":
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    elif format == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Unknown format: {format}")

    print(f"💾 Saved {len(records)} records to {path} ({format})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and normalize API data")
    parser.add_argument("--url", type=str, help="API endpoint URL")
    parser.add_argument("--output", "-o", type=str, default="./outputs/api_data.jsonl")
    parser.add_argument("--fields", type=str, nargs="*", help="Fields to extract")
    parser.add_argument("--max-pages", type=int, default=5, help="Max pages to fetch")
    parser.add_argument("--demo", action="store_true", help="Run demo with GitHub API")
    args = parser.parse_args()

    if args.demo:
        print("🌐 Demo: Fetching public GitHub repos for kagithamanoj")
        print("=" * 50)

        url = "https://api.github.com/users/kagithamanoj/repos"
        records = fetch_json(url)

        fields = ["name", "description", "language", "stargazers_count", "html_url", "created_at"]
        normalized = normalize_records(records, fields=fields)

        print(f"\n📊 Found {len(normalized)} repos:\n")
        for repo in normalized:
            stars = repo.get("stargazers_count", 0)
            lang = repo.get("language") or "—"
            desc = (repo.get("description") or "No description")[:60]
            print(f"  ⭐ {stars} | {lang:12s} | {repo['name']:30s} | {desc}")

        save_dataset(normalized, args.output)

    elif args.url:
        print(f"🌐 Fetching: {args.url}")
        records = fetch_paginated(args.url, max_pages=args.max_pages)
        normalized = normalize_records(records, fields=args.fields)
        print(f"\n📊 Fetched {len(normalized)} records")
        save_dataset(normalized, args.output)

    else:
        print("📝 API Data Ingestion Recipe")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python api_to_dataset.py --demo")
        print("  python api_to_dataset.py --url 'https://api.example.com/data' --fields id name")
        print("  python api_to_dataset.py --url 'https://api.example.com/data' --max-pages 10")
