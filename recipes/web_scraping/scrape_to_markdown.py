"""
Web Scraping to Markdown — Scrape websites into clean, LLM-ready Markdown.

Usage:
    python recipes/web_scraping/scrape_to_markdown.py --url "https://example.com" --output output.md
"""

import asyncio
import argparse
import os
from pathlib import Path


async def scrape_with_crawl4ai(url: str, output_path: str = None):
    """Scrape a URL using Crawl4AI and save as Markdown."""
    from crawl4ai import AsyncWebCrawler

    print(f"🕷️ Crawling: {url}")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        if result.success:
            markdown = result.markdown
            print(f"✅ Scraped {len(markdown)} characters")

            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text(markdown, encoding="utf-8")
                print(f"💾 Saved to {output_path}")

            return markdown
        else:
            print(f"❌ Failed to scrape: {result.error_message}")
            return None


def scrape_with_requests(url: str, output_path: str = None):
    """Fallback scraper using requests + BeautifulSoup."""
    import requests
    from bs4 import BeautifulSoup

    print(f"🕷️ Crawling (fallback): {url}")

    response = requests.get(url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (compatible; DataPipelineBot/1.0)"
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract text with basic structure
    lines = []
    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code"]):
        tag = element.name
        text = element.get_text(strip=True)
        if not text:
            continue

        if tag == "h1":
            lines.append(f"\n# {text}\n")
        elif tag == "h2":
            lines.append(f"\n## {text}\n")
        elif tag == "h3":
            lines.append(f"\n### {text}\n")
        elif tag == "h4":
            lines.append(f"\n#### {text}\n")
        elif tag == "li":
            lines.append(f"- {text}")
        elif tag in ("pre", "code"):
            lines.append(f"\n```\n{text}\n```\n")
        else:
            lines.append(text)

    markdown = "\n".join(lines)
    print(f"✅ Extracted {len(markdown)} characters")

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(markdown, encoding="utf-8")
        print(f"💾 Saved to {output_path}")

    return markdown


def scrape_multiple(urls: list[str], output_dir: str = "./outputs/scraped"):
    """Scrape multiple URLs and save each as a Markdown file."""
    from urllib.parse import urlparse

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = {}

    for url in urls:
        domain = urlparse(url).netloc.replace(".", "_")
        path = urlparse(url).path.strip("/").replace("/", "_") or "index"
        filename = f"{domain}_{path}.md"
        output_path = os.path.join(output_dir, filename)

        try:
            content = scrape_with_requests(url, output_path)
            results[url] = {"status": "success", "chars": len(content), "file": output_path}
        except Exception as e:
            print(f"❌ Failed: {url} — {e}")
            results[url] = {"status": "error", "error": str(e)}

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape websites to Markdown")
    parser.add_argument("--url", "-u", type=str, help="Single URL to scrape")
    parser.add_argument("--urls", "-U", type=str, nargs="+", help="Multiple URLs")
    parser.add_argument("--output", "-o", type=str, default="./outputs/scraped/output.md")
    parser.add_argument("--use-crawl4ai", action="store_true", help="Use Crawl4AI (async)")
    args = parser.parse_args()

    if args.url:
        if args.use_crawl4ai:
            asyncio.run(scrape_with_crawl4ai(args.url, args.output))
        else:
            scrape_with_requests(args.url, args.output)
    elif args.urls:
        scrape_multiple(args.urls)
    else:
        # Demo
        print("📝 Demo: scraping example.com")
        scrape_with_requests("https://example.com", "./outputs/scraped/example.md")
