import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document


def load_and_chunk(filepath):
    if filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        full_text = []
        for page in reader.pages:
            current_text = page.extract_text()
            if current_text:
                full_text.append(current_text)
        text = "\n".join(full_text)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=145,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        article_matches = list(re.finditer(r"(?im)^(?<!\w)Article\s+\(?\d+\)?\b", text))
        if article_matches:
            raw_chunks = []
            for index, match in enumerate(article_matches):
                start = match.start()
                end = article_matches[index + 1].start() if index + 1 < len(article_matches) else len(text)
                article_text = text[start:end].strip()
                if "Article (25)" in article_text[:20]:
                    print(f"LENGTH: {len(article_text)}")
                    print(f"FULL TEXT: {article_text}")
                if not article_text:
                    continue
                if len(article_text) <= 500:
                    raw_chunks.append(article_text)
                else:
                    raw_chunks.extend(splitter.split_text(article_text))

            chunks = []
            for piece in raw_chunks:
                cleaned_piece = piece.strip()
                if cleaned_piece:
                    chunks.append({"text": cleaned_piece, "source_file": filepath})
            return chunks

        raw_chunks = splitter.split_text(text)
        chunks = []
        for piece in raw_chunks:
            chunks.append({"text": piece, "source_file": filepath})
        return chunks

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
result = load_all_chunks()
for chunk in result:
    if "Article (24)" in chunk["text"] or "Article (25)" in chunk["text"]:
        print(chunk["text"])
        print("---")