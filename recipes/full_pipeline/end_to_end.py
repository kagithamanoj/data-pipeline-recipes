"""
End-to-End Pipeline — Scrape → Clean → Embed → Query in one command.

Usage:
    python recipes/full_pipeline/end_to_end.py --urls https://example.com --query "What is this about?"
"""

import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def run_pipeline(urls: list[str], query: str, output_dir: str = "./outputs"):
    """Run the full pipeline: scrape → clean → embed → query."""

    from recipes.web_scraping.scrape_to_markdown import scrape_with_requests
    from recipes.data_cleaning.text_cleaner import clean_markdown, deduplicate_paragraphs
    from recipes.embedding.embed_and_store import chunk_documents, build_faiss_index, query_index

    scraped_dir = os.path.join(output_dir, "scraped")
    store_dir = os.path.join(output_dir, "vectorstore")

    # ── Step 1: Scrape ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📥 STEP 1: Scraping URLs")
    print("=" * 60)

    docs = []
    for i, url in enumerate(urls):
        output_path = os.path.join(scraped_dir, f"page_{i}.md")
        content = scrape_with_requests(url, output_path)
        if content:
            docs.append({"content": content, "source": url, "filename": f"page_{i}.md"})

    if not docs:
        print("❌ No content scraped. Exiting.")
        return

    # ── Step 2: Clean ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🧹 STEP 2: Cleaning Text")
    print("=" * 60)

    for doc in docs:
        original_len = len(doc["content"])
        doc["content"] = clean_markdown(doc["content"])
        doc["content"] = deduplicate_paragraphs(doc["content"])
        print(f"   {doc['source']}: {original_len} → {len(doc['content'])} chars")

    # ── Step 3: Embed ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🔢 STEP 3: Embedding & Indexing")
    print("=" * 60)

    chunks = chunk_documents(docs)
    vectorstore = build_faiss_index(chunks, persist_dir=store_dir)

    # ── Step 4: Query ───────────────────────────────────────────────────────
    if query:
        print("\n" + "=" * 60)
        print("🔍 STEP 4: Querying")
        print("=" * 60)

        query_index(query, persist_dir=store_dir)

    print("\n✅ Pipeline complete!")
    print(f"   Scraped: {len(docs)} pages")
    print(f"   Chunks: {len(chunks)}")
    print(f"   Vector store: {store_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-End Data Pipeline")
    parser.add_argument("--urls", "-u", nargs="+", required=True, help="URLs to scrape")
    parser.add_argument("--query", "-q", type=str, help="Query to run after indexing")
    parser.add_argument("--output", "-o", type=str, default="./outputs")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY in .env file!")
        exit(1)

    run_pipeline(args.urls, args.query, args.output)
