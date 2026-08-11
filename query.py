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


def get_answer(question):
    labeled_chunks = []
    question_embedding = model.encode(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=8
    )
    retrieved_chunks = results["documents"][0]


    for text, metadata in zip(retrieved_chunks, results["metadatas"][0]):
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