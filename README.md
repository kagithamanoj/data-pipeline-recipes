# data-pipeline-recipes

A collection of modular data pipeline components for AI and machine learning workflows. This repository provides recipes for web scraping, text cleaning, document embedding, and full end-to-end integration.

## Directory Structure

```text
data-pipeline-recipes/
├── recipes/
│   ├── web_scraping/      # URL to Markdown extraction
│   ├── data_cleaning/     # Text normalization and denoising
│   ├── embedding/         # Vector storage and retrieval
│   └── full_pipeline/     # Composability examples
└── docs/                  # Recipe documentation
```

## Recipes

- **Web Scraping**: Extract clean Markdown from web pages using BeautifulSoup or async rendering.
- **Text Cleaning**: Normalize unicode, remove HTML artifacts, and deduplicate content for LLM training or inference.
- **Embedding & Storage**: Document chunking and indexing using OpenAI embeddings and local FAISS storage.
- **End-to-End**: A complete Scrape -> Clean -> Embed -> Query pipeline implemented in a single command.

## Setup

```bash
# Installation
pip install -r requirements.txt

# Environment
cp .env.example .env
# Add OPENAI_API_KEY to .env
```

## Usage

Run individual components or the full orchestration script:

```bash
# Clean a text file
python recipes/data_cleaning/text_cleaner.py --input raw.txt --output clean.txt

# Run integrated pipeline
python recipes/full_pipeline/end_to_end.py --urls https://example.com --query "Summary"
```

---

**Manoj Kumar Kagitha**
[GitHub](https://github.com/kagithamanoj)