# Annual Report RAG Chatbot

A fully local Retrieval-Augmented Generation (RAG) system that answers questions about a single document, the **Infosys Integrated Annual Report 2025-26** (~400 pages). It runs on a CPU-only laptop using Ollama, with no API keys.

Built as a time-boxed project, so the scope is deliberately small: **one document, partly manual cleaning, a small local model**. See [Limitations](#limitations).

## Features
- PDF to clean per-page Markdown (text, tables, hand-fixed chart data)
- Table-safe chunking with page numbers kept as metadata
- Semantic search with a local embedding model and a persistent vector store
- Follow-up questions: the new question is rewritten into a standalone one before searching
- Short in-session chat history (nothing is stored after the program exits)
- Answers are restricted to the retrieved context and say so when the answer isn't there

## Pipeline

```
PDF -> pymupdf4llm (per page .md) -> manual cleaning -> chunking (+ page metadata)
    -> nomic-embed-text embeddings -> ChromaDB
    
Question -> (rewrite using chat history) -> embed -> top-k chunks -> qwen3:4b -> answer
```

## Tech stack
| Part | Tool |
|---|---|
| PDF extraction | PyMuPDF, `pymupdf4llm` |
| Embeddings | `nomic-embed-text` (via Ollama) |
| Vector store | ChromaDB (persistent) |
| LLM | `qwen3:4b` (via Ollama, `think=False`) |
| Language | Python |

## Data cleaning (the most time-consuming part)

1. **Extraction:** converted the PDF to Markdown with `pymupdf4llm`, **one file per page** (`001.md`, `002.md`, ...). Per-page files made it easy to fix one page without touching the rest, and to keep page numbers for citations.
2. **Problem found:** most pages and tables parsed well, but tables and charts that use icons or emoji to mark rows, and chart-only pages, came out wrong. OCR (RapidOCR) did not help, since the markers are shapes and glyphs rather than text.
3. **Removed pages:**
   - completely jumbled pages (unreadable after extraction)
   - index / contents pages (their page numbers don't match the PDF's page indices, so they would mislead retrieval)
4. **Manual fixes:**
   - repaired broken paragraphs and tables
   - rebuilt tables from scratch for pages whose data only appeared in graphs
   - general cleanup of leftover junk characters
5. **Decision:** with ~300 pages and most already correct, fixing only the bad pages by hand was faster and more reliable than writing per-page regex rules.

> The cleaning is **not exhaustive**. Some pages may still contain minor formatting errors.

## Chunking
- Each page is split into blocks at blank lines, then blocks are combined into chunks of about 2,000 characters (~500 tokens).
- Tables stay in one block, so they are never cut in half. A table longer than the limit stays whole.
- Each chunk stores its **page number** as metadata, taken from the page filename.
- Note: page numbers are PDF page indices, which may differ from the page numbers printed in the report.

## Retrieval and answering
1. If there is chat history, the LLM rewrites the new question into a standalone question (for example, "what about Europe?" becomes "What was Infosys's revenue in Europe?"). On the first question this step is skipped.
2. The question is embedded and the top 3 chunks are fetched from ChromaDB.
3. The chunks (with their page numbers) and the last few chat turns go to `qwen3:4b` with a system prompt that tells it to answer only from the context and to say when the answer isn't there.
4. History keeps only the plain question and answer, not the retrieved text, so the prompt doesn't grow each turn.

## Setup

```bash
# 1. Install Ollama, then pull the models
ollama pull qwen3:4b
ollama pull nomic-embed-text

# 2. Install Python dependencies
pip install -U ollama chromadb pymupdf pymupdf4llm

# 3. Build the index (run once)
python chunk_embed.py

# 4. Chat
python main.py

# 5. Requirements
pip install -r requirements.txt
```

## Example questions
- What is Infosys's revenue across regions and business segments?
- What are the company's values?
- *(follow-up)* And how did that change compared with last year?

## Evaluation
Tested with a set of questions whose answers were checked against the report.

| # | Question type | Result |
|---|---|---|
| 1-5 | Table lookups | 4 / 5 |
| 6-10 | Paragraph / text questions | 5 / 5 |
| 11-13 | Follow-up questions | 3 / 3 |
| 14-15 | Not in the document | 2 / 2 |


## Limitations
- **Single document:** only one annual report is indexed.
- **Partly manual cleaning:** the pipeline is not fully automatic. Pages with icon-marked tables or charts needed manual fixes or removal, and some pages were dropped. Scaling to more documents would need a vision-model step for chart and icon pages.
- **Small local model:** `qwen3:4b` can miss details or misread dense tables.
- **Speed:** runs on CPU, so answers take longer than a hosted API.
- **Page numbers:** citations use PDF page indices, not the printed page numbers.
- **Chat history is in-memory only** and lost when the program closes.

## Possible improvements
- Vision-model step for chart and icon pages
- Hybrid search (keyword + vector) for exact figures and names
- Reranking of retrieved chunks
- Simple Streamlit / Gradio interface
- Support for multiple documents

## Author
Niraj, [github.com/alaghuyaar](https://github.com/alaghuyaar)
