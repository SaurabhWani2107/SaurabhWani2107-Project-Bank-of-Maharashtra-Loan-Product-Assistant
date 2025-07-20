import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
import faiss
import numpy as np
from collections import Counter

# --- CONFIG ---
DATA_DIR = "Extracteddata_scriptwise"
INDEX_DIR = "rag_pipeline/faiss_index"
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
DOCSTORE_PATH = os.path.join(INDEX_DIR, "docstore.json")
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
EMBED_MODEL = "models/embedding-001"

# --- SETUP ---
os.makedirs(INDEX_DIR, exist_ok=True)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=GOOGLE_API_KEY)

# --- LOAD FILES ---
def load_files(data_dir):
    files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    docs = []
    for fname in files:
        with open(os.path.join(data_dir, fname), "r", encoding="utf-8") as f:
            text = f.read()
            docs.append({"filename": fname, "text": text})
    return docs

# --- CHUNKING ---
def chunk_docs(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    all_chunks = []
    for doc in docs:
        chunks = splitter.split_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk": chunk,
                "filename": doc["filename"],
                "chunk_id": f"{doc['filename']}_chunk_{i}"
            })
    return all_chunks

# --- EMBEDDING ---
def embed_chunks(chunks):
    embeddings = []
    for chunk in tqdm(chunks, desc="Embedding chunks"):
        # Use the correct Gemini embedding API
        response = genai.embed_content(
            model=EMBED_MODEL,
            content=chunk["chunk"],
            task_type="retrieval_document"
        )
        emb = response["embedding"]
        embeddings.append(emb)
    return np.array(embeddings, dtype="float32")

# --- MAIN ---
def main():
    if os.path.exists(INDEX_PATH) and os.path.exists(DOCSTORE_PATH):
        print("Index and docstore already exist. Skipping embedding.")
        return

    print("Loading files...")
    docs = load_files(DATA_DIR)
    print(f"Loaded {len(docs)} files.")
    print("Loaded files:", [doc["filename"] for doc in docs])

    print("Chunking documents...")
    chunks = chunk_docs(docs)
    print(f"Created {len(chunks)} chunks.")

    # Print chunk count per file
    file_counts = Counter([chunk["filename"] for chunk in chunks])
    print("Chunks per file:", file_counts)

    print("Embedding chunks...")
    embeddings = embed_chunks(chunks)

    print("Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    print(f"Saving FAISS index to {INDEX_PATH}")
    faiss.write_index(index, INDEX_PATH)

    print(f"Saving metadata to {DOCSTORE_PATH}")
    with open(DOCSTORE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print("Done! Knowledge base is ready.")

if __name__ == "__main__":
    main()
