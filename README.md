# 🔄 Data Pipeline Recipes

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangChain](https://img.shields.io/badge/LangChain-🦜-green)](https://docs.langchain.com)

> Modular, reusable data pipeline components for AI/ML workflows — scrape, clean, embed, and query.

## 🎯 What's Inside

| Recipe | File | Description |
|--------|------|-------------|
| 🕷️ **Web Scraping** | `recipes/web_scraping/scrape_to_markdown.py` | Scrape any URL to clean Markdown |
| 🧹 **Text Cleaning** | `recipes/data_cleaning/text_cleaner.py` | Normalize, deduplicate, clean text for LLMs |
| 🔢 **Embedding** | `recipes/embedding/embed_and_store.py` | Embed documents and store in FAISS |
| 🔄 **Full Pipeline** | `recipes/full_pipeline/end_to_end.py` | Scrape → Clean → Embed → Query in one command |

## 🏗️ Architecture

```
               ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌───────┐
  URLs/Files → │  Scrape   │ → │  Clean    │ → │  Embed    │ → │ Query  │
               └──────────┘     └──────────┘     └──────────┘     └───────┘
               Crawl4AI /       Unicode norm     OpenAI Embed     FAISS
               Requests +       Dedup, strip     Chunk + Index    Similarity
               BeautifulSoup    HTML/noise                        Search
```

## 🚀 Quick Start

```bash
git clone https://github.com/kagithamanoj/data-pipeline-recipes.git
cd data-pipeline-recipes
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY
```

### Run Individual Recipes

```bash
# Scrape a website to Markdown
python recipes/web_scraping/scrape_to_markdown.py --url "https://docs.python.org/3/"

# Clean text
python recipes/data_cleaning/text_cleaner.py --input raw.txt --output clean.txt

# Embed & query documents
python recipes/embedding/embed_and_store.py --input ./docs/ --query "What is Python?"
```

### Run the Full Pipeline

```bash
# Scrape → Clean → Embed → Query — one command
python recipes/full_pipeline/end_to_end.py \
  --urls https://example.com https://docs.python.org/3/ \
  --query "What is this about?"
```

## 📦 Recipes

### 🕷️ Web Scraping
Scrape websites into clean Markdown. Supports Crawl4AI (async, JS rendering) and requests+BeautifulSoup fallback.

### 🧹 Text Cleaning
Clean raw text for LLM processing: remove HTML, normalize unicode, deduplicate paragraphs, strip navigation artifacts.

### 🔢 Embedding & Storage
Load text files → chunk with LangChain splitter → embed with OpenAI → store in FAISS.

### 🔄 End-to-End Pipeline
Combines all steps into one composable pipeline.

## 📄 License

MIT — see [LICENSE](LICENSE).

---

**Built by** [Manoj Kumar Kagitha](https://github.com/kagithamanoj) 🚀