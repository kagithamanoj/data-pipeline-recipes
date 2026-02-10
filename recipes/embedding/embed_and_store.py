"""
Embed and Store — Convert text documents into embeddings and store in FAISS.

Usage:
    python recipes/embedding/embed_and_store.py --input ./outputs/scraped/ --query "What is machine learning?"
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def load_text_files(directory: str) -> list[dict]:
    """Load all text/markdown files from a directory."""
    docs = []
    path = Path(directory)

    for ext in ("*.md", "*.txt", "*.text"):
        for file in path.glob(f"**/{ext}"):
            content = file.read_text(encoding="utf-8", errors="ignore")
            if content.strip():
                docs.append({
                    "content": content,
                    "source": str(file),
                    "filename": file.name,
                })

    print(f"📂 Loaded {len(docs)} documents from {directory}")
    return docs


def chunk_documents(docs: list[dict], chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    """Split documents into chunks with metadata."""
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in docs:
        splits = splitter.split_text(doc["content"])
        for i, text in enumerate(splits):
            chunks.append({
                "content": text,
                "source": doc["source"],
                "chunk_id": f"{doc['filename']}_{i}",
            })

    print(f"✂️ Created {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks


def build_faiss_index(chunks: list[dict], persist_dir: str = "./vectorstore"):
    """Embed chunks and build a FAISS index."""
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document

    embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

    documents = [
        Document(
            page_content=chunk["content"],
            metadata={"source": chunk["source"], "chunk_id": chunk["chunk_id"]},
        )
        for chunk in chunks
    ]

    print("🔢 Generating embeddings...")
    vectorstore = FAISS.from_documents(documents, embeddings)

    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(persist_dir)
    print(f"💾 Vector store saved to {persist_dir}")

    return vectorstore


def query_index(query: str, persist_dir: str = "./vectorstore", top_k: int = 4):
    """Query the FAISS index."""
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS

    embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
    vectorstore = FAISS.load_local(persist_dir, embeddings, allow_dangerous_deserialization=True)

    results = vectorstore.similarity_search_with_score(query, k=top_k)

    print(f"\n🔍 Query: \"{query}\"")
    print(f"   Top {top_k} results:\n")

    for i, (doc, score) in enumerate(results, 1):
        print(f"   {i}. [Score: {score:.4f}] {doc.metadata.get('source', 'unknown')}")
        print(f"      {doc.page_content[:150]}...\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed and Store in FAISS")
    parser.add_argument("--input", "-i", type=str, help="Directory of text files to embed")
    parser.add_argument("--query", "-q", type=str, help="Query the vector store")
    parser.add_argument("--store", "-s", type=str, default="./vectorstore", help="Vector store path")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY in .env file!")
        exit(1)

    if args.input:
        docs = load_text_files(args.input)
        if docs:
            chunks = chunk_documents(docs, chunk_size=args.chunk_size)
            build_faiss_index(chunks, persist_dir=args.store)

    if args.query:
        query_index(args.query, persist_dir=args.store, top_k=args.top_k)

    if not args.input and not args.query:
        print("Usage:")
        print("  Index:  python embed_and_store.py --input ./docs/")
        print("  Query:  python embed_and_store.py --query 'your question'")
