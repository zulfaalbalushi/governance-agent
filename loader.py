import os 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document

def load_and_chunk(filepath):


    if filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        full_text = []
        for page in reader.pages:
            current_text = page.extract_text()
            full_text.append(current_text)
        text = "\n".join(full_text)
    elif filepath.endswith(".docx"):
        doc = Document(filepath)
        paragraphs = []
        for para in doc.paragraphs:
            current_text = para.text
            paragraphs.append(current_text)
        text = "\n".join(paragraphs)
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read() 

    splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=145,
    separators=["\n\n", "\n", ". ", " ", ""]
)
    raw_chunks = splitter.split_text(text)
    chunks = []
    for piece in raw_chunks:
        chunks.append({"text": piece, "source_file": filepath})

    return chunks

def load_all_chunks():
    docs = os.listdir("docs")
    all_chunks = []
    for filename in docs:
        if filename.startswith("."):
            continue
        filepath = "docs/" + filename
        result = load_and_chunk(filepath)
        all_chunks.extend(result)
    return all_chunks

result = load_all_chunks()
print(len(result))
print(result[0])