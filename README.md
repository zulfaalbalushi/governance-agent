# governance-agent

## Known Limitations

- **Retrieval depends on vocabulary overlap.** Retrieval ranks chunks by embedding similarity to the question, so it relies on the user's wording overlapping with the source document's actual terminology. A question about "penalties" may rank the correct chunk (which uses the word "fine") far outside the retrieval window even when that chunk exists in the corpus. Query expansion — rephrasing the question via an LLM before retrieval (`expand_query` in `query.py`) — partially mitigates this by querying multiple phrasings, but it does not guarantee catching every vocabulary gap.

- **Chunking strategy differs by file type.** PDF chunking splits on `Article (N)` boundaries to keep facts and definitions whole, falling back to size-based splitting only when a single article exceeds `chunk_size`. DOCX files use size-based splitting only, since they do not follow a numbered-article structure, which can split a single logical fact/definition across chunks.

- **`n_results` is fixed, not adaptive.** The number of chunks retrieved per query is a fixed value (`25`), applied regardless of the confidence or similarity of the matches. It does not shrink when results are clearly on-topic or expand when the top matches are weak.
