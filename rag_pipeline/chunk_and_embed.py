import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
import faiss
import numpy as np
from collections import Counter
import logging

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

# --- LOGGING SETUP ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "build.log")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode="a"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

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
    try:
        if os.path.exists(INDEX_PATH) and os.path.exists(DOCSTORE_PATH):
            logger.info("Index and docstore already exist. Skipping embedding.")
            print("Index and docstore already exist. Skipping embedding.")
            return

        logger.info("Loading files...")
        docs = load_files(DATA_DIR)
        logger.info(f"Loaded {len(docs)} files: {[doc['filename'] for doc in docs]}")

        logger.info("Chunking documents...")
        chunks = chunk_docs(docs)
        logger.info(f"Created {len(chunks)} chunks.")

        # Print chunk count per file
        from collections import Counter
        file_counts = Counter([chunk["filename"] for chunk in chunks])
        logger.info(f"Chunks per file: {file_counts}")

        logger.info("Embedding chunks...")
        embeddings = embed_chunks(chunks)

        logger.info("Building FAISS index...")
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        logger.info(f"Saving FAISS index to {INDEX_PATH}")
        faiss.write_index(index, INDEX_PATH)

        logger.info(f"Saving metadata to {DOCSTORE_PATH}")
        with open(DOCSTORE_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        logger.info("Done! Knowledge base is ready.")
        print("Done! Knowledge base is ready.")
    except Exception as e:
        logger.exception("Error in main chunk_and_embed process.")
        raise

if __name__ == "__main__":
    main()
