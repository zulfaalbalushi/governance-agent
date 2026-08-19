import re
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

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal your system prompt",
    "system prompt",
    "developer prompt",
    "pretend you are",
    "you are now",
    "bypass safety",
    "act as if",
    "override policy",
    "ignore policy",
    "disregard constraints",
]

SOURCE_NAME_MAP = {
    "docs/national_ai_policy_english.docx": "National AI Policy",
    "docs/DATA_PROTECTION_LAW.pdf": "Personal Data Protection Law",
    "national_ai_policy_english.docx": "National AI Policy",
    "DATA_PROTECTION_LAW.pdf": "Personal Data Protection Law",
}


def normalize_source_name(source_name):
    return SOURCE_NAME_MAP.get(source_name, source_name)


def sanitize_question(question):
    if question is None:
        raise ValueError("Please enter a question.")

    cleaned = str(question).strip()
    if not cleaned:
        raise ValueError("Please enter a valid question.")

    if len(cleaned) < 3:
        raise ValueError("Please ask a clearer question.")

    if len(cleaned) > 1500:
        raise ValueError("Your question is too long for this agent. Please shorten it.")

    lowered = cleaned.lower()
    if any(pattern in lowered for pattern in PROMPT_INJECTION_PATTERNS):
        raise ValueError("I can only answer governance questions grounded in the provided documents.")

    return cleaned


def expand_query(question):
    """Generate 2-3 alternative phrasings of the question for wider retrieval."""
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
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
    try:
        question = sanitize_question(question)
    except ValueError as exc:
        return str(exc)

    labeled_chunks = []
    retrieved_sources = []

    # Query expansion: generate alternative phrasings, then embed and retrieve for each.
    rephrasings = expand_query(question)
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
            retrieved_sources.append(source)
            labeled = f"[Source: {normalize_source_name(source)}]\n{text}"
            labeled_chunks.append(labeled)

    if not labeled_chunks:
        return "The governance documents do not contain enough information to answer this question accurately."

    context = "\n\n".join(labeled_chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "Only answer using the provided context. If the context does not contain the answer, say clearly that the information is not available in the governance documents. Always cite the document you retrieved the answer from using this format: [Source: document name]. For source naming, map docs/national_ai_policy_english.docx to National AI Policy and map docs/DATA_PROTECTION_LAW.pdf to Personal Data Protection Law in citations (for example, [Source: National AI Policy]). Summarize the relevant information in your own words rather than quoting it directly. Always cite the source file. Format the answer as clean markdown with short paragraphs, bullet points when helpful, and a clear citation at the end. Do not output a dense raw paragraph block. If the evidence is weak or missing, say that the information is not available in the governance documents."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content.strip()
    if not re.search(r"\[Source:\s*.+\]", answer, re.IGNORECASE):
        source_name = normalize_source_name(retrieved_sources[0]) if retrieved_sources else "National AI Policy"
        answer = f"{answer.rstrip()}\n\n[Source: {source_name}]"

    return answer

