import chromadb
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
from loader import load_all_chunks
all_chunks = load_all_chunks()

vector = model.encode("A sample sentence")


texts = []

for items in all_chunks:
    texts.append(items["text"])


embeddings = model.encode(texts)

ids = []

for i in range(len(texts)): 
    chunk_id = "chunks_" + str(i)
    ids.append(chunk_id)



metadatas = []

for i in all_chunks:
    metadatas.append({"source_file": i["source_file"]})


client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="governance_docs")

collection.add(
    ids=ids,
    embeddings=embeddings,
    documents=texts,
    metadatas=metadatas
)


print(collection.count())