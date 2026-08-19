# governance-agent

## Overview

A retrieval-augmented generation (RAG) agent that answers governance and compliance questions about Oman's AI policy and personal data protection law. It is grounded in official Oman government documents rather than the model's parametric knowledge: every answer is drawn from retrieved text and includes a citation to the source document. When the retrieved context does not cover a question, the agent states that the information is not available rather than guessing.

The goal is to provide a grounded, auditable way for users to query Oman's AI governance and data protection framework — useful for compliance and policy research where ungrounded answers are not acceptable.

## Tech Stack

- **Python** — application language.1
- **Flask** — web server and HTTP endpoints (`app.py`).
- **sentence-transformers** (`all-MiniLM-L6-v2`) — embedding model for chunk and query vectors.
- **ChromaDB** — persistent vector store for document chunks (`chroma_db/`).
- **Groq API** with `openai/gpt-oss-20b` — used for query expansion and answer generation (`query.py`).
- **pypdf** and **python-docx** — document loaders for PDF and DOCX sources (`loader.py`).
- **LangChain** `RecursiveCharacterTextSplitter` — text chunking.

## Setup / Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd <repo-directory>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set the Groq API key. Create a `.env` file in the project root containing:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. Build the vector store from the documents in `docs/`:
   ```bash
   python embed_and_store.py
   ```

6. Start the server:
   ```bash
   python app.py
   ```
   The landing page is served at `/` and the chat interface at `/chat`. Questions are submitted to `/ask` (POST).


## Architecture

The pipeline has an offline indexing stage and an online query stage.

**Indexing (offline, `embed_and_store.py` → `loader.py`):**
1. **Load documents** — all files in `docs/` are loaded; PDFs via `pypdf`, DOCX via `python-docx`.
2. **Chunk** — text is split into chunks (article-aware for PDFs, size-based otherwise) using `RecursiveCharacterTextSplitter`.
3. **Embed** — each chunk is encoded into a vector with `all-MiniLM-L6-v2`.
4. **Store** — chunks, embeddings, and `source_file` metadata are written to a persistent ChromaDB collection (`governance_docs`).

**Query (online, `query.py`):**
1. **Expand** — the question is rephrased into 2–3 alternative phrasings via the Groq model to improve vocabulary coverage.
2. **Retrieve** — each phrasing is embedded and used to query ChromaDB; duplicate chunks across phrasings are removed.
3. **Generate** — retrieved chunks are passed as context to the Groq model with a system prompt that restricts answers to the context, requires a citation, and instructs it to refuse when the context is insufficient.

## Key Features

- **Article-aware chunking for PDFs** — PDFs are split on `Article (N)` boundaries so individual facts and definitions stay intact; size-based splitting is used only as a fallback for over-long articles. DOCX files use size-based splitting.
- **Query expansion for retrieval** — the user's question is rephrased before retrieval to catch terminology mismatches between the question and the source documents.
- **Citations with friendly document names** — answers cite their source using readable names (e.g. *National AI Policy*, *Personal Data Protection Law*) rather than raw file paths.
- **Refusal when context is insufficient** — the generation step is constrained to the retrieved context and will explicitly state when the governance documents do not contain the answer.

## Known Limitations

- **Retrieval depends on vocabulary overlap.** Retrieval ranks chunks by embedding similarity to the question, so it relies on the user's wording overlapping with the source document's actual terminology. A question about "penalties" may rank the correct chunk (which uses the word "fine") far outside the retrieval window even when that chunk exists in the corpus. Query expansion — rephrasing the question via an LLM before retrieval (`expand_query` in `query.py`) — partially mitigates this by querying multiple phrasings, but it does not guarantee catching every vocabulary gap.

- **Chunking strategy differs by file type.** PDF chunking splits on `Article (N)` boundaries to keep facts and definitions whole, falling back to size-based splitting only when a single article exceeds `chunk_size`. DOCX files use size-based splitting only, since they do not follow a numbered-article structure, which can split a single logical fact/definition across chunks.

- **`n_results` is fixed, not adaptive.** The number of chunks retrieved per query is a fixed value (`25`), applied regardless of the confidence or similarity of the matches. It does not shrink when results are clearly on-topic or expand when the top matches are weak.
