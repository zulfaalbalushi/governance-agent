from dotenv import load_dotenv
from groq import Groq
import os
import chromadb
os.environ["HF_HUB_OFFLINE"] = "1"
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=api_key)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="governance_docs")


def expand_query(question):
    """Generate 2-3 alternative phrasings of the question for wider retrieval."""
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.2,
        max_tokens=200,
        messages=[
            {"role": "system", "content": "Rewrite the user's legal/governance question into 2-3 alternative phrasings that might use different terminology a governance document would use (e.g. penalty vs fine, formal vs casual). Return only the alternative phrasings, one per line, with no numbering or extra commentary."},
            {"role": "user", "content": f"Question: {question}"}
        ]
    )
    return [
        line.strip()
        for line in response.choices[0].message.content.splitlines()
        if line.strip()
    ]


def get_answer(question):
    labeled_chunks = []

    # Query expansion: generate alternative phrasings, then embed and retrieve for each.
    rephrasings = expand_query(question)
    print(rephrasings)
    all_queries = [question] + rephrasings

    seen_texts = set()
    for q in all_queries:
        q_embedding = model.encode(q)
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=25
        )
        for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
            if text in seen_texts:
                continue
            seen_texts.add(text)
            source = metadata["source_file"]
            labeled = f"[Source: {source}]\n{text}"
            labeled_chunks.append(labeled)

    context = "\n\n".join(labeled_chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Only answer using the provided context. If the context does not contain the answer, say clearly that the information is not available in the governance documents. Always cite the document you retrieved the answer from, [Source: document name. Summarize the relevant information in your own words rather than quoting it directly. Always cite the source file.]"},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

